"""
Download new annual and monthly NTD tables.

TODO: bq_utils needs credentials now because of the way the kwargs pop and look for it.
Find out default and set it.

fix date columns in monthly table, not yet able to download
"""

import gcsfs
import google.auth
from google.cloud import bigquery
from snapshot_utils import bq_utils
from snapshot_utils.project_vars import GCS_FILE_PATH
from update_vars import min_year

credentials, project = google.auth.default()


def download_annual_ntd(
    project_name: str,
    dataset_name: str,
    table_name: str = "fct_service_data_and_operating_expenses_time_series_by_mode",
    min_year: int = min_year,
):
    """
    What should filters be?
    Visualizations plot latest year?
    """
    basic_query = bq_utils.basic_sql_query(project_name, dataset_name, table_name)

    query_params = bq_utils.set_bq_query_params(
        scalar_query_parameter={"min_year": min_year},
    )
    job_config = bigquery.QueryJobConfig(query_parameters=query_params)

    sql_query_statement = f"{basic_query} WHERE year >= @min_year AND last_report_year >= @min_year AND(CONTAINS_SUBSTR(primary_uza_name, ', CA') OR CONTAINS_SUBSTR(primary_uza_name, 'California'))"

    df = bq_utils.bq_faster_download(
        sql_query_statement,
        project=project_name,
        credentials=credentials,
        job_config=job_config,
    )

    df = df.drop(columns=["dt", "execution_ts"]).pipe(bq_utils.fix_date_columns)

    return df


def download_ntd_crosswalk(
    project_name: str,
    dataset_name: str,
    table_name: str = "",
):
    """ """
    df = bq_utils.download_table(
        project_name=project_name,
        dataset_name=dataset_name,
        table_name=table_name,
        date_col=None,
    )

    return df


if __name__ == "__main__":
    NTD_DATASET = "mart_ntd_funding_and_expenses"

    # download the annual table
    annual_df = download_annual_ntd(
        project_name=project,
        dataset_name=NTD_DATASET,
        table_name="fct_service_data_and_operating_expenses_time_series_by_mode",
        min_year=min_year,
    )
    annual_df.to_parquet(
        f"{GCS_FILE_PATH}annual.parquet", filesystem=gcsfs.GCSFileSystem()
    )
    print("downloaded annual warehouse table")

    # download crosswalk
    crosswalk = download_ntd_crosswalk(
        project_name=project,
        dataset_name="mart_transit_database",
        table_name="bridge_ntd_x_geography",
    )

    crosswalk.to_parquet(
        f"{GCS_FILE_PATH}crosswalk.parquet", filesystem=gcsfs.GCSFileSystem()
    )

    print("downloaded crosswalk for ntd_id to RTPA")
