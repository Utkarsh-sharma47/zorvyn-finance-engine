from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import Department, Role


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    department: Department
    role: Role


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    department: Department
    role: Role
    is_active: bool
