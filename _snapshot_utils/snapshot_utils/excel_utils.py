"""
Functions for exporting Excel files
"""

import shutil
from pathlib import Path
from typing import Literal

import gcsfs
import pandas as pd

from snapshot_utils.project_vars import GCS_FILE_PATH


def readable_rtpa(rtpa_name: str) -> str:
    """
    Return a snakecased version of RTPA name.
    """
    return rtpa_name.replace(" ", "_").replace("/", "_").lower()


def import_filtered_rtpa_file(
    gcs_file_name: str = "", one_rtpa: str = ""
) -> pd.DataFrame:
    """
    Filter the GCS parquet by RTPA.
    """
    df = pd.read_parquet(
        f"{GCS_FILE_PATH}{gcs_file_name}",
        filesystem=gcsfs.GCSFileSystem(),
        filters=[[("rtpa", "==", one_rtpa)]],
    ).reset_index(drop=True)

    return df


def insert_excel_cover_sheet(
    report_aggregation: Literal["annual", "monthly"],
    excel_output_foldername: str,
    rtpa_name: str,
) -> str:
    """
    Create Excel workbook for RTPA.
    Insert cover_sheet.
    Return the Excel filename of this specific RTPA.
    """
    rtpa_snakecase = readable_rtpa(rtpa_name)

    if report_aggregation == "annual":
        cover_sheet_path = Path("./annual_cover_sheet_template.xlsx")
        cover_sheet_index_col = "**NTD Annual Ridership by RTPA**"

    elif report_aggregation == "monthly":
        cover_sheet_path = Path("./monthly_cover_sheet_template.xlsx")
        cover_sheet_index_col = "**NTD Monthly Ridership by RTPA**"

    # create folder to store each RTPA's Excel
    Path(excel_output_foldername).mkdir(parents=True, exist_ok=True)

    # define Excel filename for individual RTPA
    rtpa_excel_filename = Path(f"./{excel_output_foldername}/{rtpa_snakecase}.xlsx")

    # Read in templated cover sheet for RTPA and save out
    cover_sheet = pd.read_excel(
        cover_sheet_path, index_col=cover_sheet_index_col, engine="openpyxl"
    )
    cover_sheet.to_excel(rtpa_excel_filename, sheet_name="README", engine="openpyxl")
    print(f"created {rtpa_excel_filename}")

    # Need to return the filename created for this RTPA Excel sheet, use in subsequent step
    return rtpa_excel_filename


def export_aggregations_as_excel_sheets(
    report_aggregation: Literal["annual", "monthly"],
    rtpa_excel_filename: str,
    one_rtpa: str,
):
    """
    Add individual Excel sheets for each RTPA.
    - full df
    - annual: agency, mode, type of service, reporter type
    - monthly: agency, mode, type of service
    """
    with pd.ExcelWriter(rtpa_excel_filename, mode="a") as writer:
        import_filtered_rtpa_file(
            f"{report_aggregation}_with_crosswalk.parquet", one_rtpa
        ).to_excel(writer, sheet_name="RTPA Ridership", index=False)
        import_filtered_rtpa_file(
            f"{report_aggregation}/agency.parquet", one_rtpa
        ).to_excel(writer, sheet_name="Aggregated by Agency", index=False)
        import_filtered_rtpa_file(
            f"{report_aggregation}/mode.parquet", one_rtpa
        ).to_excel(writer, sheet_name="Aggregated by Mode", index=False)
        import_filtered_rtpa_file(
            f"{report_aggregation}/type_of_service.parquet", one_rtpa
        ).to_excel(writer, sheet_name="Aggregated by TOS", index=False)

        if report_aggregation == "annual":
            import_filtered_rtpa_file(
                f"{report_aggregation}/reporter_type.parquet", one_rtpa
            ).to_excel(writer, sheet_name="Aggregated by Reporter Type", index=False)

    print(f"completed Excel exports: {rtpa_excel_filename}")
    return


def zip_excel(excel_folder_name: str):
    """
    Zip the excel workbook as .zip.
    Each RTPA as an individual Excel workbook within folder.
    Each Excel workbook has multiple sheets.
    """
    shutil.make_archive(f"./{excel_folder_name}", "zip", excel_folder_name)
    return
