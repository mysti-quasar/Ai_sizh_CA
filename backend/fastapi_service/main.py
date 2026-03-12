"""
SIZH CA - FastAPI Tally Connector & File Processing Service
=============================================================
- WebSocket endpoint for live Tally agent connection
- REST endpoints for file upload, parsing, Gemini OCR, and AI processing
- Valkey-backed job queue for async processing
"""

import os
import json
import uuid
import asyncio
import logging
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Optional

import httpx
import pandas as pd
import redis
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Form, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .tally_manager import TallyConnectionManager
from .file_parser import parse_uploaded_file
from .mapping_engine import apply_field_mapping, apply_gst_mapping, apply_rule_matching
from .gemini_ocr import extract_with_gemini, ocr_image_to_text
from .tally_xml_connector import build_voucher_xml, build_batch_xml, send_to_tally, fetch_from_tally, sync_pending_vouchers

# ── Logger ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG,
    format="[SIZH FastAPI] %(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("sizh.upload")

# ── Valkey connection ────────────────────────────────────────────────────────
VALKEY_URL = os.getenv("VALKEY_URL", "redis://127.0.0.1:6379/0")
valkey = redis.from_url(VALKEY_URL, decode_responses=True)

# ── Django API base ──────────────────────────────────────────────────────────
DJANGO_API = os.getenv("DJANGO_API_URL", "http://localhost:8000/api")

# ── Tally connection manager (singleton) ─────────────────────────────────────
tally_manager = TallyConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    yield
    # Cleanup on shutdown
    await tally_manager.disconnect_all()


