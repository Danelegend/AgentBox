from pydantic import BaseModel
from typing import Protocol, Tuple, Optional, List
from adapters import EmailDeliveryPort, DnsPort
from storage import EmailAccountStorage
from services.errors import (
    DomainVerificationError,
    UserCreationError,
    UserNotFoundError
)
from util.domain_utils import parse_email, split_domain

import logging
logger = logging.getLogger(__name__)

class CreateInboxResult(BaseModel):
    id: str
    message: str


class IInboxService(Protocol):
    def create_inbox(self, email: str) -> CreateInboxResult:
        """
        Creates an inbox with the provided email
        """
        ...
    
    def get_inbox(self, email: str) -> str:
        """
        Gets the inbox id from a given email
        """
        ...

    def list_inboxes(self, domain: Optional[str] = None) -> List[str]:
        """
        Gets all the inboxes on a given domain
        """
        ...

    def delete_inbox(self, inbox_id: str) -> bool:
        """
        Deletes an inbox with the given inbox_id
        """
        ...


class InboxService(IInboxService):
    def __init__(
        self,
        email_delivery: EmailDeliveryPort,
        email_account_storage: EmailAccountStorage
    ):
        self.email_delivery = email_delivery
        self.email_account_storage = email_account_storage
    
    def create_inbox(self, email: str) -> CreateInboxResult:
        local, domain = parse_email(email)
        sub, apex = split_domain(domain)

        # Check that the domain exists
        if not self.email_delivery.subdomain_exists(sub, apex):
            raise ValueError(f"Subdomain {sub}.{apex} does not exist")
        
        # Create user
        inbox_id = _create_user_email(local, domain, self.email_delivery, self.email_account_storage)

        return CreateInboxResult(
            id=inbox_id,
            message="inbox created"
        )
    
    def get_inbox(self, email: str) -> Optional[str]:
        return self.email_account_storage.get_inbox_id(email)

    def list_inboxes(self, domain: Optional[str] = None) -> List[str]:
        ...

    def delete_inbox(self, inbox_id: str) -> bool:
        email = self.email_account_storage.get_email_address(inbox_id)

        local, domain = parse_email(email)

        result = self.email_delivery.delete_user(local, domain)

        return result


def _create_user_email(local: str, domain: str, email_delivery: EmailDeliveryPort, email_account_storage: EmailAccountStorage) -> str:
    password = email_delivery.create_user(local, domain)
    if not password:
        raise UserCreationError(f"Failed to create user on {domain}")
    
    inbox_id = email_account_storage.save_account(f"{local}@{domain}")
    
    return inbox_id

