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

def download_annual_service_and_opex(
    client: bigquery.Client,
    filesystem: gcsfs.GCSFileSystem,
) -> None:
    query = """
        SELECT *
        FROM `cal-itp-data-infra.mart_ntd_funding_and_expenses.fct_service_data_and_operating_expenses_time_series_by_mode`
        WHERE year >= @year
          AND source_state IN UNNEST(@state)
    """

    query_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("year", "INT64", 2015),
            bigquery.ArrayQueryParameter(
                "state", "STRING", ["CA", "OR", "AZ", "NV"]
            ),
        ]
    )

    query_job = client.query(query, job_config=query_config)
    df = query_job.result().to_dataframe()

    df.drop(columns=["dt", "execution_ts"]).to_parquet(
        f"{GCS_FILE_PATH}annual_service_and_opex.parquet",
        filesystem=filesystem,
    )

    print("exported annual service parquet")


def download_operating_and_capital_funding(
    client: bigquery.Client,
    filesystem: gcsfs.GCSFileSystem,
) -> None:
    query = """
        SELECT *
        FROM `cal-itp-data-infra.mart_ntd_funding_and_expenses.fct_operating_and_capital_funding_time_series`
        WHERE year >= @year
          AND source_state IN UNNEST(@state)
    """

    query_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("year", "INT64", 2015),
            bigquery.ArrayQueryParameter(
                "state", "STRING", ["CA", "OR", "AZ", "NV"]
            ),
        ]
    )

    query_job = client.query(query, job_config=query_config)
    df = query_job.result().to_dataframe()

    df.drop(columns=["dt", "execution_ts"]).to_parquet(
        f"{GCS_FILE_PATH}operating_and_capital_funding.parquet",
        filesystem=filesystem,
    )

    print("exported operating and capital funding parquet")


def download_capital_expenditures(
    client: bigquery.Client,
    filesystem: gcsfs.GCSFileSystem,
) -> None:
    query = """
        SELECT *
        FROM `cal-itp-data-infra.mart_ntd_funding_and_expenses.fct_capital_expenditures_time_series`
        WHERE year >= @year
          AND source_state IN UNNEST(@state)
    """

    query_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("year", "INT64", 2015),
            bigquery.ArrayQueryParameter(
                "state", "STRING", ["CA", "OR", "AZ", "NV"]
            ),
        ]
    )

    query_job = client.query(query, job_config=query_config)
    df = query_job.result().to_dataframe()

    df.drop(columns=["dt", "execution_ts"]).to_parquet(
        f"{GCS_FILE_PATH}capital_expenditures.parquet",
        filesystem=filesystem,
    )

    print("exported capital expenditures parquet")


if __name__ == "__main__":
    import google.auth

    credentials, project = google.auth.default()

    client = bigquery.Client(
        project=project,
        credentials=credentials,
    )
    filesystem = gcsfs.GCSFileSystem()

    download_annual_service_and_opex(client, filesystem)
    download_operating_and_capital_funding(client, filesystem)
    download_capital_expenditures(client, filesystem)

