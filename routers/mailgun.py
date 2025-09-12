from fastapi import APIRouter, Request, Depends, HTTPException, Form

router = APIRouter(prefix="/mailgun", tags=["mailgun"])

@router.post(
    "/webhooks/inbound",
    summary="Mailgun inbound webhook endpoint"
)
async def inbound_webhook(
    request: Request,
    timestamp: str = Form(..., alias="timestamp"),
    token: str = Form(..., alias="token"),
    signature: str = Form(..., alias="signature"),
    sender: str = Form(..., alias="sender"),
    recipient: str = Form(..., alias="recipient"),
    subject: str = Form(..., alias="subject"),
    body_plain: str = Form(..., alias="body-plain"),
) -> None:
    # Verify signature
    if not verify_webhook_signature(timestamp, token, signature):
        raise HTTPException(status_code=401, detail="invalid signature")

    # Persist inbound email using storage/service later
    # For now, accept and return 200 to Mailgun
    return {"status": "ok"}