"""Orchestrates the fraud data pipeline: generate -> load -> dbt run -> dbt test."""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    "owner": "alex",
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="fraud_pipeline",
    description="End-to-end fraud data pipeline",
    schedule_interval="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    default_args=default_args,
    tags=["fraud", "portfolio"],
) as dag:

    generate_data = BashOperator(
        task_id="generate_data",
        bash_command="echo 'Step 1: generating transactions...'",
    )

    load_to_bigquery = BashOperator(
        task_id="load_to_bigquery",
        bash_command="echo 'Step 2: loading raw data into BigQuery...'",
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command="echo 'Step 3: running dbt models (staging -> marts)...'",
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command="echo 'Step 4: running dbt data-quality tests...'",
    )

    # Define the order: each task depends on the previous one
    generate_data >> load_to_bigquery >> dbt_run >> dbt_test