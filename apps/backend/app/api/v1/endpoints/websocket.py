from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.websocket_manager import manager

router = APIRouter(
    tags=["Websocket"]
)

@router.websocket("/ws/events")
async def websocket_events(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            #Keep the connection alive by waiting for client mesaage
            await websocket.receive_text()

    except WebSocketDisconnect:
        manager.disconnect(websocket)