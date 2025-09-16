from datetime import datetime

from pydantic import BaseModel, EmailStr
from typing import Literal, Optional


class DNSRecord(BaseModel):
    name: str
    record_type: Literal["MX", "TXT", "CNAME"]
    value: str
    priority: Optional[int] = None
    
    def __repr__(self) -> str:
        return f"DNSRecord(name={self.name}, priority={self.priority}, record_type={self.record_type}, value={self.value})"

class InboxRecord(BaseModel):
    inbox_id: str
    email: str

class EmailRecord(BaseModel):
    from_email: str
    to_email: str
    subject: str
    body: str
    message_time: datetime

class IncomingEmailRecord(BaseModel):
    message_id: str
    sender: EmailStr
    recipient: EmailStr
    subject: str
    body: str
    reply_id: str
    timestamp: datetime