"""Load simple geospatial data to BigQuery"""
from ..utils import default_gcp_project
from ..utils_geo import gdf_to_bigquery

GBQ_DATASET = "geo_reference"


def load_data(url: str, name: str) -> None:
    """
    ### Load Geospatial Data

    Given a URL, load geospatial data into BigQuery
    """
    import geopandas

    project_id = default_gcp_project()

    gdf = geopandas.read_file(url)
    gdf_to_bigquery(
        gdf,
        destination_table=f"{GBQ_DATASET}.{name}",
        project_id=project_id,
        if_exists="replace",
    )


if __name__ == "__main__":
    import sys

    # TODO: perhaps make a real CLI here.
    assert len(sys.argv) == 3, "Expected exactly two arguments: URL and dataset name"
    load_data(sys.argv[1], sys.argv[2])
