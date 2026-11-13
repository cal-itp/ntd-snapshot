import re

import gcsfs
import geopandas as gpd
import numpy as np
import pandas as pd
import requests
from _utils import GCS_FILE_PATH

filesystem = gcsfs.GCSFileSystem()


# ============================================================
# 1. LOADING DATA
# ============================================================


def load_service_and_opex():
    return pd.read_parquet(
        f"{GCS_FILE_PATH}annual_service_and_opex.parquet", filesystem=filesystem
    )


def load_cap_op_funding():
    return pd.read_parquet(
        f"{GCS_FILE_PATH}operating_and_capital_funding.parquet", filesystem=filesystem
    )


def load_capex():
    return pd.read_parquet(
        f"{GCS_FILE_PATH}capital_expenditures.parquet", filesystem=filesystem
    )


def load_crosswalk():
    return pd.read_parquet(
        f"{GCS_FILE_PATH}ntd_rtpa_crosswalk.parquet", filesystem=filesystem
    )


# ============================================================
# 2. DATA CLEANING AND FILTERING
# ============================================================


def normalize_uza_name(x):
    if pd.isna(x):
        return x
    x = str(x).strip()
    return re.sub(r"-+", "-", x)


def subset_california(df):
    return df[df["source_state"] == "CA"].copy()


def load_uza_shapes():
    url = "https://www2.census.gov/geo/tiger/TIGER2024/UAC20/tl_2024_us_uac20.zip"
    return gpd.read_file(url)


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

    df = df.copy()
    df["mode_group"] = df["mode_full_name"].map(
        lambda x: "Bus" if x in bus_modes else "Rail" if x in rail_modes else "Other"
    )
    return df


def add_service_type_full_name(df):
    service_mapping = {
        "DO": "Directly Operated",
        "PT": "Purchased Transportation — General",
        "TX": "Purchased Transportation — Taxi",
        "TN": "Purchased Transportation — Transportation Network Company",
    }

    df = df.copy()
    df["type_of_service_full_name"] = df["type_of_service"].map(service_mapping)
    return df


# ============================================================
# 3. CPI ADJUSTMENT
# ============================================================


def get_annual_average_cpi(start_year, end_year):
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
    df = df.merge(cpi_annual, on="year", how="left")

    for col in value_cols:
        df[f"{col}_real"] = (df[col] * base_cpi / df["cpi"]).round(2)

    return df


# ============================================================
# 4. AGGREGATION
# ============================================================


