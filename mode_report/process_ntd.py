import re

import gcsfs
import geopandas as gpd
import numpy as np
import pandas as pd
import requests
from _utils import GCS_FILE_PATH

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


def normalize_uza_name(x):
    if pd.isna(x):
        return x

    x = str(x).strip()
    x = re.sub(r"-+", "-", x)
    return x


def aggregate_capex_to_agency_year(df):
    """
    Aggregate CapEx from mode level to agency-year level.

    Final grain:
        one row per ntd_id × year
    """

    df_agency = df.groupby(["ntd_id", "year"], as_index=False).agg(
        {
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
            "source_state": "first",
        }
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

    df_agency = df.groupby(["ntd_id", "year"], as_index=False).agg(
        {
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
            "source_state": "first",
        }
    )

    # Check final grain
    if df_agency.duplicated(["ntd_id", "year"]).any():
        raise ValueError("Duplicate ntd_id × year combinations remain.")

    return df_agency


def subset_california(df):
    return df[df["source_state"] == "CA"].copy()


def reconcile_modes_for_merge(df_capex, df_opex):
    """
    Reconcile mode names for the merged CapEx/OpEx dataset only.

    Shared modes are kept unchanged.
    Modes appearing in only one dataset are mapped to "Other".
    The original mode name is preserved in `original_mode_full_name`.

    This function does NOT modify the input DataFrames.
    """

    capex = df_capex.copy()
    opex = df_opex.copy()

    # Preserve original mode names
    capex["original_mode_full_name"] = capex["mode_full_name"]
    opex["original_mode_full_name"] = opex["mode_full_name"]

    # Modes that exist in both datasets
    shared_modes = set(capex["mode_full_name"].dropna()) & set(
        opex["mode_full_name"].dropna()
    )

    # Dataset-specific modes -> Other
    capex["mode_full_name"] = capex["mode_full_name"].where(
        capex["mode_full_name"].isin(shared_modes),
        "Other",
    )

    opex["mode_full_name"] = opex["mode_full_name"].where(
        opex["mode_full_name"].isin(shared_modes),
        "Other",
    )

    # Recalculate mode groups after reconciliation
    capex = add_mode_group(capex)
    opex = add_mode_group(opex)

    return capex, opex


def merge_capex_opex(df_capex, df_opex):
    """
    Merge CapEx and OpEx after reconciling modes.

    The input DataFrames are copied, so the original independent
    CapEx and OpEx datasets are not modified.

    Final grain:
        one row per ntd_id × year × mode_full_name
    """

    capex, opex = reconcile_modes_for_merge(
        df_capex,
        df_opex,
    )

    merge_keys = [
        "ntd_id",
        "year",
        "mode_full_name",
        "reporter_type",
        "reporting_module",
        "agency_status",
        "source_state",
        "source_agency",
    ]

    # Aggregate to the merge grain
    # OpEx can have multiple rows per mode/year because of
    # type_of_service. CapEx can also have multiple source rows.
    # Sum numeric expenditure/service measures before merging.

    capex_numeric = [
        "total_capital_expenditures_real",
        "rolling_stock_expenditures_real",
        "facilities_expenditures_real",
        "other_expenditures_real",
    ]

    opex_numeric = [
        "operating_expenses_total_real",
        "operating_expenses_vehicle_operations_real",
        "operating_expenses_vehicle_maintenance_real",
        "operating_expenses_nonvehicle_maintenance_real",
        "operating_expenses_general_administration_real",
        "fare_revenue_real",
        "unlinked_passenger_trips",
        "vehicle_revenue_hours",
        "vehicle_revenue_miles",
        "passenger_miles_traveled",
        "vehicles_operated_in_maxiumum_service",
    ]

    # Only aggregate columns that actually exist
    capex_numeric = [col for col in capex_numeric if col in capex.columns]

    opex_numeric = [col for col in opex_numeric if col in opex.columns]

    capex = capex.groupby(merge_keys, as_index=False)[capex_numeric].sum()

    opex = opex.groupby(merge_keys, as_index=False)[opex_numeric].sum()

    # Merge
    merged = capex.merge(
        opex,
        on=merge_keys,
        how="outer",
        suffixes=("_capex", "_opex"),
        indicator=True,
    )

    return merged


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
            df.loc[nonzero, category_col] / df.loc[nonzero, total_col]
        )

    return df


