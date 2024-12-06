from langchain_core.tools import tool
from langchain_core.runnables.config import RunnableConfig

from src.database import create_or_update_user, get_user_by_id
from src.slot_filling import SlotFilling


@tool("inform_name")
def inform_name(client_name: str, config: RunnableConfig) -> str:
    """Salva o nome do cliente que você está conversando."""

    configuration = config.get("configurable", dict())
    user_id = configuration.get("user_id")

    if not user_id:
        raise ValueError("No User ID configured.")

    create_or_update_user(id=user_id, name=client_name)
    user = get_user_by_id(id=user_id)

    return user.to_string(index=False)


@tool("inform_age")
def inform_age(age: int, config: RunnableConfig) -> str:
    """Salva a idade do cliente que você está conversando."""

    configuration = config.get("configurable", dict())
    user_id = configuration.get("user_id")

    if not user_id:
        raise ValueError("No User ID configured.")

    create_or_update_user(id=user_id, age=age)
    user = get_user_by_id(id=user_id)

    return user.to_string(index=False)


@tool("inform_objective")
def inform_goal(description: str, config: RunnableConfig) -> str:
    """Salva o objetivo ou proposito de uso do notebook (trabalho, estudo, jogos e outros)"""

    configuration = config.get("configurable", dict())
    user_id = configuration.get("user_id")

    if not user_id:
        raise ValueError("No User ID configured.")

    create_or_update_user(id=user_id, goal=description)
    user = get_user_by_id(id=user_id)

    return user.to_string(index=False)


@tool("inform_ram")
def inform_ram(capacity: str, config: RunnableConfig) -> str:
    """Salva a capacidade de memória RAM desejada: 4GB, 8GB, 16GB ou 32GB"""

    configuration = config.get("configurable", dict())
    user_id = configuration.get("user_id")

    if not user_id:
        raise ValueError("No User ID configured.")

    create_or_update_user(id=user_id, ram=capacity)
    user = get_user_by_id(id=user_id)

    return user.to_string(index=False)


@tool("inform_gpu")
def inform_gpu(needs_gpu: str, config: RunnableConfig) -> str:
    """Salva se o computador precisa ter GPU (Sim, Não ou Talvez)"""

    configuration = config.get("configurable", dict())
    user_id = configuration.get("user_id")

    if not user_id:
        raise ValueError("No User ID configured.")

    create_or_update_user(id=user_id, needs_gpu=needs_gpu)
    user = get_user_by_id(id=user_id)

    return user.to_string(index=False)


@tool("get_info")
def get_info(config: RunnableConfig) -> str:
    """
    Retorna todas as informações do client que você está conversando: nome, idade, uso do notebook e outras coisas
    """

    configuration = config.get("configurable", dict())
    user_id = configuration.get("user_id")

    if not user_id:
        raise ValueError("No User ID configured.")

    user = get_user_by_id(id=user_id)

    return user.to_string(index=False)


def load_tools() -> list:
    return [
        inform_name,
        inform_age,
        inform_goal,
        inform_ram,
        inform_gpu,
        get_info,
        SlotFilling,
    ]
