from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from starlette import status

from database import get_db
from models import Todo
from routers.auth import get_current_user

router = APIRouter(prefix="/todo", tags=["Todo"])

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


class TodoRequest(BaseModel):
    title: str = Field(min_length=3)
    description: str = Field(min_length=3, max_length=1000)
    priority: int = Field(gt=0, lt=6)
    completed: bool = False


def get_own_todo(db: Session, todo_id: int, user: dict) -> Todo:
    """Every lookup filters by owner, so another user's todo is simply "not found" (no IDOR)."""
    todo = db.query(Todo).filter(Todo.id == todo_id, Todo.owner_id == user["id"]).first()
    if todo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    return todo


@router.get("/", status_code=status.HTTP_200_OK)
async def read_all(user: user_dependency, db: db_dependency):
    return db.query(Todo).filter(Todo.owner_id == user["id"]).all()


@router.get("/{todo_id}", status_code=status.HTTP_200_OK)
async def read_by_id(user: user_dependency, db: db_dependency, todo_id: int = Path(gt=0)):
    return get_own_todo(db, todo_id, user)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_todo(user: user_dependency, db: db_dependency, todo_request: TodoRequest):
    todo = Todo(**todo_request.model_dump(), owner_id=user["id"])
    db.add(todo)
    db.commit()
    db.refresh(todo)
    return todo


@router.put("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_todo(user: user_dependency, db: db_dependency, todo_request: TodoRequest,
                      todo_id: int = Path(gt=0)):
    todo = get_own_todo(db, todo_id, user)
    for field, value in todo_request.model_dump().items():
        setattr(todo, field, value)
    db.commit()


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(user: user_dependency, db: db_dependency, todo_id: int = Path(gt=0)):
    todo = get_own_todo(db, todo_id, user)
    db.delete(todo)
    db.commit()
