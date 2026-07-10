from abc import ABC, abstractmethod

from sqlalchemy.ext.asyncio import AsyncSession

class DetectionRule(ABC):

    name: str

    @abstractmethod
    async def evaluate(
        self,
        db: AsyncSession,
        context: dict
    ):
        pass