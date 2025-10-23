from __future__ import annotations
import os
import json
import httpx
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional, Dict, Any

# -------- Logging einrichten (Datei) --------
def _setup_file_logger() -> logging.Logger:
    """
    Richtet einen RotatingFileHandler ein.
    Pfad per ENV LOG_FILE überschreibbar (Default: /tmp/civicrm_mcp.log).
    """
    log_path = os.getenv("LOG_FILE", "/tmp/civicrm_mcp.log")
    logger = logging.getLogger("civicrm-mcp")
    if logger.handlers:
        return logger  # schon konfiguriert

    logger.setLevel(os.getenv("LOG_LEVEL", "DEBUG").upper())

    # ~5 MB pro Datei, 3 Backups
    handler = RotatingFileHandler(log_path, maxBytes=5 * 1024 * 1024, backupCount=3)
    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    handler.setFormatter(fmt)
    logger.addHandler(handler)
    logger.propagate = False  # nichts an Root-Logger weiterreichen
    return logger

_logger = _setup_file_logger()

# -------- CiviCRM Client --------
class CiviCRMClient:
    """
    Minimaler Async-Client für CiviCRM APIv4 (ajax/api4).

    Erwartete ENV-Variablen:
      - CIVI_URL       (z. B. https://example.org/civicrm/ajax/api4)
      - CIVI_USER_KEY  (API-Key; wird als 'X-Civi-Auth: Bearer <KEY>' gesendet)
      - CIVI_SITE_KEY  (Site-Key; wird als '_authxSiteKey' gesendet)
      - HTTP_TIMEOUT   (optional, Sekunden; Default 30)
      - LOG_FILE       (optional, Pfad zur Logdatei)
      - LOG_LEVEL      (optional, DEBUG/INFO/WARNING/ERROR)

    Beispiel-Aufruf:
        async with CiviCRMClient() as cli:
            out = await cli.call("Contact", "get", {"limit": 1})
    """
    def __init__(
        self,
        base_url: Optional[str] = None,
        user_key: Optional[str] = None,
        site_key: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        self.base_url = (
            base_url
            or os.getenv("CIVI_URL")
        )
        if not self.base_url:
            raise RuntimeError("CIVI_URL ist erforderlich")
        self.base_url = self.base_url.rstrip("/")

        self.user_key = user_key or os.getenv("CIVI_USER_KEY") or os.getenv("CIVICRM_USER_KEY")
        if not self.user_key:
            raise RuntimeError("CIVI_USER_KEY ist erforderlich")

        self.site_key = site_key or os.getenv("CIVI_SITE_KEY") or os.getenv("CIVICRM_SITE_KEY")
        if not self.user_key:
            raise RuntimeError("CIVI_SITE_KEY ist erforderlich")

        self.timeout = int(timeout if timeout is not None else os.getenv("HTTP_TIMEOUT", "30"))
        self._client: Optional[httpx.AsyncClient] = None

        # Kurzes Start-Log (API-Key redacted)
        _logger.debug(
            "Init CiviCRMClient base_url=%s timeout=%s user_key=%s",
            self.base_url,
            self.timeout,
            self._redact(self.user_key),
        )

    async def __aenter__(self):
        self._client = httpx.AsyncClient(timeout=self.timeout)
        _logger.debug("httpx.AsyncClient geöffnet")
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self._client:
            try:
                _logger.debug("httpx.AsyncClient wird geschlossen")
                await self._client.aclose()
            finally:
                self._client = None

    def _headers(self) -> Dict[str, str]:
        return {
            "X-Civi-Auth": f"Bearer {self.user_key}",
            "X-Requested-With": "XMLHttpRequest",
            "_authxSiteKey" : f"{self.site_key}"
        }

    @staticmethod
    def _redact(value: str, keep_last: int = 4) -> str:
        if not value:
            return ""
        return ("*" * max(0, len(value) - keep_last)) + value[-keep_last:]

    async def call(self, entity: str, action: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        POST auf: {base_url}/{Entity}/{Action}
        Body (form-encoded): params=<JSON>
        """
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
            _logger.debug("httpx.AsyncClient lazy geöffnet")

        url = f"{self.base_url}/{entity}/{action}"
        payload = {"params": json.dumps(params, separators=(",", ":"))} or {}

        _logger.debug("APIv4 POST %s payload_preview=%s", url, str(payload)[:800])

        resp = await self._client.post(url, headers=self._headers(), data=payload)
        
        _logger.debug("HTTP %s für %s", resp.status_code, url)

        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            body_preview = resp.text[:2000]
            _logger.error("HTTP Fehler %s bei %s, body_preview=%s", resp.status_code, url, body_preview)
            raise RuntimeError(f"CiviCRM HTTP {resp.status_code}: {body_preview}") from e

        try:
            data = resp.json()
        except Exception as e:
            _logger.error("JSON-Decode-Fehler bei %s, text_preview=%s", url, resp.text[:2000])
            raise

        if isinstance(data, dict) and data.get("is_error"):
            msg = data.get("error_message") or "CiviCRM returned error"
            code = data.get("error_code")
            _logger.error("CiviCRM API error: %s (code=%s)", msg, code)
            raise RuntimeError(f"CiviCRM API error: {msg} (code={code})")

        _logger.debug("APIv4 OK (%s/%s)", entity, action)
        return data
