from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl, field_validator


class LookupRequest(BaseModel):
    email: EmailStr


class LookupResponse(BaseModel):
    exists: bool
    is_verified: Optional[bool] = None
    status: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    access_token_expires_at: datetime
    public_id: str
    email: EmailStr
    name: str
    tier: str = "local"


class RefreshRequest(BaseModel):
    refresh_token: Optional[str] = None


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    plan_key: Optional[str] = None
    plan_path: Optional[str] = None
    next: Optional[str] = None
    utm: Optional[dict] = None


class SendVerificationRequest(BaseModel):
    email: EmailStr


class MagicLinkRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class ConfirmEmailRequest(BaseModel):
    token: str


class ConfirmEmailResponse(BaseModel):
    ok: bool
    first_verification: bool | None = None
    plan_key: Optional[str] = None
    plan_path: Optional[str] = None
    next: Optional[str] = None
    email: Optional[EmailStr] = None
    user_id: Optional[str] = None


class AccountProfileResponse(BaseModel):
    id: str
    public_id: str
    email: EmailStr
    name: str
    is_verified: bool
    created_at: Optional[datetime]
    tier_key: Optional[str] = "local"
    tier_label: Optional[str] = "Local"


class UpdateProfileRequest(BaseModel):
    name: str


class DeleteAccountRequest(BaseModel):
    token: str


class ContactRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)

    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    message: str = Field(..., min_length=5, max_length=3000)
    topic: Optional[str] = Field(default=None, max_length=50)
    company: Optional[str] = Field(default=None, max_length=150)
    mobile: Optional[str] = Field(default=None, max_length=50)
    page_url: Optional[HttpUrl] = Field(default=None, alias="pageUrl")
    user_id: Optional[str] = Field(default=None, alias="userId")
    user_plan: Optional[str] = Field(default=None, alias="userPlan")
    plan_key: Optional[str] = Field(default=None, alias="planKey")
    honeypot: Optional[str] = Field(default=None, alias="website")

    @field_validator("message")
    @classmethod
    def message_not_empty(cls, value: str) -> str:
        if not value or len(value.strip()) < 5:
            raise ValueError("Message is too short")
        return value


class NewsletterSubscribeRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)

    email: EmailStr
    name: Optional[str] = Field(default=None, max_length=150)
    source: Optional[str] = Field(default=None, max_length=50)
    page_url: Optional[HttpUrl] = Field(default=None, alias="pageUrl")
    user_id: Optional[str] = Field(default=None, alias="userId")
    user_plan: Optional[str] = Field(default=None, alias="userPlan")
    honeypot: Optional[str] = Field(default=None, alias="website")


class NewsletterUnsubscribeRequest(BaseModel):
    token: str = Field(..., min_length=10, max_length=400)
    reason: Optional[str] = Field(default=None, max_length=500)


class GoogleAuthLoginRequest(BaseModel):
    credential: str


class GoogleLinkConfirmRequest(BaseModel):
    token: str


class GoogleAuthExchangeResponse(BaseModel):
    status: Literal["linked", "created", "link_required"]
    login: Optional[LoginResponse] = None
    link_token: Optional[str] = None
    email: Optional[EmailStr] = None
    existing_name: Optional[str] = None
    google_name: Optional[str] = None


class Pagination(BaseModel):
    total: int
    limit: int
    offset: int


class AdminUser(BaseModel):
    id: str
    public_id: str
    name: str
    email: str
    is_verified: bool
    deleted: bool
    created_at: datetime
    last_login_at: Optional[datetime]


class AdminUserSummary(BaseModel):
    total_users: int
    active_today: int


class AdminUserListResponse(BaseModel):
    users: List[AdminUser]
    summary: AdminUserSummary
    pagination: Pagination
