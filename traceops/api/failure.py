from fastapi import (
    APIRouter,
    HTTPException,
    BackgroundTasks,
)

from traceops.core.schemas import (
    ReportFailureRequest,
    ReportFailureResponse,
)

from traceops.tracing.phoenix_client import (
    get_trace,
)

from traceops.tracing.parser import (
    parse_trace,
)

from traceops.eval.generator import (
    generate_test,
)

from traceops.github_automation.pr_creator import (
    create_pr,
)

from datetime import datetime

import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/failure",
    tags=["failure-reporting"],
)

# ---------------------------------------------------------
# Simple in-memory pipeline log
# (replace with DB in production)
# ---------------------------------------------------------

_pipeline_log: list[dict] = []


@router.post(
    "/report",
    response_model=ReportFailureResponse,
)
async def report_failure(
    req: ReportFailureRequest,
    background_tasks: BackgroundTasks,
):
    """
    Triggered when a user clicks 👎.

    Returns immediately while the
    TraceOps pipeline runs asynchronously.
    """

    logger.info(
        f"Failure reported for trace_id: "
        f"{req.trace_id}"
    )

    if not req.trace_id:
        raise HTTPException(
            status_code=400,
            detail="trace_id is required",
        )

    async def run_traceops_pipeline(
        trace_id: str,
        note: str,
    ):
        try:
            logger.info(
                f"[Pipeline] Fetching trace "
                f"{trace_id}"
            )

            raw_trace = await get_trace(
                trace_id
            )

            logger.info(
                "[Pipeline] Parsing trace"
            )

            parsed = parse_trace(
                raw_trace
            )

            logger.info(
                "[Pipeline] Generating test"
            )

            test = generate_test(
                parsed
            )

            logger.info(
                "[Pipeline] Opening GitHub PR"
            )

            pr = create_pr(test)

            logger.info(
                f"[Pipeline] Success → "
                f"{pr.pr_url}"
            )

            _pipeline_log.append({
                "trace_id": trace_id,
                "status": "success",
                "pr_url": pr.pr_url,
                "failure_type": (
                    parsed.failure_type.value
                ),
                "timestamp": str(
                    datetime.utcnow()
                ),
            })

        except Exception as e:
            logger.error(
                f"[Pipeline] Failed: {e}",
                exc_info=True,
            )

            _pipeline_log.append({
                "trace_id": trace_id,
                "status": "error",
                "error": str(e),
                "timestamp": str(
                    datetime.utcnow()
                ),
            })

    background_tasks.add_task(
        run_traceops_pipeline,
        req.trace_id,
        req.user_note or "",
    )

    return ReportFailureResponse(
        status="accepted",
        message=(
            f"Failure report queued for "
            f"trace {req.trace_id}. "
            "Pipeline running asynchronously."
        ),
    )


@router.get("/recent")
async def get_recent_failures(
    limit: int = 10,
):
    """
    Return recent pipeline executions.

    Useful for frontend dashboards.
    """

    return {
        "failures": _pipeline_log[-limit:]
    }