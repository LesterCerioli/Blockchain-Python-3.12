from abc import ABC, abstractmethod

from ..entities.tokenization_choice import TokenizationChoice


class IChoiceRepository(ABC):
    @abstractmethod
    async def save(self, choice: TokenizationChoice) -> None:
        ...

    @abstractmethod
    async def list_by_user(self, user_id: str) -> list[TokenizationChoice]:
        ...

    @abstractmethod
    async def get_by_id(self, user_id: str, choice_id: str) -> TokenizationChoice | None:
        ...
