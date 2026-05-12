from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from backend.api.websocket.manager import manager
from backend.core.database import get_db

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/judge/{submission_id}")
async def judge_status_websocket(
    websocket: WebSocket,
    submission_id: str,
    token: str,
    db: Session = Depends(get_db),
):
    """WebSocket endpoint for real-time judge status updates."""
    # Validate token
    try:
        from backend.core.security import decode_token
        payload = decode_token(token)
        if payload.get("type") != "access":
            await websocket.close(code=4003)
            return
    except Exception:
        await websocket.close(code=4003)
        return

    await manager.connect(submission_id, websocket)
    try:
        while True:
            # Keep connection alive, wait for messages
            data = await websocket.receive_text()
            # Handle any client messages if needed
    except WebSocketDisconnect:
        manager.disconnect(submission_id, websocket)
