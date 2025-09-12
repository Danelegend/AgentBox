from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import v1_router, mailgun_router
from contextlib import asynccontextmanager
from services import build_inbox_service, build_domain_service, EmailServiceProvider
from storage import compose_storage_manager, InboxStorageManager, EmailAccountStorage
from adapters import build_email_delivery, build_dns
from util.logging_config import configure_logging

@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    
    app.state.storage_manager = compose_storage_manager()
    
    app.state.inbox_storage_manager = InboxStorageManager(app.state.storage_manager)
    
    app.state.email_delivery = build_email_delivery("MAILGUN")
    app.state.dns = build_dns("PORKBUN")
    
    app.state.email_account_storage = EmailAccountStorage(app.state.storage_manager)
    
    app.state.email_service_provider = EmailServiceProvider(
        app.state.email_delivery,
        app.state.inbox_storage_manager,
        app.state.email_account_storage
    )
    
    app.state.inbox_service = build_inbox_service(
        app.state.storage_manager,
        app.state.email_delivery,
        app.state.email_account_storage
    )
    
    app.state.domain_service = build_domain_service(
        app.state.email_delivery,
        app.state.dns
    )
    
    yield


app = FastAPI(
    title="AgentBox API",
    version="0.1.0",
    description="FastAPI backend template with v1 endpoint stubs",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router)
app.include_router(mailgun_router)

if __name__ == "__main__":
    import uvicorn
    import dotenv
    
    dotenv.load_dotenv()
    
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)


