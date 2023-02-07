"""Microsoft building footprint data."""
from __future__ import annotations

from datetime import datetime

from airflow.decorators import dag
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import (
    KubernetesPodOperator,
)
from common.defaults import DEFAULT_ARGS, DEFAULT_K8S_OPERATOR_ARGS
from kubernetes.client import models as k8s_models


@dag(
    description="Load Microsoft building footprints data",
    start_date=datetime(2023, 1, 25),
    schedule_interval="@monthly",
    default_args=DEFAULT_ARGS,
)
def state_building_footprints_dag():
    """
    Load MS building footprints dataset.

    This is a larger job, so requests more pod resources.
    """
    _ = KubernetesPodOperator(
        task_id="load_state_building_footprints",
        arguments=["python", "-m", "app.geo_reference.building_footprints"],
        container_resources=k8s_models.V1ResourceRequirements(
            requests={"memory": "32Gi", "cpu": "8"},
        ),
        **DEFAULT_K8S_OPERATOR_ARGS,
    )


run = state_building_footprints_dag()