def get_annual_average_cpi(start_year, end_year):
    """Fetch BLS CPI data, calculate annual averages, and save to GCS_FILE_PATH."""
    url = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
    payload = {
        "seriesid": ["CUUR0000SA0"],
        "startyear": str(start_year),
        "endyear": str(end_year),
    }

    response = requests.post(url, json=payload)
    response.raise_for_status()
    data = response.json()
    if data.get("status") != "REQUEST_SUCCEEDED":
        raise ValueError(f"BLS API error: {data}")

    cpi = pd.DataFrame(data["Results"]["series"][0]["data"])
    cpi["year"] = pd.to_numeric(cpi["year"])
    cpi["value"] = pd.to_numeric(cpi["value"])
    cpi = cpi[cpi["period"].str.startswith("M")]
    cpi_annual = (
        cpi.groupby("year", as_index=False)["value"]
        .mean()
        .rename(columns={"value": "cpi"})
    )

    cpi_annual.to_csv(f"{GCS_FILE_PATH}cpi_annual.csv", index=False)
    return cpi_annual


def add_real_values(df, value_cols, cpi_annual, base_cpi):
    """
    Merge annual CPI and calculate values in 2024 real dollars.

    value_cols: list of nominal columns to convert to real dollars.
    """

    df = df.merge(
        cpi_annual,
        on="year",
        how="left",
    )

    for value_col in value_cols:
        real_col = f"{value_col}_real"
        df[real_col] = (df[value_col] * base_cpi / df["cpi"]).round(2)

    return df


def compute_hhi(df, component_columns, group_column, year_column):
    """
    Calculates spending concentration by group and year based on
    the distribution of spending across component categories.
    """
    grouped = (
        df.groupby([year_column, group_column])[component_columns].sum().reset_index()
    )

    component_total = grouped[component_columns].sum(axis=1)

    shares = grouped[component_columns].div(component_total, axis=0)

    grouped["hhi"] = shares.pow(2).sum(axis=1)

    return grouped[[year_column, group_column, "hhi"]]


def spending_per_capita(df, value_column, population_column, group_column, year_column):
    grouped = (
        df.groupby([year_column, group_column])
        .agg(value=(value_column, "sum"), population=(population_column, "sum"))
        .reset_index()
    )
    grouped["per_capita"] = grouped["value"] / grouped["population"]
    return grouped


def spending_volatility(df, value_column, group_column, year_column, target_year):
    trend = (
        df.groupby([year_column, group_column])[value_column]
        .sum()
        .reset_index()
        .sort_values([group_column, year_column])
    )

    trend["yoy_change"] = trend.groupby(group_column)[value_column].pct_change()

    result = trend[trend[year_column] == target_year].copy()

    result["volatility"] = result["yoy_change"].abs()

    return result[[group_column, "volatility"]]


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


# ---------------------------------------------------------------------
# Mode report
# ---------------------------------------------------------------------


