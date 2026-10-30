import re

import gcsfs
import geopandas as gpd
import numpy as np
import pandas as pd
import requests
from _utils import GCS_FILE_PATH

filesystem = gcsfs.GCSFileSystem()


######################################### 1. Loading Data #########################################
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


def load_crosswalk():
    filesystem = gcsfs.GCSFileSystem()
    return pd.read_parquet(
        f"{GCS_FILE_PATH}ntd_rtpa_crosswalk.parquet",
        filesystem=filesystem,
    )


######################################### 2. Data Cleaning and Filtering #########################################
def normalize_uza_name(x):
    if pd.isna(x):
        return x

    x = str(x).strip()
    x = re.sub(r"-+", "-", x)
    return x


def subset_california(df):
    return df[df["source_state"] == "CA"].copy()


def load_uza_shapes():
    url = "https://www2.census.gov/geo/tiger/TIGER2024/UAC20/tl_2024_us_uac20.zip"
    return gpd.read_file(url)


######################################### 3. CPI Adjustment and Dollar Conversion #########################################
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


######################################### 4. Aggregation #########################################


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


######################################### 5. Mode Classification and Reconciliation #########################################
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


# def reconcile_modes_for_merge(df_capex, df_opex):
#     """
#     Reconcile mode names for the merged CapEx/OpEx dataset only.

#     Shared modes are kept unchanged.
#     Modes appearing in only one dataset are mapped to "Other".
#     The original mode name is preserved in `original_mode_full_name`.

#     This function does NOT modify the input DataFrames.
#     """

#     capex = df_capex.copy()
#     opex = df_opex.copy()

#     # Preserve original mode names
#     capex["original_mode_full_name"] = capex["mode_full_name"]
#     opex["original_mode_full_name"] = opex["mode_full_name"]

#     # Modes that exist in both datasets
#     shared_modes = set(capex["mode_full_name"].dropna()) & set(
#         opex["mode_full_name"].dropna()
#     )

#     # Dataset-specific modes -> Other
#     capex["mode_full_name"] = capex["mode_full_name"].where(
#         capex["mode_full_name"].isin(shared_modes),
#         "Other",
#     )

#     opex["mode_full_name"] = opex["mode_full_name"].where(
#         opex["mode_full_name"].isin(shared_modes),
#         "Other",
#     )

#     # Recalculate mode groups after reconciliation
#     capex = add_mode_group(capex)
#     opex = add_mode_group(opex)

#     return capex, opex


def merge_capex_opex(df_capex, df_opex):
    """
    Merge CapEx and OpEx at the mode-year level.

    The input DataFrames are copied, so the original independent
    CapEx and OpEx datasets are not modified.

    Aggregates across all agencies and service types.

    Includes service measures needed to calculate CAPEX
    per vehicle revenue hour, mile, and passenger trip.

    Final grain:
        one row per year × mode_full_name
    """
    capex, opex = df_capex.copy(), df_opex.copy()
    keys = ["year", "mode_full_name"]

    capex = capex.groupby(keys, as_index=False)["total_capital_expenditures_real"].sum(
        min_count=1
    )

    opex_cols = [
        "operating_expenses_total_real",
        "vehicle_revenue_hours",
        "vehicle_revenue_miles",
        "unlinked_passenger_trips",
    ]

    opex = opex.groupby(keys, as_index=False)[opex_cols].sum(min_count=1)

    return (
        capex.merge(opex, on=keys, how="outer").sort_values(keys).reset_index(drop=True)
    )


######################################### 6. Spending and additional metrics #########################################
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
    """
    Calculates total spending per capita by mode group and year.

    Expenditure is aggregated across all agencies and service types.
    Population is counted once per agency and year.

    Final grain:
        one row per year × mode_group
    """
    keys = [year_column, group_column]

    spending = df.groupby(keys)[value_column].sum(min_count=1).rename("value")

    population = (
        df.drop_duplicates(["ntd_id", year_column])
        .groupby(keys)[population_column]
        .sum(min_count=1)
        .rename("population")
    )

    grouped = pd.concat([spending, population], axis=1).reset_index()

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


def create_mode_spending_metrics(df_capex, df_opex):

    # OPEX metrics
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

    opex_pc = spending_per_capita(
        df_opex, "operating_expenses_total_real", "uza_population", "mode_group", "year"
    )
    opex_vol = spending_volatility(
        df_opex, "operating_expenses_total_real", "mode_group", "year", 2024
    )

    # CAPEX metrics
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

    capex_pc = spending_per_capita(
        df_capex,
        "total_capital_expenditures_real",
        "uza_population",
        "mode_group",
        "year",
    )
    capex_vol = spending_volatility(
        df_capex, "total_capital_expenditures_real", "mode_group", "year", 2024
    )

    # Merge metrics
    for metrics in [opex_hhi, opex_pc]:
        df_opex = df_opex.merge(metrics, on=["year", "mode_group"], how="left")
    df_opex = df_opex.merge(opex_vol, on="mode_group", how="left")

    for metrics in [capex_hhi, capex_pc]:
        df_capex = df_capex.merge(metrics, on=["year", "mode_group"], how="left")
    df_capex = df_capex.merge(capex_vol, on="mode_group", how="left")

    return df_capex, df_opex


