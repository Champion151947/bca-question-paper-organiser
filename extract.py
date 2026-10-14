"""extract.py - Extract text from question paper PDFs.

Uses PyMuPDF for text-based PDFs. If a PDF has no usable text layer it is
rendered to images and OCR'd with pytesseract (if Tesseract is installed) and
the result is marked as method='ocr'.

Results are cached in _cache/text/<key>.json so re-runs do not repeat OCR.
Originals are never modified.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import re
import shutil
import sys
import time
from pathlib import Path

import fitz  # PyMuPDF

MIN_TEXT_CHARS = 150             # ignore tiny text layers ("Scanned by ...")
DEFAULT_DPI = 300
OCR_VERSION = "psm4-v3"          # bump to invalidate cached OCR

# Some papers embed math via the SymbolMT font whose glyphs live in the
# Private Use Area. Without correction those show as empty boxes.  In that
# font U+F0XX is the Latin-1 char U+00XX, and the U+F8EE..FB / U+F8EB..F8
# clusters are matrix bracket pieces (middle pieces outnumber the corners).
_PUA_LATIN1_BASE = 0xF000
_PUA_MATRIX = {
    0xF8EE: "\u23A1",  # left, top       (
    0xF8EF: "\u23A2",  # left, middle
    0xF8F0: "\u23A3",  # left, bottom    )
    0xF8F9: "\u23A4",  # right, top
    0xF8FA: "\u23A5",  # right, middle
    0xF8FB: "\u23A6",  # right, bottom
    0xF8EB: "\u23A1",
    0xF8EC: "\u23A2",
    0xF8ED: "\u23A3",
    0xF8F6: "\u23A4",
    0xF8F7: "\u23A5",
    0xF8F8: "\u23A6",
}


def fix_pua(text: str) -> str:
    """Translate SymbolMT Private-Use-Area characters into real Unicode."""
    if not text:
        return text
    out = []
    for ch in text:
        o = ord(ch)
        if 0xE000 <= o <= 0xF8FF:
            r = _PUA_MATRIX.get(o)
            if r is None and 0xE000 <= o <= 0xF0FF:
                lat = o - _PUA_LATIN1_BASE
                if 0x20 <= lat <= 0xFF:
                    r = chr(lat)
            if r:
                out.append(r)
        else:
            out.append(ch)
    return "".join(out)

_TESSERACT_CANDIDATES = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Tesseract-OCR", "tesseract.exe"),
    os.path.join(os.environ.get("LOCALAPPDATA", ""), "Tesseract-OCR", "tesseract.exe"),
]


def find_tesseract() -> str | None:
    """Return the path to the tesseract executable, or None."""
    p = shutil.which("tesseract")
    if p:
        return p
    for c in _TESSERACT_CANDIDATES:
        if c and os.path.isfile(c):
            return c
    return None


def _word_score(text: str) -> int:
    return len(re.findall(r"[A-Za-z]{3,}", text))


_QNUM_LINE = re.compile(r"(?m)^\s*\(?(\d{1,2})[\.\)]\s+\S")
_BARE_NUM = re.compile(r"(?m)^\s*\(?\d{1,2}[\.\)]?\s*$")


def _qnum_score(text: str) -> int:
    """Count inline 'N. text' lines - a proxy for correct reading order."""
    return len(_QNUM_LINE.findall(text))


def _bare_numbers(text: str) -> int:
    """Count lines that are just a number (sign of a split number column)."""
    return len(_BARE_NUM.findall(text))


def _tess(img, config: str) -> str:
    import pytesseract
    try:
        return pytesseract.image_to_string(img, config=config)
    except Exception:
        return ""


def _ocr_page(page: "fitz.Page", dpi: int = DEFAULT_DPI) -> str:
    from PIL import Image

    pix = page.get_pixmap(dpi=dpi)
    img = Image.open(io.BytesIO(pix.tobytes("png")))

    # Some papers print question numbers in a narrow left column. PSM 4 then
    # reads that column as a separate block (numbers on their own lines) and
    # loses the pairing with the text, while PSM 6 merges them line-by-line.
    # Score both by how many inline "N. text" lines they recover and pick the
    # better one.
    p4 = _tess(img, "--psm 4")
    p6 = _tess(img, "--psm 6")
    best = max((p4, p6), key=lambda t: (_qnum_score(t), _word_score(t)))

    # If the page still looks poor (e.g. rotated scan), try other rotations.
    if _word_score(best) < 15:
        for ang in (90, 180, 270):
            rot = img.rotate(ang, expand=True)
            for cfg in ("--psm 4", "--psm 6"):
                t = _tess(rot, cfg)
                if (_qnum_score(t), _word_score(t)) > \
                        (_qnum_score(best), _word_score(best)):
                    best = t
    return best


def _cache_key(path: str) -> str:
    st = os.stat(path)
    raw = "%s|%d|%d|%s|%d" % (os.path.abspath(path), st.st_size,
                              int(st.st_mtime), OCR_VERSION, DEFAULT_DPI)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def extract_pdf(path: str, ocr: bool = True, use_cache: bool = True,
                cache_dir: str | None = None, dpi: int = DEFAULT_DPI) -> dict:
    """Extract text from a single PDF.

    Returns dict with keys: text, method, error.
    method is one of: text, ocr, ocr_empty, no_text, no_tesseract, error.
    """
    result = {"text": "", "method": "text", "error": None}

    cache_file = None
    if use_cache and cache_dir:
        os.makedirs(cache_dir, exist_ok=True)
        try:
            cache_file = os.path.join(cache_dir, _cache_key(path) + ".json")
            if os.path.isfile(cache_file):
                with open(cache_file, "r", encoding="utf-8") as fh:
                    cached = json.load(fh)
                # Re-extract if a cached "text" result is now suspiciously short
                if not (cached.get("method") == "text"
                        and len((cached.get("text") or "").strip())
                        < MIN_TEXT_CHARS):
                    # Re-OCR cached scans whose numbers landed in a separate
                    # column (a run of bare number-only lines).
                    if not (cached.get("method") == "ocr"
                            and _bare_numbers(cached.get("text") or "") >= 3):
                        return cached
        except Exception:
            cache_file = None

    try:
        doc = fitz.open(path)
    except Exception as exc:  # unreadable / corrupt
        result["method"] = "error"
        result["error"] = "%s: %s" % (type(exc).__name__, exc)
        _write_cache(cache_file, result)
        return result

    text_parts: list[str] = []
    for page in doc:
        try:
            text_parts.append(page.get_text())
        except Exception as exc:
            result["error"] = "%s: %s" % (type(exc).__name__, exc)
    text = "\n".join(text_parts)

    if len(text.strip()) >= MIN_TEXT_CHARS:
        result["text"] = text
        result["method"] = "text"
        doc.close()
        _write_cache(cache_file, result)
        return result

    if not ocr:
        result["text"] = text
        result["method"] = "no_text"
        doc.close()
        _write_cache(cache_file, result)
        return result

    tess = find_tesseract()
    if not tess:
        result["text"] = text
        result["method"] = "no_tesseract"
        result["error"] = "Tesseract engine not found; OCR skipped."
        doc.close()
        _write_cache(cache_file, result)
        return result

    import pytesseract
    pytesseract.pytesseract.tesseract_cmd = tess

    ocr_parts: list[str] = []
    for page in doc:
        try:
            ocr_parts.append(_ocr_page(page, dpi=dpi))
        except Exception as exc:
            result["error"] = "OCR %s: %s" % (type(exc).__name__, exc)
    ocr_text = "\n".join(ocr_parts)
    doc.close()

    result["text"] = ocr_text
    result["method"] = "ocr" if len(ocr_text.strip()) >= MIN_TEXT_CHARS else "ocr_empty"
    _write_cache(cache_file, result)
    return result


def _write_cache(cache_file: str | None, result: dict) -> None:
    if not cache_file:
        return
    try:
        with open(cache_file, "w", encoding="utf-8") as fh:
            json.dump(result, fh, ensure_ascii=False)
    except Exception:
        pass


def find_pdfs(root: str) -> list[str]:
    """Recursively find every PDF under root (sorted)."""
    out = []
    for dirpath, _dirnames, filenames in os.walk(root):
        for fn in filenames:
            if fn.lower().endswith(".pdf"):
                out.append(os.path.join(dirpath, fn))
    return sorted(out)


def run_extract(pdfs: list[str], root: str, cache_dir: str,
                ocr: bool = True, limit: int | None = None,
                logger=None) -> list[dict]:
    """Extract text for a list of PDFs, showing a progress counter.

    Returns a list of dicts: {path, rel, text, method, error}.
    """
    results: list[dict] = []
    total = len(pdfs) if limit is None else min(limit, len(pdfs))
    start = time.time()
    for i, path in enumerate(pdfs[:total], 1):
        rel = os.path.relpath(path, root)
        try:
            res = extract_pdf(path, ocr=ocr, use_cache=True, cache_dir=cache_dir)
        except Exception as exc:  # never let one file break the run
            res = {"text": "", "method": "error",
                   "error": "%s: %s" % (type(exc).__name__, exc)}
        rec = {"path": path, "rel": rel, **res}
        rec["text"] = fix_pua(rec.get("text") or "")
        results.append(rec)
        if logger and res["method"] in ("error", "no_tesseract"):
            logger(rel, res["error"] or res["method"])
        elapsed = time.time() - start
        sys.stdout.write("\r  extracting [%d/%d] %-60.60s  (%s)" % (
            i, total, rel, res["method"]))
        sys.stdout.flush()
    sys.stdout.write("\n")
    return results


if __name__ == "__main__":
    base = os.path.dirname(os.path.abspath(__file__))
    pdfs = find_pdfs(base)
    print("Found %d PDFs" % len(pdfs))
    print("Tesseract:", find_tesseract())
