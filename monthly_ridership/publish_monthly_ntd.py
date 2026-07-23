"""
Publish NTD monthly ridership by RTPA.
"""

import os
import shutil

import gcsfs
import pandas as pd
from snapshot_utils import excel_utils, publish_utils
from snapshot_utils.project_vars import GCS_FILE_PATH, PUBLIC_GCS

fs = gcsfs.GCSFileSystem()

# list columns to keep for Excel, in order they should appear
MONTHLY_COLS = [
    # NTD identifier columns
    "agency",
    "ntd_id",
    "year",
    "month",
    "month_first_day",
    "mode",
    "mode_full_name",
    "_3_mode",
    "type_of_service",
    "type_of_service_full_name",
    "service_type",
    "reporter_type",
    "mode_type_of_service_status",
    "uza_name",
    "uace_cd",
    # metric cols
    "upt",
    "upt_prior_year",
    "upt_change_1yr",
    "upt_pct_change_1yr",
    "voms",
    "vrh",
    "vrm",
    "rtpa",
]


def monthly_data_to_publish(report_aggregation: str):
    """
    Prep monthly data for publishing.
    Subset columns, rename, etc.
    When multiple data products share the same table, use this to decide which columns
    are relevant to be used.
    """
    df = (
        pd.read_parquet(
            f"{GCS_FILE_PATH}{report_aggregation}_with_crosswalk.parquet",
            filesystem=gcsfs.GCSFileSystem(),
            columns=MONTHLY_COLS,
        )
        .reindex(columns=MONTHLY_COLS)
        .dropna(subset="rtpa")
    )

    # For Excel, make sure this displays as date instead of datetime
    df = df.assign(month_first_day=df.month_first_day.dt.date)

    return df


def monthly_report_by_rtpa(
    report_aggregation: str = "monthly",
    upload_to_public: bool = False,
):
    """
    Create zipped Excel folder called YYYY_MONTH_monthly_report_data.zip (2026_January),
    with each RTPA having its own Excel sheet.

    Each Excel sheet has:
    - cover page with data dictionary
    - full data table for that RTPA
    - data table aggregated by agency
    - data table aggregated by mode
    - data table aggregated by type of service
    """
    df = monthly_data_to_publish(report_aggregation)

    # the latest month available
    # format of file has year-month_full_name
    MOST_RECENT_MONTH = pd.to_datetime(df.month_first_day).max().strftime("%Y_%B")

    excel_output_foldername = f"{MOST_RECENT_MONTH}_{report_aggregation}_report_data"
    zipped_excel_output_foldername = f"{excel_output_foldername}.zip"

    for one_rtpa in df.rtpa.unique():
        rtpa_excel_filename = excel_utils.insert_excel_cover_sheet(
            report_aggregation, excel_output_foldername, one_rtpa
        )
        excel_utils.export_aggregations_as_excel_sheets(
            report_aggregation, rtpa_excel_filename, one_rtpa
        )

    # create zipped Excel
    excel_utils.zip_excel(excel_output_foldername)

    # Upload zipped Excel to GCS
    fs.put(
        zipped_excel_output_foldername,
        f"{GCS_FILE_PATH}publish/{zipped_excel_output_foldername}",
    )
    os.remove(zipped_excel_output_foldername)
    shutil.rmtree(f"{excel_output_foldername}/")

    # Publish to public GCS, copy zipped file in private GCS to public GCS
    if upload_to_public:
        publish_utils.write_to_public_gcs(
            f"{GCS_FILE_PATH}publish/{zipped_excel_output_foldername}",
            f"ntd_monthly_ridership/{zipped_excel_output_foldername}",
            PUBLIC_GCS,
        )

    return


if __name__ == "__main__":
    monthly_report_by_rtpa(report_aggregation="monthly", upload_to_public=True)
