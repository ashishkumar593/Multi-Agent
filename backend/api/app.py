"""FastAPI application factory and service wiring."""
from pathlib import Path
from backend.core.config import settings
from backend.core.logging import logger
from backend.core.middleware import RequestTracingMiddleware
from backend.graph.workflow import ResearchWorkflow
from backend.rag.retriever import HybridRetriever
from backend.rag.store import VectorStore
from backend.services.document_service import DocumentService
from backend.services.research_service import ResearchService

# Initialize singletons for vector store, retriever, workflow, and services
vector_store = VectorStore(persist_dir=settings.chroma_persist_dir)
retriever = HybridRetriever(vector_store=vector_store)
workflow = ResearchWorkflow(retriever=retriever)

research_service = ResearchService(retriever=retriever)
document_service = DocumentService(retriever=retriever)

try:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from backend.api.routes import company_router, documents_router, health_router, reports_router, research_router

    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        docs_url="/docs",
        openapi_url="/openapi.json",
        description="Production Multi-Agent Deep Research & Cited Report Generation Platform",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    if RequestTracingMiddleware is not object:
        app.add_middleware(RequestTracingMiddleware)

    # Mount discrete route modules
    if health_router:
        app.include_router(health_router)
    if research_router:
        app.include_router(research_router)
    if documents_router:
        app.include_router(documents_router)
    if reports_router:
        app.include_router(reports_router)
    if company_router:
        app.include_router(company_router)

except ImportError:
    app = None  # type: ignore
