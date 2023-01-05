"""Geospatial utilities"""
from __future__ import annotations

import warnings
from typing import Literal

import geopandas
import geopandas.array
import pandas_gbq.schema
import shapely.ops
from google.cloud import bigquery
from google.cloud.exceptions import NotFound


def gdf_to_bigquery(
    gdf: geopandas.GeoDataFrame,
    destination_table: str,
    project_id: str | None = None,
    cluster: str | bool = False,
    chunksize: int | None = None,
    if_exists: Literal["fail", "replace", "append"] = "fail",
    table_schema: list[dict] | None = None,
    location: str | None = None,
) -> None:
    """
    A wrapper around `gdf.to_gbq` which does some additional validation and ensures
    that the geometry objects are loaded correctly. For documentation of parameters,
    see gdf.to_gbq.

    One additional parameter is `cluster`, which can be set to True, or a column name.
    This creates a table with clustering. Since this can only be done at table creation
    time, ``if_exists`` cannot be set to ``append``. If ``cluster=True``, the default
    geometry column is selected.
    """
    assert isinstance(gdf, geopandas.GeoDataFrame)

    if gdf.crs.srs != "epsg:4326":
        warnings.warn(
            f"GeoDataFrame has a projected coordinate system {gdf.crs.srs},"
            " but BigQuery only supports WGS84. Converting to to that."
        )
        gdf = gdf.to_crs(epsg=4326)  # type: ignore

    assert gdf.crs.srs == "epsg:4326"

    # Ensure that the geometry columns are properly oriented and valid geometries.
    # GBQ is fairly unforgiving, so this step is often required.
    gdf = gdf.assign(
        **{
            name: gdf[name].make_valid().apply(shapely.ops.orient, args=(1,))
            for name, dtype in gdf.dtypes.items()
            if isinstance(dtype, geopandas.array.GeometryDtype)
        }
    )  # type: ignore

    # Identify the geometry columns, create a table schema that identifies the relevant
    # ones as geometries to avoid later conversion with temp tables.
    schema = pandas_gbq.schema.generate_bq_schema(gdf)
    schema = {
        "fields": [
            {**f, "type": "GEOGRAPHY"}
            if isinstance(gdf[f["name"]].dtype, geopandas.array.GeometryDtype)
            else f
            for f in schema["fields"]
        ]
    }
    schema = pandas_gbq.schema.update_schema(schema, {"fields": table_schema or []})

    # If clustering is set, we have to create the table ahead of time and set the
    # clustering columns then.
    if cluster:
        if if_exists == "append":
            raise ValueError(
                "Cannot append to existing table and set a clustering column"
            )
        col = cluster if isinstance(cluster, str) else gdf.geometry.name
        if not col:
            raise ValueError("Invalid clustering column {col}")

        # Set up the table definition
        tref = bigquery.Table(f"{project_id}.{destination_table}")
        tref.schema = pandas_gbq.schema.to_google_cloud_bigquery(schema)
        tref.clustering_fields = [col]

        client = bigquery.Client(project=project_id)

        # Handle if_exists
        try:
            client.get_table(tref)
            if if_exists == "fail":
                raise RuntimeError(f"Table {destination_table} already exists!")
            elif if_exists == "replace":
                client.delete_table(tref)
        except NotFound:
            pass

        # Create the table.
        client.create_table(tref)

        # We've created a new table, now set if_exists to append to insert data into the
        # now-ready empty table.
        if_exists = "append"

    # Write to BiqQuery!
    gdf.to_gbq(
        destination_table=destination_table,
        project_id=project_id,
        if_exists=if_exists,
        table_schema=schema["fields"],
        chunksize=chunksize,
        location=location,
    )
