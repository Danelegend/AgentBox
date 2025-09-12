
from fastapi import APIRouter, Request, Depends, HTTPException

from schemas import *
from services import IInboxService, IDomainService, IEmailService

from services.errors import DomainVerificationError

router = APIRouter(prefix="/v1", tags=["v1"])

def get_domain_service(request: Request) -> IDomainService:
    return request.app.state.domain_service

def get_inbox_service(request: Request) -> IInboxService:
    return request.app.state.inbox_service

def get_email_service(request: Request, inbox_id: str) -> IEmailService:
    return request.app.state.email_service_provider.get(
        inbox_id
    )

@router.post(
    "/domain",
    summary="Attempts to create a domain"
)
async def create_domain(
    payload: CreateDomainRequest,
    domain_service: IDomainService = Depends(get_domain_service)
) -> CreateDomainRequest:
    try:
        result = domain_service.register_domain(payload.domain, None)
        
        if result.status == "pending":
            raise DomainVerificationError(f"Domain {payload.domain} is pending")
    except DomainVerificationError as e:
        raise HTTPException(status_code=202, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return CreateDomainResponse(
        domain=result.domain,
        status=result.status
    )

@router.delete(
    "/domain/{domain}",
    summary="Deletes a domain"
)
async def delete_domain(
    domain: str,
    domain_service: IDomainService = Depends(get_domain_service)
) -> bool:
    try:
        result = domain_service.delete_domain(domain)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return result

@router.post(
    "/inbox",
    response_model=CreateInboxResponse,
    summary="Creates an inbox as per the payload, setting up the subdomain if necessary"
)
async def create_inbox(
    payload: CreateInboxRequest,
    request: Request,
    inbox_service: IInboxService = Depends(get_inbox_service)
) -> CreateInboxResponse:
    try:
        result = inbox_service.create_inbox(payload.email)
        get_email_service(request, result.id)
    except DomainVerificationError as e:
        raise HTTPException(status_code=202, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return CreateInboxResponse(
        id=result.id,
        message=result.message
    )

@router.post(
    "/email",
    summary="Sends an email"
)
async def send_email(
    payload: SendEmailRequest,
    request: Request
):
    email_service = get_email_service(request, payload.inbox_id)
    
    try:
        email_service.send_email(
            to_email=payload.to_email,
            subject=payload.subject,
            body=payload.body
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return {"message": "Email sent"}