def create_mode_report_data():
    df_capex = add_mode_group(subset_california(load_capex()))
    df_opex = add_mode_group(subset_california(load_service_and_opex()))

    df_capex["uza_name"] = df_capex["uza_name"].apply(normalize_uza_name)

    df_opex["primary_uza_name"] = df_opex["primary_uza_name"].apply(normalize_uza_name)

    # Convert nominal values to 2024 dollars
    cpi_annual = get_annual_average_cpi(2015, 2024)
    base_cpi = cpi_annual.loc[cpi_annual["year"] == 2024, "cpi"].iloc[0]

    df_capex = add_real_values(
        df_capex,
        [
            "total_capital_expenditures",
            "rolling_stock_expenditures",
            "facilities_expenditures",
            "other_expenditures",
        ],
        cpi_annual,
        base_cpi,
    )

    df_opex = add_real_values(
        df_opex,
        [
            "operating_expenses_total",
            "operating_expenses_vehicle_operations",
            "operating_expenses_vehicle_maintenance",
            "operating_expenses_nonvehicle_maintenance",
            "operating_expenses_general_administration",
            "fare_revenue",
            "opex_per_vrm",
            "opex_per_vrh",
            "opex_per_upt",
        ],
        cpi_annual,
        base_cpi,
    )

    # Calculate efficiency metrics
    df_opex["trips_per_vrm"] = (
        df_opex["unlinked_passenger_trips"] / df_opex["vehicle_revenue_miles"]
    )
    df_opex["log_opex_vrm"] = np.log10(
        df_opex["opex_per_vrm_real"].where(df_opex["opex_per_vrm_real"] > 0)
    )
    df_opex["log_trips_vrm"] = np.log10(
        df_opex["trips_per_vrm"].where(df_opex["trips_per_vrm"] > 0)
    )

    df_opex["trips_per_vrh"] = (
        df_opex["unlinked_passenger_trips"] / df_opex["vehicle_revenue_hours"]
    )
    df_opex["log_opex_vrh"] = np.log10(
        df_opex["opex_per_vrh_real"].where(df_opex["opex_per_vrh_real"] > 0)
    )
    df_opex["log_trips_vrh"] = np.log10(
        df_opex["trips_per_vrh"].where(df_opex["trips_per_vrh"] > 0)
    )

    # Cost Effectivenesss Metrics
    df_opex["fare_revenue_per_trip"] = (
        df_opex["fare_revenue"] / df_opex["unlinked_passenger_trips"]
    )

    df_opex["subsidy_per_trip"] = (
        df_opex["operating_expenses_total"] - df_opex["fare_revenue"]
    ) / df_opex["unlinked_passenger_trips"]

    # Calculate HHI, spending per capita, and volatility
    opex_hhi = compute_hhi(
        df_opex,
        [
            "operating_expenses_vehicle_operations_real",
            "operating_expenses_vehicle_maintenance_real",
            "operating_expenses_nonvehicle_maintenance_real",
            "operating_expenses_general_administration_real",
        ],
        "mode_group",
        "year",
    )
    capex_hhi = compute_hhi(
        df_capex,
        [
            "rolling_stock_expenditures_real",
            "facilities_expenditures_real",
            "other_expenditures_real",
        ],
        "mode_group",
        "year",
    )

    opex_pc = spending_per_capita(
        df_opex, "operating_expenses_total_real", "uza_population", "mode_group", "year"
    )
    capex_pc = spending_per_capita(
        df_capex,
        "total_capital_expenditures_real",
        "uza_population",
        "mode_group",
        "year",
    )

    opex_vol = spending_volatility(
        df_opex, "operating_expenses_total_real", "mode_group", "year", 2024
    )
    capex_vol = spending_volatility(
        df_capex, "total_capital_expenditures_real", "mode_group", "year", 2024
    )

    for metrics in [opex_hhi, opex_pc]:
        df_opex = df_opex.merge(metrics, on=["year", "mode_group"], how="left")
    df_opex = df_opex.merge(opex_vol, on="mode_group", how="left")

    for metrics in [capex_hhi, capex_pc]:
        df_capex = df_capex.merge(metrics, on=["year", "mode_group"], how="left")
    df_capex = df_capex.merge(capex_vol, on="mode_group", how="left")

    df_merged = merge_capex_opex(
        df_capex,
        df_opex,
    )

    df_merged = add_mode_group(df_merged)

    df_merged["capex_per_vrh_real"] = (
        df_merged["total_capital_expenditures_real"]
        / df_merged["vehicle_revenue_hours"]
    )
    df_merged["capex_per_vrm_real"] = (
        df_merged["total_capital_expenditures_real"]
        / df_merged["vehicle_revenue_miles"]
    )
    df_merged["capex_per_upt_real"] = (
        df_merged["total_capital_expenditures_real"]
        / df_merged["unlinked_passenger_trips"]
    )

    return df_capex, df_opex, df_merged


if __name__ == "__main__":
    df_capex, df_opex, df_merged = create_mode_report_data()
    export_to_gcs(df_capex, "mode_report_capex_data", filesystem)
    export_to_gcs(df_opex, "mode_report_opex_data", filesystem)
    export_to_gcs(
        df_merged,
        "mode_report_capex_opex_data",
        filesystem,
    )


def load_processed_data_for_mode_report(
    capex_file="mode_report_capex_data.parquet",
    opex_file="mode_report_opex_data.parquet",
    merged_file="mode_report_capex_opex_data.parquet",
):
    df_capex = pd.read_parquet(
        f"{GCS_FILE_PATH}{capex_file}",
        filesystem=filesystem,
    )

    df_opex = pd.read_parquet(
        f"{GCS_FILE_PATH}{opex_file}",
        filesystem=filesystem,
    )

    df_merged = pd.read_parquet(
        f"{GCS_FILE_PATH}{merged_file}",
        filesystem=filesystem,
    )

    return df_capex, df_opex, df_merged
