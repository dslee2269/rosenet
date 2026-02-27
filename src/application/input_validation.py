"""Input validation use-case for Phase 1."""

from __future__ import annotations

from collections import Counter

from src.config.constants import (
    EXPECTED_SECTOR_COUNT,
    EXPECTED_SECTORS,
    EXPECTED_TICKERS_PER_SECTOR,
)
from src.domain.models import SectorConstituent


class InputValidationError(ValueError):
    """Raised when input constraints are violated."""


def validate_sector_constituents(rows: list[SectorConstituent]) -> None:
    if not rows:
        raise InputValidationError("CSV 데이터가 비어 있습니다.")

    sector_counter = Counter(row.sector for row in rows)
    sectors = set(sector_counter.keys())
    expected_sectors = set(EXPECTED_SECTORS)

    if len(sectors) != EXPECTED_SECTOR_COUNT:
        raise InputValidationError(
            f"섹터 개수 불일치: 기대={EXPECTED_SECTOR_COUNT}, 실제={len(sectors)}"
        )

    if sectors != expected_sectors:
        missing = sorted(expected_sectors - sectors)
        extra = sorted(sectors - expected_sectors)
        raise InputValidationError(
            "섹터 목록 불일치: "
            f"missing={missing if missing else '없음'}, "
            f"extra={extra if extra else '없음'}"
        )

    wrong_sector_counts = {
        sector: count
        for sector, count in sector_counter.items()
        if count != EXPECTED_TICKERS_PER_SECTOR
    }
    if wrong_sector_counts:
        raise InputValidationError(
            "섹터당 종목 수 불일치: "
            + ", ".join(
                f"{sector}={count}(기대 {EXPECTED_TICKERS_PER_SECTOR})"
                for sector, count in sorted(wrong_sector_counts.items())
            )
        )

    ticker_counter = Counter(row.ticker for row in rows)
    duplicated_tickers = sorted([ticker for ticker, count in ticker_counter.items() if count > 1])
    if duplicated_tickers:
        raise InputValidationError(f"중복 Ticker 발견: {duplicated_tickers}")
