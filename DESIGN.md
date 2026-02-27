# DESIGN

## 1. 전체 폴더 구조 및 모듈 설계

아래 구조는 **도메인 중심 + 어댑터 분리(Ports & Adapters)** 원칙을 따릅니다.

```text
rosenet/
├─ apps/
│  ├─ api-server/                 # 조회/관리용 HTTP API
│  ├─ realtime-worker/            # 실시간 수집/정규화/발행
│  ├─ batch-worker/               # 장마감 집계/재계산
│  └─ scheduler/                  # 주기 작업 트리거(선택)
│
├─ packages/
│  ├─ domain/                     # 순수 비즈니스 규칙
│  │  ├─ market/
│  │  │  ├─ entities/             # Symbol, Sector, Tick, Candle
│  │  │  ├─ value-objects/        # Price, Volume, Timestamp, MarketCode
│  │  │  ├─ services/             # 집계 규칙, 지표 계산 규칙
│  │  │  └─ events/               # TickReceived, SectorAggregated
│  │  └─ common/
│  │     ├─ errors/
│  │     └─ types/
│  │
│  ├─ application/                # 유스케이스(오케스트레이션)
│  │  ├─ use-cases/
│  │  │  ├─ ingest-realtime-tick/
│  │  │  ├─ aggregate-sector-total/
│  │  │  ├─ recalculate-day-summary/
│  │  │  └─ query-sector-snapshot/
│  │  ├─ ports/
│  │  │  ├─ inbound/              # API/Worker 입력 포트
│  │  │  └─ outbound/             # 저장소/브로커/외부API 출력 포트
│  │  ├─ dto/
│  │  └─ mappers/
│  │
│  ├─ infrastructure/             # 기술 세부 구현체
│  │  ├─ adapters/
│  │  │  ├─ inbound/
│  │  │  │  ├─ http/              # REST handlers
│  │  │  │  ├─ ws/                # websocket consumers
│  │  │  │  └─ jobs/              # cron/queue consumers
│  │  │  └─ outbound/
│  │  │     ├─ persistence/
│  │  │     │  ├─ postgres/
│  │  │     │  └─ redis/
│  │  │     ├─ messaging/
│  │  │     │  ├─ kafka/
│  │  │     │  └─ nats/
│  │  │     └─ external/
│  │  │        └─ krx-gateway/    # KRX 연계 클라이언트
│  │  ├─ config/                  # 환경별 설정 로더
│  │  ├─ observability/           # logging, metrics, tracing
│  │  └─ security/                # authn/authz(필요 시)
│  │
│  ├─ contracts/                  # 스키마/이벤트 계약
│  │  ├─ api/
│  │  ├─ events/
│  │  └─ db/
│  │
│  ├─ shared/                     # 공통 유틸
│  │  ├─ time/
│  │  ├─ math/
│  │  ├─ serialization/
│  │  └─ testkit/
│  │
│  └─ tests/
│     ├─ unit/
│     ├─ integration/
│     └─ e2e/
│
├─ ops/
│  ├─ docker/
│  ├─ k8s/
│  ├─ scripts/
│  └─ dashboards/
│
├─ docs/
│  ├─ architecture/
│  ├─ adr/
│  └─ runbooks/
│
├─ SPEC.md
├─ DESIGN.md
├─ ACCEPTANCE.md
└─ TICKETS.md
```

### 1.1 계층별 책임
- **Domain**: 거래/섹터 집계 규칙의 단일 진실 공급원. 외부 프레임워크 의존 금지.
- **Application**: 유스케이스 단위 트랜잭션 경계, 포트 호출 순서 관리.
- **Infrastructure**: DB/메시지브로커/외부연동 등 기술 구현.
- **Apps**: 실행 엔트리포인트(프로세스/배포 단위).

### 1.2 핵심 모듈 경계
1. `ingest-realtime-tick` 유스케이스
   - 입력: KRX 원천 tick(실시간)
   - 처리: 유효성 검사 → 표준 포맷 정규화 → 이벤트 발행
   - 출력 포트: `TickRepository`, `EventPublisher`

2. `aggregate-sector-total` 유스케이스
   - 입력: 정규화 tick stream
   - 처리: 섹터/업종 기준 실시간 합산, 시장구분별 집계
   - 출력 포트: `SectorAggregateRepository`, `SnapshotCache`

3. `query-sector-snapshot` 유스케이스
   - 입력: API query(시장, 섹터, 시각)
   - 처리: 캐시 우선 조회, 미스 시 저장소 fallback
   - 출력: API DTO

4. `recalculate-day-summary` 유스케이스
   - 입력: 장마감 시점 이벤트/스케줄
   - 처리: 일별 집계 재산출 및 정합성 검증
   - 출력: `DaySummaryRepository`, 감사 로그

### 1.3 의존성 규칙
- 단방향: `apps → infrastructure → application → domain`
- `domain`은 어떤 구현체도 import하지 않음.
- `application`은 `ports` 인터페이스만 참조.
- `infrastructure`에서만 외부 SDK/DB 드라이버 사용.

### 1.4 확장 포인트
- 브로커 교체: `EventPublisher` 포트 구현만 교체(kafka/nats).
- 저장소 교체: `*Repository` 포트 구현만 교체(postgres/redis/other).
- 데이터 소스 추가: `external/*-gateway` 어댑터 신규 추가.

### 1.5 설계 결정(초안)
- 모놀리식 저장소 + 멀티 앱 실행 구조를 기본으로 시작.
- 실시간/배치 워커를 분리해 장애 격리.
- 계약(`contracts`)을 분리해 API/이벤트 스키마 버전 관리.


### 1.6 지수 기준 정의(명확화)
- 전체 계산 기간은 `2022-01-03 ~ today`를 고정으로 유지한다.
- `RawIndex(t)`는 `2022-01-03`부터 전 구간 누적 방식으로 계산한다.
- 2022 기준 지수는 다음과 같이 정의한다.
  - `Index_2022(t) = RawIndex(t) / RawIndex("2022-01-03") * 1000`
- 2025 기준 지수는 다음과 같이 정의한다(단, 계산 구간은 여전히 2022부터 유지).
  - `Index_2025(t) = RawIndex(t) / RawIndex("2025-01-02") * 1000`
- `2025-01-02` 데이터가 없으면, 가장 가까운 **이전 거래일**의 `RawIndex` 값을 기준점으로 사용한다.
