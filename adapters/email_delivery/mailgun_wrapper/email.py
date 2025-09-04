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
) -> bool:
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
    
    print(req.json())
    
    return req.status_code == 200