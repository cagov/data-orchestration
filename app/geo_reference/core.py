"""Load simple geospatial data to BigQuery"""
from ..utils_geo import gdf_to_bigquery

# TODO: make these configurable and target staging/prod
GBQ_DATASET = "geo_reference"
PROJECT_ID = "caldata-sandbox"


def load_data(url: str, name: str) -> None:
    """
    ### Load Geospatial Data

    Given a URL, load geospatial data into BigQuery
    """
    import geopandas

    gdf = geopandas.read_file(url)
    gdf_to_bigquery(
        gdf,
        destination_table=f"{GBQ_DATASET}.{name}",
        project_id=PROJECT_ID,
        if_exists="replace",
    )


if __name__ == "__main__":
    import sys

    # TODO: perhaps make a real CLI here.
    assert len(sys.argv) == 3, "Expected exactly two arguments: URL and dataset name"
    load_data(sys.argv[1], sys.argv[2])
