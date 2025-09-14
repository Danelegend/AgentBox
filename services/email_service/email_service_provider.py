from adapters import EmailDeliveryPort
from storage import InboxStorageManager, EmailAccountStorage
from .email_service import IEmailService
from .compose import build_email_service

from typing import Dict

class EmailServiceProvider:
    def __init__(
        self,
        email_delivery: EmailDeliveryPort,
        inbox_storage_manager: InboxStorageManager,
        email_account_storage: EmailAccountStorage
    ):
        self.email_delivery = email_delivery
        self.inbox_storage_manager = inbox_storage_manager
        self.email_account_storage = email_account_storage
        
        self.email_services: Dict[str, IEmailService] = {}
    
    def get_by_inbox_id(self, inbox_id: str) -> IEmailService:
        if inbox_id not in self.email_services:
            self.email_services[inbox_id] = build_email_service(
                inbox_id=inbox_id,
                email_delivery=self.email_delivery,
                inbox_storage_manager=self.inbox_storage_manager,
                email_account_storage=self.email_account_storage
            )

        return self.email_services[inbox_id]

    def get_by_email(self, email: str) -> IEmailService:
        inbox_id = self.email_account_storage.get_inbox_id(email)
        
        if inbox_id is None:
            raise ValueError(f"No inbox found for {email}")
        
        return self.get_by_inbox_id(inbox_id)
