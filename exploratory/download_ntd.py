"""
Downnload NTD tables for exploratory analysis.

Go back to basics for SQL queries, write out long form, be able
to have parameterized queries.

google.cloud.bigquery: using the SQL way can inject parameters,
how to ensure it's safe though. leave empty args by default.

pandas_gbq: couldn't get parameters to work in config
https://googleapis.dev/python/pandas-gbq/latest/reading.html
"""

import gcsfs
from _utils import GCS_FILE_PATH
from google.cloud import bigquery

if __name__ == "__main__":
    import google.auth

    credentials, project = google.auth.default()

    annual_service_query = """
        SELECT * 
        FROM `cal-itp-data-infra.mart_ntd_funding_and_expenses.fct_service_data_and_operating_expenses_time_series_by_mode`
        WHERE year >= @year AND source_state IN UNNEST(@state)
    """

    service_params = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("year", "INT64", 2015),
            bigquery.ArrayQueryParameter("state", "STRING", ["CA", "OR", "AZ", "NV"]),
        ]
    )

    client = bigquery.Client(project=project, credentials=credentials)
    query_job = client.query(annual_service_query, job_config=service_params)
    df = query_job.result().to_dataframe()

    df.drop(columns=["dt", "execution_ts"]).to_parquet(
        f"{GCS_FILE_PATH}annual_service_and_opex.parquet",
        filesystem=gcsfs.GCSFileSystem(),
    )

    # compare this to bq_utils.bq_faster_download
    print("exported annual service parquet")
