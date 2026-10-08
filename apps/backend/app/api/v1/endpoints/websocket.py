"""Authenticated WebSocket endpoints."""

from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
    status,
)

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.core.websocket_manager import manager
from app.db.session import AsyncSessionLocal
from app.models.user import User


router = APIRouter(
    tags=["Websocket"],
)


async def authenticate_websocket(
    websocket: WebSocket,
    db: AsyncSession,
) -> User | None:
    """
    Authenticate a WebSocket connection using its JWT query parameter.

    Returns the active user when authentication succeeds.
    """

    token = websocket.query_params.get("token")

    if not token:
        return None

    payload = decode_access_token(token)

    if not payload:
        return None

    user_id = payload.get("sub")

    if not user_id:
        return None

    try:
        parsed_user_id = int(user_id)
    except (TypeError, ValueError):
        return None

    user = await db.get(
        User,
        parsed_user_id,
    )

    if user is None or not user.is_active:
        return None

    return user


@router.websocket("/ws/events")
async def websocket_events(
    websocket: WebSocket,
) -> None:
    """Stream live security-event notifications to authenticated users."""

    async with AsyncSessionLocal() as db:
        user = await authenticate_websocket(
            websocket,
            db,
        )

    if user is None:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
        )
        return

    await manager.connect(websocket)

    try:
        while True:
            # Waiting for client messages also lets us detect disconnects.
            await websocket.receive_text()

    except WebSocketDisconnect:
        pass

    finally:
        manager.disconnect(websocket)