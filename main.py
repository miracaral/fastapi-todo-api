from fastapi import FastAPI

from routers.auth import router as auth_router
from routers.todo import router as todo_router

app = FastAPI(title="Todo API", description="FastAPI + SQLAlchemy REST API with JWT authentication")
app.include_router(auth_router)
app.include_router(todo_router)

# The schema is managed by Alembic: run `alembic upgrade head` before starting the app.


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}
