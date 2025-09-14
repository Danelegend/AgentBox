"""
This is the persistance layer of the inbox storage
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from storage import StorageManager

class InboxSchema(BaseModel):
    inbox_id: str # Key for the inbox to associate this with
    message_id: str # Unique id created for this message
    from_email: str
    to_email: str
    subject: str
    body: str
    timestamp: datetime
    reply_id: Optional[str] = None # Optional reference of who the email is replying to

INBOX_TABLE_NAME = "inbox"

class InboxStorageManager:
    def __init__(self, storage_manager: StorageManager):
        self.storage_manager = storage_manager

        self.storages: Dict[str, 'InboxStorage'] = {}

    def get_or_create_inbox_storage(self, inbox_id: str):
        if inbox_id not in self.storages:
            self.storages[inbox_id] = InboxStorage(inbox_id, self.storage_manager)

        return self.storages[inbox_id]


class InboxStorage:
    def __init__(self, inbox_id: str, storage_manager: StorageManager):
        self.inbox_id = inbox_id
        self.storage_manager = storage_manager

        self.storage_manager.create_table(INBOX_TABLE_NAME, InboxSchema)

    def save_email(
        self,
        message_id: str,
        from_email: str,
        to_email: str,
        subject: str,
        body: str,
        timestamp: datetime,
        reply_id: Optional[str] = None
    ):
        self.storage_manager.insert_entry(
            INBOX_TABLE_NAME,
            InboxSchema(
                inbox_id=self.inbox_id,
                message_id=message_id,
                from_email=from_email,
                to_email=to_email,
                subject=subject,
                body=body,
                timestamp=timestamp,
                reply_id=reply_id
            ).model_dump()
        )

    def get_emails(self) -> List[InboxSchema]:
        return self.storage_manager.read_entries(INBOX_TABLE_NAME)
