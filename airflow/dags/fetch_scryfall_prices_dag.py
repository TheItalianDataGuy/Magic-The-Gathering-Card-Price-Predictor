from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models import Variable
import sys
from pathlib import Path

# Add the src directory to sys.path
project_src = Path(__file__).resolve().parent.parent / "src"
sys.path.append(str(project_src))

from data_ingestion.fetch_scryfall_prices import main

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2025, 4, 17),
    'email': Variable.get("alert_emails", default_var=[], deserialize_json=True),
    'email_on_failure': True,
    'email_on_retry': True,
    'email_on_success': True,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'fetch_scryfall_prices',
    default_args=default_args,
    description='Daily run of fetch_scryfall_prices.py using Airflow',
    schedule_interval='0 8 * * *',
    catchup=False,
    tags=['scryfall', 'prices'],
)

run_fetch_scryfall = PythonOperator(
    task_id='run_fetch_scryfall_prices',
    python_callable=main,
    dag=dag,
)
