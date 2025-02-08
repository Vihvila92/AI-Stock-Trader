from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from app.database import get_management_db
from datetime import datetime
import json  # Add this import

router = APIRouter(prefix="/ws", tags=["WebSocket"])

# Active WebSocket connections
active_connections = {}

def log_event(db: Session, level: str, source: str, message: str, metadata: dict = None):
    """Log an event into the logs table in the database."""
    db.execute(text("""
        INSERT INTO logs (level, source, message, metadata)
        VALUES (:level, :source, :message, :metadata::json)
    """), {
        "level": level,
        "source": source,
        "message": message,
        "metadata": None if metadata is None else json.dumps(metadata)
    })
    db.commit()

@router.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Received: {data}")

@router.websocket("/agents/{agent_id}")
async def websocket_agent(websocket: WebSocket, agent_id: int, db: Session = Depends(get_management_db)):
    """
    WebSocket endpoint for agents to communicate with the Management System.
    """
    # Authenticate the agent before accepting the connection
    agent = db.execute(text("""
        SELECT id, name, status FROM agents WHERE id = :agent_id
    """), {"agent_id": agent_id}).fetchone()

    if not agent or agent["status"] != "active":
        log_event(
            db,
            level="WARNING",
            source=f"agent:{agent_id}",
            message="Unauthorized or inactive agent attempted to connect",
        )
        await websocket.close(code=1008)  # Policy violation
        raise HTTPException(status_code=403, detail="Unauthorized or inactive agent")

    # Accept the WebSocket connection
    await websocket.accept()
    active_connections[agent_id] = websocket
    log_event(
        db,
        level="INFO",
        source=f"agent:{agent_id}",
        message="WebSocket connection established",
        metadata={"agent_id": agent_id}
    )

    try:
        while True:
            # Wait for a message from the agent
            data = await websocket.receive_json()

            # Handle specific messages from the agent
            if data.get("type") == "status_update":
                # Update the agent's last seen and status in the database
                db.execute(text("""
                    UPDATE agents SET last_seen = :last_seen
                    WHERE id = :agent_id
                """), {"last_seen": datetime.utcnow(), "agent_id": agent_id})
                db.commit()

                log_event(
                    db,
                    level="INFO",
                    source=f"agent:{agent_id}",
                    message="Status update received",
                    metadata=data
                )

            elif data.get("type") == "task_complete":
                # Handle task completion (optional feature)
                log_event(
                    db,
                    level="INFO",
                    source=f"agent:{agent_id}",
                    message="Task completed",
                    metadata={"task_id": data.get("task_id")}
                )

            else:
                # Unknown message type
                log_event(
                    db,
                    level="WARNING",
                    source=f"agent:{agent_id}",
                    message="Unknown message received",
                    metadata=data
                )

    except WebSocketDisconnect:
        log_event(
            db,
            level="INFO",
            source=f"agent:{agent_id}",
            message="WebSocket connection closed by agent"
        )
        print(f"Agent {agent_id} disconnected")
        # Remove the connection from active connections
        if agent_id in active_connections:
            del active_connections[agent_id]
    except Exception as e:
        log_event(
            db,
            level="ERROR",
            source=f"agent:{agent_id}",
            message="WebSocket connection error",
            metadata={"error": str(e)}
        )
        print(f"Error with agent {agent_id}: {str(e)}")
        if agent_id in active_connections:
            del active_connections[agent_id]
        await websocket.close(code=1011)  # Internal server error
