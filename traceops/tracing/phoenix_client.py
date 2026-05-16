import httpx
import logging

from traceops.core.config import settings

logger = logging.getLogger(__name__)

PHOENIX_BASE = (
    settings.phoenix_collector_endpoint
    .rstrip("/")
)


async def get_trace(
    trace_id: str,
) -> dict:
    """
    Fetch spans for a trace from Phoenix.
    """

    headers = {}

    # Only use API key for cloud Phoenix
    if (
        settings.phoenix_api_key
        and "127.0.0.1" not in PHOENIX_BASE
        and "localhost" not in PHOENIX_BASE
    ):
        headers["api_key"] = (
            settings.phoenix_api_key
        )

    project_name = "traceops-lite"

    async with httpx.AsyncClient(
        timeout=15.0
    ) as client:

        try:

            resp = await client.get(
                (
                    f"{PHOENIX_BASE}"
                    f"/v1/projects/"
                    f"{project_name}"
                    f"/spans"
                ),
                headers=headers,
                params={
                    "trace_id": trace_id,
                },
            )

            resp.raise_for_status()

            

            data = resp.json()

            logger.info(
                f"Retrieved "
                f"{len(data.get('data', []))} spans "
                f"for trace {trace_id}"
            )

            return data

        except Exception as e:

            logger.error(
                f"Phoenix fetch failed: {e}"
            )

            return {
                "trace_id": trace_id,
                "data": [],
                "error": str(e),
            }