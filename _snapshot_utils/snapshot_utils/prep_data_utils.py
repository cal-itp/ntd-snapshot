"""
Separate out the utility functions needed for aggregation or visualization.
"""

import gcsfs
import pandas as pd

from snapshot_utils.project_vars import GCS_FILE_PATH


def merge_with_crosswalk(
    ntd_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Merge the NTD df with the RTPA crosswalk on ntd_id.
    """
    crosswalk = pd.read_parquet(
        f"{GCS_FILE_PATH}crosswalk.parquet",
        filesystem=gcsfs.GCSFileSystem(),
        columns=["ntd_id_2022", "rtpa_name", "rtpa_name_split"],
    ).rename(columns={"ntd_id_2022": "ntd_id"})

    df = pd.merge(ntd_df, crosswalk, on="ntd_id", how="left")

    return df


def calculate_upt_change_by_group(
    df: pd.DataFrame,
    group_cols: list,
    sum_cols: list,
    prior_col: str,
) -> pd.DataFrame:
    """ """
    grouped_df = (
        df.groupby(group_cols, dropna=False)
        .agg({**{c: "sum" for c in sum_cols}})
        .reset_index()
    )

    # calculate percent change. Turn decimal (0-1) to number (0-100) for easier display in charts.
    # must make sure that the sorting is intact for monthly or annual (sort by year or month_first_day)
    grouped_df = grouped_df.assign(
        pct_change_1_yr=(grouped_df.upt - grouped_df[prior_col])
        .divide(grouped_df[prior_col])
        .round(4)
        * 100
    )

    return grouped_df


def calculate_efficiency_metrics_by_group(
    df: pd.DataFrame, group_cols: list
) -> pd.DataFrame:
    """
    The columns get renamed several times, try to consolidate this to just once?
    should vrh and vrm be abbreviated (monthly model) or full name (annual model)?
    """
    metric_cols = [
        "unlinked_passenger_trips",
        "vehicle_revenue_miles",
        "vehicle_revenue_hours",
        "operating_expenses_total",
    ]

    # remove rows where we might divide by zero
    df2 = df[
        df[
            [
                "unlinked_passenger_trips",
                "vehicle_revenue_hours",
                "vehicle_revenue_miles",
            ]
        ].sum(axis=1)
        != 0
    ].reset_index(drop=True)

    grouped_df = (
        df2.sort_values(group_cols)
        .groupby(group_cols)
        .agg({c: "sum" for c in metric_cols})
        .reset_index()
    )

    grouped_df = grouped_df.assign(
        opex_per_upt=grouped_df.operating_expenses_total.divide(
            grouped_df.unlinked_passenger_trips
        ).round(2),
        opex_per_vrh=grouped_df.operating_expenses_total.divide(
            grouped_df.vehicle_revenue_hours
        ).round(2),
        opex_per_vrm=grouped_df.operating_expenses_total.divide(
            grouped_df.vehicle_revenue_miles
        ).round(2),
        upt_per_vrh=grouped_df.unlinked_passenger_trips.divide(
            grouped_df.vehicle_revenue_hours
        ).round(2),
        upt_per_vrm=grouped_df.unlinked_passenger_trips.divide(
            grouped_df.vehicle_revenue_miles
        ).round(2),
    )

    return grouped_df


def aggregate_by_agency(
    df: pd.DataFrame, previous_upt_col: str, time_cols: list, geography_cols: list
):
    return (
        calculate_upt_change_by_group(
            df,
            group_cols=["ntd_id", "agency"] + time_cols + geography_cols,
            sum_cols=["upt", previous_upt_col, "upt_change_1yr"],
            prior_col=previous_upt_col,
        )
        .sort_values(["ntd_id"] + time_cols + geography_cols)
        .reset_index(drop=True)
    )


def aggregate_by_mode(
    df: pd.DataFrame, previous_upt_col: str, time_cols: list, geography_cols: list
):
    return (
        calculate_upt_change_by_group(
            df,
            group_cols=["mode", "mode_full_name"] + time_cols + geography_cols,
            sum_cols=["upt", previous_upt_col, "upt_change_1yr"],
            prior_col=previous_upt_col,
        )
        .sort_values(["mode", "mode_full_name"] + time_cols + geography_cols)
        .reset_index(drop=True)
    )


def aggregate_by_tos(
    df: pd.DataFrame, previous_upt_col: str, time_cols: list, geography_cols: list
):
    return (
        calculate_upt_change_by_group(
            df,
            group_cols=["type_of_service", "type_of_service_full_name"]
            + time_cols
            + geography_cols,
            sum_cols=["upt", previous_upt_col, "upt_change_1yr"],
            prior_col=previous_upt_col,
        )
        .sort_values(
            ["type_of_service", "type_of_service_full_name"]
            + time_cols
            + geography_cols
        )
        .reset_index(drop=True)
    )


def aggregate_by_reporter_type(
    df: pd.DataFrame, previous_upt_col: str, time_cols: list, geography_cols: list
):
    return (
        calculate_upt_change_by_group(
            df,
            group_cols=["reporter_type"] + time_cols + geography_cols,
            sum_cols=["upt", previous_upt_col, "upt_change_1yr"],
            prior_col=previous_upt_col,
        )
        .sort_values(["reporter_type"] + time_cols + geography_cols)
        .reset_index(drop=True)
    )


def proportion_of_upt_by_agency(df: pd.DataFrame) -> pd.DataFrame:
    """
    Find the proportion of UPT each agency contributes relative
    to the RTPA total.
    Used in report for sorted bar chart.
    """
    initial_agg = (
        df.groupby("agency")
        .agg(total_upt=("upt", "sum"))
        .reset_index()
        .astype({"total_upt": "int64"})
        .sort_values(by="total_upt", ascending=False)
    )
    # % total columns
    initial_agg["pct_of_total_upt"] = (
        (initial_agg["total_upt"] / initial_agg["total_upt"].sum()) * 100
    ).round(decimals=2)

    return initial_agg
