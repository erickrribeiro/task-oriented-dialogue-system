import os
from typing import Literal, Optional, TypedDict

from langchain_core.prompt_values import PromptValue
from typing_extensions import Annotated

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from langchain_openai import ChatOpenAI

from src.database import get_user_by_id
from src.recommendation_system import simple_recommendation_system
from src.tools import load_tools
from src.persona import system_prompt_template as persona


class DialogStateTracking(TypedDict):
    """Dialogue State Tracking (DST) is useful for tracing user' belief state given dialogue"""

    language: Optional[str] = "Portuguese"
    user_info: Optional[dict] = dict()
    user_message: Optional[str] = None
    finished = False
    messages: Annotated[list, add_messages]


def domain_state_tracker(user_id: int, messages: list, language: str) -> PromptValue:
    user_info = get_user_by_id(id=user_id).to_dict(orient="records")
    return (
        persona.invoke(
            {
                "language": language,
                "user_info": user_info,
                "messages": messages,
            }
        ),
        user_info,
    )


# Nodes
def call_llm(state: DialogStateTracking, config: RunnableConfig) -> dict:
    configuration = config.get("configurable", dict())
    user_id = configuration.get("user_id")

    if not user_id:
        raise ValueError("No User ID configured.")

    messages, user_info = domain_state_tracker(
        user_id, state["messages"], state["language"]
    )
    ai_message = llm_with_tool.invoke(messages)
    if isinstance(ai_message, AIMessage) and ai_message.tool_calls:
        args = ai_message.tool_calls[0]["args"]
        print("\n\nARGS:", args)

    return {"messages": ai_message, "user_info": user_info}


def finalize_dialogue(state: DialogStateTracking):
    """
    Add a tool message to the history so the graph can see that it`s time to create the user story
    """
    language = state["language"]
    prompt = [
        HumanMessage(
            content=f"""
        Say you are generating a personalized notebook recommendation based on the information you have gathered.
        Please wait for a while.

        Respond in the {language} language.
        """
        )
    ]
    response = llm.invoke(prompt)

    return {"messages": [response]}


def generate_recommendation(state: DialogStateTracking) -> dict:
    messages = simple_recommendation_system(
        user_info=state["user_info"],
        messages=state["messages"],
        language=state["language"],
    )
    response = llm.invoke(messages)

    return {"messages": [response]}


def dialog_policy_learning(
    state: DialogStateTracking,
) -> Literal["finalize_dialogue", END]:
    """Dialogue Policy Learning (DPL) is responsable to determine the next step to take."""
    messages = state["messages"]

    if isinstance(messages[-1], AIMessage) and messages[-1].tool_calls:
        print("tool", messages[-1].tool_calls)
        if messages[-1].tool_calls[-1]["name"] == "SlotFilling":
            return "finalize_dialogue"
        else:
            return END
    else:
        return END


# Definindo o LLM

llm = ChatOpenAI(
    model="gpt-4o",
    openai_api_key=os.environ.get("OPENAI_API_KEY"),
    temperature=0,
)

tools = load_tools()
llm_with_tool = llm.bind_tools(tools)

# Definindo o grafo
workflow = StateGraph(DialogStateTracking)
workflow.add_node("agent", call_llm)

tool_node = ToolNode(tools=tools)
workflow.add_node("tools", tool_node)

workflow.add_node("finalize_dialogue", finalize_dialogue)
workflow.add_node("generate_recommendation", generate_recommendation)

# Definindo as conexões
workflow.add_edge(START, "agent")

workflow.add_conditional_edges("agent", tools_condition)
workflow.add_edge("tools", "agent")

workflow.add_conditional_edges("agent", dialog_policy_learning)
workflow.add_edge("finalize_dialogue", "generate_recommendation")
workflow.add_edge("generate_recommendation", END)

memory = MemorySaver()
graph = workflow.compile(checkpointer=memory)
