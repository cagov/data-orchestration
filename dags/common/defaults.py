"""Shared default arguments for DAGs"""
from __future__ import annotations

from datetime import timedelta
from typing import Any

from common.slack import post_to_slack_on_failure

DEFAULT_ARGS: dict[str, Any] = {
    "owner": "CalData",
    "depends_on_past": False,
    "email": ["odi-caldata-dse@innovation.ca.gov"],
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "on_failure_callback": post_to_slack_on_failure,
}


DEFAULT_K8S_OPERATOR_ARGS = {
    # This pod namespace inherits the same permissions as the airflow workers/scheduler from GCP
    "namespace": "composer-user-workloads",
    # TODO: figure out a nice workflow for when/how to update the image tag.
    "image": "us-west1-docker.pkg.dev/caldata-sandbox/dse-orchestration-us-west1/analytics:5fb840d",
    "kubernetes_conn_id": "kubernetes_default",
    "config_file": "/home/airflow/composer_kube_config",
    # Default startup timeout is often not long enough to pull the image
    "startup_timeout_seconds": 300,
}
