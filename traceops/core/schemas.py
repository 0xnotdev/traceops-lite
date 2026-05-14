from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

import uuid


# ── Failure classification ────────────────────────────────
class FailureType(str, Enum):
    HALLUCINATION = "hallucination"
    BAD_RETRIEVAL = "bad_retrieval"
    STALE_CONTEXT = "stale_context"
    WRONG_TOOL_USE = "wrong_tool_use"
    POOR_REASONING = "poor_reasoning"
    BROKEN_PROMPT = "broken_prompt"
    UNKNOWN = "unknown"


# ── Failure report (from thumbs-down click) ───────────────
class FailureReport(BaseModel):
    """Payload sent when user clicks thumbs-down."""

    trace_id: str
    user_note: Optional[str] = None
    reported_at: datetime = Field(default_factory=datetime.utcnow)


# ── Parsed trace (output of trace parser) ─────────────────
class ParsedTrace(BaseModel):
    """Clean, structured representation of a Phoenix trace."""

    trace_id: str
    query: str
    retrieved_chunks: list[str]
    llm_response: str

    sources: list[str] = Field(default_factory=list)

    model: str = "unknown"
    latency_ms: int = 0
    token_count: int = 0

    failure_type: FailureType = FailureType.UNKNOWN

    raw_spans: list[dict[str, Any]] = Field(default_factory=list)


# ── Generated eval test ───────────────────────────────────
class GeneratedTest(BaseModel):
    """A DeepEval test case generated from a production failure."""

    test_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])

    trace_id: str
    failure_type: FailureType

    test_file_content: str
    test_file_name: str

    generated_at: datetime = Field(default_factory=datetime.utcnow)


# ── GitHub PR result ──────────────────────────────────────
class PRResult(BaseModel):
    pr_url: str
    pr_number: int
    branch_name: str
    commit_sha: str
    test_file: str


# ── Full pipeline result ──────────────────────────────────
class TraceOpsResult(BaseModel):
    """The complete result of processing one failure report."""

    trace_id: str
    parsed_trace: ParsedTrace
    generated_test: GeneratedTest
    pr_result: PRResult

    total_latency_ms: int = 0


# ── API request / response ────────────────────────────────
class ChatRequest(BaseModel):
    question: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    trace_id: str
    session_id: str


class ReportFailureRequest(BaseModel):
    trace_id: str
    user_note: Optional[str] = None


class ReportFailureResponse(BaseModel):
    status: str
    pr_url: Optional[str] = None
    message: str