from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

def hello():
    print("hello from DAG on MWAA/S3!")

with DAG(
    dag_id="example_hello19",
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=["demo"],
) as dag:
    PythonOperator(
        task_id="hello_task19",
        python_callable=hello,
    )