######################################### 7. Efficiency Metrics #########################################


def create_mode_efficiency(df_opex):
    """
    Creates mode-level operating efficiency and cost-effectiveness metrics.

    Aggregates operating expenditures, fare revenue, and service measures
    across all agencies and service types before calculating ratios.

    Includes:
        - OPEX per vehicle revenue hour
        - OPEX per vehicle revenue mile
        - OPEX per unlinked passenger trip
        - Farebox recovery
        - Fare revenue per trip
        - Net subsidy per trip

    Final grain:
        one row per year × mode_full_name
    """
    keys = ["year", "mode_full_name"]

    df = df_opex.copy()

    df = df.groupby(keys, as_index=False).agg(
        operating_expenses_total_real=("operating_expenses_total_real", "sum"),
        fare_revenue_real=("fare_revenue_real", "sum"),
        vehicle_revenue_hours=("vehicle_revenue_hours", "sum"),
        vehicle_revenue_miles=("vehicle_revenue_miles", "sum"),
        unlinked_passenger_trips=("unlinked_passenger_trips", "sum"),
    )

    # Operating cost efficiency
    df["opex_per_vrh"] = (
        df["operating_expenses_total_real"] / df["vehicle_revenue_hours"]
    )

    df["opex_per_vrm"] = (
        df["operating_expenses_total_real"] / df["vehicle_revenue_miles"]
    )

    df["opex_per_upt"] = (
        df["operating_expenses_total_real"] / df["unlinked_passenger_trips"]
    )

    # Cost effectiveness
    df["farebox_recovery"] = (
        df["fare_revenue_real"] / df["operating_expenses_total_real"]
    )

    df["fare_revenue_per_trip"] = (
        df["fare_revenue_real"] / df["unlinked_passenger_trips"]
    )

    df["net_subsidy_per_trip"] = (
        df["operating_expenses_total_real"] - df["fare_revenue_real"]
    ) / df["unlinked_passenger_trips"]

    return df


def create_agency_mode_efficiency(df_opex):
    """
    Creates agency-level operating efficiency and cost-effectiveness metrics.

    Final grain:
        one row per year × ntd_id × mode_full_name
    """

    keys = ["year", "ntd_id", "mode_full_name"]

    df = df_opex.copy()

    # Aggregate agency records by year and mode
    df = df.groupby(keys, as_index=False).agg(
        source_agency=("source_agency", "first"),
        operating_expenses_total_real=("operating_expenses_total_real", "sum"),
        fare_revenue_real=("fare_revenue_real", "sum"),
        vehicle_revenue_hours=("vehicle_revenue_hours", "sum"),
        vehicle_revenue_miles=("vehicle_revenue_miles", "sum"),
        unlinked_passenger_trips=("unlinked_passenger_trips", "sum"),
    )

    # Operating efficiency
    df["opex_per_vrh"] = (
        df["operating_expenses_total_real"] / df["vehicle_revenue_hours"]
    )
    df["opex_per_vrm"] = (
        df["operating_expenses_total_real"] / df["vehicle_revenue_miles"]
    )
    df["opex_per_upt"] = (
        df["operating_expenses_total_real"] / df["unlinked_passenger_trips"]
    )

    # Cost effectiveness
    df["farebox_recovery_ratio"] = (
        df["fare_revenue_real"] / df["operating_expenses_total_real"]
    )
    df["fare_revenue_per_trip"] = (
        df["fare_revenue_real"] / df["unlinked_passenger_trips"]
    )
    df["net_subsidy_per_trip"] = (
        df["operating_expenses_total_real"] - df["fare_revenue_real"]
    ) / df["unlinked_passenger_trips"]

    # Service utilization
    df["trips_per_vrm"] = df["unlinked_passenger_trips"] / df["vehicle_revenue_miles"]
    df["trips_per_vrh"] = df["unlinked_passenger_trips"] / df["vehicle_revenue_hours"]

    # Log-transformed metrics
    df["log_opex_vrm"] = np.log10(df["opex_per_vrm"].where(df["opex_per_vrm"] > 0))
    df["log_trips_vrm"] = np.log10(df["trips_per_vrm"].where(df["trips_per_vrm"] > 0))
    df["log_opex_vrh"] = np.log10(df["opex_per_vrh"].where(df["opex_per_vrh"] > 0))
    df["log_trips_vrh"] = np.log10(df["trips_per_vrh"].where(df["trips_per_vrh"] > 0))

    return df


