from datetime import datetime, timezone

from airflow import DAG
import logging
from airflow.operators.python import PythonOperator, get_current_context

from src.config.settings import get_settings
from src.database.mongodb import MongoDatabase
from src.services.reporting_service import generate_hourly_report


def build_report() -> None:
    context = get_current_context()
    database = MongoDatabase(get_settings())
    try:
        database.ensure_indexes()
        generate_hourly_report(database, context["data_interval_end"])
    finally:
        database.close()


with DAG(
    dag_id="earthquake_hourly_report",
    schedule="0 * * * *",
    start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
    catchup=False,
    tags=["earthquakes"],
) as dag:
    PythonOperator(task_id="generate_hourly_report", python_callable=build_report)
