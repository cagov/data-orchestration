"""Relatively simple geospatial reference data ingests"""
from __future__ import annotations

from datetime import datetime, timedelta

import geopandas
from airflow.decorators import dag, task
from common.geo import gdf_to_bigquery

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

# TODO: make these configurable and target staging/prod
GBQ_DATASET = "geo_reference"
PROJECT_ID = "caldata-sandbox"

DEFAULT_ARGS = {
    "owner": "CalData",
    "depends_on_past": False,
    "email": ["odi-caldata-dse@innovation.ca.gov"],
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}


@task
def load_data(url: str, name: str) -> None:
    """
    ### Load Geospatial Data

    Given a URL, load geospatial data into BigQuery
    """
    gdf = geopandas.read_file(url)
    gdf_to_bigquery(
        gdf,
        destination_table=f"{GBQ_DATASET}.{name}",
        project_id="caldata-sandbox",
        if_exists="replace",
    )


# Somewhat awkward construction to avoid late-binding
# loop variable nonsense.
# cf. https://github.com/apache/airflow/discussions/21278
def _make_dag(url: str, name: str):
    @dag(
        dag_id=dag_id,
        description=f"Load data for {name}",
        start_date=datetime(2022, 12, 13),
        schedule_interval="@monthly",
        default_args=DEFAULT_ARGS,
    )
    def _load_data_dag():
        load_data(url, name)

    return _load_data_dag


for name, url in REFERENCE_DATA.items():
    dag_id = f"load_{name}"
    globals()[dag_id] = _make_dag(url, name)()
