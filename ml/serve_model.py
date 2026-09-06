"""Serve the fraud detection model as a real-time API."""

from pathlib import Path
import joblib
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel

# Load the trained model + the feature columns it expects
MODEL_PATH = Path(__file__).resolve().parent / "fraud_model.joblib"
bundle = joblib.load(MODEL_PATH)
model = bundle["model"]
columns = bundle["columns"]

app = FastAPI(title="Fraud Detection API")


# The shape of an incoming transaction
class Transaction(BaseModel):
    amount: float
    country: str
    merchant_category: str
    payment_method: str
    currency: str


def to_features(txn: Transaction) -> pd.DataFrame:
    """Turn one transaction into the 27-column feature row the model expects."""
    raw = pd.DataFrame([txn.dict()])
    encoded = pd.get_dummies(raw)
    # Align to the exact columns used at training (fill missing with 0)
    return encoded.reindex(columns=columns, fill_value=0)


# High-risk values (same signals the fraud patterns were built on)
HIGH_RISK_COUNTRIES = {"NG", "RU", "CN", "XX"}
HIGH_RISK_CATEGORIES = {"crypto", "gaming", "gift_cards"}
AMOUNT_THRESHOLD = 1000


def explain_fraud(txn: "Transaction") -> str:
    """Explain, in plain language, which signals triggered the fraud flag.

    Rule-based for now. To use a real LLM, replace the body with a call to
    Gemini/Bedrock, passing these detected signals in a structured prompt.
    """
    signals = []
    if txn.country in HIGH_RISK_COUNTRIES:
        signals.append(f"high-risk country ({txn.country})")
    if txn.amount > AMOUNT_THRESHOLD:
        signals.append(f"unusually high amount ({txn.amount:.0f})")
    if txn.merchant_category in HIGH_RISK_CATEGORIES:
        signals.append(f"high-risk category ({txn.merchant_category})")

    if not signals:
        return "Flagged by the model, but no obvious rule-based signal stood out."
    return "Flagged for: " + ", ".join(signals) + "."

@app.get("/")
def health():
    return {"status": "ok", "model": "fraud-xgboost"}


@app.post("/predict")
def predict(txn: Transaction):
    X = to_features(txn)
    proba = float(model.predict_proba(X)[0][1])
    is_fraud = proba >= 0.5
    response = {"is_fraud": is_fraud, "fraud_probability": round(proba, 4)}
    if is_fraud:
        response["explanation"] = explain_fraud(txn)
    return response