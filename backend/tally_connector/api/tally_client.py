import asyncio
import logging
import socket
from dataclasses import dataclass
from typing import Any

import httpx

logger = logging.getLogger("tally_connector.tally_client")


@dataclass
class ConnectorResponse:
    success: bool
    status_code: int
    content: str
    error: str = ""


class TallyClient:
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 9000,
        timeout_seconds: int = 20,
        max_retries: int = 3,
        retry_backoff_seconds: float = 1.5,
    ):
        self.host = host
        self.port = port
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.retry_backoff_seconds = retry_backoff_seconds

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    async def detect_port(self, candidate_ports: list[int] | None = None) -> int | None:
        ports = candidate_ports or [9000, 9001, 9002, 9100]
        for port in ports:
            if await self._is_port_open(port):
                self.port = port
                logger.info("Tally XML server detected on port %s", port)
                return port
        return None

    async def is_tally_running(self) -> bool:
        return await self._is_port_open(self.port)

    async def _is_port_open(self, port: int) -> bool:
        loop = asyncio.get_running_loop()

        def check() -> bool:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            try:
                return sock.connect_ex((self.host, port)) == 0
            finally:
                sock.close()

        return await loop.run_in_executor(None, check)

    async def send_xml(self, xml_payload: str) -> ConnectorResponse:
        error = ""

        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                    response = await client.post(
                        self.base_url,
                        content=xml_payload.encode("utf-8"),
                        headers={"Content-Type": "application/xml"},
                    )

                response_text = response.text
                success = response.status_code == 200 and "LINEERROR" not in response_text
                return ConnectorResponse(
                    success=success,
                    status_code=response.status_code,
                    content=response_text,
                    error="" if success else "Tally returned a failure response",
                )
            except Exception as exc:
                error = str(exc)
                logger.warning(
                    "Tally call failed (attempt %s/%s): %s",
                    attempt,
                    self.max_retries,
                    error,
                )
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_backoff_seconds * attempt)

        return ConnectorResponse(success=False, status_code=0, content="", error=error or "Unknown Tally error")


class CloudAPIClient:
    def __init__(
        self,
        base_url: str,
        api_token: str,
        company_id: str,
        device_id: str,
        timeout_seconds: int = 20,
        max_retries: int = 3,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_token = api_token
        self.company_id = company_id
        self.device_id = device_id
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_token}",
            "X-Company-ID": self.company_id,
            "X-Device-ID": self.device_id,
        }

    async def post_json(self, endpoint: str, payload: dict[str, Any]) -> ConnectorResponse:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        error = ""

        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                    response = await client.post(url, json=payload, headers=self.headers)
                return ConnectorResponse(
                    success=response.status_code < 400,
                    status_code=response.status_code,
                    content=response.text,
                    error="" if response.status_code < 400 else response.text,
                )
            except Exception as exc:
                error = str(exc)
                logger.warning(
                    "Cloud POST failed (attempt %s/%s) endpoint=%s error=%s",
                    attempt,
                    self.max_retries,
                    endpoint,
                    error,
                )
                if attempt < self.max_retries:
                    await asyncio.sleep(attempt)

        return ConnectorResponse(success=False, status_code=0, content="", error=error or "Cloud API error")

    async def get_json(self, endpoint: str, params: dict[str, Any] | None = None) -> tuple[bool, Any, str]:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        error = ""

        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                    response = await client.get(url, params=params or {}, headers=self.headers)
                if response.status_code >= 400:
                    return False, None, response.text
                return True, response.json(), ""
            except Exception as exc:
                error = str(exc)
                logger.warning(
                    "Cloud GET failed (attempt %s/%s) endpoint=%s error=%s",
                    attempt,
                    self.max_retries,
                    endpoint,
                    error,
                )
                if attempt < self.max_retries:
                    await asyncio.sleep(attempt)

        return False, None, error or "Cloud API error"
