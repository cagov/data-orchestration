"""Microsoft building footprint data"""
from __future__ import annotations

from datetime import datetime

from airflow.decorators import dag
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import (
    KubernetesPodOperator,
)
from common.defaults import DEFAULT_ARGS
from kubernetes.client import models as k8s_models


@dag(
    description="Load Microsoft building footprints data",
    start_date=datetime(2023, 1, 23),
    schedule_interval="@monthly",
    default_args=DEFAULT_ARGS,
)
def state_building_footprints_dag():
    _ = KubernetesPodOperator(
        task_id="load_state_building_footprints",
        name="load_state_building_footprints",
        arguments=["python", "-m", "app.geo_reference.building_footprints"],
        namespace="composer-user-workloads",
        image="us-west1-docker.pkg.dev/caldata-sandbox/dse-orchestration-us-west1/analytics:5fb840d",
        kubernetes_conn_id="kubernetes_default",
        config_file="/home/airflow/composer_kube_config",
        startup_timeout_seconds=300,
        container_resources=k8s_models.V1ResourceRequirements(
            requests={"memory": "32Gi", "cpu": "8"},
        ),
    )


run = state_building_footprints_dag()
