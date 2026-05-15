from traceops.core.config import settings
import logging

logger = logging.getLogger(__name__)

_instrumented = False


def setup_tracing():
    """
    Phoenix tracing disabled temporarily.
    """

    global _instrumented

    if _instrumented:
        return

    if not settings.phoenix_api_key:
        logger.warning("Phoenix API key missing — tracing disabled.")
        _instrumented = True
        return

    from phoenix.otel import register
    from openinference.instrumentation.langchain import LangChainInstrumentor

    tracer_provider = register(
        project_name="traceops-lite",
        endpoint=f"{settings.phoenix_collector_endpoint}/v1/traces",
        headers={"api_key": settings.phoenix_api_key},
    )

    LangChainInstrumentor().instrument(
        tracer_provider=tracer_provider
    )

    _instrumented = True

    logger.info("Phoenix tracing initialized")