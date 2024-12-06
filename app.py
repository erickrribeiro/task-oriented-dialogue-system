import os
from collections import defaultdict

import streamlit as st
from langchain_core.messages import ToolMessage, AIMessage
from openai import OpenAI

from src.database import (
    create_database,
    get_user_by_id,
    create_or_update_user,
    delete_user_by_id,
)

if "run_database" not in st.session_state:
    st.session_state["run_database"] = True

if st.session_state["run_database"]:
    create_database()
    st.session_state["run_database"] = False
if "start" not in st.session_state:
    st.session_state["start"] = True


def start_or_stop_conversation() -> None:
    state = st.session_state["start"]
    if state:
        st.session_state["start"] = False
    else:
        user_id = st.session_state["user_id"]
        create_or_update_user(user_id)
        st.session_state["start"] = True


@st.fragment(run_every="5s")
def user_info_fragment():
    with st.status("Loading User Info...", expanded=True):
        user_id = st.session_state["user_id"]
        df = get_user_by_id(id=user_id)
        st.dataframe(df, key="user_info")


with st.sidebar:
    st.subheader("Configurations")
    if "OPENAI_API_KEY" not in os.environ:
        openai_api_key = st.text_input(
            "OpenAI API Key", key="chatbot_api_key", type="password"
        )
        "[Get a OPENAI API key](https://platform.openai.com/account/api-keys)"
    else:
        openai_api_key = os.environ["OPENAI_API_KEY"]

    debug = st.toggle(
        label="Enable Debug",
        value=True,
        disabled=st.session_state["start"],
    )

    st.divider()
    st.text_input(
        "Choose your ID:",
        value=1,
        disabled=st.session_state["start"],
        key="user_id",
    )
    languages = [
        "Portuguese",
        "English",
        "Spanish",
        "French",
        "German",
        "Chinese",
        "Japanese",
        "Korean",
    ]
    selected_language = st.selectbox(
        label="Choose your preferred language:",
        options=languages,
        disabled=st.session_state["start"],
    )
    st.write(st.session_state.start)
    button_label = "Encerrar Chat" if st.session_state["start"] else "Iniciar Chat"
    st.button(
        button_label,
        type="secondary",
        use_container_width=True,
        key="btn_start",
        on_click=start_or_stop_conversation,
    )

    if st.button(label="Apagar Usuário", use_container_width=True, type="primary"):
        deleted = delete_user_by_id(id=st.session_state["user_id"])
        st.toast("User: " + st.session_state["user_id"] + str(deleted))

    st.divider()
    if st.session_state["start"]:
        user_info_fragment()

if "messages" not in st.session_state:
    user_id = st.session_state["user_id"]
    st.session_state["messages"] = defaultdict(list)
    st.session_state["messages"][user_id] = [
        {"role": "assistant", "content": "Como eu posso ajudar?"}
    ]

if "sensitive_check" not in st.session_state:
    st.session_state["sensitive_check"] = False

global last_event

if not st.session_state["start"]:
    st.write(
        'Clique no botão "Iniciar Conversa" para conversar com o vendedor automático.'
    )
    st.stop()

st.title("💬 Assistente de Vendas!")

user_id = st.session_state["user_id"]
for message in st.session_state["messages"][user_id]:
    st.chat_message(message["role"]).write(message["content"])

if prompt := st.chat_input(placeholder="Converse com o vendedor automático..."):
    if not openai_api_key:
        st.info("Por favor, adicione sua chave da OpenAI para continuar.")
        st.stop()
    else:
        os.environ["OPENAI_API_KEY"] = openai_api_key
        from src.agent import graph

        config = {
            "configurable": {
                "thread_id": "session_" + user_id,
                "user_id": user_id,
            },
        }
        snapshot = graph.get_state(config)

        if not snapshot.next or st.session_state["sensitive_check"]:
            client = OpenAI(api_key=openai_api_key)
            st.session_state["messages"][user_id].append(
                {"role": "user", "content": prompt}
            )
            st.chat_message("user").write(prompt)
            events = graph.stream(
                input={
                    "user_message": prompt,
                    "messages": [("user", prompt)],
                    "language": selected_language,
                },
                config=config,
                stream_mode="values",
            )
            if not st.session_state["sensitive_check"]:
                for event in events:
                    st.session_state["event"] = event
                    if isinstance(event["messages"][-1], ToolMessage):
                        msg = event["messages"][-1].content
                        if debug:
                            st.session_state["messages"][user_id].append(
                                {"role": "assistant", "content": msg}
                            )
                            st.chat_message("", avatar="🧰").write(msg)

                    elif isinstance(event["messages"][-1], AIMessage):
                        if tools := event["messages"][-1].additional_kwargs.get(
                            "tool_calls"
                        ):
                            for tool in tools:
                                name = tool["function"]["name"]
                                args = tool["function"]["arguments"]
                                if debug:
                                    msg = f"Chamando a função {name} com os argumentos {args}"
                                    st.session_state["messages"][user_id].append(
                                        {"role": "assistant", "content": msg}
                                    )
                                    st.chat_message("", avatar="🧰").write(msg)
                        else:
                            msg = event["messages"][-1].content
                            st.session_state["messages"][user_id].append(
                                {"role": "assistant", "content": msg}
                            )
                            st.chat_message("assistant").write(msg)

            if st.session_state["sensitive_check"]:
                if prompt.strip() == "yes":
                    result = graph.invoke(
                        None,
                        config,
                    )
                else:
                    result = graph.invoke(
                        {
                            "messages": [
                                ToolMessage(
                                    tool_call_id=st.session_state["event"]["messages"][
                                        -1
                                    ].tool_calls[0]["id"],
                                    content=f"API call denied by user. Reasoning: '{prompt}'. Continue assisting, "
                                    f"accounting for the user's input.",
                                )
                            ]
                        },
                        config,
                    )
                msg = result["messages"][-1].content
                st.session_state["messages"][user_id].append(
                    {"role": "assistant", "content": msg}
                )
                st.chat_message("assistant").write(msg)
                st.session_state["sensitive_check"] = False
            snapshot = graph.get_state(config)
            if snapshot.next and not st.session_state["sensitive_check"]:
                sensitive_check = (
                    "Do you approve of the above actions? Type 'yes' to continue;"
                    " otherwise, explain the requested change.\n\n"
                )
                st.session_state["messages"][user_id].append(
                    {"role": "assistant", "content": sensitive_check}
                )
                st.chat_message("assistant").write(sensitive_check)
                st.session_state["sensitive_check"] = True

        with st.sidebar:
            st.divider()
