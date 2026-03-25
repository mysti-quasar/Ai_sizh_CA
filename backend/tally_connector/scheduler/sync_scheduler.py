import asyncio
import logging
from typing import Any

from ..api.xml_builder import (
    build_ledger_create_xml,
    build_stock_item_create_xml,
    build_voucher_create_xml,
)
from ..sync.ledger_sync import run_ledger_sync
from ..sync.stock_sync import run_stock_sync
from ..sync.voucher_sync import run_voucher_sync

logger = logging.getLogger("tally_connector.scheduler")


class SyncScheduler:
    def __init__(self, service: Any):
        self.service = service
        self._jobs: list[asyncio.Task] = []
        self._running = False

    async def start(self) -> None:
        if self._running:
            return
        self._running = True

        # Configurable polling intervals
        ledger_interval = self.service.config.get("ledger_sync_interval", 60)
        voucher_interval = self.service.config.get("voucher_sync_interval", 30)
        stock_interval = self.service.config.get("stock_sync_interval", 300)
        queue_interval = self.service.config.get("task_worker_interval", 10)

        self._jobs = [
            asyncio.create_task(self._loop_sync("ledgers", ledger_interval)),
            asyncio.create_task(self._loop_sync("vouchers", voucher_interval)),
            asyncio.create_task(self._loop_sync("stock_items", stock_interval)),
            asyncio.create_task(self._loop_pending_tasks(queue_interval)),
        ]

    async def stop(self) -> None:
        self._running = False
        for job in self._jobs:
            job.cancel()
        self._jobs.clear()

    async def run_manual_sync(self, entities: list[str], sync_type: str = "manual") -> dict[str, Any]:
        results: dict[str, Any] = {}
        for entity in entities:
            if entity == "ledgers":
                results[entity] = await run_ledger_sync(self.service, sync_type=sync_type)
            elif entity == "vouchers":
                results[entity] = await run_voucher_sync(self.service, sync_type=sync_type)
            elif entity in ("stock", "stock_items"):
                results["stock_items"] = await run_stock_sync(self.service, sync_type=sync_type)
            else:
                results[entity] = {"ok": False, "error": "unsupported entity"}
        return results

    async def _loop_sync(self, entity: str, interval_seconds: int) -> None:
        while self._running:
            try:
                if entity == "ledgers":
                    await run_ledger_sync(self.service, sync_type="scheduled")
                elif entity == "vouchers":
                    await run_voucher_sync(self.service, sync_type="scheduled")
                elif entity == "stock_items":
                    await run_stock_sync(self.service, sync_type="scheduled")
            except Exception as exc:
                logger.exception("Scheduled sync failed for entity=%s error=%s", entity, exc)
            await asyncio.sleep(interval_seconds)

    async def _loop_pending_tasks(self, interval_seconds: int) -> None:
        while self._running:
            try:
                await self.process_pending_tasks()
            except Exception as exc:
                logger.exception("Pending task worker loop failed: %s", exc)
            await asyncio.sleep(interval_seconds)

    async def process_pending_tasks(self) -> None:
        tasks = self.service.cache.claim_tasks(limit=50)
        for task in tasks:
            task_id = task["id"]
            retry_count = int(task.get("retry_count", 0))
            payload = task.get("payload", {})
            task_type = task.get("task_type", "")

            try:
                if task_type == "push_to_tally":
                    await self._execute_push_task(payload)
                else:
                    raise ValueError(f"Unsupported task_type: {task_type}")

                self.service.cache.complete_task(task_id)
            except Exception as exc:
                self.service.cache.fail_task(task_id, str(exc), retry_count + 1)

    async def _execute_push_task(self, payload: dict[str, Any]) -> None:
        operation = payload.get("operation", "")
        data = payload.get("data", {})

        if operation in ("create_ledger", "create_customer", "create_supplier"):
            # Customers and suppliers are represented as ledgers in Tally.
            if operation == "create_customer":
                data = {**data, "parent": data.get("parent", "Sundry Debtors")}
            if operation == "create_supplier":
                data = {**data, "parent": data.get("parent", "Sundry Creditors")}
            xml = build_ledger_create_xml(data, company_name=self.service.company_name)
        elif operation == "create_voucher":
            xml = build_voucher_create_xml(data, company_name=self.service.company_name)
        elif operation == "create_stock_item":
            xml = build_stock_item_create_xml(data, company_name=self.service.company_name)
        else:
            raise ValueError(f"Unsupported push operation: {operation}")

        result = await self.service.tally_client.send_xml(xml)
        if not result.success:
            raise RuntimeError(result.error or "Failed to push data to Tally")

        callback = payload.get("callback", {})
        endpoint = callback.get("endpoint")
        if endpoint:
            callback_payload = {
                "operation": operation,
                "status": "success",
                "tally_response": result.content,
                "reference_id": callback.get("reference_id", ""),
            }
            callback_result = await self.service.cloud_client.post_json(endpoint, callback_payload)
            if not callback_result.success:
                raise RuntimeError(callback_result.error or "Failed callback to backend")
