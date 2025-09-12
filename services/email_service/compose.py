from adapters import EmailDeliveryPort
from storage import InboxStorageManager, EmailAccountStorage
from .email_service import EmailService, IEmailService

def build_email_service(
    inbox_id: str,
    email_delivery: EmailDeliveryPort,
    inbox_storage_manager: InboxStorageManager,
    email_account_storage: EmailAccountStorage
) -> IEmailService:
    return EmailService(
        inbox_id=inbox_id,
        email_delivery=email_delivery,
        inbox_storage_manager=inbox_storage_manager,
        email_account_storage=email_account_storage
    )
