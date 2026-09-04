"""Generate synthetic payment transaction for the fraud detection platform"""

import random
import uuid
from datetime import datetime, timezone
import time
import json

# Pools of realistic values to pick from
COUNTRIES = ["ES", "FR", "DE", "IT", "PT", "NL", "US", "GB"]
CURRENCIES = ["EUR", "EUR", "EUR", "USD", "GBP"]  # EUR repeated = more likely
MERCHANT_CATEGORIES = ["groceries", "restaurants", "travel", "electronics", "fashion", "gaming"]
PAYMENT_METHODS = ["card", "card", "card", "wallet", "transfer"]  # card most common

# High-risk values used to inject fraud signals
HIGH_RISK_COUNTRIES = ["NG", "RU", "CN", "XX"]
HIGH_RISK_CATEGORIES = ["gaming", "crypto", "gift_cards"]

def generate_normal_transaction() -> dict:
    """Create one realistic, non-fraudulent transaction"""
    return{
        "transaction_id": str(uuid.uuid4()),
        "user_id": f"user_{random.randint(1,1000)}",
        "amount": round(random.uniform(5, 300), 2),
        "currency": random.choice(CURRENCIES),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "country": random.choice(COUNTRIES),
        "ip_address": f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(0,255)}",
        "device_id": f"device_{random.randint(1, 500)}",
        "merchant": f"merchant_{random.randint(1, 200)}",
        "merchant_category": random.choice(MERCHANT_CATEGORIES),
        "payment_method": random.choice(PAYMENT_METHODS),
        "is_fraud": 0,  # normal transaction
    }

def generate_fraudulent_transaction() -> dict:
    """Create one transaction with 1-2 fraud signals injected."""
    # Start from a normal transaction and corrupt it
    txn = generate_normal_transaction()
    txn["is_fraud"] = 1

    # Pick 1 or 2 fraud patterns at random
    patterns = random.sample(["amount", "country", "category"], k=random.randint(1, 2))

    if "amount" in patterns:
        txn["amount"] = round(random.uniform(2000, 9000), 2)   # anomalous amount
    if "country" in patterns:
        txn["country"] = random.choice(HIGH_RISK_COUNTRIES)     # high-risk country
    if "category" in patterns:
        txn["merchant_category"] = random.choice(HIGH_RISK_CATEGORIES)  # high-risk category

    return txn

def transaction_stream(fraud_rate: float = 0.02, delay: float = 0.1):
    """Yield transactions forever: mostly normal, ~2% fraud."""
    while True:
        if random.random() < fraud_rate:
            txn = generate_fraudulent_transaction()
        else:
            txn = generate_normal_transaction()
        yield txn
        time.sleep(delay)


if __name__ == "__main__":
    # Print the live stream as newline-delimited JSON (Ctrl+C to stop)
    for txn in transaction_stream():
        print(json.dumps(txn))