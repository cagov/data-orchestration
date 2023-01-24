"""Relatively simple geospatial reference data ingests"""
from __future__ import annotations

from datetime import datetime

from airflow.decorators import dag, task_group
from airflow.operators.empty import EmptyOperator
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import (
    KubernetesPodOperator,
)
from common.defaults import DEFAULT_ARGS

REFERENCE_DATA = {
    "incorporated_cities": (
        "https://gis.data.ca.gov/datasets/CALFIRE-Forestry"
        "::california-incorporated-cities-1.geojson"
        "?outSR=%7B%22latestWkid%22%3A3857%2C%22wkid%22%3A102100%7D"
    ),
    "counties": (
        "https://gis.data.ca.gov/datasets/CALFIRE-Forestry"
        "::california-county-boundaries.geojson"
        "?outSR=%7B%22latestWkid%22%3A3857%2C%22wkid%22%3A102100%7D"
    ),
}


@dag(
    dag_id="core_geo_reference_data_dag",
    start_date=datetime(2022, 1, 23),
    schedule_interval="@monthly",
    default_args=DEFAULT_ARGS,
)
def core_geo_reference_data_dag():
    @task_group
    def core_data_group():
        for name, url in REFERENCE_DATA.items():
            task_id = f"load_{name}"
            locals()[task_id] = KubernetesPodOperator(
                task_id=task_id,
                name=task_id,
                arguments=["python", "-m", "app.geo_reference.core", url, name],
                namespace="composer-user-workloads",
                image="us-west1-docker.pkg.dev/caldata-sandbox/dse-orchestration-us-west1/analytics:94feb9a",
                kubernetes_conn_id="kubernetes_default",
                config_file="/home/airflow/composer_kube_config",
                startup_timeout_seconds=300,
            )

    finalize = EmptyOperator(task_id="finalize")

    core_data_group() >> finalize


run = core_geo_reference_data_dag()
