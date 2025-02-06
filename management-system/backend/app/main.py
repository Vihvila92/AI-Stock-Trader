from fastapi import FastAPI
from app.routers import users, auth, websocket

app = FastAPI(
    title="Management System API",
    description="API with REST, WebSockets, and PostgreSQL",
    version="1.0.0"
)

app.include_router(users.router)
app.include_router(auth.router)
app.include_router(websocket.router)

@app.get("/")
def root():
    return {"message": "Management System API is running!"}