def add_capex_efficiency(df):
    df["capex_per_vrh_real"] = (
        df["total_capital_expenditures_real"] / df["vehicle_revenue_hours"]
    )
    df["capex_per_vrm_real"] = (
        df["total_capital_expenditures_real"] / df["vehicle_revenue_miles"]
    )
    df["capex_per_upt_real"] = (
        df["total_capital_expenditures_real"] / df["unlinked_passenger_trips"]
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


######################################### 8. Data Export and Report Loading #########################################
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


def load_processed_data_for_mode_report(
    capex_file="mode_report_capex_data.parquet",
    opex_file="mode_report_opex_data.parquet",
    merged_file="mode_report_capex_opex_data.parquet",
    mode_efficiency_file="mode_efficiency_opex_data.parquet",
    agency_mode_efficiency_file="agency_mode_efficiency_data.parquet",
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

    df_mode_efficiency = pd.read_parquet(
        f"{GCS_FILE_PATH}{mode_efficiency_file}",
        filesystem=filesystem,
    )

    df_agency_mode_efficiency = pd.read_parquet(
        f"{GCS_FILE_PATH}{agency_mode_efficiency_file}",
        filesystem=filesystem,
    )

    return df_capex, df_opex, df_merged, df_mode_efficiency, df_agency_mode_efficiency


# ---------------------------------------------------------------------
# Mode report
# ---------------------------------------------------------------------


def create_mode_report_data():

    # Load and prepare data
    df_capex = add_mode_group(subset_california(load_capex()))
    df_opex = add_mode_group(subset_california(load_service_and_opex()))

    df_capex["uza_name"] = df_capex["uza_name"].apply(normalize_uza_name)
    df_opex["primary_uza_name"] = df_opex["primary_uza_name"].apply(normalize_uza_name)

    # Convert to 2024 dollars
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

    # Spending metrics
    df_capex, df_opex = create_mode_spending_metrics(df_capex, df_opex)

    # Efficiency metrics
    df_mode_efficiency = add_mode_group(create_mode_efficiency(df_opex))
    df_agency_mode_efficiency = add_mode_group(create_agency_mode_efficiency(df_opex))

    # Merge CAPEX and OPEX
    df_merged = add_mode_group(merge_capex_opex(df_capex, df_opex))

    # CAPEX per service measure
    df_merged = add_capex_efficiency(df_merged)

    return df_capex, df_opex, df_merged, df_mode_efficiency, df_agency_mode_efficiency


if __name__ == "__main__":
    df_capex, df_opex, df_merged, df_mode_efficiency, df_agency_mode_efficiency = (
        create_mode_report_data()
    )
    export_to_gcs(df_capex, "mode_report_capex_data", filesystem)
    export_to_gcs(df_opex, "mode_report_opex_data", filesystem)
    export_to_gcs(df_merged, "mode_report_capex_opex_data", filesystem)
    export_to_gcs(df_mode_efficiency, "mode_efficiency_opex_data", filesystem)
    export_to_gcs(df_agency_mode_efficiency, "agency_mode_efficiency_data", filesystem)


####################################################################### AGENCY REPORT #######################################################################
def get_agency_profile(df_opex, ntd_id):
    """Return a compact, one-row profile for any NTD agency ID."""
    d = df_opex[df_opex["ntd_id"].astype(str) == str(ntd_id)]
    if d.empty:
        raise ValueError(f"No agency found for ntd_id={ntd_id}")

    r = d.sort_values("year").iloc[-1]
    return pd.DataFrame(
        [
            {
                "Agency": r["source_agency"],
                "NTD ID": r["ntd_id"],
                "Location": f"{r['source_city']}, {r['source_state']}",
                "Reporter Type": r["reporter_type"],
                "UZA Name": r["primary_uza_name"],
                "UZA Population": r["uza_population"],
                "Status": r["agency_status"],
                "Last Reported": r["last_report_year"],
            }
        ]
    )


def merge_rtpa_ntd(df, df_crosswalk):
    return pd.merge(
        df,
        df_crosswalk[
            ["ntd_id_2022", "rtpa_name", "caltrans_district", "county_name", "mpo_name"]
        ],
        left_on="ntd_id",
        right_on="ntd_id_2022",
        how="left",
    )


# Agency report


def create_agency_report_data():
    df_capex = add_mode_group(subset_california(load_capex()))
    df_opex = add_mode_group(subset_california(load_service_and_opex()))
    df_funding = subset_california(load_cap_op_funding())
    df_opex = merge_rtpa_ntd(df_opex, load_crosswalk())
    df_capex = merge_rtpa_ntd(df_capex, load_crosswalk())

    return df_capex, df_opex, df_funding


if __name__ == "__main__":
    df_capex, df_opex, df_funding = create_agency_report_data()
    export_to_gcs(df_capex, "agency_report_capex", filesystem)
    export_to_gcs(df_opex, "agency_report_opex", filesystem)
    export_to_gcs(df_funding, "agency_report_funding", filesystem)


def load_processed_data_for_agency_report(
    capex_file="agency_report_capex.parquet",
    opex_file="agency_report_opex.parquet",
    funding_file="agency_report_funding.parquet",
):
    df_capex = pd.read_parquet(
        f"{GCS_FILE_PATH}{capex_file}",
        filesystem=filesystem,
    )

    df_opex = pd.read_parquet(
        f"{GCS_FILE_PATH}{opex_file}",
        filesystem=filesystem,
    )

    df_funding = pd.read_parquet(
        f"{GCS_FILE_PATH}{funding_file}",
        filesystem=filesystem,
    )

    return df_capex, df_opex, df_funding
