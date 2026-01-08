import os
import json
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple, List
from urllib.parse import urlparse

import requests
from secret_key import PERPLEXITY_API_KEY

# ================= PERPLEXITY =================
if not PERPLEXITY_API_KEY:
    raise RuntimeError("PERPLEXITY_API_KEY not set in secret_key.py")

PPLX_ENDPOINT = "https://api.perplexity.ai/chat/completions"
PPLX_MODEL = "sonar"

# ================= PATHS =================
ROOT_DIR = Path(__file__).resolve().parents[1]
CACHE_PATH = ROOT_DIR / "data" / "stock_cache" / "stocks_cache.json"

# ================= SETTINGS =================
MAX_ABS_DAILY_CHANGE = 20.0
DEBUG_RAW_MAX_CHARS = 900

# Small / low-liquidity markets where 0.0 change might be ok
LOW_LIQUIDITY_COUNTRIES = {"AL", "AZ", "BA", "ME", "MK", "GE", "MD", "MT", "UA", "BY", "AM"}

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

def is_http_url(s: Any) -> bool:
    return isinstance(s, str) and (s.startswith("https://") or s.startswith("http://"))

def is_pdf_url(url: str) -> bool:
    return url.lower().split("?")[0].endswith(".pdf")

def netloc(url: str) -> str:
    try:
        return (urlparse(url).netloc or "").lower()
    except Exception:
        return ""

def load_cache() -> Dict[str, Any]:
    if not CACHE_PATH.exists():
        return {}
    try:
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}

def save_cache_atomic(cache: Dict[str, Any]) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = CACHE_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, CACHE_PATH)

def _clean_debug_raw(s: str) -> str:
    s = (s or "").strip()
    s = re.sub(r"\s+", " ", s)
    return s[:DEBUG_RAW_MAX_CHARS]

def extract_json_or_null(text: str) -> Optional[Dict[str, Any]]:
    """Extract a JSON object from model output; safely remove thousands commas inside numbers only."""
    if not isinstance(text, str):
        return None
    t = text.strip()

    # strip code fences
    t = re.sub(r"^\s*```(?:json)?\s*", "", t, flags=re.IGNORECASE)
    t = re.sub(r"\s*```\s*$", "", t).strip()

    if t.lower() == "null":
        return None

    # keep only first {...}
    m = re.search(r"\{.*\}", t, flags=re.DOTALL)
    if not m:
        return None
    t = m.group(0).strip()

    # first try
    try:
        obj = json.loads(t)
        return obj if isinstance(obj, dict) else None
    except Exception:
        pass

    # sanitize 1,234.56 -> 1234.56 ONLY inside numeric literals (not delimiters)
    def strip_thousands_commas(s: str) -> str:
        # numbers NOT in quotes
        s = re.sub(
            r'(:\s*)(-?\d{1,3}(?:,\d{3})+(?:\.\d+)?)(?=\s*[,}])',
            lambda mo: mo.group(1) + mo.group(2).replace(",", ""),
            s
        )
        # numbers IN quotes
        s = re.sub(
            r'(:\s*")(-?\d{1,3}(?:,\d{3})+(?:\.\d+)?)(\")',
            lambda mo: mo.group(1) + mo.group(2).replace(",", "") + mo.group(3),
            s
        )
        return s

    t2 = strip_thousands_commas(t)
    try:
        obj = json.loads(t2)
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None

def parse_number(x: Any) -> Optional[float]:
    if isinstance(x, (int, float)):
        return float(x)
    if not isinstance(x, str):
        return None

    s = x.strip().replace("%", "").strip()
    s = re.sub(r"[^0-9,\.\-\s+]", "", s).strip()
    if not s:
        return None
    s = s.replace(" ", "")

    if "," in s and "." in s:
        # 1,234.56 or 1.234,56
        last_comma = s.rfind(",")
        last_dot = s.rfind(".")
        if last_dot > last_comma:
            s = s.replace(",", "")
        else:
            s = s.replace(".", "")
            s = s.replace(",", ".")
    else:
        if "," in s and "." not in s:
            parts = s.split(",")
            if len(parts) == 2 and len(parts[1]) == 3 and len(parts[0]) >= 1:
                s = s.replace(",", "")
            else:
                s = s.replace(",", ".")
        elif "." in s and "," not in s:
            parts = s.split(".")
            if len(parts) > 2 or (len(parts) == 2 and len(parts[1]) == 3):
                s = s.replace(".", "")

    try:
        return float(s)
    except Exception:
        return None

