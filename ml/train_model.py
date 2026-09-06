"""Train a fraud detection model on the cleaned transactions from BigQuery."""

from pathlib import Path
from google.cloud import bigquery
from google.oauth2 import service_account
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
from xgboost import XGBClassifier
import joblib

PROJECT_ID = "fraud-platform-507716"
KEY_PATH = Path(__file__).resolve().parents[1] / ".secrets" / "bigquery_key.json"


def load_data():
    """Load the cleaned transactions from BigQuery into a pandas DataFrame."""
    credentials = service_account.Credentials.from_service_account_file(str(KEY_PATH))
    client = bigquery.Client(credentials=credentials, project=PROJECT_ID)
    query = "SELECT * FROM `fraud-platform-507716.fraud.stg_transactions`"
    df = client.query(query).to_dataframe()
    return df

def prepare_features(df):
    """Turn raw columns into numeric features the model can use."""
    # Columns we use as predictive signals
    feature_cols = ["amount", "country", "merchant_category", "payment_method", "currency"]
    X = df[feature_cols].copy()
    y = df["is_fraud"].astype(int)

    # One-hot encode the text columns (country=CN -> country_CN=1, ...)
    X = pd.get_dummies(X, columns=["country", "merchant_category", "payment_method", "currency"])

    return X, y

def evaluate(name, model, X_train, y_train, X_test, y_test):
    """Train a model and print its evaluation."""
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    print(f"\n===== {name} =====")
    print("Confusion matrix:")
    print(confusion_matrix(y_test, y_pred))
    print(classification_report(y_test, y_pred, digits=3))
    return model


def main():
    df = load_data()
    print(f"Loaded {len(df)} transactions ({df['is_fraud'].mean()*100:.2f}% fraud)")

    X, y = prepare_features(df)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"Train: {len(X_train)} | Test: {len(X_test)}")

    # Baseline: Random Forest
    rf = RandomForestClassifier(
        n_estimators=100, class_weight="balanced", random_state=42
    )
    evaluate("Random Forest", rf, X_train, y_train, X_test, y_test)

    # XGBoost (scale_pos_weight handles the imbalance)
    n_neg = (y_train == 0).sum()
    n_pos = (y_train == 1).sum()
    xgb = XGBClassifier(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.1,
        scale_pos_weight=n_neg / n_pos,   # tell XGBoost fraud is rare
        eval_metric="logloss",
        random_state=42,
    )
    xgb = evaluate("XGBoost", xgb, X_train, y_train, X_test, y_test)



    # Save the winning model (XGBoost) to disk
    model_path = Path(__file__).resolve().parent / "fraud_model.joblib"
    joblib.dump({"model": xgb, "columns": list(X.columns)}, model_path)
    print(f"\nModel saved to {model_path.name}")


if __name__ == "__main__":
    main()
