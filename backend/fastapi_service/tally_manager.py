"""
SIZH CA - Tally WebSocket Connection Manager
=============================================
Maintains live WebSocket connections to local Tally agents,
one per client. Tracks connection state and company name.
"""

import json
import asyncio
from datetime import datetime
from typing import Dict, Optional
from fastapi import WebSocket


class TallyConnection:
    """Represents a single Tally agent WebSocket connection."""

    def __init__(self, client_id: str, websocket: WebSocket):
        self.client_id = client_id
        self.websocket = websocket
        self.connected_at = datetime.utcnow()
        self.last_heartbeat = datetime.utcnow()
        self.company_name: Optional[str] = None
        self.tally_version: Optional[str] = None

    def to_dict(self):
        return {
            "client_id": self.client_id,
            "connected": True,
            "company_name": self.company_name,
            "tally_version": self.tally_version,
            "connected_at": self.connected_at.isoformat(),
            "last_heartbeat": self.last_heartbeat.isoformat(),
        }


class TallyConnectionManager:
    """Manages all active Tally WebSocket connections."""

    def __init__(self):
        self._connections: Dict[str, TallyConnection] = {}

    @property
    def active_count(self) -> int:
        return len(self._connections)

    async def connect(self, client_id: str, websocket: WebSocket):
        await websocket.accept()
        self._connections[client_id] = TallyConnection(client_id, websocket)

    def disconnect(self, client_id: str):
        self._connections.pop(client_id, None)

    async def disconnect_all(self):
        for conn in list(self._connections.values()):
            try:
                await conn.websocket.close()
            except Exception:
                pass
        self._connections.clear()

    def is_connected(self, client_id: str) -> bool:
        return client_id in self._connections

    def get_status(self, client_id: str) -> Optional[dict]:
        conn = self._connections.get(client_id)
        if not conn:
            return None
        return conn.to_dict()

    def get_all_status(self) -> list:
        return [conn.to_dict() for conn in self._connections.values()]

    async def send_to_client(self, client_id: str, message: str):
        conn = self._connections.get(client_id)
        if conn:
            await conn.websocket.send_text(message)

    async def handle_message(self, client_id: str, raw_data: str):
        """
        Handle incoming messages from the Tally agent.
        Expected message formats (JSON):
        - { "type": "heartbeat" }
        - { "type": "company_info", "company_name": "...", "tally_version": "..." }
        - { "type": "ledger_data", "ledgers": [...] }
        - { "type": "item_data", "items": [...] }
        - { "type": "sync_complete", "action": "..." }
        """
        conn = self._connections.get(client_id)
        if not conn:
            return

        try:
            data = json.loads(raw_data)
        except json.JSONDecodeError:
            # Might be raw XML from Tally - store it for processing
            return

        msg_type = data.get("type", "")

        if msg_type == "heartbeat":
            conn.last_heartbeat = datetime.utcnow()

        elif msg_type == "company_info":
            conn.company_name = data.get("company_name")
            conn.tally_version = data.get("tally_version")

        elif msg_type == "ledger_data":
            # Forward ledger data to Django for bulk upsert
            await self._forward_to_django(
                client_id, "/masters/ledgers/bulk-upsert/",
                {"ledgers": data.get("ledgers", [])}
            )

        elif msg_type == "item_data":
            await self._forward_to_django(
                client_id, "/masters/items/bulk-upsert/",
                {"items": data.get("items", [])}
            )

    async def _forward_to_django(self, client_id: str, endpoint: str, payload: dict):
        """Forward data from Tally agent to Django REST API."""
        import httpx
        import os

        django_api = os.getenv("DJANGO_API_URL", "http://localhost:8000/api")
        try:
            async with httpx.AsyncClient() as http:
                await http.post(
                    f"{django_api}{endpoint}",
                    json=payload,
                    timeout=30,
                )
        except Exception as e:
            print(f"[TallyManager] Failed to forward to Django: {e}")
