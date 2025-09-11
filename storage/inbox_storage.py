"""
This is the persistance layer of the inbox storage
"""

from datetime import datetime
from typing import List

from pydantic import BaseModel

from storage_manager import StorageManager

class InboxSchema(BaseModel):
    email: str # Key for the inbox to associate this with
    from_email: str
    to_email: str
    subject: str
    body: str
    creation_time: datetime

INBOX_TABLE_NAME = "inbox"

class InboxStorageManager:
    def __init__(self, storage_manager: StorageManager):
        self.storage_manager = storage_manager

        self.storages: Dict[str, 'InboxStorage'] = {}

    def get_or_create_inbox_storage(email: str):
        if email not in self.storages:
            self.storages[email] = InboxStorage(email, self.storage_manager)

        return self.storages[email]


class InboxStorage:
    def __init__(self, email: str, storage_manager: StorageManager):
        self.email = email
        self.storage_manager = storage_manager

        self.storage_manager.create_table(INBOX_TABLE_NAME, InboxSchema)

    def save_email(
        self,
        from_email: str,
        to_email: str,
        subject: str,
        body: str,
        creation_time: datetime
    ):
        self.storage_manager.insert_entry(
            INBOX_TABLE_NAME,
            InboxSchema(
                email=self.email,
                from_email=from_email,
                to_email=to_email,
                subject=subject,
                body=body,
                creation_time=creation_time
            ).model_dump()
        )

    def get_emails(self) -> List[InboxSchema]:
        return self.storage_manager.read_entries(INBOX_TABLE_NAME)
