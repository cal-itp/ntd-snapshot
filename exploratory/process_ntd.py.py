import geopandas as gpd
import pandas as pd
from _utils import GCS_FILE_PATH


def load_service_and_opex():
    return pd.read_parquet(f"{GCS_FILE_PATH}annual_service_and_opex.parquet")

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
        lambda x: ("Bus" 
                   if x in bus_modes
                   else "Rail"
                   if x in rail_modes
                   else "Other"
                  )
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
    uza_shapes = gpd.read_file(url)

    return uza_shapes

