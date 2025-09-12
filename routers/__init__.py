from .v1 import router as v1_router
from .mailgun import router as mailgun_router

__all__ = [
    "v1_router", 
    "mailgun_router"
]

