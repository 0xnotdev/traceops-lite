from fastapi import FastAPI
from contextlib import asynccontextmanager
from traceops.core.tracer import setup_tracing
import logging

logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting TraceOps Lite...")
    setup_tracing()
    logger.info("Phoenix tracing active.")
    yield
    logger.info("Shutting down.")

app = FastAPI(
    title="TraceOps Lite",
    description="AI Reliability Engineering — turns production failures into regression tests.",
    version="0.1.0",
    lifespan=lifespan,
)
@app.get("/")
async def health():
    return {"status": "ok", "service": "traceops-lite"}


from traceops.api.chat import router as chat_router
from traceops.api.failure import router as failure_router

app.include_router(chat_router)
app.include_router(failure_router)