from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import get_settings
from app.api.endpoints import buckets, objects, search, documents, elasticsearch
from app.services.index_initializer import index_initializer

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await index_initializer.initialize_indices()
    yield
    # Shutdown


app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(buckets.router, prefix="/api/v1")
app.include_router(objects.router, prefix="/api/v1")
app.include_router(search.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(elasticsearch.router, prefix="/api/v1")


@app.get("/", tags=["Health"])
async def root():
    return {
        "message": "MinIO File Manager API",
        "version": settings.api_version,
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )