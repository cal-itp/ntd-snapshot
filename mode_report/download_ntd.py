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
from exploratory._utils import GCS_FILE_PATH
from google.cloud import bigquery


def download_annual_service_and_opex(
    client: bigquery.Client,
    filesystem: gcsfs.GCSFileSystem,
    min_year: int = 2015,
    state: list[str] | None = None,
) -> None:
    if state is None:
        state = ["CA", "OR", "AZ", "NV"]

    query = """
        SELECT *
        FROM `cal-itp-data-infra.mart_ntd_funding_and_expenses.fct_service_data_and_operating_expenses_time_series_by_mode`
        WHERE year >= @year
          AND source_state IN UNNEST(@state)
    """

    query_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("year", "INT64", min_year),
            bigquery.ArrayQueryParameter("state", "STRING", state),
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
    min_year: int = 2015,
    state: list[str] | None = None,
) -> None:
    if state is None:
        state = ["CA", "OR", "AZ", "NV"]

    query = """
        SELECT *
        FROM `cal-itp-data-infra.mart_ntd_funding_and_expenses.fct_operating_and_capital_funding_time_series`
        WHERE year >= @year
          AND source_state IN UNNEST(@state)
    """

    query_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("year", "INT64", min_year),
            bigquery.ArrayQueryParameter("state", "STRING", state),
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
    min_year: int = 2015,
    state: list[str] | None = None,
) -> None:
    if state is None:
        state = ["CA", "OR", "AZ", "NV"]

    query = """
        SELECT *
        FROM `cal-itp-data-infra.mart_ntd_funding_and_expenses.fct_capital_expenditures_time_series`
        WHERE year >= @year
          AND source_state IN UNNEST(@state)
    """

    query_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("year", "INT64", min_year),
            bigquery.ArrayQueryParameter("state", "STRING", state),
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

    min_year = 2015
    state = ["CA", "OR", "AZ", "NV"]

    download_annual_service_and_opex(
        client,
        filesystem,
        min_year=min_year,
        state=state,
    )
    download_operating_and_capital_funding(
        client,
        filesystem,
        min_year=min_year,
        state=state,
    )
    download_capital_expenditures(
        client,
        filesystem,
        min_year=min_year,
        state=state,
    )
