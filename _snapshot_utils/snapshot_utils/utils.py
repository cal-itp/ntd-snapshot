"""
General utility functions.
"""

import os
from pathlib import Path
from typing import Literal

import gcsfs
import geopandas as gpd  # type: ignore

fs = gcsfs.GCSFileSystem()


def sanitize_file_path(file_name: str) -> str:
    """
    Remove the .parquet or .geojson in a filepath.
    """
    return str(Path(file_name).stem)


def parse_file_directory(file_name: str) -> str:
    """
    Grab the directory of the filename.
    For GCS bucket, we do not want '.' as the parent
    directory, we want to parse and put together the
    GCS filepath correctly.
    """
    if str(Path(file_name).parent) != ".":
        return str(Path(file_name).parent)
    else:
        return ""


def geoparquet_gcs_export(
    gdf: gpd.GeoDataFrame,
    gcs_file_path: str,
    file_name: str,
    **kwargs,
):
    """
    Save geodataframe as parquet locally,
    then move to GCS bucket and delete local file.

    gdf: geopandas.GeoDataFrame
    gcs_file_path: str
                    Ex: gs://calitp-analytics-data/data-analyses/my-folder/
    file_name: str
                Filename, with or without .parquet.
    """
    # Parse out file_name into stem (file_name_sanitized)
    # and parent (file_directory_sanitized)
    file_name_sanitized = Path(sanitize_file_path(file_name))
    file_directory_sanitized = parse_file_directory(file_name)

    # Make sure GCS path includes the directory we want the file to go to
    expanded_gcs = f"{Path(gcs_file_path).joinpath(file_directory_sanitized)}/"
    expanded_gcs = str(expanded_gcs).replace("gs:/", "gs://")

    gdf.to_parquet(f"{file_name_sanitized}.parquet", **kwargs)
    fs.put(
        f"{file_name_sanitized}.parquet",
        f"{str(expanded_gcs)}{file_name_sanitized}.parquet",
    )
    os.remove(f"{file_name_sanitized}.parquet", **kwargs)


def geojson_gcs_export(
    gdf: gpd.GeoDataFrame,
    gcs_file_path: str,
    file_name: str,
    geojson_type: str = "geojson",
):
    """
    Save geodataframe as geojson locally,
    then move to GCS bucket and delete local file.

    gcs_file_path: str
                    Ex: gs://calitp-analytics-data/data-analyses/my-folder/
    file_name: str
                name of file (with .geojson or .geojsonl).
    """

    if geojson_type == "geojson":
        DRIVER = "GeoJSON"
    elif geojson_type == "geojsonl":
        DRIVER = "GeoJSONSeq"
    else:
        raise ValueError("Not a valid geojson type! Use `geojson` or `geojsonl`")

    file_name_sanitized = sanitize_file_path(file_name)

    gdf.to_file(f"./{file_name_sanitized}.{geojson_type}", driver=DRIVER)

    fs.put(
        f"./{file_name_sanitized}.{geojson_type}",
        f"{gcs_file_path}{file_name_sanitized}.{geojson_type}",
    )
    os.remove(f"./{file_name_sanitized}.{geojson_type}")


def read_geojson(
    gcs_file_path: str,
    file_name: str,
    geojson_type: Literal["geojson", "geojsonl"] = "geojson",
    save_locally: bool = False,
) -> gpd.GeoDataFrame:
    """
    Parameters:
    gcs_file_path: str
                    Ex: gs://calitp-analytics-data/data-analyses/my-folder/
    file_name: str
                name of file (with or without the .geojson).
    geojson_type: str.
                    valid values are geojson or geojsonl.
    save_locally: bool
                    defaults to False. if True, will save geojson locally.
    """
    file_name_sanitized = sanitize_file_path(file_name)

    object_path = fs.open(f"{gcs_file_path}{file_name_sanitized}.{geojson_type}")
    gdf = gpd.read_file(object_path)

    if geojson_type == "geojson":
        DRIVER = "GeoJSON"
    elif geojson_type == "geojsonl":
        DRIVER = "GeoJSONSeq"

    if save_locally:
        gdf.to_file(f"./{file_name}.{geojson_type}", driver=DRIVER)

    return gdf
