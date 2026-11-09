import os
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from starlette import status

from database import get_db
from models import User

router = APIRouter(prefix="/auth", tags=["Authentication"])

# The signing key comes from the environment (.env), never from the source code.
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is not set. Copy .env.example to .env and set a random value.")
ALGORITHM = "HS256"
ACCESS_TOKEN_MINUTES = 60

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="/auth/token")

db_dependency = Annotated[Session, Depends(get_db)]


class CreateUserRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    first_name: str
    last_name: str
    password: str = Field(min_length=8)
    phone_number: str | None = None
    # No "role" field: a user must not be able to make themselves an admin at sign-up.


class Token(BaseModel):
    access_token: str
    token_type: str


def create_access_token(username: str, user_id: int, role: str, expires_delta: timedelta) -> str:
    payload = {"sub": username, "id": user_id, "role": role,
               "exp": datetime.now(timezone.utc) + expires_delta}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def authenticate_user(username: str, password: str, db: Session):
    user = db.query(User).filter(User.username == username).first()
    if not user or not bcrypt_context.verify(password, user.hashed_password):
        return None
    return user


async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]) -> dict:
    unauthorized = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                 detail="Could not validate credentials",
                                 headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise unauthorized
    username, user_id = payload.get("sub"), payload.get("id")
    if username is None or user_id is None:
        raise unauthorized
    # A dict (key: value). The original code used commas here, which built a set and broke every protected route.
    return {"username": username, "id": user_id, "role": payload.get("role")}


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency, create_user_request: CreateUserRequest):
    taken = db.query(User).filter((User.username == create_user_request.username) |
                                  (User.email == create_user_request.email)).first()
    if taken:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username or email already registered")
    user = User(
        username=create_user_request.username,
        email=create_user_request.email,
        first_name=create_user_request.first_name,
        last_name=create_user_request.last_name,
        role="user",
        is_active=True,
        hashed_password=bcrypt_context.hash(create_user_request.password),
        phone_number=create_user_request.phone_number,
    )
    db.add(user)
    db.commit()
    return {"id": user.id, "username": user.username}


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependency):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password",
                            headers={"WWW-Authenticate": "Bearer"})
    token = create_access_token(user.username, user.id, user.role, timedelta(minutes=ACCESS_TOKEN_MINUTES))
    return {"access_token": token, "token_type": "bearer"}
