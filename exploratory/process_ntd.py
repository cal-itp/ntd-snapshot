import gcsfs
import geopandas as gpd
import pandas as pd
from _utils import GCS_FILE_PATH
import requests


def load_service_and_opex():
    filesystem = gcsfs.GCSFileSystem()
    return pd.read_parquet(
        f"{GCS_FILE_PATH}annual_service_and_opex.parquet",
        filesystem=filesystem,
    )


def load_cap_op_funding():
    filesystem = gcsfs.GCSFileSystem()
    return pd.read_parquet(
        f"{GCS_FILE_PATH}operating_and_capital_funding.parquet",
        filesystem=filesystem,
    )

def load_capex():
    filesystem = gcsfs.GCSFileSystem()
    return pd.read_parquet(
        f"{GCS_FILE_PATH}capital_expenditures.parquet",
        filesystem=filesystem,
    )


def subset_california(df):
    return df[df["source_state"] == "CA"].copy()


def add_mode_group(df):
    bus_modes = ["Bus", "Bus Rapid Transit", "Commuter Bus", "Trolleybus"]
    rail_modes = [
        "Commuter Rail",
        "Heavy Rail",
        "Light Rail",
        "Streetcar",
        "Hybrid Rail",
        "Monorail / Automated Guideway",
        "Cable Car",
    ]

    df["mode_group"] = df["mode_full_name"].map(
        lambda x: "Bus" if x in bus_modes else "Rail" if x in rail_modes else "Other"
    )

    return df


def round_tooltip_columns(df):
    columns_to_round = [
        "opex_per_vrh",
        "opex_per_vrm",
        "opex_per_upt",
        "upt_per_vrh",
        "upt_per_vrm",
        "farebox_recovery_ratio",
    ]

    df[columns_to_round] = df[columns_to_round].round(2)

    return df


def load_uza_shapes():
    url = "https://www2.census.gov/geo/tiger/TIGER2024/UAC20/tl_2024_us_uac20.zip"
    return gpd.read_file(url)

def calculate_shares(df, total_col, source_cols, suffix):
    """
    Calculate the share of each funding source relative to a total.

    Parameters
    ----------
    total_col : str, Column containing the overall total.

    source_cols : dict, Mapping of source names to their corresponding columns.

    suffix : str, Suffix used in the generated share column names.
    """
    nonzero = df[total_col] > 0

    for source, category_col in source_cols.items():
        share_col = f"{source}_{suffix}_share"

        df.loc[nonzero, share_col] = (
            df.loc[nonzero, category_col]
            / df.loc[nonzero, total_col]
        )

    return df

def get_annual_average_cpi(start_year, end_year):
    """Fetch BLS CPI data and calculate the annual average CPI."""

    url = "https://api.bls.gov/publicAPI/v2/timeseries/data/"

    payload = {
        "seriesid": ["CUUR0000SA0"],
        "startyear": str(start_year),
        "endyear": str(end_year)
    }

    response = requests.post(url, json=payload)
    response.raise_for_status()

    data = response.json()
    cpi_data = data["Results"]["series"][0]["data"]

    # Convert API response to DataFrame
    cpi = pd.DataFrame(cpi_data)

    # Convert columns to numeric
    cpi["year"] = pd.to_numeric(cpi["year"])
    cpi["value"] = pd.to_numeric(cpi["value"])

    # Keep monthly observations only
    cpi = cpi[cpi["period"].str.startswith("M")]

    # Calculate annual average CPI
    cpi_annual = (
        cpi.groupby("year", as_index=False)["value"]
           .mean()
           .rename(columns={"value": "cpi"})
    )

    return cpi_annual

def add_real_values(df, value_cols, cpi_annual, base_cpi):
    """
    Merge annual CPI and calculate values in 2024 real dollars.

    value_cols: dictionary of {nominal_column: real_column}
    """

    df = df.merge(
        cpi_annual,
        on="year",
        how="left"
    )

    for value_col, real_col in value_cols.items():
        df[real_col] = (
            df[value_col] * base_cpi / df["cpi"]
        ).round(2)

    return df


def aggregate_capex_to_agency_year(df):
    """
    Aggregate CapEx from mode level to agency-year level.

    Final grain:
        one row per ntd_id × year
    """

    df_agency = (
        df
        .groupby(["ntd_id", "year"], as_index=False)
        .agg({
            # Expenditure amounts: sum across modes
            "total_capital_expenditures": "sum",
            "rolling_stock_expenditures": "sum",
            "facilities_expenditures": "sum",
            "other_expenditures": "sum",

            # Agency/year characteristics: take first value
            "legacy_ntd_id": "first",
            "agency_status": "first",
            "census_year": "first",
            "last_report_year": "first",
            "reporter_type": "first",
            "reporting_module": "first",
            "uace_code": "first",
            "uza_area_sq_miles": "first",
            "uza_name": "first",
            "uza_population": "first",
            "source_agency": "first",
            "source_city": "first",
            "source_state": "first"
        })
    )

    # Check final grain
    if df_agency.duplicated(["ntd_id", "year"]).any():
        raise ValueError("Duplicate ntd_id × year combinations remain.")

    return df_agency

def aggregate_opex_to_agency_year(df):
    """
    Aggregate OpEx from mode/service level to agency-year level.

    Final grain:
        one row per ntd_id × year
    """

    df_agency = (
        df
        .groupby(["ntd_id", "year"], as_index=False)
        .agg({
            # Expenditure amounts: sum across modes and service types
            "operating_expenses_total": "sum",
            "operating_expenses_vehicle_operations": "sum",
            "operating_expenses_vehicle_maintenance": "sum",
            "operating_expenses_nonvehicle_maintenance": "sum",
            "operating_expenses_general_administration": "sum",

            # Agency/year characteristics: take first value
            "agency_status": "first",
            "census_year": "first",
            "last_report_year": "first",
            "reporter_type": "first",
            "reporting_module": "first",
            "uace_code": "first",
            "uza_area_sq_miles": "first",
            "primary_uza_name": "first",
            "uza_population": "first",
            "source_agency": "first",
            "source_city": "first",
            "source_state": "first"
        })
    )

    # Check final grain
    if df_agency.duplicated(["ntd_id", "year"]).any():
        raise ValueError("Duplicate ntd_id × year combinations remain.")
        
    return df_agency


