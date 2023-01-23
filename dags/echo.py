"""Echo dag"""
import datetime

from airflow import models
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import (
    KubernetesPodOperator,
)
from common.defaults import DEFAULT_ARGS
from kubernetes.client import models as k8s_models

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
        arguments=["bq", "ls"],
        namespace="composer-user-workloads",
        image="us-west1-docker.pkg.dev/caldata-sandbox/dse-orchestration-us-west1/analytics:358a4cd",
        kubernetes_conn_id="kubernetes_default",
        config_file="/home/airflow/composer_kube_config",
        container_resources=k8s_models.V1ResourceRequirements(
            requests={"memory": "32Gi", "cpu": "8"},
        ),
        startup_timeout_seconds=300,
    )
