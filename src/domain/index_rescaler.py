"""Rescaling helpers for 2022/2025 index baselines."""

from __future__ import annotations

import logging

import pandas as pd

LOGGER = logging.getLogger(__name__)


def _normalize_weekly_base(target_date: str) -> pd.Timestamp:
    target_ts = pd.Timestamp(target_date)
    return target_ts.to_period("W-FRI").end_time.normalize()


def resolve_base_date(raw_index: pd.Series, target_date: str) -> str:
    """Resolve actual base date from weekly raw-index timeline.

    Priority:
    1) Weekly anchor date that contains target_date (W-FRI end date).
    2) If missing, nearest previous index date <= target_date.
    """

    if raw_index.empty:
        raise ValueError("raw_index is empty")
    if not isinstance(raw_index.index, pd.DatetimeIndex):
        raise TypeError("raw_index index must be DatetimeIndex")

    index = raw_index.sort_index().index
    weekly_anchor = _normalize_weekly_base(target_date)

    if weekly_anchor in index:
        resolved = weekly_anchor
        LOGGER.info(
            "[index-base] target=%s weekly_anchor=%s resolved=%s reason=weekly-anchor",
            target_date,
            weekly_anchor.date(),
            resolved.date(),
        )
        return resolved.strftime("%Y-%m-%d")

    target_ts = pd.Timestamp(target_date)
    previous = index[index <= target_ts]
    if len(previous) == 0:
        raise ValueError(f"기준일({target_date}) 이전에 사용 가능한 주간 인덱스가 없습니다.")

    resolved = previous[-1]
    LOGGER.info(
        "[index-base] target=%s weekly_anchor=%s resolved=%s reason=fallback-previous",
        target_date,
        weekly_anchor.date(),
        resolved.date(),
    )
    return resolved.strftime("%Y-%m-%d")


def _assert_base_is_1000(index_series: pd.Series, base_date: str) -> None:
    value = float(index_series.loc[pd.Timestamp(base_date)])
    assert abs(value - 1000.0) < 1e-9, f"base_date={base_date} value={value} != 1000"


def build_index_2022(raw_index: pd.Series) -> pd.Series:
    base_date = resolve_base_date(raw_index, "2022-01-03")
    base_value = float(raw_index.loc[pd.Timestamp(base_date)])
    index_2022 = (raw_index / base_value) * 1000.0
    index_2022.name = "Index_2022"
    _assert_base_is_1000(index_2022, base_date)
    LOGGER.info("[index-2022] base_date=%s", base_date)
    return index_2022


def build_index_2025(raw_index: pd.Series) -> pd.Series:
    base_date = resolve_base_date(raw_index, "2025-01-02")
    base_value = float(raw_index.loc[pd.Timestamp(base_date)])
    index_2025 = (raw_index / base_value) * 1000.0
    index_2025.name = "Index_2025"
    _assert_base_is_1000(index_2025, base_date)
    LOGGER.info("[index-2025] base_date=%s", base_date)
    return index_2025
