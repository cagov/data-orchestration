"""Geospatial utilities"""
from __future__ import annotations

import warnings
from typing import Literal

import geopandas
import geopandas.array
import shapely.ops


def gdf_to_bigquery(
    gdf: geopandas.GeoDataFrame,
    destination_table: str,
    project_id: str | None = None,
    chunksize: int | None = None,
    if_exists: Literal["fail", "replace", "append"] = "fail",
    table_schema: list[dict] | None = None,
    location: str | None = None,
) -> None:
    """
    A wrapper around `gdf.to_gbq` which does some additional validation and ensures
    that the geometry objects are loaded correctly. For documentation of parameters,
    see gdf.to_gbq.
    """
    assert isinstance(gdf, geopandas.GeoDataFrame)

    if gdf.crs.srs != "epsg:4326":
        warnings.warn(
            f"GeoDataFrame has a projected coordinate system {gdf.crs.srs},"
            " but BigQuery only supports WGS84. Converting to to that."
        )
        gdf = gdf.to_crs(epsg=4326)  # type: ignore

    assert gdf.crs.srs == "epsg:4326"

    # Identify the geometry columns, create a table schema that identifies
    if table_schema is None:
        table_schema = [
            {"name": name, "type": "GEOGRAPHY"}
            for name, dtype in gdf.dtypes.items()
            if isinstance(dtype, geopandas.array.GeometryDtype)
        ]

    # Ensure that the geometry columns are properly oriented and valid geometries.
    # GBQ is fairly unforgiving, so this step is often required.
    gdf = gdf.assign(
        **{
            name: gdf[name].make_valid().apply(shapely.ops.orient, args=(1,))
            for name, dtype in gdf.dtypes.items()
            if isinstance(dtype, geopandas.array.GeometryDtype)
        }
    )  # type: ignore

    # Write to BiqQuery!
    gdf.to_gbq(
        destination_table=destination_table,
        project_id=project_id,
        if_exists=if_exists,
        table_schema=table_schema,
        chunksize=chunksize,
        location=location,
    )
