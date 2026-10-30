"""
Downnload NTD tables for exploratory analysis.
"""

import gcsfs
from _utils import GCS_FILE_PATH
from google.cloud import bigquery
from snapshot_utils import bq_utils

client = bigquery.Client()
filesystem = gcsfs.GCSFileSystem()


def download_annual_service_and_opex(
    min_year: int = 2015,
    state: list[str] = ["CA", "OR", "AZ", "NV"],
) -> None:
    query = """
        SELECT 
            * EXCEPT(execution_ts, dt)
        FROM `cal-itp-data-infra.mart_ntd_funding_and_expenses.fct_service_data_and_operating_expenses_time_series_by_mode`
    """

    bq_utils.download_table(
        query,
        filter_dict={"ntd_start_year": [min_year], "ntd_us_source_states": state},
        output_path=f"{GCS_FILE_PATH}annual_service_and_opex.parquet",
    )

    print("exported annual service parquet")

    return


def download_operating_and_capital_funding(
    min_year: int = 2015,
    state: list[str] = ["CA", "OR", "AZ", "NV"],
) -> None:

    query = """
        SELECT 
            * EXCEPT (execution_ts, dt)
        FROM `cal-itp-data-infra.mart_ntd_funding_and_expenses.fct_operating_and_capital_funding_time_series`
    """
    bq_utils.download_table(
        query,
        filter_dict={"ntd_start_year": [min_year], "ntd_us_source_states": state},
        output_path=f"{GCS_FILE_PATH}operating_and_capital_funding.parquet",
    )

    print("exported operating and capital funding parquet")

    return


def download_capital_expenditures(
    min_year: int = 2015,
    state: list[str] = ["CA", "OR", "AZ", "NV"],
) -> None:

    query = """
        SELECT 
            * EXCEPT (execution_ts, dt)
        FROM `cal-itp-data-infra.mart_ntd_funding_and_expenses.fct_capital_expenditures_time_series`
    """
    bq_utils.download_table(
        query,
        filter_dict={"ntd_start_year": [min_year], "ntd_us_source_states": state},
        output_path=f"{GCS_FILE_PATH}capital_expenditures.parquet",
    )

    print("exported capital expenditures parquet")
    return


def download_ntd_rtpa_crosswalk(client, filesystem) -> None:
    query = """
        SELECT *
        FROM `cal-itp-data-infra.mart_transit_database.bridge_ntd_x_geography`
    """

    df = client.query(query).result().to_dataframe()
    df.to_parquet(
        f"{GCS_FILE_PATH}ntd_rtpa_crosswalk.parquet",
        filesystem=filesystem,
    )

    print("ntd_rtpa_crosswalk parquet")


if __name__ == "__main__":
    min_year = 2015
    state = ["CA", "OR", "AZ", "NV"]

    download_annual_service_and_opex(
        min_year=min_year,
        state=state,
    )
    download_operating_and_capital_funding(
        min_year=min_year,
        state=state,
    )
    download_capital_expenditures(
        min_year=min_year,
        state=state,
    )

    download_ntd_rtpa_crosswalk(
        client,
        filesystem,
    )
