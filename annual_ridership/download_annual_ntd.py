"""
Download annual NTD tables.
"""

from snapshot_utils import bq_utils
from snapshot_utils.project_vars import GCS_FILE_PATH
from update_vars import min_year

if __name__ == "__main__":
    # download the annual table
    service_sql_query = """
        SELECT * FROM `cal-itp-data-infra.mart_ntd_funding_and_expenses.fct_service_data_and_operating_expenses_time_series_by_mode`
    """
    annual_filter_dict = {"ntd_start_year": [min_year]}

    bq_utils.download_table(
        service_sql_query,
        annual_filter_dict,
        additional_sql_condition="( CONTAINS_SUBSTR(primary_uza_name, ', CA') OR CONTAINS_SUBSTR(primary_uza_name, 'California') )",
        output_path=f"{GCS_FILE_PATH}annual.parquet",
    )
    print("downloaded annual warehouse table")

    # download crosswalk
    crosswalk_sql_query = "SELECT * FROM `cal-itp-data-infra.mart_transit_database.bridge_ntd_x_geography`"

    bq_utils.download_table(
        crosswalk_sql_query,
        filter_dict={},
        output_path=f"{GCS_FILE_PATH}crosswalk.parquet",
    )

    print("downloaded crosswalk for ntd_id to RTPA")
