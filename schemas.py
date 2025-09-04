from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field

# --------- REQUESTS ---------
class CreateInboxRequest(BaseModel):
    email: EmailStr


class CreateInboxSessionRequest(BaseModel):
    ttl: int = Field(..., default=3600)


# --------- RESPONSES --------
class CreateInboxResponse(BaseModel):
    id: str
    session_token: str
    message: str


class CreateInboxSessionResponse(BaseModel):
    session_token: str
    expires_at: datetime
    message: str