app = FastAPI(
    title="SIZH CA - Tally Connector & Processing Service",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════════════════════════════════════
# HEALTH
# ═══════════════════════════════════════════════════════════════════════════════


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "SIZH CA FastAPI",
        "tally_connections": tally_manager.active_count,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# TALLY WEBSOCKET CONNECTOR
# ═══════════════════════════════════════════════════════════════════════════════


@app.websocket("/ws/tally/{client_id}")
async def tally_websocket(websocket: WebSocket, client_id: str):
    """
    WebSocket endpoint for the local Tally Agent.
    The agent connects and maintains a live bidirectional channel.
    Messages from agent: Tally XML responses, sync data, heartbeats.
    Messages to agent: Tally XML requests (fetch ledgers, send vouchers).
    """
    logger.info("[Tally WS] Agent connected | client_id=%s", client_id)
    await tally_manager.connect(client_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await tally_manager.handle_message(client_id, data)
    except WebSocketDisconnect:
        logger.info("[Tally WS] Agent disconnected | client_id=%s", client_id)
        tally_manager.disconnect(client_id)


@app.get("/tally/status")
async def tally_status():
    """Return the current Tally connection status for all clients."""
    return {
        "connections": tally_manager.get_all_status(),
        "active_count": tally_manager.active_count,
    }


@app.get("/tally/status/{client_id}")
async def tally_client_status(client_id: str):
    """Return Tally connection status for a specific client."""
    info = tally_manager.get_status(client_id)
    if not info:
        return {"connected": False, "company_name": None}
    return info


@app.post("/tally/sync-ledgers/{client_id}")
async def sync_ledgers(client_id: str, token: str = Query(...)):
    """Request the Tally agent to send ledger data, then push to Django."""
    if not tally_manager.is_connected(client_id):
        raise HTTPException(status_code=503, detail="Tally agent not connected")

    # Send request to Tally agent via WebSocket
    request_xml = """<ENVELOPE>
        <HEADER><TALLYREQUEST>Export Data</TALLYREQUEST></HEADER>
        <BODY><EXPORTDATA><REQUESTDESC>
            <REPORTNAME>List of Ledgers</REPORTNAME>
        </REQUESTDESC></EXPORTDATA></BODY>
    </ENVELOPE>"""

    await tally_manager.send_to_client(client_id, json.dumps({
        "action": "fetch_ledgers",
        "xml": request_xml,
    }))

    return {"status": "sync_requested", "client_id": client_id}


@app.post("/tally/sync-items/{client_id}")
async def sync_items(client_id: str, token: str = Query(...)):
    """Request the Tally agent to send stock item data."""
    if not tally_manager.is_connected(client_id):
        raise HTTPException(status_code=503, detail="Tally agent not connected")

    request_xml = """<ENVELOPE>
        <HEADER><TALLYREQUEST>Export Data</TALLYREQUEST></HEADER>
        <BODY><EXPORTDATA><REQUESTDESC>
            <REPORTNAME>List of Stock Items</REPORTNAME>
        </REQUESTDESC></EXPORTDATA></BODY>
    </ENVELOPE>"""

    await tally_manager.send_to_client(client_id, json.dumps({
        "action": "fetch_items",
        "xml": request_xml,
    }))

    return {"status": "sync_requested", "client_id": client_id}


@app.post("/tally/send-vouchers/{client_id}")
async def send_vouchers(client_id: str, token: str = Query(...)):
    """
    Send approved vouchers to Tally — two methods supported:
    1. Via WebSocket agent (if connected) – forwards XML through the agent
    2. Via direct HTTP to Tally XML Server (if Tally is reachable on LAN)

    Fetches pending TallyVoucher records from Django, builds XML, sends.
    """
    # Fetch pending vouchers from Django
    vouchers = []
    try:
        async with httpx.AsyncClient() as http:
            resp = await http.get(
                f"{DJANGO_API}/transactions/vouchers/",
                params={"sync_status": "pending", "format": "json"},
                headers={"Authorization": f"Bearer {token}"},
                timeout=15,
            )
            if resp.status_code == 200:
                data = resp.json()
                vouchers = data.get("results", data) if isinstance(data, dict) else data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch vouchers: {e}")

    if not vouchers:
        logger.info("[Tally:SendVouchers] No pending vouchers | client_id=%s", client_id)
        return {"status": "no_pending_vouchers", "client_id": client_id}

    # Get company name from Tally connection
    tally_info = tally_manager.get_status(client_id)
    company_name = tally_info.get("company_name", "") if tally_info else ""

    logger.info(
        "[Tally:SendVouchers] Sending %s vouchers | client_id=%s | company=%s",
        len(vouchers), client_id, company_name,
    )

    # Method 1: If Tally agent is connected via WebSocket, send XML through it
    if tally_manager.is_connected(client_id):
        xml = build_batch_xml(vouchers, company_name)
        await tally_manager.send_to_client(client_id, json.dumps({
            "action": "import_vouchers",
            "xml": xml,
            "voucher_count": len(vouchers),
        }))
        logger.info("[Tally:SendVouchers] Sent via WebSocket agent | client_id=%s | count=%s", client_id, len(vouchers))
        return {
            "status": "sent_via_agent",
            "client_id": client_id,
            "voucher_count": len(vouchers),
        }

    # Method 2: Direct HTTP to Tally XML Server
    logger.info("[Tally:SendVouchers] No WS agent — using direct HTTP to Tally XML Server | client_id=%s", client_id)
    result = await sync_pending_vouchers(vouchers, company_name)
    logger.info("[Tally:SendVouchers] Direct send result | client_id=%s | result=%s", client_id, result)
    return {
        "status": "sent_direct",
        "client_id": client_id,
        **result,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# FILE UPLOAD & PROCESSING
# ═══════════════════════════════════════════════════════════════════════════════


@app.post("/upload/parse")
async def upload_and_parse(
    file: UploadFile = File(...),
    job_id: str = Form(...),
    voucher_type: str = Form("banking"),
):
    """
    Parse an uploaded file (Excel/CSV/PDF/Image).
    For PDFs and images, automatically uses Gemini OCR if the standard
    parser returns raw_text or requires_ocr.
    Returns: column headers + preview rows.
    Stores parsed data in Valkey keyed by job_id.
    """
    try:
        content = await file.read()
        filename = file.filename or "unknown"
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        file_size_kb = round(len(content) / 1024, 1)

        logger.info(
            "[Upload:Parse] START | job_id=%s | file=%s | type=%s | size=%sKB | voucher_type=%s",
            job_id, filename, ext, file_size_kb, voucher_type,
        )

        # First try standard parser (Excel/CSV work directly)
        use_gemini = False
        if ext in ("pdf", "png", "jpg", "jpeg", "tiff", "bmp", "webp"):
            logger.info("[Upload:Parse] Routing to Gemini OCR (binary/image format) | job_id=%s | ext=%s", job_id, ext)
            use_gemini = True
        else:
            logger.debug("[Upload:Parse] Trying standard parser | job_id=%s | ext=%s", job_id, ext)
            result = parse_uploaded_file(content, ext, filename)
            if result.get("requires_ocr") or (
                len(result.get("headers", [])) == 1 and result["headers"][0] == "raw_text"
            ):
                logger.info("[Upload:Parse] Standard parser returned raw_text — escalating to Gemini | job_id=%s", job_id)
                use_gemini = True
            else:
                logger.debug(
                    "[Upload:Parse] Standard parser OK | job_id=%s | headers=%s | rows=%s",
                    job_id, result.get("headers", []), len(result.get("rows", [])),
                )

        if use_gemini:
            # Use Gemini for OCR + structured extraction
            logger.info("[Upload:Parse] Calling Gemini API | job_id=%s | filename=%s | voucher_type=%s", job_id, filename, voucher_type)
            try:
                gemini_result = await extract_with_gemini(content, filename, ext, voucher_type)
                row_count = len(gemini_result.get("rows", []))
                doc_type = gemini_result.get("document_type", voucher_type)
                logger.info(
                    "[Upload:Parse] Gemini extraction SUCCESS | job_id=%s | document_type=%s | rows=%s | headers=%s",
                    job_id, doc_type, row_count, gemini_result.get("headers", []),
                )
                result = {
                    "headers": gemini_result.get("headers", []),
                    "rows": gemini_result.get("rows", []),
                    "source": "gemini",
                    "detected_type": doc_type,
                }
                # Store raw Gemini response for audit
                valkey.setex(
                    f"job:{job_id}:gemini_raw",
                    3600,
                    json.dumps(gemini_result, default=str),
                )
                # Update job in Django with detected document type
                try:
                    async with httpx.AsyncClient() as http:
                        await http.patch(
                            f"{DJANGO_API}/transactions/jobs/{job_id}/",
                            json={"detected_document_type": doc_type},
                            timeout=10,
                        )
                except Exception:
                    pass
            except RuntimeError as e:
                if "GEMINI_API_KEY" in str(e):
                    logger.warning("[Upload:Parse] GEMINI_API_KEY not set — using fallback parser | job_id=%s", job_id)
                    # Gemini not configured – fall back to raw parse
                    if ext in ("pdf", "png", "jpg", "jpeg", "tiff", "bmp", "webp"):
                        result = parse_uploaded_file(content, ext, filename)
                    result["source"] = "fallback"
                else:
                    raise
            except Exception as e:
                logger.error("[Upload:Parse] Gemini extraction FAILED | job_id=%s | error=%s", job_id, e, exc_info=True)
                # Gemini failed – fall back to standard parser
                if ext in ("pdf", "png", "jpg", "jpeg", "tiff", "bmp", "webp"):
                    result = parse_uploaded_file(content, ext, filename)
                result["source"] = "fallback"
                result["gemini_error"] = str(e)
        else:
            result["source"] = "parser"

        row_count = len(result.get("rows", []))
        logger.info(
            "[Upload:Parse] DONE | job_id=%s | source=%s | rows=%s | headers=%s",
            job_id, result.get("source"), row_count, result.get("headers", []),
        )

        # Store parsed data in Valkey for field-mapping step
        valkey.setex(
            f"job:{job_id}:parsed",
            3600,  # 1 hour TTL
            json.dumps(result, default=str),
        )

        # Update job status
        valkey.setex(
            f"job:{job_id}:status",
            3600,
            json.dumps({
                "status": "parsed",
                "row_count": row_count,
                "source": result.get("source", "parser"),
            }),
        )

        return {
            "job_id": job_id,
            "headers": result.get("headers", []),
            "preview": result.get("rows", [])[:10],
            "total_rows": row_count,
            "file_type": ext,
            "source": result.get("source", "parser"),
            "detected_type": result.get("detected_type", voucher_type),
        }

    except Exception as e:
        logger.error("[Upload:Parse] UNHANDLED ERROR | job_id=%s | error=%s", job_id, e, exc_info=True)
        valkey.setex(
            f"job:{job_id}:status",
            3600,
            json.dumps({"status": "failed", "error": str(e)}),
        )
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/upload/gemini-extract")
async def gemini_extract(
    file: UploadFile = File(...),
    job_id: str = Form(...),
    voucher_type: str = Form("banking"),
):
    """
    Dedicated Gemini OCR + extraction endpoint.
    Always uses Gemini regardless of file type.
    Returns structured rows matching Tally voucher fields.
    """
    try:
        content = await file.read()
        filename = file.filename or "unknown"
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

        logger.info(
            "[Upload:GeminiExtract] START | job_id=%s | file=%s | ext=%s | voucher_type=%s",
            job_id, filename, ext, voucher_type,
        )

        gemini_result = await extract_with_gemini(content, filename, ext, voucher_type)
        row_count = len(gemini_result.get("rows", []))
        doc_type = gemini_result.get("document_type", voucher_type)

        logger.info(
            "[Upload:GeminiExtract] SUCCESS | job_id=%s | document_type=%s | rows=%s",
            job_id, doc_type, row_count,
        )

        # Store in Valkey
        valkey.setex(f"job:{job_id}:parsed", 3600, json.dumps(gemini_result, default=str))
        valkey.setex(f"job:{job_id}:gemini_raw", 3600, json.dumps(gemini_result, default=str))
        valkey.setex(
            f"job:{job_id}:status",
            3600,
            json.dumps({"status": "ocr_done", "row_count": row_count, "source": "gemini"}),
        )

        return {
            "job_id": job_id,
            "document_type": doc_type,
            "headers": gemini_result.get("headers", []),
            "rows": gemini_result.get("rows", [])[:20],
            "total_rows": row_count,
            "source": "gemini",
        }
    except Exception as e:
        logger.error("[Upload:GeminiExtract] FAILED | job_id=%s | error=%s", job_id, e, exc_info=True)
        valkey.setex(
            f"job:{job_id}:status",
            3600,
            json.dumps({"status": "failed", "error": str(e)}),
        )
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/upload/save-rows")
async def save_rows_to_django(
    job_id: str = Form(...),
    token: str = Form(""),
):
    """
    Take parsed/mapped rows from Valkey and persist them into Django
    TransactionRow models. This is the Gemini → DB data mapping step.
    """
    logger.info("[Upload:SaveRows] START | job_id=%s", job_id)

    # Prefer mapped data, fall back to parsed (Gemini) data
    source_key = "mapped" if valkey.exists(f"job:{job_id}:mapped") else "parsed"
    raw = valkey.get(f"job:{job_id}:{source_key}")
    if not raw:
        logger.warning("[Upload:SaveRows] No data in Valkey | job_id=%s", job_id)
        raise HTTPException(status_code=404, detail="No parsed/mapped data found for this job.")

    logger.debug("[Upload:SaveRows] Reading from Valkey key '%s' | job_id=%s", source_key, job_id)
    data = json.loads(raw)
    rows = data if isinstance(data, list) else data.get("rows", [])

    if not rows:
        logger.warning("[Upload:SaveRows] Zero rows in Valkey data | job_id=%s", job_id)
        raise HTTPException(status_code=400, detail="No rows to save.")

    # Prepare rows for Django bulk-create
    payload = {
        "job_id": job_id,
        "rows": [],
    }
    for i, row in enumerate(rows):
        mapped_row = {
            "row_number": row.get("_row_number", i + 1),
            "raw_data": {k: v for k, v in row.items() if k not in (
                "_row_number", "extra_data", "assigned_ledger",
                "assigned_ledger_name", "matched_rule_id",
            )},
            "date": row.get("date"),
            "voucher_type": row.get("voucher_type", ""),
            "voucher_number": row.get("voucher_number", ""),
            "description": str(row.get("description", ""))[:1000],
            "narration": str(row.get("description", "")),
            "reference": str(row.get("reference", ""))[:255],
            "party_name": str(row.get("party_name", ""))[:255],
            "invoice_no": str(row.get("invoice_no", ""))[:100],
            "debit": float(row.get("debit", 0) or 0),
            "credit": float(row.get("credit", 0) or 0),
            "amount": float(row.get("amount", 0) or 0),
            "gst_rate": float(row.get("gst_rate", 0) or 0),
            "cgst": float(row.get("cgst", 0) or 0),
            "sgst": float(row.get("sgst", 0) or 0),
            "igst": float(row.get("igst", 0) or 0),
            "taxable_amount": float(row.get("taxable_amount", 0) or 0),
            "place_of_supply": str(row.get("place_of_supply", ""))[:100],
            "hsn_code": str(row.get("hsn_code", ""))[:20],
            "ledger_name": str(row.get("ledger_name", ""))[:255],
            "ledger_source": row.get("ledger_source", ""),
            "extra_data": row.get("extra_data") or row.get("extra"),
        }
        payload["rows"].append(mapped_row)

    logger.info("[Upload:SaveRows] Sending %s rows to Django | job_id=%s", len(payload["rows"]), job_id)

    # POST to Django to create TransactionRows
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        async with httpx.AsyncClient() as http:
            resp = await http.post(
                f"{DJANGO_API}/transactions/jobs/{job_id}/save-rows/",
                json=payload,
                headers=headers,
                timeout=30,
            )
            if resp.status_code >= 400:
                logger.error(
                    "[Upload:SaveRows] Django rejected rows | job_id=%s | status=%s | detail=%s",
                    job_id, resp.status_code, resp.text[:500],
                )
                return {"status": "error", "detail": resp.text, "rows_sent": len(payload["rows"])}
    except Exception as e:
        logger.error("[Upload:SaveRows] HTTP error posting to Django | job_id=%s | error=%s", job_id, e, exc_info=True)
        return {"status": "error", "detail": str(e), "rows_sent": len(payload["rows"])}

    logger.info("[Upload:SaveRows] DONE | job_id=%s | rows_saved=%s", job_id, len(payload["rows"]))
    return {
        "status": "saved",
        "job_id": job_id,
        "rows_saved": len(payload["rows"]),
    }


@app.post("/upload/apply-mapping")
async def apply_mapping(
    job_id: str = Form(...),
    mapping: str = Form(...),  # JSON string of { source_col: target_field }
    voucher_type: str = Form("banking"),
    client_state: str = Form(""),
    client_id: str = Form(""),
):
    """
    Apply the 3-layer mapping:
    1. Field Mapping (user-defined)
    2. GST Mapping (auto-calculated based on POS vs state)
    3. Rule Matching (from client's saved rules)
    """
    raw = valkey.get(f"job:{job_id}:parsed")
    if not raw:
        logger.warning("[Upload:ApplyMapping] No parsed data in Valkey | job_id=%s", job_id)
        raise HTTPException(status_code=404, detail="Parsed data not found. Re-upload the file.")

    parsed = json.loads(raw)
    field_map = json.loads(mapping)
    input_rows = len(parsed.get("rows", []))

    logger.info(
        "[Upload:ApplyMapping] START | job_id=%s | voucher_type=%s | state=%s | input_rows=%s | mapping_keys=%s",
        job_id, voucher_type, client_state, input_rows, list(field_map.keys()),
    )

    # Layer 1: Field Mapping
    mapped_rows = apply_field_mapping(parsed["rows"], field_map)
    logger.debug("[Upload:ApplyMapping] Layer 1 (Field Mapping) done | job_id=%s | rows=%s", job_id, len(mapped_rows))

    # Layer 2: GST Mapping
    mapped_rows = apply_gst_mapping(mapped_rows, voucher_type, client_state)
    logger.debug("[Upload:ApplyMapping] Layer 2 (GST Mapping) done | job_id=%s | voucher_type=%s | state=%s", job_id, voucher_type, client_state)

    # Layer 3: Rule Matching (fetch rules from Django)
    rules = []
    if client_id:
        try:
            async with httpx.AsyncClient() as http:
                resp = await http.get(
                    f"{DJANGO_API}/masters/rules/",
                    params={"format": "json"},
                    headers={"Authorization": f"Bearer {valkey.get(f'job:{job_id}:token') or ''}"},
                    timeout=10,
                )
                if resp.status_code == 200:
                    rules = resp.json().get("results", resp.json()) if isinstance(resp.json(), dict) else resp.json()
                    logger.debug("[Upload:ApplyMapping] Fetched %s rules | job_id=%s | client_id=%s", len(rules), job_id, client_id)
        except Exception as e:
            logger.warning("[Upload:ApplyMapping] Could not fetch rules (skipping) | job_id=%s | error=%s", job_id, e)

    mapped_rows = apply_rule_matching(mapped_rows, rules)
    auto_matched = sum(1 for r in mapped_rows if r.get("ledger_source") == "rule")
    logger.info(
        "[Upload:ApplyMapping] Layer 3 (Rule Matching) done | job_id=%s | rule_matches=%s / %s",
        job_id, auto_matched, len(mapped_rows),
    )

    # Store mapped result in Valkey
    valkey.setex(f"job:{job_id}:mapped", 3600, json.dumps(mapped_rows, default=str))
    valkey.setex(
        f"job:{job_id}:status",
        3600,
        json.dumps({"status": "mapped", "row_count": len(mapped_rows)}),
    )

    logger.info("[Upload:ApplyMapping] DONE | job_id=%s | total_mapped=%s", job_id, len(mapped_rows))

    return {
        "job_id": job_id,
        "rows": mapped_rows[:20],  # Preview
        "total_rows": len(mapped_rows),
        "status": "mapped",
    }


@app.get("/upload/job-status/{job_id}")
async def job_status(job_id: str):
    """Poll for async job status."""
    raw = valkey.get(f"job:{job_id}:status")
    if not raw:
        return {"job_id": job_id, "status": "not_found"}
    return {"job_id": job_id, **json.loads(raw)}


@app.get("/upload/mapped-data/{job_id}")
async def get_mapped_data(job_id: str, page: int = 1, page_size: int = 50):
    """Return paginated mapped data for the AI preview grid."""
    raw = valkey.get(f"job:{job_id}:mapped")
    if not raw:
        raise HTTPException(status_code=404, detail="Mapped data not found")

    rows = json.loads(raw)
    start = (page - 1) * page_size
    end = start + page_size

    return {
        "job_id": job_id,
        "rows": rows[start:end],
        "total_rows": len(rows),
        "page": page,
        "page_size": page_size,
        "total_pages": (len(rows) + page_size - 1) // page_size,
    }
