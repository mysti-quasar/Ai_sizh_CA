from datetime import datetime
from typing import Any

from ..api.xml_builder import build_export_report_request
from ..parser.xml_parser import parse_stock_items


async def run_stock_sync(service: Any, sync_type: str = "incremental") -> dict[str, Any]:
    started_at = datetime.utcnow().isoformat()

    request_xml = build_export_report_request(
        report_name="List of Stock Items",
        company_name=service.company_name,
    )
    tally_result = await service.tally_client.send_xml(request_xml)

    if not tally_result.success:
        service.cache.add_sync_log(
            entity="stock_items",
            sync_type=sync_type,
            status="failed",
            message=tally_result.error,
            started_at=started_at,
            ended_at=datetime.utcnow().isoformat(),
        )
        return {"ok": False, "error": tally_result.error}

    records = parse_stock_items(tally_result.content)
    changed_records = service.cache.filter_new_or_modified("stock_items", records)

    if changed_records:
        post_result = await service.cloud_client.post_json(
            "/api/connector/sync/stock-items/",
            {"records": changed_records, "sync_type": sync_type},
        )
        if not post_result.success:
            service.cache.add_sync_log(
                entity="stock_items",
                sync_type=sync_type,
                status="failed",
                message=post_result.error,
                payload={"count": len(changed_records)},
                started_at=started_at,
                ended_at=datetime.utcnow().isoformat(),
            )
            return {"ok": False, "error": post_result.error}

    service.cache.set_last_sync("stock_items", datetime.utcnow().isoformat())
    service.cache.add_sync_log(
        entity="stock_items",
        sync_type=sync_type,
        status="success",
        message=f"Synced {len(changed_records)} changed stock items",
        payload={"total": len(records), "changed": len(changed_records)},
        started_at=started_at,
        ended_at=datetime.utcnow().isoformat(),
    )
    return {"ok": True, "total": len(records), "changed": len(changed_records)}
