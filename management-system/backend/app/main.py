from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from app.routers import users, auth, websocket
from app.routers.api_management import router as management_router
import asyncio
from app.routers.api_agents import router as agents_router


app = FastAPI(
    title="Management System API",
    description="API with REST, WebSockets, and PostgreSQL",
    version="1.0.0",
    docs_url="/api/doc",           # Changed from /docs
    redoc_url="/api/redoc",        # Changed from /redoc
    openapi_url="/api/openapi.json" # Changed from /openapi.json
)

app.include_router(users.router)
app.include_router(auth.router)
app.include_router(websocket.router)
app.include_router(management_router, prefix="/api/management", tags=["Management"])
app.include_router(agents_router, prefix="/api/agents", tags=["Agents"])


# WebSocket client tracking
connected_clients = []

@app.get("/")
def root():
    return {"message": "Management System API is running!"}

@app.websocket("/ws/progress")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)
    try:
        while True:
            # Keep the connection alive or send real-time updates
            await asyncio.sleep(10)
    except WebSocketDisconnect:
        connected_clients.remove(websocket)
