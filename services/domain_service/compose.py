from adapters import EmailDeliveryPort, DnsPort
from .domain_service import DomainService, IDomainService

def build_domain_service(
    email_delivery: EmailDeliveryPort,
    dns: DnsPort
) -> IDomainService:
    return DomainService(
        email_delivery,
        dns
    )