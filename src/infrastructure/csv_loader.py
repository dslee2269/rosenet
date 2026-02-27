"""CSV parsing for sector constituents input."""

from __future__ import annotations

import csv
from pathlib import Path

from src.domain.models import SectorConstituent

REQUIRED_COLUMNS = ["Sector", "Ticker", "Name", "Shares(Base)"]


class CsvFormatError(ValueError):
    """Raised when the CSV format is invalid."""


def _normalize_ticker(raw_ticker: str) -> str:
    ticker = raw_ticker.strip()
    if not ticker:
        raise CsvFormatError("Ticker 값이 비어 있습니다.")

    if ticker.isdigit():
        ticker = ticker.zfill(6)

    if len(ticker) != 6:
        raise CsvFormatError(f"Ticker는 6자리여야 합니다: {raw_ticker}")

    return ticker


def _parse_shares_base(raw_shares: str) -> float:
    value = raw_shares.strip().replace(",", "")
    if not value:
        raise CsvFormatError("Shares(Base) 값이 비어 있습니다.")

    try:
        return float(value)
    except ValueError as exc:
        raise CsvFormatError(f"Shares(Base) 숫자 변환 실패: {raw_shares}") from exc


def load_sector_constituents(csv_path: str | Path) -> list[SectorConstituent]:
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"입력 CSV 파일이 없습니다: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as fp:
        reader = csv.DictReader(fp)

        if reader.fieldnames is None:
            raise CsvFormatError("CSV 헤더가 없습니다.")

        missing_columns = [col for col in REQUIRED_COLUMNS if col not in reader.fieldnames]
        if missing_columns:
            raise CsvFormatError(f"필수 컬럼 누락: {', '.join(missing_columns)}")

        rows: list[SectorConstituent] = []
        for row_num, row in enumerate(reader, start=2):
            try:
                constituent = SectorConstituent(
                    sector=row["Sector"].strip(),
                    ticker=_normalize_ticker(str(row["Ticker"])),
                    name=row["Name"].strip(),
                    shares_base=_parse_shares_base(str(row["Shares(Base)"])),
                )
            except KeyError as exc:
                raise CsvFormatError(f"{row_num}행 컬럼 접근 실패: {exc}") from exc
            except CsvFormatError as exc:
                raise CsvFormatError(f"{row_num}행 오류: {exc}") from exc

            if not constituent.sector:
                raise CsvFormatError(f"{row_num}행 오류: Sector 값이 비어 있습니다.")
            if not constituent.name:
                raise CsvFormatError(f"{row_num}행 오류: Name 값이 비어 있습니다.")

            rows.append(constituent)

    return rows
