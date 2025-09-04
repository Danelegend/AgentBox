from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.v1 import router as v1_router
from contextlib import asynccontextmanager
from services import build_inbox_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.inbox_service = build_inbox_service()
    
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

if __name__ == "__main__":
    import uvicorn
    import dotenv
    
    dotenv.load_dotenv()
    
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)


