from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
}

with DAG(
    dag_id='fetch_store_dag',
    default_args=default_args,
    description='DAG to run fetch_store.py and store data in datastore.db',
    start_date=datetime(2025, 3, 25),
    schedule_interval='@daily',
    catchup=False,
    max_active_runs=1,
    tags=['data', 'dev'],
) as dag:

    run_fetch_store = BashOperator(
        task_id='run_fetch_store_script',
        bash_command='{{ var.value.PYTHON_PATH }} /workspaces/Team-34/src/data/fetch_store.py',
        cwd='/workspaces/Team-34/src/data',
    )

    run_fetch_store