# ============ EU country configs only ============
COUNTRIES: Dict[str, Dict[str, Any]] = {
    "AT": {"query": "ATX index latest value and daily percent change"},
    "BE": {"query": "BEL 20 index latest value and daily percent change"},
    "BG": {"query": "SOFIX index latest value and daily percent change"},
    "HR": {"query": "CROBEX index latest value and daily percent change"},
    "CY": {"query": "CSE General Index latest value and daily percent change"},
    "CZ": {"query": "PX index latest value and daily percent change"},
    "DK": {"query": "OMXC25 index latest value and daily percent change"},
    "EE": {"query": "OMXTGI index latest value and daily percent change"},
    "FI": {"query": "OMXH25 index latest value and daily percent change"},
    "FR": {"query": "CAC 40 index latest value and daily percent change"},
    "DE": {"query": "DAX index latest value and daily percent change"},
    "GR": {"query": "ATHEX Composite index latest value and daily percent change"},
    "HU": {"query": "BUX index latest value and daily percent change"},
    "IE": {"query": "ISEQ 20 index latest value and daily percent change"},
    "IT": {"query": "FTSE MIB index latest value and daily percent change"},
    "LV": {"query": "OMXRGI index latest value and daily percent change"},
    "LT": {"query": "OMXVGI index latest value and daily percent change"},
    "LU": {"query": "LuxSE main stock index latest value and daily percent change"},
    "MT": {"query": "MSETRX index latest value and daily percent change"},
    "NL": {"query": "AEX index latest value and daily percent change"},
    "PL": {"query": "WIG20 index latest value and daily percent change"},
    "PT": {"query": "PSI index latest value and daily percent change"},
    "RO": {"query": "BET index latest value and daily percent change"},
    "SK": {"query": "SAX index latest value and daily percent change"},
    "SI": {"query": "SBITOP index latest value and daily percent change"},
    "ES": {"query": "IBEX 35 index latest value and daily percent change"},
    "SE": {"query": "OMXS30 index latest value and daily percent change"},
}

def _attempt_fetch(
    country_code: str,
    query: str,
) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:

    prompt = f"""
You are a financial data assistant.

Task:
- Find the main benchmark STOCK INDEX for this country code: {country_code}.
- Return ONLY a JSON object with the latest live data.

JSON schema (no extra keys):
{{
  "index": "string, index name",
  "value": number or string, latest index level,
  "change_percent": number or string, DAILY percent change vs previous close,
  "source": "https://..."
}}

Rules:
- Use any reliable financial or stock exchange website.
- Do NOT include thousands commas in numbers (write 5077.71 not 5,077.71).
- change_percent must be DAILY percent change, not YTD.
- Output must be ONLY the JSON object, no explanation text.

User query:
{query}
""".strip()

    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": PPLX_MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "stream": False,
    }

    resp = requests.post(PPLX_ENDPOINT, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    # Adjust to actual Perplexity response structure if needed
    raw = data["choices"][0]["message"]["content"].strip()
    debug = {"raw": _clean_debug_raw(raw)}

    if raw.lower().strip() == "null":
        debug["reason_code"] = "model_null"
        debug["reason"] = "Model returned null"
        return None, debug

    obj = extract_json_or_null(raw)
    if obj is None:
        debug["reason_code"] = "json_parse_failed"
        debug["reason"] = "Could not parse JSON from model output"
        return None, debug

    idx = obj.get("index")
    val_raw = obj.get("value")
    chg_raw = obj.get("change_percent")
    src = obj.get("source")

    if not isinstance(idx, str) or not idx.strip():
        debug["reason_code"] = "schema_invalid"
        debug["reason"] = "Missing/invalid 'index'"
        return None, debug

    val = parse_number(val_raw)
    if val is None:
        debug["reason_code"] = "number_invalid"
        debug["reason"] = f"Invalid 'value': {val_raw!r}"
        return None, debug

    chg = parse_number(chg_raw)
    if chg is None:
        debug["reason_code"] = "number_invalid"
        debug["reason"] = f"Invalid 'change_percent': {chg_raw!r}"
        return None, debug

    if abs(float(chg)) > MAX_ABS_DAILY_CHANGE:
        debug["reason_code"] = "change_out_of_range"
        debug["reason"] = f"change_percent out of range: {chg}"
        return None, debug

    if float(val) == 0.0 and float(chg) == 0.0 and country_code not in LOW_LIQUIDITY_COUNTRIES:
        debug["reason_code"] = "zero_data_suspect"
        debug["reason"] = "0.0 value and 0.0 change is suspicious"
        return None, debug

    if not is_http_url(src):
        debug["reason_code"] = "source_invalid"
        debug["reason"] = f"Invalid source URL: {src!r}"
        return None, debug

    return {
        "status": "ok",
        "index": idx.strip(),
        "value": float(val),
        "change_percent": float(chg),
        "source": src,
        "updated_at": utc_now_iso(),
    }, debug

def fetch_country(code: str) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
    cfg = COUNTRIES[code]
    return _attempt_fetch(
        country_code=code,
        query=cfg["query"],
    )

def run() -> None:
    cache = load_cache()

    for code in COUNTRIES.keys():
        print(f"🔍 Fetching {code}...")
        try:
            result, debug = fetch_country(code)

            if result:
                cache[code] = result
                print(f"✔ {code} updated")
            else:
                cache[code] = {
                    "status": "skipped",
                    "reason_code": debug.get("reason_code", "unknown"),
                    "reason": debug.get("reason", "no valid data"),
                    "debug_raw": debug.get("raw", ""),
                    "updated_at": utc_now_iso(),
                }
                print(f"⚠ {code} skipped ({cache[code]['reason_code']})")

        except Exception as e:
            cache[code] = {
                "status": "error",
                "reason_code": "exception",
                "reason": str(e),
                "updated_at": utc_now_iso(),
            }
            print(f"❌ {code} error: {e}")

        save_cache_atomic(cache)

    print(f"\n✅ Stock cache updated successfully -> {CACHE_PATH}")

if __name__ == "__main__":
    run()
