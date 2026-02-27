"""RawIndex generation based on equal-weight cumulative returns."""

from __future__ import annotations

import logging

import pandas as pd

LOGGER = logging.getLogger(__name__)


def build_equal_weight_raw_index(close_df: pd.DataFrame) -> pd.Series:
    """Build RawIndex from close prices.

    Formula:
    - per-timestamp return per ticker: r_i(t) = P_i(t)/P_i(t-1) - 1
    - equal-weight return: r_eq(t) = mean_i(r_i(t))
    - cumulative raw index: RawIndex(t) = RawIndex(t-1) * (1 + r_eq(t))
    - initial value: RawIndex(t0) = 1.0
    """

    if close_df.empty:
        raise ValueError("close_df is empty")
    if not isinstance(close_df.index, pd.DatetimeIndex):
        raise TypeError("close_df index must be DatetimeIndex")

    aligned = close_df.sort_index().astype("float64")
    LOGGER.info("[raw-index] input shape=%s", aligned.shape)

    returns = aligned.pct_change()
    eq_return = returns.mean(axis=1, skipna=True).fillna(0.0)

    raw_index = (1.0 + eq_return).cumprod()
    raw_index.iloc[0] = 1.0
    raw_index.name = "RawIndex"

    LOGGER.info("[raw-index] generated points=%d start=%s end=%s", len(raw_index), raw_index.index.min(), raw_index.index.max())
    return raw_index
