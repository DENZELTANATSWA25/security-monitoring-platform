"""Management of active WebSocket connections."""

from fastapi import WebSocket


class ConnectionManager:
    """Track active WebSocket clients and broadcast messages."""

    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []

    async def connect(
        self,
        websocket: WebSocket,
    ) -> None:
        """Accept and register a WebSocket connection."""

        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(
        self,
        websocket: WebSocket,
    ) -> None:
        """Remove a WebSocket connection if it is registered."""

        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(
        self,
        message: dict,
    ) -> None:
        """
        Broadcast a message to connected clients.

        Failed connections are removed without preventing delivery to healthy clients.
        """

        dead_connections: list[WebSocket] = []

        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                dead_connections.append(connection)

        for connection in dead_connections:
            self.disconnect(connection)


manager = ConnectionManager()