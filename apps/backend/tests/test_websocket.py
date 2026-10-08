"""Tests for WebSocket authentication and connection management."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import WebSocket, WebSocketDisconnect
from starlette.datastructures import QueryParams

from app.api.v1.endpoints.websocket import (
    authenticate_websocket,
    websocket_events,
)
from app.core.websocket_manager import ConnectionManager


@pytest.mark.asyncio
async def test_connect_accepts_and_registers_connection() -> None:
    """Connecting should accept and register the WebSocket."""

    manager = ConnectionManager()
    websocket = AsyncMock()

    await manager.connect(websocket)

    websocket.accept.assert_awaited_once()
    assert websocket in manager.active_connections


def test_disconnect_removes_registered_connection() -> None:
    """Disconnecting should remove a registered WebSocket."""

    manager = ConnectionManager()
    websocket = AsyncMock()

    manager.active_connections.append(websocket)

    manager.disconnect(websocket)

    assert websocket not in manager.active_connections


def test_disconnect_ignores_unknown_connection() -> None:
    """Disconnecting an unknown WebSocket should be harmless."""

    manager = ConnectionManager()
    websocket = AsyncMock()

    manager.disconnect(websocket)

    assert manager.active_connections == []


@pytest.mark.asyncio
async def test_broadcast_sends_message_to_all_connections() -> None:
    """Broadcast should deliver the same message to every client."""

    manager = ConnectionManager()

    first = AsyncMock()
    second = AsyncMock()

    manager.active_connections.extend(
        [
            first,
            second,
        ]
    )

    message = {
        "type": "security_event",
        "event": {
            "id": 42,
        },
    }

    await manager.broadcast(message)

    first.send_json.assert_awaited_once_with(message)
    second.send_json.assert_awaited_once_with(message)

    assert manager.active_connections == [
        first,
        second,
    ]


@pytest.mark.asyncio
async def test_broadcast_removes_failed_connection_and_continues() -> None:
    """
    A failed client must not prevent healthy clients receiving messages.
    """

    manager = ConnectionManager()

    failed = AsyncMock()
    healthy = AsyncMock()

    failed.send_json.side_effect = RuntimeError(
        "Connection closed"
    )

    manager.active_connections.extend(
        [
            failed,
            healthy,
        ]
    )

    message = {
        "type": "security_event",
    }

    await manager.broadcast(message)

    failed.send_json.assert_awaited_once_with(message)
    healthy.send_json.assert_awaited_once_with(message)

    assert failed not in manager.active_connections
    assert healthy in manager.active_connections


@pytest.mark.asyncio
async def test_websocket_authentication_rejects_missing_token(
    db_session,
) -> None:
    """A WebSocket without a JWT must not authenticate."""

    websocket = AsyncMock(spec=WebSocket)
    websocket.query_params = QueryParams("")

    user = await authenticate_websocket(
        websocket,
        db_session,
    )

    assert user is None


@pytest.mark.asyncio
async def test_websocket_authentication_rejects_invalid_token(
    db_session,
) -> None:
    """An invalid JWT must not authenticate."""

    websocket = AsyncMock(spec=WebSocket)
    websocket.query_params = QueryParams(
        "token=invalid-token"
    )

    with patch(
        "app.api.v1.endpoints.websocket.decode_access_token",
        return_value=None,
    ):
        user = await authenticate_websocket(
            websocket,
            db_session,
        )

    assert user is None


@pytest.mark.asyncio
async def test_websocket_authentication_rejects_token_without_subject(
    db_session,
) -> None:
    """A JWT payload without a user subject must be rejected."""

    websocket = AsyncMock(spec=WebSocket)
    websocket.query_params = QueryParams(
        "token=test-token"
    )

    with patch(
        "app.api.v1.endpoints.websocket.decode_access_token",
        return_value={},
    ):
        user = await authenticate_websocket(
            websocket,
            db_session,
        )

    assert user is None


@pytest.mark.asyncio
async def test_websocket_authentication_rejects_invalid_user_id(
    db_session,
) -> None:
    """A non-numeric JWT subject must be rejected safely."""

    websocket = AsyncMock(spec=WebSocket)
    websocket.query_params = QueryParams(
        "token=test-token"
    )

    with patch(
        "app.api.v1.endpoints.websocket.decode_access_token",
        return_value={
            "sub": "not-a-user-id",
        },
    ):
        user = await authenticate_websocket(
            websocket,
            db_session,
        )

    assert user is None


@pytest.mark.asyncio
async def test_websocket_authentication_rejects_nonexistent_user(
    db_session,
) -> None:
    """A token for a nonexistent user must be rejected."""

    websocket = AsyncMock(spec=WebSocket)
    websocket.query_params = QueryParams(
        "token=test-token"
    )

    with patch(
        "app.api.v1.endpoints.websocket.decode_access_token",
        return_value={
            "sub": "999999999",
        },
    ):
        user = await authenticate_websocket(
            websocket,
            db_session,
        )

    assert user is None


@pytest.mark.asyncio
async def test_websocket_authentication_rejects_inactive_user(
    db_session,
    viewer_user,
) -> None:
    """An inactive user must not be allowed to subscribe."""

    viewer_user.is_active = False
    await db_session.flush()

    websocket = AsyncMock(spec=WebSocket)
    websocket.query_params = QueryParams(
        "token=test-token"
    )

    with patch(
        "app.api.v1.endpoints.websocket.decode_access_token",
        return_value={
            "sub": str(viewer_user.id),
        },
    ):
        user = await authenticate_websocket(
            websocket,
            db_session,
        )

    assert user is None


@pytest.mark.asyncio
async def test_websocket_authentication_accepts_active_user(
    db_session,
    viewer_user,
) -> None:
    """
    An active authenticated viewer may subscribe to live events.

    Live-event streaming is read-only operational access, so VIEWER
    is intentionally permitted.
    """

    websocket = AsyncMock(spec=WebSocket)
    websocket.query_params = QueryParams(
        "token=test-token"
    )

    with patch(
        "app.api.v1.endpoints.websocket.decode_access_token",
        return_value={
            "sub": str(viewer_user.id),
        },
    ):
        user = await authenticate_websocket(
            websocket,
            db_session,
        )

    assert user is not None
    assert user.id == viewer_user.id
    assert user.is_active is True


@pytest.mark.asyncio
async def test_websocket_endpoint_rejects_unauthenticated_connection() -> None:
    """Unauthenticated clients must be rejected before registration."""

    websocket = AsyncMock(spec=WebSocket)

    with patch(
        "app.api.v1.endpoints.websocket.authenticate_websocket",
        return_value=None,
    ), patch(
        "app.api.v1.endpoints.websocket.AsyncSessionLocal",
    ) as session_factory, patch(
        "app.api.v1.endpoints.websocket.manager",
    ) as websocket_manager:
        db = AsyncMock()

        session_factory.return_value.__aenter__.return_value = db
        websocket_manager.connect = AsyncMock()

        await websocket_events(websocket)

    websocket.close.assert_awaited_once_with(
        code=1008,
    )
    websocket_manager.connect.assert_not_awaited()


@pytest.mark.asyncio
async def test_websocket_endpoint_cleans_up_after_disconnect() -> None:
    """An authenticated connection must be removed after disconnecting."""

    websocket = AsyncMock(spec=WebSocket)
    authenticated_user = object()

    websocket.receive_text.side_effect = WebSocketDisconnect()

    with patch(
        "app.api.v1.endpoints.websocket.authenticate_websocket",
        return_value=authenticated_user,
    ), patch(
        "app.api.v1.endpoints.websocket.AsyncSessionLocal",
    ) as session_factory, patch(
        "app.api.v1.endpoints.websocket.manager",
    ) as websocket_manager:
        db = AsyncMock()

        session_factory.return_value.__aenter__.return_value = db
        websocket_manager.connect = AsyncMock()

        await websocket_events(websocket)

    websocket_manager.connect.assert_awaited_once_with(
        websocket
    )
    websocket_manager.disconnect.assert_called_once_with(
        websocket
    )