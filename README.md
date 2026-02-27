# rosenet - Phase 2~3 (EPIC 0~3)

현재 구현 범위는 **기본 스캐폴딩 + 입력 CSV 검증 + KRX 종가 수집/캐시 + 주간 리샘플링 + RawIndex 생성**입니다.

## 포함 범위
- 프로젝트 기본 구조 (`src/`, `input/`, `output/`, `logs/`)
- `main.py` CLI
  - `--check-input`
  - `--build-weekly`
  - `--build-raw-index`
  - `--build-index`
- `input/sector_constituents.csv` 파싱/검증
- KRX 일별 종가 수집 (`pykrx`)
- 티커별 Parquet 캐시 (`data/cache`)
- 주간 종가 리샘플링 (`W-FRI`, 휴장 시 주 마지막 거래일)
- 동일가중 누적 수익률 기반 RawIndex 생성(시작값 1.0)
- Windows 실행 스크립트 (`1_SETUP.cmd`, `2_RUN.cmd`)

## 제외 범위
- 섹터 지수 합성 미구현
- 레짐/점수 계산 미구현
- 엑셀 생성 미구현

## 실행 방법
### Windows
1. `1_SETUP.cmd` 실행
2. `2_RUN.cmd` 실행 (`--check-input` 기본)

### CLI (공통)
입력 검증:
```bash
python main.py --check-input
```

주간 종가 생성:
```bash
python main.py --build-weekly
```

RawIndex 생성:
```bash
python main.py --build-raw-index
```

Index_2022 / Index_2025 생성:
```bash
python main.py --build-index
```

스모크 테스트(티커 3개 제한):
```bash
python main.py --build-index --limit-tickers 3 --start 2024-01-01
```

## 산출물
- 주간 종가 CSV: `output/data/weekly_close.csv`
- RawIndex CSV: `output/data/raw_index.csv`
- Index_2022 CSV: `output/data/index_2022.csv`
- Index_2025 CSV: `output/data/index_2025.csv`
- 티커 캐시: `data/cache/close_{ticker}_{start}_{end|today}.parquet`
- 로그: `logs/app.log`

## RawIndex 계산식
- `r_i(t) = P_i(t)/P_i(t-1) - 1`
- `r_eq(t) = mean_i(r_i(t))`
- `RawIndex(t) = RawIndex(t-1) * (1 + r_eq(t))`
- 초기값: `RawIndex(t0) = 1.0`

## 입력 검증 규칙
- 컬럼: `Sector,Ticker,Name,Shares(Base)`
- 섹터명은 고정 9개 (`src/config/constants.py`)
- 섹터당 6종목
- Ticker 중복 금지
- 위반 시 ERROR 로그 기록 후 종료


## Index 재스케일 기준일 해석
- RawIndex는 주간 인덱스(`W-FRI`)를 사용합니다.
- 기준일은 `resolve_base_date(raw_index, target_date)`로 결정됩니다.
- 우선 target_date가 속한 주의 주간 기준일(금요일)을 찾습니다.
- 해당 주간 기준일이 없으면 target_date 이전의 가장 가까운 주간 인덱스를 fallback으로 사용합니다.
- 선택된 실제 기준일은 로그에 기록됩니다.


## 최소 검증(로컬)
```bash
python -m py_compile main.py src/domain/index_rescaler.py src/domain/raw_index.py src/packages/weekly_resampler.py src/infrastructure/krx_fetcher.py
python -c "import pandas; import numpy"
```


## 빠른 실행 3줄
- 1_SETUP.cmd 실행
- 2_RUN.cmd 실행
- python main.py --build-index
