from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ml_predict import predict_aggregated

app = FastAPI(title="MyPolls ML API")

# CORS – permite frontend-ului (localhost:5173) să acceseze API-ul
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # pentru dev; restrângem mai târziu
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/pmb/2024")
def get_pmb_2024_predictions():
    """
    Returnează predicțiile ML pentru PMB 2024
    """
    predictions = predict_aggregated(verbose=False)

    return {
        "election": "PMB 2024",
        "model": "RandomForest",
        "predictions": predictions
    }
