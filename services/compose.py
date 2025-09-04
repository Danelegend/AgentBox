from adapters import PorkbunDnsAdapter, MailgunEmailDeliveryAdapter
from services.inbox_service import InboxService

def build_inbox_service() -> InboxService:
    return InboxService(
        email_delivery=MailgunEmailDeliveryAdapter(),
        dns=PorkbunDnsAdapter()
    )
