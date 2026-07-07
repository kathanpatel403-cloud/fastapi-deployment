from pydantic import BaseModel, EmailStr


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
