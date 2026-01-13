from typing import Dict, Any, Optional, List
import httpx
from datetime import datetime, timezone
from app.core.config import settings


class OpenAlgoClient:
    """
    OpenAlgo Market Data Client
    - Data only
    - Execution HARD BLOCKED
    - Fail-closed by default
    """

    def __init__(self):
        self.base_url = settings.OPENALGO_API_URL
        self.api_key = settings.OPENALGO_API_KEY
        self.headers = {"Content-Type": "application/json"}

    async def _post(self, endpoint: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if "order" in endpoint or "place" in endpoint:
            return None  # HARD EXECUTION BLOCK

        if self.api_key and "apikey" not in payload:
            payload["apikey"] = self.api_key

        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(
                f"{self.base_url}{endpoint}",
                json=payload,
                headers=self.headers
            )
            resp.raise_for_status()
            return resp.json()

    async def _get(self, endpoint: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if self.api_key and "apikey" not in params:
            params["apikey"] = self.api_key

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{self.base_url}{endpoint}", params=params)
            resp.raise_for_status()
            return resp.json()

    # ------------------------------------------------------------------
    # REAL-TIME QUOTE (Tier 1)
    # ------------------------------------------------------------------
    async def get_quote(self, symbol: str, exchange: str = "NSE") -> Optional[Dict[str, Any]]:
        response = await self._post(
            "/api/v1/quotes/",
            {"symbol": symbol, "exchange": exchange}
        )

        if not response or response.get("status") != "success":
            return None  # FAIL CLOSED

        data = response.get("data", {})
        ts = data.get("timestamp")

        if not ts:
            return None  # STALE → FAIL CLOSED

        # Check freshness
        # Note: Depending on OpenAlgo timestamp format (seconds vs ms), might need adjustment.
        # Assuming seconds based on previous '1704...' examples.
        try:
            ts_dt = datetime.fromtimestamp(ts, tz=timezone.utc)
            now = datetime.now(tz=timezone.utc)
            freshness = (now - ts_dt).total_seconds()

            if freshness >= 5:
                # Log warning or just return None?
                # The requirement says FAIL CLOSED.
                return None  # STALE → FAIL CLOSED
        except Exception:
            # If timestamp parsing fails, fail closed
            return None

        return {
            "data": data,
            "source": "openalgo",
            "data_tier": "TIER_1",
            "is_realtime": True,
            "freshness_seconds": freshness,
            "feed_health": "HEALTHY"
        }

    # ------------------------------------------------------------------
    # HISTORICAL DATA (DATE CONTROLLED)
    # ------------------------------------------------------------------
    async def get_historical(
        self,
        symbol: str,
        exchange: str,
        interval: str,
        start_date: str,
        end_date: str
    ) -> Optional[Dict[str, Any]]:
        params = {
            "symbol": symbol,
            "exchange": exchange,
            "interval": interval,
            "from": start_date, # Mapped keys to API expected params
            "to": end_date
        }

        response = await self._get("/api/v1/ticker/" + symbol, params)

        if not response or response.get("status") != "success":
            return None

        return {
            "data": response.get("data"),
            "source": "openalgo",
            "data_tier": "TIER_1",
            "is_realtime": False,
            "data_type": "HISTORICAL",
            "timezone": "IST"
        }

    # ------------------------------------------------------------------
    # INSTRUMENTS (METADATA ONLY)
    # ------------------------------------------------------------------
    async def get_instruments(self, exchange: str = "NSE") -> List[Dict[str, Any]]:
        response = await self._get("/api/v1/instruments", {"exchange": exchange})
        if not response:
            return []
        return response.get("data", [])


# SAFE SINGLETON
openalgo = OpenAlgoClient()
