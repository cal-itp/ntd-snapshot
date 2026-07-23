"""
Publish NTD annual ridership by RTPA
"""

import os
import shutil

import gcsfs
import pandas as pd
from snapshot_utils import excel_utils, publish_utils
from snapshot_utils.project_vars import GCS_FILE_PATH, PUBLIC_GCS

fs = gcsfs.GCSFileSystem()

# list columns to keep for Excel, in order they should appear
ANNUAL_COLS = [
    # NTD identifier columns
    "agency",
    "ntd_id",
    "year",
    "mode",
    "mode_full_name",
    "type_of_service",
    "type_of_service_full_name",
    "reporter_type",
    "agency_status",
    "primary_uza_name",
    # metric cols
    "upt",
    "upt_prior_year",
    "upt_change_1yr",
    "upt_pct_change_1yr",
    "rtpa",
]


def annual_data_to_publish(report_aggregation: str = "annual"):
    """
    Prep annual data for publishing.
    Subset columns, rename, etc.
    Annual ridership and UCLA performance metrics both use the same warehouse table,
    but not every column needs to be published for Excel.
    Only the relevant upt columns should be published, listed above.
    """
    df = (
        pd.read_parquet(
            f"{GCS_FILE_PATH}{report_aggregation}_with_crosswalk.parquet",
            filesystem=gcsfs.GCSFileSystem(),
            columns=ANNUAL_COLS,
        )
        .reindex(columns=ANNUAL_COLS)
        .dropna(subset="rtpa")
    )

    return df


def annual_report_by_rtpa(
    report_aggregation="annual",
    upload_to_public: bool = False,
):
    """
    Create zipped Excel folder called annual_report_data.zip,
    with each RTPA having its own Excel sheet.

    Each Excel sheet has:
    - cover page with data dictionary
    - full data table for that RTPA
    - data table aggregated by agency
    - data table aggregated by mode
    - data table aggregated by type of service
    - data table aggregated by reporter type
    """

    df = annual_data_to_publish(report_aggregation)

    # annual_report_data.zip in public GCS
    # do not need date, as each year's data contains all prior years
    # can overwrite file
    excel_output_foldername = f"{report_aggregation}_report_data"
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
            f"ntd_annual_ridership/{zipped_excel_output_foldername}",
            PUBLIC_GCS,
        )

    return


if __name__ == "__main__":
    annual_report_by_rtpa(report_aggregation="annual", upload_to_public=True)
