import os
import json
import re
from datetime import datetime
from openai import OpenAI

# ================= OPENAI =================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY not set in environment")

client = OpenAI(api_key=OPENAI_API_KEY)

# ================= PATHS =================
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_PATH = os.path.join(
    ROOT_DIR, "data", "stock_cache", "stocks_cache.json"
)

# ================= OFFICIAL SOURCES =================
OFFICIAL_SOURCES = {
    "AL": "site:borsaitaliana.it FTSE MIB",
    "AM": "site:amx.am Armenia Stock Exchange index",
    "AT": "site:wienerborse.at ATX index",
    "AZ": "site:bfb.az Baku Stock Exchange index",
    "BA": "site:zse.hr CROBEX",
    "BE": "site:euronext.com BEL 20",
    "BG": "site:bse-sofia.bg SOFIX",
    "BY": "site:bcse.by stock index",
    "CH": "site:six-group.com SMI index",
    "CZ": "site:pse.cz PX index",
    "DE": "site:deutsche-boerse.com DAX",
    "FI": "site:nasdaqomx.com OMX Helsinki",
    "FR": "site:euronext.com CAC 40",
    "GE": "site:georgianstockexchange.ge index",
    "GR": "site:athexgroup.gr ASE index",
    "IE": "site:euronext.com ISEQ",
    "IS": "site:nasdaqomx.com OMX Iceland",
    "IT": "site:borsaitaliana.it FTSE MIB",
    "KV": "site:belex.rs BELEX15",
    "LT": "site:nasdaqomx.com OMX Vilnius",
    "LV": "site:nasdaqomx.com OMX Riga",
    "MD": "site:bvb.ro BET index",
    "ME": "site:belex.rs BELEX15",
    "MK": "site:belex.rs BELEX15",
    "MT": "site:mse.com.mt Equity Price Index",
    "NO": "site:oslobors.no OSEBX",
    "PL": "site:gpw.pl WIG20",
    "PT": "site:euronext.com PSI 20",
    "RO": "site:bvb.ro BET index",
    "RS": "site:belex.rs BELEX15",
    "RU": "site:moex.com MOEX index",
    "SK": "site:bsse.sk SAX index",
    "TR": "site:borsaistanbul.com BIST 100",
    "UA": "site:ux.ua Ukrainian Exchange index",
}

# ================= CACHE =================
def load_cache():
    if not os.path.exists(CACHE_PATH):
        return {}
    with open(CACHE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_cache(data):
    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ================= AI FETCH =================
def fetch_stock_ai(country_code: str):
    query = OFFICIAL_SOURCES[country_code]

    prompt = f"""
Search ONLY official stock exchange websites.

RULES (MANDATORY):
- Use ONLY official exchange or regulator websites
- Ignore news, blogs, aggregators, PDFs
- If data is not found, return null
- Daily percentage change MUST be realistic (-15% .. +15%)

Return STRICT JSON or null:
{{
  "index": "...",
  "value": NUMBER,
  "change_percent": NUMBER,
  "source": "official website URL"
}}

Query:
{query}
"""

    response = client.responses.create(
        model="gpt-4o-mini",
        tools=[{"type": "web_search"}],
        input=[{"role": "user", "content": prompt}],
        max_output_tokens=700,
    )

    text = response.output_text
    match = re.search(r"\{.*\}", text, re.DOTALL)

    if not match:
        return None

    data = json.loads(match.group())

    if not isinstance(data.get("value"), (int, float)):
        return None

    if not isinstance(data.get("change_percent"), (int, float)):
        return None

    if abs(data["change_percent"]) > 15:
        return None

    data["updated_at"] = datetime.utcnow().isoformat() + "Z"
    return data

# ================= RUN =================
def run():
    cache = load_cache()

    for code in OFFICIAL_SOURCES.keys():
        print(f"🔍 Fetching {code}...")
        try:
            data = fetch_stock_ai(code)
            if data:
                cache[code] = data
                print(f"✔ {code} updated")
            else:
                print(f"⚠ {code} skipped (no valid data)")
        except Exception as e:
            print(f"❌ {code} error: {e}")

    save_cache(cache)
    print("\n✅ Stock cache updated successfully")

if __name__ == "__main__":
    run()
