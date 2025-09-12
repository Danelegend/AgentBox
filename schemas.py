from datetime import datetime
from typing import List, Optional, Literal

from pydantic import BaseModel, EmailStr, Field

# --------- REQUESTS ---------
class CreateDomainRequest(BaseModel):
    domain: str

class CreateInboxRequest(BaseModel):
    email: EmailStr


class SendEmailRequest(BaseModel):
    inbox_id: str
    to_email: EmailStr
    subject: str
    body: str

# --------- RESPONSES --------
class CreateDomainResponse(BaseModel):
    domain: str
    status: Literal["pending", "verified"]

class CreateInboxResponse(BaseModel):
    id: str
    message: str


class CreateInboxSessionResponse(BaseModel):
    session_token: str
    expires_at: datetime
    message: str
