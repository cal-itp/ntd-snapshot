"""
Download monthly NTD tables.
"""

from snapshot_utils import bq_utils
from snapshot_utils.project_vars import GCS_FILE_PATH
from update_vars import min_year

if __name__ == "__main__":
    # download the monthly table
    ntd_sql_query = """
        SELECT * FROM `cal-itp-data-infra.mart_ntd_ridership.fct_complete_monthly_ridership_with_adjustments_and_estimates`
    """
    monthly_filter_dict = {
        "ntd_start_year": [min_year],
        "ntd_us_states": ["CA", "OR", "AZ", "NV"],
    }

    bq_utils.download_table(
        ntd_sql_query,
        monthly_filter_dict,
        additional_sql_condition="agency IS NOT NULL",
        output_path=f"{GCS_FILE_PATH}monthly.parquet",
    )

    print("downloaded monthly warehouse table")
