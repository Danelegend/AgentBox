from typing import List
from common_types import DNSRecord
from adapters.email_delivery import EmailDeliveryPort
from adapters.email_delivery.mailgun_wrapper import (
    create_subdomain_on_eds, delete_subdomain_on_eds,
    subdomain_exists_on_eds, verify_domain_on_eds,
    create_user_on_eds, delete_user_on_eds,
    get_users_on_eds, send_email_on_eds,
    set_inbound_email_webhook
)

MAILGUN_WEBHOOK_URL = "https://5fe101026482.ngrok-free.app/mailgun/webhooks/inbound"

class MailgunEmailDeliveryAdapter(EmailDeliveryPort):
    def create_subdomain(self, subdomain: str, domain: str) -> List[DNSRecord]:
        return create_subdomain_on_eds(subdomain, domain)

    def delete_subdomain(self, subdomain: str, domain: str) -> bool:
        return delete_subdomain_on_eds(subdomain, domain)

    def subdomain_exists(self, subdomain: str, domain: str) -> bool:
        return subdomain_exists_on_eds(subdomain, domain)

    def verify_domain(self, full_domain: str) -> bool:
        return verify_domain_on_eds(full_domain)

    def create_user(self, local_part: str, domain: str) -> str:
        return create_user_on_eds(local_part, domain)

    def delete_user(self, local_part: str, domain: str) -> bool:
        return delete_user_on_eds(local_part, domain)
    
    def get_users(self, domain: str) -> List[str]:
        return get_users_on_eds(domain)
    
    def send_email(self, from_email: str, to_email: str, subject: str, body: str) -> bool:
        return send_email_on_eds(
            from_email,
            to_email,
            subject,
            body
        )
    
    def setup_inbound_email_processing(self, domain: str) -> bool:
        return set_inbound_email_webhook(domain, MAILGUN_WEBHOOK_URL)