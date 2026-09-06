# Real-Time Fraud Detection Platform

An end-to-end data platform that ingests payment transactions in real time, makes
them trusted and governed, trains a fraud-detection model on them, and serves it
as a live API with natural-language explanations.

Built to demonstrate **Data Engineering with a data-quality backbone**, plus a
**DE → ML / MLOps** layer. The domain is transaction fraud, but the architecture
is transversal: it fits fintech, marketplaces, banking or gaming.

---

## Architecture

```
 transaction generator            (Python, ~2% fraud injected)
        │  streaming (JSON)
        ▼
   raw layer  (Parquet)
        │  load
        ▼
   BigQuery  ──► dbt: staging ──► marts        + data-quality tests
   (cloud DWH)   (clean/typed)   (business)
        │
        ▼
   XGBoost fraud model  ──►  FastAPI service  ──►  prediction + explanation

   Orchestrated end-to-end with Apache Airflow (Docker):
        generate → load → dbt run → dbt test
```

---

## Tech stack

| Layer | Tools |
|-------|-------|
| Language | Python, SQL |
| Ingestion | Streaming (JSON), Parquet |
| Cloud warehouse | **BigQuery** |
| Transformation | **dbt** (staging → marts, `ref()` lineage, materializations) |
| Data quality | dbt tests (unique, not_null, accepted_values), data contracts |
| Orchestration | **Apache Airflow** (Docker) |
| Infrastructure | **Docker**, GCP service accounts / IAM |
| Machine learning | scikit-learn (Random Forest baseline), **XGBoost** |
| Model serving | **FastAPI** + Uvicorn |
| Explainability | Rule-based explanation layer (LLM/Bedrock-ready) |

---

## The pipeline, block by block

**A · Ingestion** — A generator produces realistic transactions with fraud
injected through three patterns (anomalous amount, high-risk country, high-risk
category). A streaming loop emits them (~2% fraud) and lands them, untouched, in
a raw Parquet layer with ingestion metadata.

**B · Transformation (dbt + BigQuery)** — Raw data is loaded into BigQuery and
modelled in layers with dbt: `stg_transactions` (cleaned, typed, view) →
`mart_fraud_by_country` (business-ready, table). Dependencies and lineage are
handled with `source()` / `ref()`.

**C · Data quality** — dbt tests enforce contracts on the staging model:
`transaction_id` unique & not-null, `is_fraud` in `[0, 1]`, key fields not-null.
The pipeline fails fast if bad data appears, before it reaches the model.

**D · Orchestration (Airflow)** — An Airflow DAG orchestrates the full flow
(`generate → load → dbt run → dbt test`) with task dependencies, running on a
Dockerised Airflow stack.

**E · Fraud model (ML)** — A classifier is trained on the cleaned data. A Random
Forest baseline is compared against XGBoost, handling class imbalance
(`class_weight` / `scale_pos_weight`) and evaluated with precision/recall on the
minority class (accuracy is deliberately ignored). The winning model is persisted.

**F · Serving + explanation (MLOps)** — The model is served with FastAPI: send a
transaction, get back a fraud probability. Flagged transactions include a
natural-language explanation of the signals that triggered the alert, structured
so the rule-based layer can be swapped for an LLM (Gemini / Bedrock).

---

## Key engineering decisions

- **Raw is sacred** — the raw layer stays faithful to the source; all shaping
  happens downstream in dbt, so any transformation bug is recoverable.
- **Quality as a first-class citizen** — data contracts and tests stop bad data
  early rather than letting it silently corrupt the model.
- **Right metric for the problem** — fraud is a rare event, so the model is
  judged on precision/recall/PR, not on misleading accuracy.
- **ML decides, the explanation layer describes** — the model makes the call;
  a separate layer explains it. This mirrors how ML + GenAI systems are built in
  production, and keeps the LLM (when plugged in) out of the decision itself.

> Note on results: on the synthetic data the model reaches very high scores,
> because the injected fraud patterns are highly separable and the test set is
> small. On real data, more modest metrics and cross-validation would be expected.

---

## Run it locally

```bash
# 1. Environment
python -m venv .venv && .venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 2. Ingest (generate + land raw)
python ingestion/generate_transactions.py | python ingestion/land_raw.py

# 3. Load to BigQuery, then transform + test with dbt
python ingestion/load_to_bigquery.py
cd fraud_platform && dbt run && dbt test

# 4. Train the model
python ml/train_model.py

# 5. Serve it
uvicorn ml.serve_model:app --reload
# → open http://127.0.0.1:8000/docs and POST a transaction to /predict

# 6. Orchestrate everything with Airflow
cd airflow && docker compose up -d
# → open http://localhost:8080 (airflow / airflow)
```

> Requires a GCP project with BigQuery and a service-account key placed at
> `.secrets/bigquery_key.json` (git-ignored). Docker Desktop is needed for Airflow.

---

## Roadmap

- Wire the Airflow tasks to the real scripts (currently a didactic skeleton).
- Add drift monitoring (Evidently) and orchestrated retraining.
- Plug a real LLM (Gemini / Bedrock) into the explanation layer.
- Add streaming ingestion with Kafka/Redpanda.