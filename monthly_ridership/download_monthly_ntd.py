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

credentials, project = google.auth.default()


def download_monthly_table(
    project_name: str,
    dataset_name: str,
    table_name: str = "fct_complete_monthly_ridership_with_adjustments_and_estimates",
    min_year: int = 2018,
):
    """
    What should filters be?
    Visualizations are plotting the latest year-month combo
    """
    basic_query = bq_utils.basic_sql_query(project_name, dataset_name, table_name)

    query_params = bq_utils.set_bq_query_params(
        scalar_query_parameter={"min_year": 2018, "state": "CA"},
    )

    job_config = bigquery.QueryJobConfig(query_parameters=query_params)

    # dropped the agency IS NOT NULL condition from query
    sql_query_statement = f"{basic_query} WHERE year >= @min_year AND (state = @state OR CONTAINS_SUBSTR(uza_name, ', CA')) AND agency IS NOT NULL"

    df = bq_utils.bq_faster_download(
        sql_query_statement,
        project=project_name,
        credentials=credentials,
        job_config=job_config,
    )

    df = df.drop(columns=["dt", "execution_ts", "date"]).pipe(bq_utils.fix_date_columns)

    return df


if __name__ == "__main__":
    NTD_DATASET = "mart_ntd_ridership"

    # download the monthly table
    monthly_df = download_monthly_table(
        project_name=project,
        dataset_name=NTD_DATASET,
        table_name="fct_complete_monthly_ridership_with_adjustments_and_estimates",
    )

    monthly_df.to_parquet(
        f"{GCS_FILE_PATH}monthly.parquet", filesystem=gcsfs.GCSFileSystem()
    )

    print("downloaded monthly warehouse table")
