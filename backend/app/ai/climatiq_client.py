"""Climatiq API client with lightweight caching."""
from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    value: Dict[str, Any]
    expires_at: float


class ClimatiqClient:
    """Thin wrapper around the Climatiq API with basic caching."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.climatiq.io",
        cache_ttl_seconds: int = 6 * 60 * 60,
    ) -> None:
        self.api_key = api_key or os.getenv("CLIMATIQ_API_KEY")
        self.base_url = base_url.rstrip("/")
        self.cache_ttl = cache_ttl_seconds
        self._cache: Dict[str, CacheEntry] = {}

        if not self.api_key:
            logger.warning("Climatiq API key not provided; falling back to static factors")

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _get_cache(self, key: str) -> Optional[Dict[str, Any]]:
        entry = self._cache.get(key)
        if not entry:
            return None
        if entry.expires_at < time.time():
            self._cache.pop(key, None)
            return None
        return entry.value

    def _set_cache(self, key: str, value: Dict[str, Any]) -> None:
        self._cache[key] = CacheEntry(value=value, expires_at=time.time() + self.cache_ttl)

    def get_emission_factor(
        self,
        activity_id: Optional[str] = None,
        region: Optional[str] = None,
        category: Optional[str] = None,
        lifecycle_stage: Optional[str] = None,
        **extra_params: Any,
    ) -> Optional[Dict[str, Any]]:
        """Fetch emission factors from Climatiq's /emission-factors endpoint."""
        if not self.api_key:
            return None

        params = {k: v for k, v in {
            "activity_id": activity_id,
            "region": region,
            "category": category,
            "lifecycle_stage": lifecycle_stage,
            **extra_params,
        }.items() if v}

        cache_key = f"ef|{sorted(params.items())}"
        cached = self._get_cache(cache_key)
        if cached is not None:
            return cached

        try:
            response = requests.get(
                f"{self.base_url}/data/v1/emission-factors",
                headers=self._headers(),
                params=params,
                timeout=20,
            )
            response.raise_for_status()
            data = response.json()
            results = data.get("results") or []
            if results:
                result = results[0]
                self._set_cache(cache_key, result)
                return result
            return None
        except requests.RequestException as exc:
            logger.error("Climatiq emission factor request failed: %s", exc)
            return None

    def estimate_emissions(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Call Climatiq /estimate to compute emissions for structured payloads."""
        if not self.api_key:
            return None

        cache_key = f"estimate|{hash(frozenset(payload.items()))}"
        cached = self._get_cache(cache_key)
        if cached is not None:
            return cached

        try:
            response = requests.post(
                f"{self.base_url}/estimate",
                headers=self._headers(),
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            self._set_cache(cache_key, data)
            return data
        except requests.RequestException as exc:
            logger.error("Climatiq estimate request failed: %s", exc)
            return None
