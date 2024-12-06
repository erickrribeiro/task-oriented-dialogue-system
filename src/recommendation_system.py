from langchain_core.messages import AIMessage, ToolMessage, SystemMessage


def simple_recommendation_system(user_info: str, messages: list, language: str):
    prompt_generate_recommendations = """
        Você é capaz gerar uma lista de notebooks recomendados com base nas informações a seguir:

        [Preferências do Usuário]
        {user_info}

        [Informações sobre o Idioma]
        "Respond in the {lang} language."

        O utilize o histórico de conversas a seguir para melhor a recomendação
    """

    tool_call = None
    other_msgs = list()
    for message in messages:
        if isinstance(message, AIMessage) and message.tool_calls:
            tool_call = message.tool_calls[0]["args"]
        elif isinstance(message, ToolMessage):
            continue
        elif tool_call is not None:
            other_msgs.append(message)
    print(other_msgs)
    return [
        SystemMessage(
            content=prompt_generate_recommendations.format(
                user_info=user_info,
                reqs=tool_call,
                lang=language,
            )
        )
    ] + other_msgs
