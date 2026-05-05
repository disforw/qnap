"""Container Station API client for QNAP integration."""

from __future__ import annotations

import logging
from typing import Any

import requests
import urllib3

_LOGGER = logging.getLogger(__name__)


class ContainerStationClient:
    """Client for QNAP Container Station API.

    Uses two auth mechanisms:
    - v3 API (list): QTS SID as Bearer token — reused from qnapstats._sid
    - v1 API (start/stop/restart): CS_SESS_ID cookie via separate CS login
    """

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        ssl: bool = False,
        verify_ssl: bool = True,
        timeout: int = 15,
    ) -> None:
        """Initialize the Container Station client."""
        self._scheme = "https" if ssl else "http"
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._verify_ssl = verify_ssl
        self._timeout = timeout

        self._base_v3 = f"{self._scheme}://{host}:{port}/container-station/api/v3"
        self._base_v1 = f"{self._scheme}://{host}:{port}/container-station/api/v1"

        self._cs_session: requests.Session | None = None

    # ------------------------------------------------------------------
    # CS v1 cookie auth (actions)
    # ------------------------------------------------------------------

    def _ensure_cs_session(self) -> requests.Session:
        """Return a requests.Session with a valid CS_SESS_ID cookie."""
        if self._cs_session is None or not self._cs_session.cookies.get("CS_SESS_ID"):
            session = requests.Session()
            session.verify = self._verify_ssl
            r = session.post(
                f"{self._base_v1}/login",
                json={"username": self._username, "password": self._password},
                timeout=self._timeout,
            )
            r.raise_for_status()
            if not session.cookies.get("CS_SESS_ID"):
                raise RuntimeError(f"Container Station login failed: {r.text[:200]}")
            self._cs_session = session
        return self._cs_session

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_containers(self, sid: str) -> list[dict[str, Any]]:
        """Return a list of all containers with id, name, status, image, type.

        sid: QTS session ID from qnapstats._sid — used as Bearer token for v3 API.
        """
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        headers = {"Authorization": f"Bearer {sid}"}
        resp = requests.get(
            f"{self._base_v3}/containers",
            headers=headers,
            verify=self._verify_ssl,
            timeout=self._timeout,
        )
        resp.raise_for_status()
        items_raw: list[dict[str, Any]] = (
            resp.json().get("data", {}).get("items", [])
        )
        return [
            {
                "id": c.get("id", ""),
                "name": c.get("name", ""),
                "status": c.get("status", ""),
                "image": c.get("image", ""),
                "type": c.get("type", "docker"),
            }
            for c in items_raw
        ]

    def container_action(
        self, container_id: str, container_type: str, action: str
    ) -> None:
        """Perform start / stop / restart on a container.

        Uses v1 API with CS_SESS_ID cookie auth.
        container_type is typically 'docker' or 'lxc'.
        action is 'start', 'stop', or 'restart'.
        """
        if action not in ("start", "stop", "restart"):
            raise ValueError(f"Invalid action: {action!r}")

        session = self._ensure_cs_session()
        url = f"{self._base_v1}/container/{container_type}/{container_id}/{action}"
        r = session.put(url, timeout=self._timeout)

        if r.status_code == 401:
            # CS session expired — invalidate and retry once
            self._cs_session = None
            session = self._ensure_cs_session()
            r = session.put(url, timeout=self._timeout)

        r.raise_for_status()
