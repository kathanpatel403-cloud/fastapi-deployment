from typing import Any, Generic, TypeVar
from pydantic import BaseModel, EmailStr

T = TypeVar("T")


class StandardResponse(BaseModel, Generic[T]):
    data: T
    status: int
    message: str


class UserCreate(BaseModel):
    email: EmailStr
    name: str
    is_active: bool = True


class UserOut(BaseModel):
    id: int
    email: EmailStr
    name: str
    is_active: bool
    is_admin: bool

    class Config:
        from_attributes = True
