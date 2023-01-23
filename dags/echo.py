"""Echo dag"""
import datetime

from airflow import models
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import (
    KubernetesPodOperator,
)
from common.defaults import DEFAULT_ARGS

# Define a DAG (directed acyclic graph) of tasks.
# Any task you create within the context manager is automatically added to the
# DAG object.
with models.DAG(
    "echo_dag",
    schedule_interval=datetime.timedelta(days=1),
    start_date=datetime.datetime(2023, 1, 10),
    default_args=DEFAULT_ARGS,
) as dag:
    kubernetes_min_pod = KubernetesPodOperator(
        task_id="echo",
        name="echo",
        arguments=["micromamba", "env", "list"],
        namespace="composer-user-workloads",
        image="us-west1-docker.pkg.dev/caldata-sandbox/dse-orchestration-us-west1/geo:latest",
        kubernetes_conn_id="kubernetes_default",
        config_file="/home/airflow/composer_kube_config",
    )
