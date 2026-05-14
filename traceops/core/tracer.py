from phoenix.otel import register
from openinference.instrumentation.langchain import LangChainInstrumentor

from traceops.core.config import settings

import logging


logger = logging.getLogger(__name__)

_instrumented = False


def setup_tracing():
    """
    Call once at app startup.
    Instruments all LangChain/LangGraph calls automatically.
    """

    global _instrumented

    if _instrumented:
        return

    tracer_provider = register(
        project_name="traceops-lite",
        endpoint=f"{settings.phoenix_collector_endpoint}/v1/traces",
        headers={
            "api_key": settings.phoenix_api_key
        } if settings.phoenix_api_key else {},
    )

    LangChainInstrumentor().instrument(
        tracer_provider=tracer_provider
    )

    _instrumented = True

    logger.info("Phoenix tracing initialized")