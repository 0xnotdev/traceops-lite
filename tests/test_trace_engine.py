import pytest

from traceops.tracing.parser import (
    parse_trace,
)

from traceops.eval.generator import (
    generate_test,
)

from traceops.core.schemas import (
    FailureType,
)


MOCK_TRACE = {
    "trace_id": "test1234abcd",
    "data": [
        {
            "attributes": {
                "openinference.span.kind": "CHAIN",
                "input.value": (
                    "How many PTO days "
                    "do contractors receive?"
                ),
            }
        },
        {
            "attributes": {
                "openinference.span.kind": "RETRIEVER",
                "retrieval.documents": [
                    {
                        "document.content": (
                            "OUTDATED 2023: "
                            "Contractors get "
                            "20 days PTO."
                        ),
                        "document.metadata": {
                            "source": "hr_v2.1.pdf"
                        },
                    },
                    {
                        "document.content": (
                            "CURRENT 2024: "
                            "Contractors get "
                            "10 days PTO."
                        ),
                        "document.metadata": {
                            "source": "hr_v3.0.pdf"
                        },
                    },
                ],
            }
        },
        {
            "attributes": {
                "openinference.span.kind": "LLM",
                "llm.model_name": "gpt-4o-mini",
                "output.value": (
                    "Contractors receive "
                    "20 days of PTO per year."
                ),
                "llm.token_count.total": 120,
            }
        },
    ],
}


def test_parse_trace_extracts_query():
    parsed = parse_trace(MOCK_TRACE)

    assert "PTO" in parsed.query


def test_parse_trace_extracts_chunks():
    parsed = parse_trace(MOCK_TRACE)

    assert len(parsed.retrieved_chunks) == 2


def test_parse_trace_extracts_sources():
    parsed = parse_trace(MOCK_TRACE)

    assert "hr_v2.1.pdf" in parsed.sources
    assert "hr_v3.0.pdf" in parsed.sources


def test_parse_trace_classifies_stale():
    parsed = parse_trace(MOCK_TRACE)

    assert (
        parsed.failure_type
        == FailureType.STALE_CONTEXT
    )


def test_generate_test_produces_python():
    parsed = parse_trace(MOCK_TRACE)

    generated = generate_test(parsed)

    assert (
        "def test_regression_"
        in generated.test_file_content
    )

    assert (
        "FaithfulnessMetric"
        in generated.test_file_content
    )

    assert (
        generated.test_file_name
        .endswith(".py")
    )


def test_generate_test_contains_trace_id():
    parsed = parse_trace(MOCK_TRACE)

    generated = generate_test(parsed)

    assert (
        parsed.trace_id
        in generated.test_file_content
    )