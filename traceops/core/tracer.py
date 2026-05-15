from phoenix.otel import register
from openinference.instrumentation.langchain import (
    LangChainInstrumentor,
)

from traceops.core.config import settings

import logging

logger = logging.getLogger(__name__)

_instrumented = False


def setup_tracing():
    """
    Initialize Phoenix tracing.
    """

    global _instrumented

    if _instrumented:
        return

    # Local Phoenix (no auth)
    if "localhost" in settings.phoenix_collector_endpoint:
        tracer_provider = register(
            project_name="traceops-lite",
            endpoint=(
                f"{settings.phoenix_collector_endpoint}/v1/traces"
            ),
        )

    # Cloud Phoenix
    else:
        tracer_provider = register(
            project_name="traceops-lite",
            endpoint=(
                f"{settings.phoenix_collector_endpoint}/v1/traces"
            ),
            headers={
                "api_key": settings.phoenix_api_key
            },
        )

    LangChainInstrumentor().instrument(
        tracer_provider=tracer_provider
    )

    _instrumented = True

    logger.info(
        "Phoenix tracing initialized"
    )