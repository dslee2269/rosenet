"""KRX close price fetcher with parquet cache support."""

from __future__ import annotations

import logging
from datetime import date
from pathlib import Path

import pandas as pd
from pykrx import stock

LOGGER = logging.getLogger(__name__)
CACHE_DIR = Path("data/cache")
DEFAULT_START = "2022-01-03"


def _today_str() -> str:
    return date.today().strftime("%Y-%m-%d")


def _to_krx_date(dt_str: str) -> str:
    return dt_str.replace("-", "")


def _cache_suffix(end: str | None) -> str:
    if end is None:
        return "today"
    return end


def _cache_file_path(ticker: str, start: str, end: str | None) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    suffix = _cache_suffix(end)
    return CACHE_DIR / f"close_{ticker}_{start}_{suffix}.parquet"


def _fetch_single_ticker(ticker: str, start: str, end: str) -> pd.Series:
    LOGGER.info("[fetch] ticker=%s start=%s end=%s", ticker, start, end)
    ohlcv = stock.get_market_ohlcv_by_date(_to_krx_date(start), _to_krx_date(end), ticker)
    if ohlcv.empty:
        return pd.Series(dtype="float64", name=ticker)

    close_series = ohlcv["종가"].astype("float64")
    close_series.index = pd.to_datetime(close_series.index)
    close_series.name = ticker
    return close_series


def _load_or_build_ticker_cache(ticker: str, start: str, end: str | None) -> pd.Series:
    resolved_end = _today_str() if end is None else end
    cache_path = _cache_file_path(ticker, start, end)

    if cache_path.exists():
        LOGGER.info("[cache-hit] %s", cache_path)
        cached = pd.read_parquet(cache_path)
        series = cached[ticker].astype("float64")
        series.index = pd.to_datetime(series.index)

        if end is None and not series.empty:
            last_cached_date = series.index.max().date().strftime("%Y-%m-%d")
            if last_cached_date < resolved_end:
                next_start = (
                    pd.Timestamp(last_cached_date) + pd.Timedelta(days=1)
                ).strftime("%Y-%m-%d")
                LOGGER.info(
                    "[cache-update] ticker=%s cached_end=%s new_end=%s",
                    ticker,
                    last_cached_date,
                    resolved_end,
                )
                appended = _fetch_single_ticker(ticker, next_start, resolved_end)
                if not appended.empty:
                    series = pd.concat([series, appended]).sort_index().drop_duplicates()
                    series.to_frame(name=ticker).to_parquet(cache_path)
                    LOGGER.info("[cache-write] %s (updated)", cache_path)
        return series

    series = _fetch_single_ticker(ticker, start, resolved_end)
    series.to_frame(name=ticker).to_parquet(cache_path)
    LOGGER.info("[cache-write] %s", cache_path)
    return series


def fetch_close_prices(
    tickers: list[str],
    start: str = DEFAULT_START,
    end: str | None = None,
) -> pd.DataFrame:
    """Fetch KRX close prices.

    Returns DataFrame with datetime index and ticker columns.
    """

    if not tickers:
        raise ValueError("tickers cannot be empty")

    unique_tickers = list(dict.fromkeys(tickers))
    series_list: list[pd.Series] = []

    for ticker in unique_tickers:
        series = _load_or_build_ticker_cache(ticker, start, end)
        series_list.append(series)

    prices = pd.concat(series_list, axis=1).sort_index()
    prices = prices.reindex(sorted(prices.columns), axis=1)

    LOGGER.info("[align] shape(before_ffill)=%s", prices.shape)
    prices = prices.ffill()

    nan_count = int(prices.isna().sum().sum())
    if nan_count > 0:
        LOGGER.warning("[missing] ffill 이후 NaN 잔존: %d", nan_count)
    else:
        LOGGER.info("[missing] ffill 이후 NaN 없음")

    return prices
