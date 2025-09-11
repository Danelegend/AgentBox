"""
Used to save email accounts
"""
from typing import Optional
from pydantic import BaseModel

from storage_manager import StorageManager

import logging
logger = logging.getLogger(__name__)

class EmailAccountSchema(BaseModel):
    email_id: str # id of the email account
    email: str

EMAIL_ACCOUNT_TABLE_NAME = "email_accounts"

class EmailAccountStorage:
    def __init__(self, storage_manager: StorageManager):
        self.storage_manager = storage_manager

        self.storage_manager.create_table(
            EMAIL_ACCOUNT_TABLE_NAME, 
            EmailAccountSchema,
            primary_id_column="email_id"
        )

    def save_account(self, email: str) -> str:
        """
        Returns a unique id for the email
        """
        result = self.storage_manager.insert_entry(
            EMAIL_ACCOUNT_TABLE_NAME,
            {
                "email": email
            }
        )

        return result.email_id

    def get_inboxes(self) -> List[str]:
        pass

    def get_email_address(self, inbox_id: str) -> str:
        pass

    def get_inbox_id(self, email: str) -> Optional[str]:
        entries = self.storage_manager.get_entry(
            EMAIL_ACCOUNT_TABLE_NAME,
            "email",
            email
        )

        if len(entries) == 0:
            return None

        if len(entries) > 1:
            logger.warn(f"Multiple ids for {email} found, amount={len(entries)}")

        return entries[0].email_id