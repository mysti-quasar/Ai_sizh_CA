"""
SIZH CA - File Parser
======================
Parses Excel, CSV, PDF, and image files into a uniform
{ headers: [...], rows: [{...}, ...] } structure.
"""

import io
import csv
from typing import Any

import pandas as pd


def parse_uploaded_file(content: bytes, ext: str, filename: str) -> dict:
    """
    Parse file content based on extension.
    Returns: { "headers": [...], "rows": [{col: val, ...}, ...] }
    """
    ext = ext.lower()

    if ext in ("xlsx", "xls"):
        return _parse_excel(content)
    elif ext == "csv":
        return _parse_csv(content)
    elif ext == "pdf":
        return _parse_pdf(content, filename)
    elif ext in ("png", "jpg", "jpeg", "tiff", "bmp"):
        return _parse_image(content, filename)
    else:
        raise ValueError(f"Unsupported file type: .{ext}")


def _parse_excel(content: bytes) -> dict:
    """Parse Excel file using pandas."""
    df = pd.read_excel(io.BytesIO(content), engine="openpyxl")
    df = df.dropna(how="all")  # Remove empty rows
    # Clean column names
    df.columns = [str(c).strip() for c in df.columns]
    headers = list(df.columns)
    rows = df.fillna("").to_dict(orient="records")
    return {"headers": headers, "rows": rows}


def _parse_csv(content: bytes) -> dict:
    """Parse CSV file using pandas."""
    # Try to detect encoding
    text = content.decode("utf-8", errors="replace")
    df = pd.read_csv(io.StringIO(text))
    df = df.dropna(how="all")
    df.columns = [str(c).strip() for c in df.columns]
    headers = list(df.columns)
    rows = df.fillna("").to_dict(orient="records")
    return {"headers": headers, "rows": rows}


def _parse_pdf(content: bytes, filename: str) -> dict:
    """
    Parse PDF file. Uses tabula-py if available, otherwise falls back
    to a basic text extraction approach.
    For production: integrate AWS Textract or Google Document AI.
    """
    try:
        import tabula
        dfs = tabula.read_pdf(io.BytesIO(content), pages="all", multiple_tables=True)
        if dfs:
            df = pd.concat(dfs, ignore_index=True)
            df = df.dropna(how="all")
            df.columns = [str(c).strip() for c in df.columns]
            return {
                "headers": list(df.columns),
                "rows": df.fillna("").to_dict(orient="records"),
            }
    except ImportError:
        pass

    # Fallback: return placeholder indicating OCR is needed
    return {
        "headers": ["raw_text"],
        "rows": [{"raw_text": f"[PDF file: {filename} - requires OCR processing]"}],
        "requires_ocr": True,
    }


def _parse_image(content: bytes, filename: str) -> dict:
    """
    Parse image file using OCR.
    For production: integrate Tesseract or AWS Textract.
    """
    try:
        from PIL import Image
        import pytesseract
        img = Image.open(io.BytesIO(content))
        text = pytesseract.image_to_string(img)
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        return {
            "headers": ["raw_text"],
            "rows": [{"raw_text": line} for line in lines],
        }
    except ImportError:
        pass

    # Fallback
    return {
        "headers": ["raw_text"],
        "rows": [{"raw_text": f"[Image file: {filename} - requires OCR processing]"}],
        "requires_ocr": True,
    }
