from adapters import EmailDeliveryPort
from storage import InboxStorageManager, EmailAccountStorage

from common_types import EmailRecord

from typing import Protocol, Callable, List
from datetime import datetime

import logging
logger = logging.getLogger(__name__)


class IEmailService(Protocol):
    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str
    ): 
        ...

    def on_received_email(self, received_email_callback: Callable):
        ...

    def get_emails(self) -> List[EmailRecord]:
        ...


class EmailService(IEmailService):
    def __init__(
        self,
        inbox_id: str,
        email_delivery: EmailDeliveryPort,
        inbox_storage_manager: InboxStorageManager,
        email_account_storage: EmailAccountStorage
    ):
        logger.info(f"Initializing email service for {inbox_id}")
        self.inbox_id = inbox_id
        self.email_delivery = email_delivery
                
        # Load the email from inbox_id
        self.email = email_account_storage.get_email_address(inbox_id)
        logger.info(f"Email loaded for {inbox_id} with email={self.email}")

        self.storage = inbox_storage_manager.get_or_create_inbox_storage(self.email)
        logger.info(f"Email service initialized for {inbox_id}")

    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str
    ): 
        logger.info(f"Sending email from {self.email} to {to_email}")
        email_sent = self.email_delivery.send_email(
            self.email,
            to_email,
            subject, body
        )

        if not email_sent:
            logger.error(f"Failure sending email")
            return False
        
        # Save to inbox
        self.storage.save_email(
            from_email=self.email,
            to_email=to_email,
            subject=subject,
            body=body,
            creation_time=datetime.now()
        )

        return True

    def on_received_email(self, received_email_callback: Callable):
        ...

    def get_emails(self) -> List[EmailRecord]:
        emails = self.inbox_storage.get_emails()

        return [
            EmailRecord(
                from_email=record.from_email,
                to_email=record.to_email,
                subject=record.subject,
                body=record.body,
                message_time=record.creation_time,
            ) for record in emails
        ]

