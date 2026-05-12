
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

    async def broadcast_event(self, submission_id: str, event_type: str, data: dict):
        if event_type == "result":
            await self.send_result(
                submission_id,
                data.get("status", "finished"),
                result=data.get("result"),
                execute_time=data.get("execute_time", 0),
                memory_used=data.get("memory_used", 0),
                score=data.get("score", 0),
            )
        elif event_type == "error":
            await self.send_error(
                submission_id,
                data.get("message", "Judge error"),
                data.get("code", "JUDGE_ERROR"),
            )
        else:
            await self.send_status_update(
                submission_id,
                data.get("status", event_type),
                progress=data.get("progress", 0),
                current_testcase=data.get("current_testcase", 0),
                total_testcases=data.get("total_testcases", 0),
            )

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
