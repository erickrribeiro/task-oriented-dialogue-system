from pydantic import BaseModel, Field


class SlotFilling(BaseModel):
    """Information to generate a notebook recommendations."""

    client_name: str = Field(description="O nome do cliente.")
    age: int = Field(description="A idade do cliente.")
    goal: str = Field(
        description="Proposito de uso do computador: trabalho, estudo, jogos e similares"
    )
    ram: str = Field(description="Quanto de memoria RAM: 4GB, 8GB, 16GB ou 32GB")
    has_gpu: bool = Field(description="Precisa ter GPU (Yes/No)")


slots_description = """
    - Client name: the client's name
    - Age: the client's age
    - Goal: the primary purpose of the notebook (e.g., work, study, gaming)
    - RAM: the amount of RAM needed (e.g., 8GB, 16GB)"
    - need GPU: whether the client needs a dedicated GPU (Yes, No or Maybe)
"""
