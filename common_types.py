from pydantic import BaseModel
from typing import Literal, Optional


class DNSRecord(BaseModel):
    name: str
    record_type: Literal["MX", "TXT", "CNAME"]
    value: str
    priority: Optional[int] = None
    
    def __repr__(self) -> str:
        return f"DNSRecord(name={self.name}, priority={self.priority}, record_type={self.record_type}, value={self.value})"