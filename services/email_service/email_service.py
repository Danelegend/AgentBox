from adapters import EmailDeliveryPort
from storage import InboxStorageManager, EmailAccountStorage

from common_types import EmailRecord, IncomingEmailRecord

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
    
    def handle_incoming_email(self, incoming_email: IncomingEmailRecord):
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
        try:
            email_id = self.email_delivery.send_email(
                self.email,
                to_email,
                subject, body
            )
        except Exception as e:
            logger.error(f"Failure sending email, error={e}")
            return False

        # Save to inbox
        self.storage.save_email(
            message_id=email_id,
            from_email=self.email,
            to_email=to_email,
            subject=subject,
            body=body,
            timestamp=datetime.now()
        )

        return True
    
    def handle_incoming_email(self, incoming_email: IncomingEmailRecord):
        logger.info(f"Handling incoming email from {incoming_email.sender} to {incoming_email.recipient}")
        
        self.storage.save_email(
            message_id=incoming_email.message_id,
            from_email=incoming_email.sender,
            to_email=incoming_email.recipient,
            subject=incoming_email.subject,
            body=incoming_email.body,
            timestamp=incoming_email.timestamp,
            reply_id=incoming_email.reply_id
        )

    def on_received_email(self, received_email_callback: Callable):
        ...

    def get_emails(self) -> List[EmailRecord]:
        emails = self.storage.get_emails()

        return [
            EmailRecord(
                from_email=record.from_email,
                to_email=record.to_email,
                subject=record.subject,
                body=record.body,
                message_time=record.timestamp,
            ) for record in emails
        ]

