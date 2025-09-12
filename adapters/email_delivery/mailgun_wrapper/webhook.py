from .client import get_client

import hmac
import hashlib
import os

def set_inbound_email_webhook(domain: str, webhook_url: str):
    client = get_client()
    
    data = {
        "priority": 0,
        "description": "Inbound email webhook",
        "expression": "catch_all()",
        "action": ["forward('{webhook_url}')", "stop()"],
    }
    
    req = client.routes.create(domain=domain, data=data)
    
    return req.status_code == 200

def verify_webhook_signature(timestamp: str, token: str, signature: str) -> bool:
    """
    Verifies Mailgun webhook signature using HMAC SHA256.

    According to Mailgun, signature = HMAC(api_key, timestamp + token).
    """
    api_key = os.getenv("MAILGUN_API_KEY")
    if not api_key or not timestamp or not token or not signature:
        return False

    signed_bytes = f"{timestamp}{token}".encode("utf-8")
    digest = hmac.new(api_key.encode("utf-8"), msg=signed_bytes, digestmod=hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, signature)


