from datetime import datetime
from typing import List, Optional, Literal

from pydantic import BaseModel, EmailStr, Field
from common_types import InboxRecord

# --------- REQUESTS ---------
class CreateDomainRequest(BaseModel):
    domain: str

class CreateInboxRequest(BaseModel):
    email: EmailStr


class SendEmailRequest(BaseModel):
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

class EmailRecordMetadata(BaseModel):
    opened: bool
    thread_id: str

class EmailRecord(BaseModel):
    sender: EmailStr
    recipient: EmailStr
    subject: str
    body: str
    metadata: EmailRecordMetadata
    timestamp: datetime

class GetInboxResponse(BaseModel):
    emails: List[EmailRecord]

class ListInboxesResponse(BaseModel):
    inboxes: List[InboxRecord]
