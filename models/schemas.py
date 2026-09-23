####schemas.py######

from pydantic import BaseModel, Field, field_validator
import re


class UserRegisterSchema(BaseModel):
    username: str = Field(..., min_length=3, max_length=20)
    email: str
    password: str = Field(..., min_length=8)
    role: str = "user"

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v):
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError(
                "Username must contain only letters, numbers, and underscores."
            )
        return v

    @field_validator("email")
    @classmethod
    def email_valid(cls, v):
        if not re.match(
            r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$",
            v
        ):
            raise ValueError("Please enter a valid email address.")

        return v.lower()

    @field_validator("password")
    @classmethod
    def password_complexity(cls, v):
        if not re.search(r"[A-Z]", v):
            raise ValueError(
                "Password must contain at least one uppercase letter."
            )

        if not re.search(r"[0-9]", v):
            raise ValueError(
                "Password must contain at least one number."
            )

        if not re.search(r"[@#$%^&*]", v):
            raise ValueError(
                "Password must contain at least one special character (@#$%^&*)."
            )

        return v

    @field_validator("role")
    @classmethod
    def role_valid(cls, v):
        v = v.lower()

        if v not in ("user", "admin"):
            raise ValueError("Role must be User or Admin.")

        return v


class HardwareSchema(BaseModel):
    item_name: str = Field(..., min_length=1, max_length=100)
    category: str = Field(..., min_length=1, max_length=50)
    quantity: int = Field(..., ge=0)
    unit_price: float = Field(..., ge=0)

    @field_validator("item_name", "category")
    @classmethod
    def text_not_blank(cls, v):
        if not v.strip():
            raise ValueError("This field cannot be blank.")

        return v.strip()
