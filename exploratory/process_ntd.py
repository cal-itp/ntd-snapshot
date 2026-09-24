import gcsfs
import geopandas as gpd
import pandas as pd
from _utils import GCS_FILE_PATH
import requests
from google.cloud import bigquery
filesystem = gcsfs.GCSFileSystem()


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

def export_to_gcs(
    df: pd.DataFrame,
    filename: str,
    filesystem: gcsfs.GCSFileSystem,
) -> None:
    df.to_parquet(
        f"{GCS_FILE_PATH}{filename}.parquet",
        filesystem=filesystem,
    )

    print(f"exported {filename}.parquet")


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
    """Fetch BLS CPI data, calculate annual averages, and save to GCS_FILE_PATH."""
    url = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
    payload = {"seriesid": ["CUUR0000SA0"], "startyear": str(start_year), "endyear": str(end_year)}

    response = requests.post(url, json=payload); response.raise_for_status()
    data = response.json()
    if data.get("status") != "REQUEST_SUCCEEDED": raise ValueError(f"BLS API error: {data}")

    cpi = pd.DataFrame(data["Results"]["series"][0]["data"])
    cpi["year"] = pd.to_numeric(cpi["year"]); cpi["value"] = pd.to_numeric(cpi["value"])
    cpi = cpi[cpi["period"].str.startswith("M")]
    cpi_annual = cpi.groupby("year", as_index=False)["value"].mean().rename(columns={"value": "cpi"})

    cpi_annual.to_csv(f"{GCS_FILE_PATH}cpi_annual.csv", index=False)
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



def compute_hhi(
    df,
    component_columns,
    group_column,
    year_column
):
    """
    Calculates spending concentration by group and year based on
    the distribution of spending across component categories.
    """
    grouped = (
        df.groupby([year_column, group_column])[component_columns]
        .sum()
        .reset_index()
    )

    component_total = grouped[component_columns].sum(axis=1)

    shares = grouped[component_columns].div(
        component_total,
        axis=0
    )

    grouped["hhi"] = shares.pow(2).sum(axis=1)

    return grouped[[year_column, group_column, "hhi"]]




def spending_per_capita(df, value_column, population_column, group_column, year_column):
    grouped = (df.groupby([year_column, group_column])
               .agg(value=(value_column, "sum"), population=(population_column, "sum"))
               .reset_index())
    grouped["per_capita"] = grouped["value"] / grouped["population"]
    return grouped



def spending_volatility(
    df, value_column, group_column, year_column, target_year
):
    trend = (
        df.groupby([year_column, group_column])[value_column]
        .sum()
        .reset_index()
        .sort_values([group_column, year_column])
    )

    trend["yoy_change"] = (
        trend.groupby(group_column)[value_column].pct_change()
    )

    result = trend[trend[year_column] == target_year].copy()

    result["volatility"] = result["yoy_change"].abs()

    return result[[group_column, "volatility"]]
