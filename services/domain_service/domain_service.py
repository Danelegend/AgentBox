from typing import Protocol, Optional, Callable, Literal

from pydantic import BaseModel

from adapters import EmailDeliveryPort, DnsPort
from services.errors import (
    DomainAccessError,
    SubdomainCreationError,
    DomainVerificationError
)
from .dns_verifier import DnsVerifier

from util.domain_utils import split_domain

import logging
logger = logging.getLogger(__name__)

class RegisterDomainResult(BaseModel):
    domain: str
    status: Literal["pending", "verified"]


class IDomainService(Protocol):
    def register_domain(
        self, 
        domain: str,
        verified_callback: Optional[Callable[[], None]]
    ) -> RegisterDomainResult: ...

    def verify_domain(
        self,
        domain: str
    ) -> bool:
        ...

    def delete_domain(
        self,
        domain: str
    ) -> bool:
        ...


class DomainService(IDomainService):
    def __init__(
        self,
        email_delivery: EmailDeliveryPort,
        dns: DnsPort
    ):
        self.email_delivery = email_delivery
        self.dns = dns
        
        self.dns_verifier = DnsVerifier(email_delivery)
    
    def register_domain(
        self, 
        domain: str,
        verified_callback: Optional[Callable[[], None]]
    ) -> RegisterDomainResult:
        """
        Create the domain on the DNS and EDS
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
            raise NotImplementedError("Setting up apex is not implemented")
        
        return RegisterDomainResult(
            domain=domain,
            status="verified" if domain_valid else "pending"
        )


    def verify_domain(
        self,
        domain: str
    ) -> bool:
        success = self.email_delivery.verify_domain(domain)

        return success

    def delete_domain(
        self,
        domain: str
    ) -> bool:
        sub, apex = split_domain(domain)
        if sub:
            dns_deletion_success = self.dns.delete_records(apex, sub)

            if not dns_deletion_success:
                logger.error(f"Failed to delete DNS records for subdomain={sub}.{apex}")

            eds_deletion_success = self.email_delivery.delete_subdomain(sub, apex)

            if not eds_deletion_success:
                logger.error(f"Failed to delete subdomain={sub}.{apex} on EDS")

            if not dns_deletion_success or not eds_deletion_success:
                return False
        else:
            raise NotImplementedError("Apex domain not implemented yet")
    
        return True


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


def build_domain_service(
    email_delivery: EmailDeliveryPort,
    dns: DnsPort
) -> IDomainService:
    return DomainService(
        email_delivery,
        dns
    )