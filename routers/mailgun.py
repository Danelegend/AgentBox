from fastapi import APIRouter, Request, Depends, HTTPException, Form
from services import IEmailService
from common_types import IncomingEmailRecord

import hmac
import hashlib
import os

router = APIRouter(prefix="/mailgun", tags=["mailgun"])

def get_email_service(request: Request, email: str) -> IEmailService:
    return request.app.state.email_service_provider.get_by_email(
        email
    )

@router.post(
    "/webhooks/inbound",
    summary="Mailgun inbound webhook endpoint"
)
async def inbound_webhook(
    request: Request,
) -> None:
    form = await request.form()
    
    token = form.get("token")
    signature = form.get("signature")
    timestamp = form.get("timestamp")
    
    # Verify signature
    if not verify_webhook_signature(timestamp, token, signature):
        raise HTTPException(status_code=401, detail="invalid signature")

    sender = form.get("From")
    recipient = form.get("To")
    message_id = form.get("Message-Id")
    subject = form.get("Subject")
    stripped_html = form.get("stripped-html")
    stripped_text = form.get("stripped-text")
    reply_id = form.get("In-Reply-To")
    
    email_service = get_email_service(request, recipient)

    incoming_email_request = IncomingEmailRecord(
        message_id=message_id,
        sender=sender,
        recipient=recipient,
        subject=subject,
        body=stripped_html,
        reply_id=reply_id,
        timestamp=timestamp
    )
    
    email_service.handle_incoming_email(incoming_email_request)
    
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
