
from fastapi import APIRouter, Request, Depends, HTTPException

from schemas import *
from services.inbox_service import InboxService

from services.errors import DomainVerificationError

router = APIRouter(prefix="/v1", tags=["v1"])

def get_inbox_service(request: Request) -> InboxService:
    return request.app.state.inbox_service

@router.post(
    "/inbox",
    response_model=CreateInboxResponse,
    summary="Creates an inbox as per the payload, setting up the subdomain if necessary"
)
async def create_inbox(
    payload: CreateInboxRequest,
    inbox_service: InboxService = Depends(get_inbox_service)    
) -> CreateInboxResponse:
    try:
        result = inbox_service.create_inbox(payload.email)
    except DomainVerificationError as e:
        raise HTTPException(status_code=202, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return CreateInboxResponse(
        id=result.id,
        session_token=result.session_token,
        message=result.message
    )


@router.post(
    "/inbox", 
    response_model=CreateInboxResponse, 
    summary="Creates an inbox, otherwise returns it if it already exists"
)
async def create_inbox(payload: CreateInboxRequest) -> CreateInboxResponse:
    inbox_id = "inbox_00000000"
    return CreateInboxResponse(id=inbox_id, message="inbox created (stub)")


@router.post(
    "/inbox/{inbox_id}/session",
    response_model=CreateInboxSessionRequest,
    summary="Generates a session token for an inbox"
)
async def generate_session_token(inbox_id: str) -> CreateInboxSessionResponse:
    pass
