"""Common utilities."""
from __future__ import annotations

import os


def default_gcp_project() -> str:
    """
    Get a default Project ID for the environment.

    First, this checks environment variables for `GCP_PROJECT` and
    ``GOOGLE_CLOUD_PROJECT``. If those are not set, it creates a python client and tries
    to read the Project ID off of that. If no project IDs are found, raises a
    ``RuntimeError``.
    """
    project = os.environ.get("GCP_PROJECT") or os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not project:
        try:
            import google.cloud.client

            project = google.cloud.client.ClientWithProject().project
        except Exception:  # noqa: BLE001
            pass
    if not project:
        raise RuntimeError("Unable to determine the GCP project for writing data")
    return project
