"""
Merge annual NTD data with RTPA crosswalk.

Aggregate by agency, mode, type of service, reporter_type
and save out parquets.
Filter these parquets in zipped Excel files.
"""

from pathlib import Path

import gcsfs
import pandas as pd
from calitp_portfolio.models import load_site
from calitp_portfolio.mutations import generate_parts_flat
from snapshot_utils import prep_data_utils
from snapshot_utils.project_vars import GCS_FILE_PATH


def generate_yaml(site_path: Path):
    """
    Do RTPAs show up consistently?
    From the last time this report was run,
        the list of RTPAs has changed (so annually, we can see slight shifts).
    """
    site = load_site(site_path)

    rtpa_list = (
        pd.read_parquet(
            f"{GCS_FILE_PATH}annual.parquet",
            filesystem=gcsfs.GCSFileSystem(),
            columns=["ntd_id", "source_agency", "unlinked_passenger_trips"],
        )
        .drop_duplicates()
        .pipe(prep_data_utils.merge_with_crosswalk)
        .dropna(
            subset=[
                "unlinked_passenger_trips",
                "rtpa_name",
            ]  # drop nulls from either column
        )
        .rtpa_name.unique()
        .tolist()
    )

    site = generate_parts_flat(
        site,
        param_key="rtpa",
        values=sorted(rtpa_list),
    )

    site.write_yaml(site_path)

    print(f"yaml generated at {site_path}")

    return


if __name__ == "__main__":
    # set directory as . not ./
    generate_yaml(Path("./ucla_ntd_performance_metrics.yml"))
