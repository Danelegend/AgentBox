import time
from enum import Enum
from pydantic import BaseModel
from typing import Tuple, Callable, Optional, Literal
from adapters import EmailDeliveryPort, DnsPort
from services.errors import (
    DomainAccessError,
    SubdomainCreationError,
    DomainVerificationError,
    UserCreationError,
    UserNotFoundError
)
from services.inbox_service.dns_verifier import DnsVerifier
from util.domain_utils import parse_email, split_domain


import logging
logger = logging.getLogger(__name__)

class CreateInboxResult(BaseModel):
    id: str
    message: str
    session_token: str | None = None
    
class LoadInboxResult(BaseModel):
    id: str
    message: str
    session_token: str | None = None

class CreateDomainResult(BaseModel):
    domain: str
    status: Literal["pending", "verified"]

class InboxService:
    def __init__(
        self,
        email_delivery: EmailDeliveryPort,
        dns: DnsPort
    ):
        self.email_delivery = email_delivery
        self.dns = dns
        
        self.dns_verifier = DnsVerifier(email_delivery)
    
    def create_domain(self, domain: str, verified_callback: Optional[Callable[[], None]] = None):
        """
        Creates the domain on the DNS and EDS
        """
        sub, apex = split_domain(domain)
        
        # Can we see the apex DNS
        try:
            self.dns.exists_records(apex, sub or "@")
        except Exception as e:
            raise DomainAccessError(str(e))
        
        # Create the subdomain on DNS + EDS
        if sub:
            domain_valid = self._create_subdomain(sub, apex, verified_callback)
        else:
            raise NotImplementedError("Not yet implemented for apex domains")

        return CreateDomainResult(
            domain=domain,
            status="verified" if domain_valid else "pending"
        )

    def is_domain_verified(self, domain: str) -> bool:
        # If the EDS says that the domain is verified, then we can send emails successfully
        success = self.email_delivery.verify_domain(domain)
        
        return success

    def create_inbox(self, email: str) -> CreateInboxResult:
        """
        Assumes that the domain exists
        """
        local, domain_full = parse_email(email)
        sub, apex = split_domain(domain_full)
        
        # Check that the domain exists
        if not self.email_delivery.subdomain_exists(sub, apex):
            raise ValueError(f"Subdomain {sub}.{apex} does not exist")            

        # Create user 
        inbox_id, session_token = self._create_user_email(local, domain_full)
        
        return CreateInboxResult(
            id=inbox_id,
            message="inbox created (stub)",
            session_token=session_token
        )
        
    def load_inbox(self, email: str) -> LoadInboxResult:
        local, domain_full = parse_email(email)
        sub, apex = split_domain(domain_full)
        
        # Check that the inbox exists
        users = self.email_delivery.get_users(domain_full)
        if email not in users:
            raise UserNotFoundError(f"User {email} not found")
        
        # Check that the inbox is verified
        if not self.email_delivery.verify_domain(domain_full):
            raise DomainVerificationError(f"Domain {domain_full} not verified")
        
        # Create session
        inbox_id = f"inbox_{local}_{domain_full}"
        session_token = "stub_session_token"
        
        return LoadInboxResult(
            id=inbox_id,
            message="inbox loaded (stub)",
            session_token=session_token
        )
    
    def delete_subdomain(self, domain: str) -> bool:
        """
        Deletes all emails and the domain associated with the domain
        """
        # Identify all the emails associated with the domain
        emails = self.email_delivery.get_users(domain)
        
        # Delete all the inboxes
        inbox_deletion_count = 0
        
        for email in emails:
            success = self.delete_inbox(email)
            if success:
                inbox_deletion_count += 1
                
        logger.info(f"Deleted {inbox_deletion_count} / {len(emails)} inboxes for domain={domain}")
        
        # Delete the subdomain
        sub, apex = split_domain(domain)
        if sub:
            dns_success = self.dns.delete_records(apex, sub)
            
            if not dns_success:
                logger.error(f"Failed to delete DNS records for subdomain={sub}.{apex}")
            
            eds_success = self.email_delivery.delete_subdomain(sub, apex)
            
            if not eds_success:
                logger.error(f"Failed to delete subdomain={sub}.{apex} on EDS")
            
            if not dns_success or not eds_success:
                return False
            
        return True
        
        
    def delete_inbox(self, email: str) -> bool:
        local, domain_full = parse_email(email)
        
        result = self.email_delivery.delete_user(local, domain_full)
        
        return result
    
    
    def _create_user_email(self, local: str, domain_full: str) -> Tuple[str, str]:
        password = self.email_delivery.create_user(local, domain_full)
        if not password:
            raise UserCreationError(f"Failed to create user on {domain_full}")
        
        inbox_id = f"inbox_{local}_{domain_full}"
        session_token = "stub_session_token"
        
        return inbox_id, session_token
    
    def _subdomain_verification_complete_builder(self, verified_callback: Optional[Callable[[], None]] = None) -> Callable[[str], None]:
        def _subdomain_verification_complete(domain: str):
            if verified_callback:
                verified_callback()
        return _subdomain_verification_complete
    
    def _subdomain_verification_error_builder(self) -> Callable[[str, str], None]:
        def _subdomain_verification_error(domain: str, error: str):
            pass
        return _subdomain_verification_error
    
    
    def _create_subdomain(self, sub: str, apex: str, verified_callback: Optional[Callable[[], None]] = None) -> bool:
        """
        Attempts to create the subdomain upon the apex domain.
        
        Returns True if the domain is created, and false if it is pending
        """
        
        if not (self.dns.exists_records(apex, sub) or self.email_delivery.subdomain_exists(sub, apex)):
            records = self.email_delivery.create_subdomain(sub, apex)
            if not self.dns.create_records(apex, sub, records):
                raise SubdomainCreationError(f"DNS creation failed for {sub}.{apex}")
                
            domain_pending = self.dns_verifier.add_pending_dns_verification(
                f"{sub}.{apex}",
                completion_function=self._subdomain_verification_complete_builder(verified_callback),
                error_function=self._subdomain_verification_error_builder()
            )
            
            return not domain_pending
        
        # Already exists
        return True