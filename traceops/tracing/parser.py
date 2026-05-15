from traceops.core.schemas import ParsedTrace, FailureType
import logging
import json

logger = logging.getLogger(__name__)

# OpenInference semantic convention keys
ATTR_INPUT_VALUE = "input.value"
ATTR_OUTPUT_VALUE = "output.value"
ATTR_LLM_MODEL = "llm.model_name"
ATTR_LLM_TOKENS = "llm.token_count.total"
ATTR_RETRIEVAL_DOCS = "retrieval.documents"
ATTR_SPAN_KIND = "openinference.span.kind"


def parse_trace(raw_trace: dict) -> ParsedTrace:
    """
    Convert raw Phoenix span data into a clean ParsedTrace.
    This is the core engineering layer of TraceOps.
    """

    spans = raw_trace.get("data", [])
    trace_id = raw_trace.get("trace_id", "unknown")

    if not spans:
        logger.warning(
            f"No spans found for trace {trace_id} — using empty ParsedTrace"
        )

        return ParsedTrace(
            trace_id=trace_id,
            query="unknown",
            retrieved_chunks=[],
            llm_response="unknown",
        )

    query = _extract_query(spans)
    chunks = _extract_retrieved_chunks(spans)
    llm_response = _extract_llm_response(spans)
    sources = _extract_sources(spans)
    model = _extract_model(spans)
    token_count = _extract_token_count(spans)
    failure_type = _classify_failure(
        query,
        chunks,
        llm_response,
    )

    return ParsedTrace(
        trace_id=trace_id,
        query=query,
        retrieved_chunks=chunks,
        llm_response=llm_response,
        sources=sources,
        model=model,
        token_count=token_count,
        failure_type=failure_type,
        raw_spans=spans,
    )


def _extract_query(spans: list[dict]) -> str:
    """
    Extract original user query.
    """

    for span in spans:
        attrs = span.get("attributes", {})

        kind = attrs.get(ATTR_SPAN_KIND, "")

        if kind in ("CHAIN", "AGENT"):
            value = attrs.get(ATTR_INPUT_VALUE, "")

            if isinstance(value, str) and value:
                return value[:2000]

    if spans:
        return (
            spans[0]
            .get("attributes", {})
            .get(ATTR_INPUT_VALUE, "unknown")
        )

    return "unknown"


def _extract_retrieved_chunks(
    spans: list[dict]
) -> list[str]:
    """
    Extract retrieved RAG documents.
    """

    chunks = []

    for span in spans:
        attrs = span.get("attributes", {})

        kind = attrs.get(ATTR_SPAN_KIND, "")

        if kind == "RETRIEVER":
            docs_raw = attrs.get(
                ATTR_RETRIEVAL_DOCS,
                [],
            )

            if isinstance(docs_raw, str):
                try:
                    docs_raw = json.loads(docs_raw)
                except json.JSONDecodeError:
                    docs_raw = []

            if not isinstance(docs_raw, list):
                continue

            for doc in docs_raw:
                if not isinstance(doc, dict):
                    continue

                content = doc.get(
                    "document.content",
                    "",
                )

                if content:
                    chunks.append(content)

    return chunks


def _extract_llm_response(
    spans: list[dict]
) -> str:
    """
    Extract final LLM output text.
    """

    for span in spans:
        attrs = span.get("attributes", {})

        if attrs.get(ATTR_SPAN_KIND) == "LLM":
            output = attrs.get(
                ATTR_OUTPUT_VALUE,
                "",
            )

            if isinstance(output, str):
                return output

    return ""


def _extract_sources(
    spans: list[dict]
) -> list[str]:
    """
    Extract retrieval document sources.
    """

    sources = []

    for span in spans:
        attrs = span.get("attributes", {})

        if attrs.get(ATTR_SPAN_KIND) == "RETRIEVER":
            docs_raw = attrs.get(
                ATTR_RETRIEVAL_DOCS,
                [],
            )

            if isinstance(docs_raw, str):
                try:
                    docs_raw = json.loads(docs_raw)
                except Exception:
                    docs_raw = []

            if not isinstance(docs_raw, list):
                continue

            for doc in docs_raw:
                if not isinstance(doc, dict):
                    continue

                meta = doc.get(
                    "document.metadata",
                    {},
                )

                if isinstance(meta, dict):
                    src = meta.get("source", "")

                    if src:
                        sources.append(src)

    return list(set(sources))


def _extract_model(
    spans: list[dict]
) -> str:
    """
    Extract LLM model name.
    """

    for span in spans:
        model = (
            span.get("attributes", {})
            .get(ATTR_LLM_MODEL)
        )

        if model:
            return str(model)

    return "unknown"


def _extract_token_count(
    spans: list[dict]
) -> int:
    """
    Sum token usage across spans.
    """

    total = 0

    for span in spans:
        tokens = (
            span.get("attributes", {})
            .get(ATTR_LLM_TOKENS, 0)
        )

        if isinstance(tokens, (int, float)):
            total += int(tokens)

    return total


def _classify_failure(
    query: str,
    chunks: list[str],
    response: str,
) -> FailureType:
    """
    Simple heuristic failure classifier.
    """

    if not chunks:
        return FailureType.BAD_RETRIEVAL

    has_old = any(
        (
            "2023" in chunk
            or "OUTDATED" in chunk
        )
        for chunk in chunks
    )

    has_new = any(
        (
            "2024" in chunk
            or "CURRENT" in chunk
        )
        for chunk in chunks
    )

    if has_old and has_new:
        return FailureType.STALE_CONTEXT

    if has_old:
        return FailureType.HALLUCINATION

    return FailureType.UNKNOWN