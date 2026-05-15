import httpx
import logging

from traceops.core.config import settings

logger = logging.getLogger(__name__)

PHOENIX_BASE = settings.phoenix_collector_endpoint.rstrip("/")


async def get_trace(trace_id: str) -> dict:
    """
    Fetch all spans for a given trace_id from Arize Phoenix.
    Returns raw span data.
    """

    # Phoenix currently disabled in your setup
    if not settings.phoenix_api_key:
        logger.warning(
            "Phoenix API key missing — returning mock trace."
        )

        return {
            "trace_id": trace_id,
            "data": [],
            "mock": True,
        }

    headers = {
        "api_key": settings.phoenix_api_key
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            resp = await client.get(
                f"{PHOENIX_BASE}/v1/traces/{trace_id}/spans",
                headers=headers,
            )

            resp.raise_for_status()

            data = resp.json()

            logger.info(
                f"Retrieved {len(data.get('data', []))} spans "
                f"for trace {trace_id}"
            )

            return data

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(
                    f"Trace {trace_id} not found — "
                    "Phoenix may not have indexed it yet"
                )

                return {
                    "data": [],
                    "trace_id": trace_id,
                    "not_found": True,
                }

            raise

        except httpx.RequestError as e:
            logger.error(f"Phoenix connection error: {e}")

            return {
                "data": [],
                "trace_id": trace_id,
                "connection_error": str(e),
            }