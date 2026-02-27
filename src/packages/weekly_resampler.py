"""Weekly resampling helpers."""

from __future__ import annotations

import pandas as pd


def resample_to_weekly(df: pd.DataFrame) -> pd.DataFrame:
    """Resample daily close prices to weekly close.

    Rule:
    - Friday anchored week (`W-FRI`)
    - If Friday is holiday/no trading day, use last available trading day in that week.
    """

    if df.empty:
        return df.copy()

    if not isinstance(df.index, pd.DatetimeIndex):
        raise TypeError("DataFrame index must be DatetimeIndex")

    weekly = df.sort_index().resample("W-FRI").last()
    return weekly.dropna(how="all")
