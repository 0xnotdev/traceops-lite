from fastapi import APIRouter, HTTPException

from opentelemetry import trace

from traceops.core.schemas import (
    ChatRequest,
    ChatResponse,
)

from traceops.chatbot.graph import rag_graph

import uuid
import logging


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
)

tracer = trace.get_tracer(__name__)


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest):

    session_id = (
        req.session_id
        or str(uuid.uuid4())
    )

    try:

        with tracer.start_as_current_span(
            "chat_request"
        ) as span:

            state = {
                "question": req.question,
                "retrieved_chunks": [],
                "sources": [],
                "answer": "",
                "session_id": session_id,
                "error": None,
            }

            result = rag_graph.invoke(state)

            # REAL OpenTelemetry trace ID
            trace_id = format(
                span.get_span_context().trace_id,
                "032x",
            )

            logger.info(
                f"Trace ID for this request: "
                f"{trace_id}"
            )

            return ChatResponse(
                answer=result["answer"],
                trace_id=trace_id,
                session_id=session_id,
            )

    except Exception as e:

        logger.error(f"Chat error: {e}")

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )