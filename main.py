from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from src.application.input_validation import InputValidationError, validate_sector_constituents
from src.config.constants import CSV_FILE_PATH, LOG_FILE_PATH
from src.infrastructure.csv_loader import CsvFormatError, load_sector_constituents
from src.infrastructure.logging_setup import configure_logging


def run_check_input() -> int:
    logger = logging.getLogger(__name__)

    try:
        rows = load_sector_constituents(CSV_FILE_PATH)
        validate_sector_constituents(rows)
    except (FileNotFoundError, CsvFormatError, InputValidationError) as exc:
        logger.error("입력 검증 실패: %s", exc)
        print("[FAIL] 입력 검증 실패")
        return 1
    except Exception as exc:  # defensive fallback
        logger.error("예상치 못한 오류: %s", exc)
        print("[FAIL] 예상치 못한 오류")
        return 1

    logger.info("입력 검증 성공: 총 %d건", len(rows))
    print("[OK] 입력 검증 성공")
    return 0


def run_build_weekly(start: str, end: str | None, limit_tickers: int | None) -> int:
    logger = logging.getLogger(__name__)

    try:
        rows = load_sector_constituents(CSV_FILE_PATH)
        validate_sector_constituents(rows)
        tickers = [row.ticker for row in rows]
        if limit_tickers:
            tickers = tickers[:limit_tickers]

        from src.infrastructure.krx_fetcher import fetch_close_prices
        from src.packages.weekly_resampler import resample_to_weekly

        logger.info("[build-weekly] tickers=%d start=%s end=%s", len(tickers), start, end or "today")
        daily_close = fetch_close_prices(tickers=tickers, start=start, end=end)
        weekly_close = resample_to_weekly(daily_close)

        output_path = Path("output/data/weekly_close.csv")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        weekly_close.to_csv(output_path, encoding="utf-8-sig")

        logger.info("[build-weekly] saved=%s shape=%s", output_path, weekly_close.shape)
        print(f"[OK] 주간 종가 생성 완료: {output_path}")
        return 0
    except (FileNotFoundError, CsvFormatError, InputValidationError, ValueError) as exc:
        logger.error("주간 종가 생성 실패: %s", exc)
        print("[FAIL] 주간 종가 생성 실패")
        return 1
    except ModuleNotFoundError as exc:
        logger.error("필수 라이브러리 누락: %s", exc)
        print("[FAIL] 필수 라이브러리 누락 (requirements 설치 필요)")
        return 1
    except Exception as exc:  # defensive fallback
        logger.exception("예상치 못한 오류: %s", exc)
        print("[FAIL] 예상치 못한 오류")
        return 1


def run_build_raw_index(start: str, end: str | None, limit_tickers: int | None) -> int:
    logger = logging.getLogger(__name__)

    try:
        rows = load_sector_constituents(CSV_FILE_PATH)
        validate_sector_constituents(rows)
        tickers = [row.ticker for row in rows]
        if limit_tickers:
            tickers = tickers[:limit_tickers]

        from src.infrastructure.krx_fetcher import fetch_close_prices
        from src.packages.weekly_resampler import resample_to_weekly
        from src.domain.raw_index import build_equal_weight_raw_index

        logger.info("[build-raw-index] step=fetch tickers=%d start=%s end=%s", len(tickers), start, end or "today")
        daily_close = fetch_close_prices(tickers=tickers, start=start, end=end)

        logger.info("[build-raw-index] step=resample weekly")
        weekly_close = resample_to_weekly(daily_close)

        logger.info("[build-raw-index] step=raw-index")
        raw_index = build_equal_weight_raw_index(weekly_close)

        output_path = Path("output/data/raw_index.csv")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        raw_index.to_frame(name="RawIndex").to_csv(output_path, encoding="utf-8-sig")

        logger.info("[build-raw-index] saved=%s shape=%s", output_path, raw_index.shape)
        print(f"[OK] RawIndex 생성 완료: {output_path}")
        return 0
    except (FileNotFoundError, CsvFormatError, InputValidationError, ValueError, TypeError) as exc:
        logger.error("RawIndex 생성 실패: %s", exc)
        print("[FAIL] RawIndex 생성 실패")
        return 1
    except ModuleNotFoundError as exc:
        logger.error("필수 라이브러리 누락: %s", exc)
        print("[FAIL] 필수 라이브러리 누락 (requirements 설치 필요)")
        return 1
    except Exception as exc:  # defensive fallback
        logger.exception("예상치 못한 오류: %s", exc)
        print("[FAIL] 예상치 못한 오류")
        return 1


