"""Microsoft building footprint data"""
from __future__ import annotations

from datetime import datetime, timedelta

from airflow.decorators import dag, task
from common.geo import gdf_to_bigquery

# # Snippet to get state listing, which we don't want airflow to run all the time during parsing
# import re
# import requests

# readme = requests.get(
#     "https://raw.githubusercontent.com/microsoft/USBuildingFootprints/master/README.md"
# ).text
# base = r"https:\/\/usbuildingdata\.blob\.core\.windows\.net\/usbuildings\-v2\/"
# STATES = re.findall(base + r"([A-z.]+)\.geojson\.zip", readme)
# assert len(STATES) == 51  # 50 States + DC

STATES = [
    "Alabama",
    "Alaska",
    "Arizona",
    "Arkansas",
    "California",
    "Colorado",
    "Connecticut",
    "Delaware",
    "DistrictofColumbia",
    "Florida",
    "Georgia",
    "Hawaii",
    "Idaho",
    "Illinois",
    "Indiana",
    "Iowa",
    "Kansas",
    "Kentucky",
    "Louisiana",
    "Maine",
    "Maryland",
    "Massachusetts",
    "Michigan",
    "Minnesota",
    "Mississippi",
    "Missouri",
    "Montana",
    "Nebraska",
    "Nevada",
    "NewHampshire",
    "NewJersey",
    "NewMexico",
    "NewYork",
    "NorthCarolina",
    "NorthDakota",
    "Ohio",
    "Oklahoma",
    "Oregon",
    "Pennsylvania",
    "RhodeIsland",
    "SouthCarolina",
    "SouthDakota",
    "Tennessee",
    "Texas",
    "Utah",
    "Vermont",
    "Virginia",
    "Washington",
    "WestVirginia",
    "Wisconsin",
    "Wyoming",
]

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
        if_exists="fail",
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