def aggregate_capex_to_agency_year(df):
    agg = {
        "total_capital_expenditures": "sum",
        "rolling_stock_expenditures": "sum",
        "facilities_expenditures": "sum",
        "other_expenditures": "sum",
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

    df_agency = df.groupby(["ntd_id", "year"], as_index=False).agg(agg)

    if df_agency.duplicated(["ntd_id", "year"]).any():
        raise ValueError("Duplicate ntd_id × year combinations remain.")

    return df_agency


def aggregate_opex_to_agency_year(df):
    agg = {
        "operating_expenses_total": "sum",
        "operating_expenses_vehicle_operations": "sum",
        "operating_expenses_vehicle_maintenance": "sum",
        "operating_expenses_nonvehicle_maintenance": "sum",
        "operating_expenses_general_administration": "sum",
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

    df_agency = df.groupby(["ntd_id", "year"], as_index=False).agg(agg)

    if df_agency.duplicated(["ntd_id", "year"]).any():
        raise ValueError("Duplicate ntd_id × year combinations remain.")

    return df_agency


def calculate_shares(df, total_col, source_cols, suffix):
    nonzero = df[total_col] > 0

    for source, category_col in source_cols.items():
        share_col = f"{source}_{suffix}_share"
        df.loc[nonzero, share_col] = (
            df.loc[nonzero, category_col] / df.loc[nonzero, total_col]
        )

    return df


# ============================================================
# 5. CAPEX / OPEX MERGE FOR MODE REPORT
# ============================================================


def merge_capex_opex(df_capex, df_opex):
    keys = ["year", "mode_full_name"]
    capex = df_capex.copy()
    opex = df_opex.copy()

    capex = capex.groupby(keys, as_index=False)["total_capital_expenditures_real"].sum(
        min_count=1
    )

    opex_cols = ["operating_expenses_total_real"]
    opex = opex.groupby(keys, as_index=False)[opex_cols].sum(min_count=1)

    return (
        capex.merge(opex, on=keys, how="outer").sort_values(keys).reset_index(drop=True)
    )


# ============================================================
# 6. SPENDING METRICS
# ============================================================


def create_spending_metrics(
    df,
    component_columns,
    value_column,
    group_columns,
    year_column="year",
    population_column="uza_population",
    population_method="first",
):
    keys = [year_column] + group_columns

    grouped = df.groupby(keys, as_index=False).agg(
        spending=(value_column, lambda x: x.sum(min_count=1)),
        **{col: (col, lambda x: x.sum(min_count=1)) for col in component_columns},
    )

    component_totals = grouped[component_columns].sum(axis=1, min_count=1)
    shares = grouped[component_columns].div(component_totals.replace(0, np.nan), axis=0)
    grouped["hhi"] = shares.pow(2).sum(axis=1, min_count=1)

    # Population and per-capita calculations
    if population_method == "agency_average":
        agency_keys = [year_column, "ntd_id"] + group_columns

        agency_metrics = df.groupby(agency_keys, as_index=False).agg(
            agency_spending=(value_column, lambda x: x.sum(min_count=1)),
            population=(population_column, "first"),
        )

        agency_metrics["agency_per_capita"] = agency_metrics[
            "agency_spending"
        ] / agency_metrics["population"].replace(0, np.nan)

        population = agency_metrics.groupby(keys, as_index=False).agg(
            population=("population", "mean"), per_capita=("agency_per_capita", "mean")
        )

    elif population_method == "unique_uza":
        uza_population = df.dropna(subset=["uace_code"]).drop_duplicates(
            [year_column, "mode_group", "uace_code"]
        )

        population = uza_population.groupby(keys, as_index=False).agg(
            population=(population_column, "sum")
        )

    else:
        population = df.groupby(keys, as_index=False).agg(
            population=(population_column, "first")
        )

    grouped = grouped.merge(population, on=keys, how="left", validate="one_to_one")

    if population_method != "agency_average":
        grouped["per_capita"] = grouped["spending"] / grouped["population"].replace(
            0, np.nan
        )

    grouped = grouped.sort_values(group_columns + [year_column])
    grouped["volatility"] = (
        grouped.groupby(group_columns)["spending"].pct_change().abs()
    )

    return grouped


def create_mode_spending_metrics(df_capex, df_opex):
    configs = [
        (
            df_opex,
            [
                "operating_expenses_vehicle_operations_real",
                "operating_expenses_vehicle_maintenance_real",
                "operating_expenses_nonvehicle_maintenance_real",
                "operating_expenses_general_administration_real",
            ],
            "operating_expenses_total_real",
        ),
        (
            df_capex,
            [
                "rolling_stock_expenditures_real",
                "facilities_expenditures_real",
                "other_expenditures_real",
            ],
            "total_capital_expenditures_real",
        ),
    ]

    metric_columns = ["spending", "hhi", "population", "per_capita", "volatility"]

    results = []

    for df, components, total in configs:
        metrics = create_spending_metrics(
            df, components, total, ["mode_group"], population_method="agency_average"
        )

        metrics = metrics[["year", "mode_group"] + metric_columns]
        df = df.drop(columns=metric_columns, errors="ignore")

        results.append(
            df.merge(
                metrics, on=["year", "mode_group"], how="left", validate="many_to_one"
            )
        )

    return results[1], results[0]


def create_agency_spending_metrics(df_capex, df_opex):
    keys = ["year", "ntd_id", "mode_full_name"]

    configs = [
        (
            df_opex,
            [
                "operating_expenses_vehicle_operations_real",
                "operating_expenses_vehicle_maintenance_real",
                "operating_expenses_nonvehicle_maintenance_real",
                "operating_expenses_general_administration_real",
            ],
            "operating_expenses_total_real",
        ),
        (
            df_capex,
            [
                "rolling_stock_expenditures_real",
                "facilities_expenditures_real",
                "other_expenditures_real",
            ],
            "total_capital_expenditures_real",
        ),
    ]

    metric_columns = ["spending", "hhi", "population", "per_capita", "volatility"]

    results = []

    for df, components, total in configs:
        metrics = create_spending_metrics(
            df,
            components,
            total,
            ["ntd_id", "mode_full_name"],
            population_method="first",
        )

        metrics = metrics[keys + metric_columns]
        df = df.drop(columns=metric_columns, errors="ignore")

        results.append(df.merge(metrics, on=keys, how="left", validate="many_to_one"))

    return results[1], results[0]


# ============================================================
# 7. EFFICIENCY METRICS
# ============================================================


def create_mode_efficiency(df_opex):
    keys = ["year", "mode_full_name"]
    df = df_opex.copy()

    df = df.groupby(keys, as_index=False).agg(
        operating_expenses_total_real=("operating_expenses_total_real", "sum"),
        fare_revenue_real=("fare_revenue_real", "sum"),
        vehicle_revenue_hours=("vehicle_revenue_hours", "sum"),
        vehicle_revenue_miles=("vehicle_revenue_miles", "sum"),
        unlinked_passenger_trips=("unlinked_passenger_trips", "sum"),
    )

    df["opex_per_vrh"] = df["operating_expenses_total_real"] / df[
        "vehicle_revenue_hours"
    ].replace(0, np.nan)
    df["opex_per_vrm"] = df["operating_expenses_total_real"] / df[
        "vehicle_revenue_miles"
    ].replace(0, np.nan)
    df["opex_per_upt"] = df["operating_expenses_total_real"] / df[
        "unlinked_passenger_trips"
    ].replace(0, np.nan)
    df["farebox_recovery"] = df["fare_revenue_real"] / df[
        "operating_expenses_total_real"
    ].replace(0, np.nan)
    df["fare_revenue_per_trip"] = df["fare_revenue_real"] / df[
        "unlinked_passenger_trips"
    ].replace(0, np.nan)
    df["net_subsidy_per_trip"] = (
        df["operating_expenses_total_real"] - df["fare_revenue_real"]
    ) / df["unlinked_passenger_trips"].replace(0, np.nan)

    return df


def create_agency_mode_efficiency(df_opex):
    keys = ["year", "ntd_id", "mode_full_name"]
    df = df_opex.copy()

    df = df.groupby(keys, as_index=False).agg(
        source_agency=("source_agency", "first"),
        operating_expenses_total_real=("operating_expenses_total_real", "sum"),
        fare_revenue_real=("fare_revenue_real", "sum"),
        vehicle_revenue_hours=("vehicle_revenue_hours", "sum"),
        vehicle_revenue_miles=("vehicle_revenue_miles", "sum"),
        unlinked_passenger_trips=("unlinked_passenger_trips", "sum"),
    )

    df["opex_per_vrh"] = df["operating_expenses_total_real"] / df[
        "vehicle_revenue_hours"
    ].replace(0, np.nan)
    df["opex_per_vrm"] = df["operating_expenses_total_real"] / df[
        "vehicle_revenue_miles"
    ].replace(0, np.nan)
    df["opex_per_upt"] = df["operating_expenses_total_real"] / df[
        "unlinked_passenger_trips"
    ].replace(0, np.nan)
    df["farebox_recovery_ratio"] = df["fare_revenue_real"] / df[
        "operating_expenses_total_real"
    ].replace(0, np.nan)
    df["fare_revenue_per_trip"] = df["fare_revenue_real"] / df[
        "unlinked_passenger_trips"
    ].replace(0, np.nan)
    df["net_subsidy_per_trip"] = (
        df["operating_expenses_total_real"] - df["fare_revenue_real"]
    ) / df["unlinked_passenger_trips"].replace(0, np.nan)
    df["trips_per_vrm"] = df["unlinked_passenger_trips"] / df[
        "vehicle_revenue_miles"
    ].replace(0, np.nan)
    df["trips_per_vrh"] = df["unlinked_passenger_trips"] / df[
        "vehicle_revenue_hours"
    ].replace(0, np.nan)

    df["log_opex_vrm"] = np.log10(df["opex_per_vrm"].where(df["opex_per_vrm"] > 0))
    df["log_trips_vrm"] = np.log10(df["trips_per_vrm"].where(df["trips_per_vrm"] > 0))
    df["log_opex_vrh"] = np.log10(df["opex_per_vrh"].where(df["opex_per_vrh"] > 0))
    df["log_trips_vrh"] = np.log10(df["trips_per_vrh"].where(df["trips_per_vrh"] > 0))

    return df


def attach_agency_peer_group(df, df_opex):
    cols = ["ntd_id", "year", "rtpa_name", "reporting_module"]

    modules = df_opex.drop_duplicates(["ntd_id", "year"], keep="last")[cols].copy()
    modules["ntd_id"] = modules["ntd_id"].astype(str)

    df = df.copy()
    df["ntd_id"] = df["ntd_id"].astype(str)
    df = df.merge(modules, on=["ntd_id", "year"], how="left", validate="many_to_one")
    df["peer_group"] = df["reporting_module"]

    return df


def round_tooltip_columns(df):
    columns = [
        "opex_per_vrh",
        "opex_per_vrm",
        "opex_per_upt",
        "upt_per_vrh",
        "upt_per_vrm",
        "farebox_recovery_ratio",
    ]
    existing = [col for col in columns if col in df.columns]
    df[existing] = df[existing].round(2)
    return df


######################################### 8. Data Export and Report Loading #########################################


def export_to_gcs(
    df: pd.DataFrame, filename: str, filesystem: gcsfs.GCSFileSystem, folder: str = ""
) -> None:
    path = f"{GCS_FILE_PATH}{folder}/" if folder else GCS_FILE_PATH
    df.to_parquet(f"{path}{filename}.parquet", filesystem=filesystem)
    print(f"exported {path}{filename}.parquet")


def load_processed_data_for_mode_report(
    capex_file="mode_report_capex_data.parquet",
    opex_file="mode_report_opex_data.parquet",
    merged_file="mode_report_capex_opex_data.parquet",
    mode_efficiency_file="mode_efficiency_opex_data.parquet",
    agency_mode_efficiency_file="agency_mode_efficiency_data.parquet",
):
    folder = f"{GCS_FILE_PATH}mode_report/"
    df_capex = pd.read_parquet(f"{folder}{capex_file}", filesystem=filesystem)
    df_opex = pd.read_parquet(f"{folder}{opex_file}", filesystem=filesystem)
    df_merged = pd.read_parquet(f"{folder}{merged_file}", filesystem=filesystem)
    df_mode_efficiency = pd.read_parquet(
        f"{folder}{mode_efficiency_file}", filesystem=filesystem
    )
    df_agency_mode_efficiency = pd.read_parquet(
        f"{folder}{agency_mode_efficiency_file}", filesystem=filesystem
    )
    return df_capex, df_opex, df_merged, df_mode_efficiency, df_agency_mode_efficiency


def load_processed_data_for_agency_report(
    capex_file="agency_report_capex.parquet",
    opex_file="agency_report_opex.parquet",
    funding_file="agency_report_funding.parquet",
    agency_mode_efficiency_file_opex="agency_mode_efficiency_data_opex.parquet",
    agency_mode_efficiency_file_capex="agency_mode_efficiency_data_capex.parquet",
):
    folder = f"{GCS_FILE_PATH}agency_report/"
    df_capex = pd.read_parquet(f"{folder}{capex_file}", filesystem=filesystem)
    df_opex = pd.read_parquet(f"{folder}{opex_file}", filesystem=filesystem)
    df_funding = pd.read_parquet(f"{folder}{funding_file}", filesystem=filesystem)
    df_agency_mode_efficiency_opex = pd.read_parquet(
        f"{folder}{agency_mode_efficiency_file_opex}", filesystem=filesystem
    )
    df_agency_mode_efficiency_capex = pd.read_parquet(
        f"{folder}{agency_mode_efficiency_file_capex}", filesystem=filesystem
    )
    return (
        df_capex,
        df_opex,
        df_funding,
        df_agency_mode_efficiency_opex,
        df_agency_mode_efficiency_capex,
    )


# ---------------------------------------------------------------------
# Mode report
# ---------------------------------------------------------------------


def create_mode_report_data():
    df_capex = add_mode_group(subset_california(load_capex()))
    df_opex = add_mode_group(
        add_service_type_full_name(subset_california(load_service_and_opex()))
    )
    df_capex["uza_name"] = df_capex["uza_name"].apply(normalize_uza_name)
    df_opex["primary_uza_name"] = df_opex["primary_uza_name"].apply(normalize_uza_name)

    cpi_annual = pd.read_csv(f"{GCS_FILE_PATH}cpi_annual.csv")
    cpi_annual["year"] = pd.to_numeric(cpi_annual["year"])
    cpi_annual["cpi"] = pd.to_numeric(cpi_annual["cpi"])
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

    df_capex, df_opex = create_mode_spending_metrics(df_capex, df_opex)
    df_mode_efficiency = add_mode_group(create_mode_efficiency(df_opex))
    df_agency_mode_efficiency = add_mode_group(create_agency_mode_efficiency(df_opex))
    df_merged = add_mode_group(merge_capex_opex(df_capex, df_opex))

    return df_capex, df_opex, df_merged, df_mode_efficiency, df_agency_mode_efficiency


# ---------------------------------------------------------------------
# Agency report
# ---------------------------------------------------------------------


def get_agency_profile(df_opex, ntd_id):
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


def create_agency_report_data():
    df_capex = add_mode_group(subset_california(load_capex()))
    df_opex = add_mode_group(
        add_service_type_full_name(subset_california(load_service_and_opex()))
    )
    df_funding = subset_california(load_cap_op_funding())

    df_opex = merge_rtpa_ntd(df_opex, load_crosswalk())
    df_capex = merge_rtpa_ntd(df_capex, load_crosswalk())
    df_funding = merge_rtpa_ntd(df_funding, load_crosswalk())

    cpi_annual = pd.read_csv(f"{GCS_FILE_PATH}cpi_annual.csv")
    cpi_annual["year"] = pd.to_numeric(cpi_annual["year"])
    cpi_annual["cpi"] = pd.to_numeric(cpi_annual["cpi"])
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

    df_capex, df_opex = create_agency_spending_metrics(df_capex, df_opex)

    df_agency_mode_efficiency_opex = attach_agency_peer_group(
        add_mode_group(create_agency_mode_efficiency(df_opex)), df_opex
    )

    # Capital efficiency is not calculated here because the CapEx dataset does not contain service measures.
    keys = ["year", "ntd_id", "mode_full_name"]
    df_agency_mode_efficiency_capex = df_capex.groupby(keys, as_index=False).agg(
        source_agency=("source_agency", "first"),
        total_capital_expenditures_real=("total_capital_expenditures_real", "sum"),
    )
    df_agency_mode_efficiency_capex = add_mode_group(df_agency_mode_efficiency_capex)
    df_agency_mode_efficiency_capex = attach_agency_peer_group(
        df_agency_mode_efficiency_capex, df_opex
    )

    return (
        df_capex,
        df_opex,
        df_funding,
        df_agency_mode_efficiency_opex,
        df_agency_mode_efficiency_capex,
    )


# ---------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------

if __name__ == "__main__":
    df_capex, df_opex, df_merged, df_mode_efficiency, df_agency_mode_efficiency = (
        create_mode_report_data()
    )
    export_to_gcs(df_capex, "mode_report_capex_data", filesystem, folder="mode_report")
    export_to_gcs(df_opex, "mode_report_opex_data", filesystem, folder="mode_report")
    export_to_gcs(
        df_merged, "mode_report_capex_opex_data", filesystem, folder="mode_report"
    )
    export_to_gcs(
        df_mode_efficiency,
        "mode_efficiency_opex_data",
        filesystem,
        folder="mode_report",
    )
    export_to_gcs(
        df_agency_mode_efficiency,
        "agency_mode_efficiency_data",
        filesystem,
        folder="mode_report",
    )

    (
        df_capex,
        df_opex,
        df_funding,
        df_agency_mode_efficiency_opex,
        df_agency_mode_efficiency_capex,
    ) = create_agency_report_data()
    export_to_gcs(df_capex, "agency_report_capex", filesystem, folder="agency_report")
    export_to_gcs(df_opex, "agency_report_opex", filesystem, folder="agency_report")
    export_to_gcs(
        df_funding, "agency_report_funding", filesystem, folder="agency_report"
    )
    export_to_gcs(
        df_agency_mode_efficiency_opex,
        "agency_mode_efficiency_data_opex",
        filesystem,
        folder="agency_report",
    )
    export_to_gcs(
        df_agency_mode_efficiency_capex,
        "agency_mode_efficiency_data_capex",
        filesystem,
        folder="agency_report",
    )
