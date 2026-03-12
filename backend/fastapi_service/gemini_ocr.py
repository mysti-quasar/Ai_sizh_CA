"""
SIZH CA – Gemini OCR & Structured Data Extraction
====================================================
Uses Google Gemini API (vision + text models) to:
  1. OCR scanned PDFs / images (JPEG, PNG, TIFF)
  2. Extract structured financial / invoice data from any document
  3. Return rows that mirror Tally voucher fields
"""

import io
import os
import json
import base64
import re
from typing import Any

import google.generativeai as genai

# ── Configure Gemini ────────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Prompt template – instructs Gemini to output JSON matching Tally fields
_EXTRACTION_PROMPT = """You are an expert Indian financial data extraction system.
Analyse the uploaded document (which may be a bank statement, sales invoice,
purchase bill, journal voucher, ledger list, or stock item list) and return
**only** a JSON object with the following structure. Do NOT return anything
outside the JSON block.

{{
  "document_type": "banking" | "sales" | "purchase" | "sales_return" | "purchase_return" | "journal" | "ledger" | "items",
  "headers": [ <list of column / field names detected> ],
  "rows": [
    {{
      "date": "DD-MM-YYYY or DD/MM/YYYY",
      "voucher_type": "Payment | Receipt | Contra | Journal | Sales | Purchase | Credit Note | Debit Note",
      "voucher_number": "string or null",
      "reference": "Ref / Chq / UTR number or empty string",
      "description": "narration / particulars",
      "party_name": "party / ledger name or empty string",
      "ledger_name": "suggested Tally ledger name if identifiable, else empty string",
      "debit": 0.00,
      "credit": 0.00,
      "amount": 0.00,
      "gst_rate": 0.00,
      "cgst": 0.00,
      "sgst": 0.00,
      "igst": 0.00,
      "taxable_amount": 0.00,
      "place_of_supply": "State name or code or empty string",
      "hsn_code": "HSN/SAC code or empty string",
      "invoice_no": "invoice number or empty string",
      "extra": {{ ... any other relevant key-value pairs ... }}
    }}
    // ... one object per line-item / transaction row
  ]
}}

Rules:
- Ensure every monetary value is a number (not a string).
- If a field is not found in the document, set it to null or 0 as appropriate.
- For bank statements: map withdrawals → debit, deposits → credit.
- For invoices: calculate taxable_amount and GST splits where possible.
- Return the JSON **only** – no markdown fences, no commentary.
"""


def _configure_genai():
    """Lazy-configure the Gemini client."""
    key = GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
    if not key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Add it to backend/.env or as an environment variable."
        )
    genai.configure(api_key=key)


def _extract_json(text: str) -> dict:
    """Robustly extract the first JSON object from Gemini's response text."""
    # Strip markdown code fences if present
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*$", "", text)
    text = text.strip()

    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Find first { ... } block
    depth = 0
    start = None
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start is not None:
                try:
                    return json.loads(text[start : i + 1])
                except json.JSONDecodeError:
                    start = None

    raise ValueError("Could not parse a valid JSON object from Gemini response.")


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════════


async def extract_with_gemini(
    content: bytes,
    filename: str,
    file_ext: str,
    voucher_type_hint: str = "",
) -> dict[str, Any]:
    """
    Send a document (PDF / image / Excel text) to Gemini and return
    structured extraction as { document_type, headers, rows }.

    Parameters
    ----------
    content : raw bytes of the uploaded file
    filename : original file name
    file_ext : lowercase extension (pdf, png, jpg, xlsx, csv …)
    voucher_type_hint : optional hint from the user's selection

    Returns
    -------
    dict  –  { "document_type": str, "headers": list, "rows": list[dict] }
    """
    _configure_genai()

    model = genai.GenerativeModel("gemini-2.0-flash")

    hint_line = ""
    if voucher_type_hint:
        hint_line = f"\n\nHint: The user selected voucher type = '{voucher_type_hint}'. Use it if the document type is ambiguous."

    prompt = _EXTRACTION_PROMPT + hint_line

    # Decide how to send the file to Gemini
    if file_ext in ("png", "jpg", "jpeg", "tiff", "bmp", "webp"):
        mime_map = {
            "png": "image/png",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "tiff": "image/tiff",
            "bmp": "image/bmp",
            "webp": "image/webp",
        }
        mime = mime_map.get(file_ext, "image/png")
        image_part = {"inline_data": {"mime_type": mime, "data": base64.b64encode(content).decode()}}
        response = model.generate_content([prompt, image_part])

    elif file_ext == "pdf":
        pdf_part = {"inline_data": {"mime_type": "application/pdf", "data": base64.b64encode(content).decode()}}
        response = model.generate_content([prompt, pdf_part])

    else:
        # For text-based files (CSV / already-parsed Excel), send as text
        text_content = content.decode("utf-8", errors="replace")[:50000]  # Gemini context limit safety
        response = model.generate_content(
            f"{prompt}\n\n--- DOCUMENT CONTENT ---\n{text_content}"
        )

    raw_text = response.text
    result = _extract_json(raw_text)

    # Normalise structure
    if "rows" not in result:
        result["rows"] = []
    if "headers" not in result:
        # Derive headers from first row's keys
        if result["rows"]:
            result["headers"] = list(result["rows"][0].keys())
        else:
            result["headers"] = []
    if "document_type" not in result:
        result["document_type"] = voucher_type_hint or "banking"

    return result


async def ocr_image_to_text(content: bytes, file_ext: str) -> str:
    """Simple OCR: extract raw text from an image via Gemini vision."""
    _configure_genai()
    model = genai.GenerativeModel("gemini-2.0-flash")

    mime_map = {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "tiff": "image/tiff",
        "bmp": "image/bmp",
        "webp": "image/webp",
        "pdf": "application/pdf",
    }
    mime = mime_map.get(file_ext, "image/png")
    part = {"inline_data": {"mime_type": mime, "data": base64.b64encode(content).decode()}}
    response = model.generate_content(
        ["Extract ALL text from this document image. Return plain text only, preserving table structure with pipes (|) as column separators.", part]
    )
    return response.text
