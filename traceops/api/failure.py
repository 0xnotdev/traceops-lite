from fastapi import (
    APIRouter,
    HTTPException,
    BackgroundTasks,
)

from traceops.core.schemas import (
    ReportFailureRequest,
    ReportFailureResponse,
)

import logging


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/failure",
    tags=["failure-reporting"],
)


@router.post(
    "/report",
    response_model=ReportFailureResponse,
)
async def report_failure(
    req: ReportFailureRequest,
    background_tasks: BackgroundTasks,
):
    """
    Called when user clicks 👎 thumbs-down.

    Returns immediately while the
    full TraceOps pipeline runs in background.
    """

    logger.info(
        f"Failure reported for trace_id: {req.trace_id}"
    )

    if not req.trace_id:
        raise HTTPException(
            status_code=400,
            detail="trace_id is required",
        )

    # Background pipeline
    async def run_traceops_pipeline(
        trace_id: str,
        note: str,
    ):
        try:
            from traceops.tracing.phoenix_client import get_trace

            from traceops.tracing.parser import parse_trace

            from traceops.eval.generator import generate_test

            from traceops.github_automation.pr_creator import create_pr

            logger.info(
                f"[Pipeline] Fetching trace {trace_id}..."
            )

            raw_trace = await get_trace(trace_id)

            logger.info(
                "[Pipeline] Parsing trace..."
            )

            parsed = parse_trace(raw_trace)

            logger.info(
                "[Pipeline] Generating DeepEval test..."
            )

            test = generate_test(parsed)

            logger.info(
                "[Pipeline] Opening GitHub PR..."
            )

            pr = create_pr(test)

            logger.info(
                f"[Pipeline] Done! PR: {pr.pr_url}"
            )

        except Exception as e:
            logger.error(
                f"[Pipeline] Failed: {e}",
                exc_info=True,
            )

    background_tasks.add_task(
        run_traceops_pipeline,
        req.trace_id,
        req.user_note or "",
    )

    return ReportFailureResponse(
        status="accepted",
        message=(
            f"Failure report queued for trace "
            f"{req.trace_id}. "
            f"PR will be created shortly."
        ),
    )