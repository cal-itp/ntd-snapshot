"""
Big Query utils to download Big Query tables
"""

from pathlib import Path
from typing import Literal

import gcsfs
import google.auth
from google.cloud import bigquery, bigquery_storage

from snapshot_utils import utils

credentials, project = google.auth.default()
client = bigquery.Client(project=project, credentials=credentials)
bqstorage_client = bigquery_storage.BigQueryReadClient(credentials=credentials)


def bigquery_partition_and_job_config(
    name: Literal[
        "service_date",
        "_feed_valid_from",
        "feed_key",
        "month_first_day",
        "ntd_start_year",
        "ntd_us_states",
    ],
    list_of_values: list = [],
) -> tuple:
    """
    Most common partition columns in warehouse.
    Be able to use a list of values we want and have it set up the
    Big Query parameterized query correctly - needs the sql query portion + job_config.
    """

    if name == "service_date":
        where_partition_condition = "service_date IN UNNEST(@service_date_list)"
        job_config = bigquery.ArrayQueryParameter(
            "service_date_list", "DATETIME", list_of_values
        )
    elif name == "_feed_valid_from":
        where_partition_condition = (
            "DATE(_feed_valid_from) IN UNNEST(@feed_valid_value)"
        )
        job_config = bigquery.ArrayQueryParameter(
            "feed_valid_value", "DATE", list_of_values
        )
    elif name == "feed_key":
        where_partition_condition = "feed_key IN UNNEST(@feed_key_list)"
        job_config = bigquery.ArrayQueryParameter(
            "feed_key_list", "STRING", list_of_values
        )
    elif name == "month_first_day":
        where_partition_condition = "month_first_day >= @gtfs_rollup_start_date"
        job_config = bigquery.ScalarQueryParameter(
            "gtfs_rollup_start_date", "INT64", list_of_values[0]
        )
    elif name == "ntd_start_year":
        where_partition_condition = "year >= @min_year"
        job_config = bigquery.ScalarQueryParameter(
            "min_year", "INT64", list_of_values[0]
        )
    elif name == "ntd_us_states":
        where_partition_condition = "state IN UNNEST(@us_state_list)"
        job_config = bigquery.ArrayQueryParameter(
            "us_state_list", "STRING", list_of_values
        )

    return where_partition_condition, job_config


def download_table(
    sql_query: str = "",
    filter_dict: dict = {
        "service_date": [],
    },
    additional_sql_condition: str = None,
    output_path: str = "",
    geography_column: str = None,
    client: bigquery.Client = client,
    filesystem: gcsfs.GCSFileSystem = gcsfs.GCSFileSystem(),
    bqstorage_client: google.cloud.bigquery_storage_v1.BigQueryReadClient = None,
):
    """
    Download a table from the warehouse and export,
    with the ability to filter by our partitioning and clustering columns
    more easily.

    Most common partition columns are set up here using query_parameters
    with the correct data types.

    sql_query: Input the table to query. SELECT * FROM some_table or SELECT col1, col2 FROM some_table.

    filter_dict: order matters, put the partition columns first, then the clustering columns.

    geography_column: if column is GEOGRAPHY in Big Query, set this to return a geodataframe.
         Use only for points, not linestrings.
         Linestrings in warehouse are ARRAYS of points, not GEOGRAPHY.

    client: set to production env, can switch to staging.

    filesystem: need this to export to GCS.

    bqstorage_client: for large dfs that might eat up too much memory,
        use this to make use of Big Query to GCS in the backend. We want to save in GCS anyway, so this improvement in how BQ tables can be loaded gives us performance improvement, but can add to costs. Use this when we would be scanning the table, but unable to save it out in GCS.
    """
    where_condition_list = []
    job_config_list = []

    for name, list_of_values in filter_dict.items():
        where_condition, one_config = bigquery_partition_and_job_config(
            name, list_of_values
        )
        where_condition_list.append(where_condition)
        job_config_list.append(one_config)

    # https://stackoverflow.com/questions/493819/why-is-it-string-joinlist-instead-of-list-joinstring
    if additional_sql_condition is not None:
        where_condition_list.append(additional_sql_condition)

    # For certain tables, we don't need extra filters.
    # use default arg for filter_dict to prevent querying entire tables
    if len(filter_dict) == 0:
        sql_query_expanded = sql_query
    else:
        sql_query_expanded = f"""
            {sql_query} WHERE {" AND ".join(where_condition_list)}
        """

    job_config = bigquery.QueryJobConfig(query_parameters=job_config_list)

    query_job = client.query(sql_query_expanded, job_config=job_config)

    # parse the output path
    filename = Path(output_path).name

    # this would only support pt_geom, not linestrings, since we store those as arrays of points
    if geography_column is not None:
        df = query_job.result().to_geodataframe(
            bqstorage_client=bqstorage_client, geography_column=geography_column
        )
        utils.geoparquet_gcs_export(df, output_path.replace(filename, ""), filename)

    else:
        df = query_job.result().to_arrow(bqstorage_client=bqstorage_client).to_pandas()

    df.to_parquet(output_path, filesystem=filesystem)

    print(f"exported: {output_path}")
    return
