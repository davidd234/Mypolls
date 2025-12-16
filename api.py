import json
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ml_predict import predict_aggregated

# ================= APP =================
app = FastAPI(title="MyPolls API")

# ================= CORS =================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= PATHS =================
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
STOCK_CACHE_PATH = os.path.join(
    ROOT_DIR, "data", "stock_cache", "stocks_cache.json"
)

# ================= UTILS =================
def load_stock_cache():
    if not os.path.exists(STOCK_CACHE_PATH):
        return {}
    with open(STOCK_CACHE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

# ================= ML ENDPOINT =================
@app.get("/api/pmb/2024")
def get_pmb_2024_predictions():
    return {
        "election": "PMB 2024",
        "model": "RandomForest",
        "predictions": predict_aggregated(verbose=False),
    }

# ================= STOCK ENDPOINT =================
@app.get("/api/country/{code}/stock")
def get_country_stock(code: str):
    code = code.upper()
    cache = load_stock_cache()

    if code not in cache:
        return {
            "error": "No stock data available",
            "country": code
        }

    return {
        "country": code,
        **cache[code]
    }