def run_build_index(start: str, end: str | None, limit_tickers: int | None) -> int:
    logger = logging.getLogger(__name__)

    try:
        rows = load_sector_constituents(CSV_FILE_PATH)
        validate_sector_constituents(rows)
        tickers = [row.ticker for row in rows]
        if limit_tickers:
            tickers = tickers[:limit_tickers]

        from src.domain.index_rescaler import build_index_2022, build_index_2025
        from src.domain.raw_index import build_equal_weight_raw_index
        from src.infrastructure.krx_fetcher import fetch_close_prices
        from src.packages.weekly_resampler import resample_to_weekly

        logger.info("[build-index] step=fetch tickers=%d start=%s end=%s", len(tickers), start, end or "today")
        daily_close = fetch_close_prices(tickers=tickers, start=start, end=end)

        logger.info("[build-index] step=resample weekly")
        weekly_close = resample_to_weekly(daily_close)

        logger.info("[build-index] step=raw-index")
        raw_index = build_equal_weight_raw_index(weekly_close)

        logger.info("[build-index] step=index-2022")
        index_2022 = build_index_2022(raw_index)

        logger.info("[build-index] step=index-2025")
        index_2025 = build_index_2025(raw_index)

        out_dir = Path("output/data")
        out_dir.mkdir(parents=True, exist_ok=True)
        index_2022.to_frame(name="Index_2022").to_csv(out_dir / "index_2022.csv", encoding="utf-8-sig")
        index_2025.to_frame(name="Index_2025").to_csv(out_dir / "index_2025.csv", encoding="utf-8-sig")

        logger.info("[build-index] saved=%s", out_dir)
        print("[OK] Index_2022 / Index_2025 생성 완료")
        return 0
    except (FileNotFoundError, CsvFormatError, InputValidationError, ValueError, TypeError, AssertionError) as exc:
        logger.error("Index 생성 실패: %s", exc)
        print("[FAIL] Index 생성 실패")
        return 1
    except ModuleNotFoundError as exc:
        logger.error("필수 라이브러리 누락: %s", exc)
        print("[FAIL] 필수 라이브러리 누락 (requirements 설치 필요)")
        return 1
    except Exception as exc:  # defensive fallback
        logger.exception("예상치 못한 오류: %s", exc)
        print("[FAIL] 예상치 못한 오류")
        return 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="KRX rebuild bootstrap CLI")
    parser.add_argument(
        "--check-input",
        action="store_true",
        help="input/sector_constituents.csv의 형식/제약 조건 검증만 수행",
    )
    parser.add_argument(
        "--build-weekly",
        action="store_true",
        help="CSV 종목 기반 KRX 종가 수집 후 주간 종가로 변환 저장",
    )
    parser.add_argument(
        "--build-raw-index",
        action="store_true",
        help="CSV 종목 기반 주간 종가에서 RawIndex(시작값 1.0) 생성",
    )
    parser.add_argument(
        "--build-index",
        action="store_true",
        help="RawIndex 기반 Index_2022 / Index_2025 생성",
    )
    parser.add_argument("--start", default="2022-01-03", help="조회 시작일(YYYY-MM-DD)")
    parser.add_argument("--end", default=None, help="조회 종료일(YYYY-MM-DD), 기본값=today")
    parser.add_argument(
        "--limit-tickers",
        type=int,
        default=None,
        help="스모크 테스트용 티커 제한 개수(예: 3)",
    )
    return parser.parse_args()


def main() -> int:
    configure_logging(LOG_FILE_PATH)
    args = parse_args()

    if args.check_input:
        return run_check_input()
    if args.build_weekly:
        return run_build_weekly(args.start, args.end, args.limit_tickers)
    if args.build_raw_index:
        return run_build_raw_index(args.start, args.end, args.limit_tickers)
    if args.build_index:
        return run_build_index(args.start, args.end, args.limit_tickers)

    print("지원 옵션: --check-input | --build-weekly | --build-raw-index | --build-index")
    logging.getLogger(__name__).info("기본 실행: 옵션 미지정")
    return 0


if __name__ == "__main__":
    sys.exit(main())
