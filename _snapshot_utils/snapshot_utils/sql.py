import os

import pandas as pd

CALITP_BQ_MAX_BYTES = os.environ.get("CALITP_BQ_MAX_BYTES", 5_000_000_000)
CALITP_BQ_LOCATION = os.environ.get("CALITP_BQ_LOCATION", "us-west2")


def to_snakecase(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert DataFrame column names to snakecase.

    Note that this function also strips some non-ascii charactures, such as '"'.
    """

    return df.rename(
        columns=lambda s: s.lower()
        .replace(" ", "_")
        .replace("&", "_")
        .replace("(", "_")
        .replace(")", "_")
        .replace(".", "_")
        .replace("-", "_")
        .replace("/", "_")
        .replace('"', "")
        .replace("'", "")
    ).rename(columns=lambda s: "_%s" % s if s[0].isdigit() else s)
