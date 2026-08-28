from pydantic import BaseModel, EmailStr, Field


class ForgotPasswordIn(BaseModel):
    email: EmailStr


class ResetPasswordIn(BaseModel):
    token: str = Field(min_length=20, max_length=256)
    password: str = Field(min_length=8, max_length=128)


class VerifyEmailIn(BaseModel):
    token: str = Field(min_length=20, max_length=256)


class AuthMessageOut(BaseModel):
    status: str = "ok"
    message: str


class SessionOut(BaseModel):
    id: str
    current: bool = False
    is_active: bool
    expires_at: str
    created_at: str
