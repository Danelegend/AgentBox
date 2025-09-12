from adapters import EmailDeliveryPort
from storage import StorageManager, EmailAccountStorage

from services.inbox_service import IInboxService, InboxService

def build_inbox_service(
    storage_manager: StorageManager,
    email_delivery: EmailDeliveryPort,
    email_account_storage: EmailAccountStorage
) -> IInboxService:
    return InboxService(
        email_delivery=email_delivery,
        email_account_storage=email_account_storage
    )