"""Microsoft building footprint data"""
from __future__ import annotations

from datetime import datetime, timedelta

from airflow.decorators import dag, task
from common.geo import gdf_to_bigquery

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
def load_state_footprints() -> None:
    import geopandas

    print("Downloading data")
    gdf = geopandas.read_file(
        "https://usbuildingdata.blob.core.windows.net/usbuildings-v2/Alaska.geojson.zip"
    )

    print("Writing data to gbq")
    gdf_to_bigquery(
        gdf,
        "geo_reference.alaska_building_footprints",
        project_id="caldata-sandbox",
        cluster=True,
        if_exists="replace",
    )


@dag(
    description="Load Microsoft building footprints data",
    start_date=datetime(2023, 1, 4),
    schedule_interval="@monthly",
    default_args=DEFAULT_ARGS,
)
def load_state_building_footprints():
    load_state_footprints()


run = load_state_building_footprints()
