from __future__ import annotations

from ..utils_geo import gdf_to_bigquery

# TODO: make these configurable and target staging/prod
GBQ_DATASET = "geo_reference"
PROJECT_ID = "caldata-sandbox"


def load_state_footprints() -> None:
    import geopandas

    print("Downloading data")
    gdf = geopandas.read_file(
        "https://usbuildingdata.blob.core.windows.net/usbuildings-v2/California.geojson.zip"
    )

    print("Writing data to gbq")
    gdf_to_bigquery(
        gdf,
        f"{GBQ_DATASET}.california_building_footprints",
        project_id=PROJECT_ID,
        cluster=True,
        if_exists="replace",
    )


if __name__ == "__main__":
    load_state_footprints()
