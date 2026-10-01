# Base interface for all security detection rules.

from abc import ABC, abstractmethod
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession
from app.models.login_attempt import LoginAttempt
from app.models.security_event import SecurityEvent
from app.services.detection.result import DetectionResult

@dataclass(frozen=True)
class DetectionContext:
    """
    Structured input supplied to detection rules.

    A context may represent a security event, an authentication attempt, or both.
    Rules must ignore contexts that are not relevant to them.
    """
    event: SecurityEvent | None = None
    login_attempt: LoginAttempt | None = None

class DetectionRule(ABC):
    # Contract implemented by every detection rule.

    name: str

    @abstractmethod
    async def evaluate(
        self,
        db: AsyncSession,
        context: DetectionContext,
    ) -> DetectionResult:
        """
        Evaluate the supplied security context.

        Rules that do not apply to the supplied context should return DetectionResult.not_triggered().
        """
        raise NotImplementedError