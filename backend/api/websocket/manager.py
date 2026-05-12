
from fastapi import WebSocket


class ConnectionManager:
    """Manages WebSocket connections for judge status updates."""

    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, submission_id: str, websocket: WebSocket):
        """Connect a WebSocket client to a submission."""
        await websocket.accept()
        if submission_id not in self.active_connections:
            self.active_connections[submission_id] = []
        self.active_connections[submission_id].append(websocket)

    def disconnect(self, submission_id: str, websocket: WebSocket):
        """Disconnect a WebSocket client from a submission."""
        if submission_id in self.active_connections:
            if websocket in self.active_connections[submission_id]:
                self.active_connections[submission_id].remove(websocket)
            if not self.active_connections[submission_id]:
                del self.active_connections[submission_id]

    async def send_status_update(
        self,
        submission_id: str,
        status: str,
        progress: int = 0,
        current_testcase: int = 0,
        total_testcases: int = 0,
    ):
        """Send status update to all clients watching a submission."""
        if submission_id not in self.active_connections:
            return

        message = {
            "type": "status_update",
            "data": {
                "submission_id": submission_id,
                "status": status,
                "progress": progress,
                "current_testcase": current_testcase,
                "total_testcases": total_testcases,
            },
        }

        disconnected = []
        for connection in self.active_connections[submission_id]:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)

        for conn in disconnected:
            self.disconnect(submission_id, conn)

    async def send_result(
        self,
        submission_id: str,
        status: str,
        result: str | None = None,
        execute_time: int = 0,
        memory_used: int = 0,
        score: int = 0,
    ):
        """Send final result to all clients watching a submission."""
        if submission_id not in self.active_connections:
            return

        message = {
            "type": "result",
            "data": {
                "submission_id": submission_id,
                "status": status,
                "result": result,
                "execute_time": execute_time,
                "memory_used": memory_used,
                "score": score,
            },
        }

        disconnected = []
        for connection in self.active_connections[submission_id]:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)

        for conn in disconnected:
            self.disconnect(submission_id, conn)

    async def send_error(self, submission_id: str, message: str, code: str = "JUDGE_ERROR"):
        """Send error message to all clients watching a submission."""
        if submission_id not in self.active_connections:
            return

        error_message = {
            "type": "error",
            "data": {
                "message": message,
                "code": code,
            },
        }

        disconnected = []
        for connection in self.active_connections[submission_id]:
            try:
                await connection.send_json(error_message)
            except Exception:
                disconnected.append(connection)

        for conn in disconnected:
            self.disconnect(submission_id, conn)


manager = ConnectionManager()
