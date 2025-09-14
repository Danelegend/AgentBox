from adapters.email_delivery.mailgun_wrapper.client import get_client

from typing import List

import logging
logger = logging.getLogger(__name__)

def send_email_on_eds(
    from_email: str,
    to_email: str, 
    subject: str, 
    body: str,
    cc: List[str] = []
) -> str:
    client = get_client()
    
    data = {
        "from": from_email,
        "to": to_email,
        "cc": cc,
        "subject": subject,
        "html": body,
    }
    
    _, domain = from_email.split("@", 1)
    
    req = client.messages.create(
        data=data,
        domain=domain
    )
    
    if req.status_code != 200:
        logger.error(f"Failed to send email, resp={req.json()}")
        raise Exception(f"Failed to send email, resp={req.json()}")
    
    data = req.json()
    email_id = data["id"]
    
    return email_id