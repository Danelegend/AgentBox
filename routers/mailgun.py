from fastapi import APIRouter, Request, Depends, HTTPException, Form

import hmac
import hashlib
import os

router = APIRouter(prefix="/mailgun", tags=["mailgun"])

@router.post(
    "/webhooks/inbound",
    summary="Mailgun inbound webhook endpoint"
)
async def inbound_webhook(
    request: Request,
) -> None:
    form = await request.form()
    
    sender = form.get("From")
    recipient = form.get("To")
    message_id = form.get("Message-ID")
    subject = form.get("Subject")
    timestamp = form.get("timestamp")
    stripped_html = form.get("stripped-html")
    stripped_text = form.get("stripped-text")
    
    token = form.get("token")
    signature = form.get("signature")

    # Verify signature
    if not verify_webhook_signature(timestamp, token, signature):
        raise HTTPException(status_code=401, detail="invalid signature")

    return {"status": "ok"}

def verify_webhook_signature(timestamp: str, token: str, signature: str) -> bool:
    """
    Verifies Mailgun webhook signature using HMAC SHA256.

    According to Mailgun, signature = HMAC(api_key, timestamp + token).
    """
    api_key = os.getenv("MAILGUN_WEBHOOK_SIGNING_KEY")
    if not api_key or not timestamp or not token or not signature:
        return False

    signed_bytes = f"{timestamp}{token}".encode("utf-8")
    digest = hmac.new(api_key.encode("utf-8"), msg=signed_bytes, digestmod=hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, signature)
