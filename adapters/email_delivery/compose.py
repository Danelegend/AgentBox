from .email_delivery import EmailDeliveryPort
from .email_delivery_mailgun import MailgunEmailDeliveryAdapter

from typing import Literal

EMAIL_DELIVERY_OPTIONS = Literal["MAILGUN"]

def build_email_delivery(email_delivery_type: EMAIL_DELIVERY_OPTIONS) -> EmailDeliveryPort:
    if email_delivery_type == "MAILGUN":
        return MailgunEmailDeliveryAdapter()
    else:
        raise ValueError(f"Invalid email delivery type: {email_delivery_type}")
