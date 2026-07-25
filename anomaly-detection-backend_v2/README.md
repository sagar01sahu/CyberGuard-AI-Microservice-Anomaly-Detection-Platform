# Anomaly Detection Backend — Middle Layer Orchestrator

Spring Boot 3.x / Java 17 backend that ingests synthetic access logs, calls out
to an external Python AI microservice for risk scoring, persists results to
PostgreSQL, and serves alerts to a React dashboard.

## Architecture at a glance

```
Python log generator ──POST /api/v1/logs/ingest (X-API-Key)──▶ IngestionController
                                                                      │
                                                                      ▼
                                                          LogProcessingService
                                                        (save log, pull history,
                                                         call AI engine, alert)
                                                                      │
                                                     ┌────────────────┴────────────────┐
                                                     ▼                                  ▼
                                          PostgreSQL (AccessLog,               Python AI engine
                                             RiskAlert)                        POST /predict
                                                     ▲
                                                     │
React dashboard ──GET /api/v1/alerts/live (Bearer JWT)──▶ DashboardController
```

## Project layout

```
src/main/java/com/security/anomalydetection/
├── AnomalyDetectionApplication.java   Spring Boot entry point
├── entity/          AccessLog, RiskAlert JPA entities
├── repository/      AccessLogRepository, RiskAlertRepository (Spring Data)
├── dto/
│   ├── incoming/    Wire schema from the Python log generator (snake_case)
│   ├── ai/          Request/response DTOs for the AI engine's /predict call
│   └── outgoing/    Wire schema returned to the React dashboard
├── client/          AiEngineClient interface + WebClient-based implementation
├── service/         LogProcessingService (the orchestration brain) +
│                     PendingAnalysisRetryScheduler (retries failed AI calls)
├── security/         JwtService, JwtAuthenticationFilter, ApiKeyAuthFilter
├── config/          SecurityConfig, WebClientConfig
├── controller/       IngestionController, DashboardController, AuthController
└── exception/       AiEngineUnavailableException, GlobalExceptionHandler
```

## Design decisions worth knowing about

- **Two auth schemes, one filter chain.** `POST /api/v1/logs/ingest` is
  guarded by a static `X-API-Key` header (`ApiKeyAuthFilter`) since the
  caller is a trusted machine, not an interactive user. Every other endpoint
  requires a `Bearer` JWT (`JwtAuthenticationFilter`). Both filters no-op on
  paths that aren't theirs via `shouldNotFilter`, so they never conflict.
- **No login endpoint in the original spec.** In production, JWTs for the
  dashboard would come from a real IdP (Okta, Cognito, your own auth
  service, etc.) and `JwtAuthenticationFilter` just verifies them.
  `AuthController#issueDevToken` is a `@Profile("dev")`-only helper so you
  can mint a test token locally (`POST /api/v1/auth/dev-token?subject=me`)
  without standing up a full identity provider. **Do not enable the `dev`
  profile in production.**
- **`AiEngineClient` is an interface.** `LogProcessingService` depends on
  the interface, not `WebClient` directly, so the orchestration logic can
  be unit-tested with a plain Mockito mock instead of a fake HTTP server on
  every test. `AiEngineClientImpl` is the real WebClient-backed
  implementation, covered separately by `AiEngineClientImplTest` using
  OkHttp's `MockWebServer`.
- **Fallback path.** If the AI engine call fails or times out, the
  `AccessLog` row is still committed (never lost) with
  `processing_status = PENDING_ANALYSIS`. `PendingAnalysisRetryScheduler`
  periodically retries those rows (`ai-engine.retry-interval-ms`, default
  60s).
- **Isolation level.** `@Transactional(isolation = Isolation.READ_COMMITTED)`
  is used deliberately, not REPEATABLE_READ/SERIALIZABLE — see the Javadoc
  on `LogProcessingService` for the reasoning.
- **Timeouts.** `WebClientConfig` sets a connect timeout and read/write
  timeouts on the Netty HTTP client so a hanging AI engine can never block
  an ingestion request indefinitely; `AiEngineClientImpl` also bounds
  `.block(...)` with a response timeout.
- **Constant-time API key comparison.** `ApiKeyAuthFilter` uses
  `MessageDigest.isEqual` instead of `String.equals` to avoid leaking
  timing information about the correct key.

## Running locally

Requires Java 17+, Maven, and a running PostgreSQL instance (or override
`spring.datasource.url` to point elsewhere).

```bash
export DB_USERNAME=postgres
export DB_PASSWORD=postgres
export JWT_SECRET=$(openssl rand -base64 48)
export INGEST_API_KEY=$(openssl rand -hex 24)
export AI_ENGINE_BASE_URL=http://localhost:8000   # your Python AI microservice

mvn spring-boot:run                                # add -Dspring-boot.run.profiles=dev
                                                     # to enable the dev-token endpoint
```

### Example requests

```bash
# Ingest a log (from the Python generator)
curl -X POST http://localhost:8080/api/v1/logs/ingest \
  -H "X-API-Key: $INGEST_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
        "entity_id": "user_4589",
        "auth_method": "password",
        "auth_status": "SUCCESS",
        "timestamp": "2026-07-25T08:15:00Z",
        "source_ip": "10.0.0.5",
        "geo_location": { "lat": 37.77, "lon": -122.41 },
        "device_id": "device-1",
        "os_version": "Windows 11",
        "user_agent": "Mozilla/5.0",
        "resource_accessed": "/marketing/budget.pdf"
      }'

# Mint a dev JWT (only if you started the app with the "dev" profile)
TOKEN=$(curl -s -X POST "http://localhost:8080/api/v1/auth/dev-token?subject=analyst" | jq -r .token)

# Fetch live alerts for the dashboard
curl http://localhost:8080/api/v1/alerts/live -H "Authorization: Bearer $TOKEN"
```

## Running the tests

```bash
mvn test
```

The test suite does **not** require a running PostgreSQL instance or a real
AI engine — it uses H2 (in-memory, Postgres compatibility mode) for
persistence and OkHttp's `MockWebServer` to stand in for the Python AI
engine, so it runs entirely offline and deterministically.

| Test class | What it covers |
|---|---|
| `LogProcessingServiceTest` | Full orchestration logic (mocked collaborators): saves-then-scores ordering, alert creation above/below threshold, AI-outage fallback, history exclusion of the just-saved row, retry path. |
| `PendingAnalysisRetrySchedulerTest` | Retry scheduler calls `reanalyzeExistingLog` for every pending row. |
| `JwtServiceTest` | Token round-trip, wrong secret, wrong issuer, expiry. |
| `JwtAuthenticationFilterTest` | Bypass rules, missing/malformed/invalid/valid Bearer tokens. |
| `ApiKeyAuthFilterTest` | Bypass rules, missing/wrong/correct API key. |
| `AiEngineClientImplTest` | Real WebClient wiring against a fake HTTP server: success parsing, 5xx handling, connection failure, unknown-field tolerance. |
| `AccessLogRepositoryTest`, `RiskAlertRepositoryTest` | Custom Spring Data query methods against a real (H2) database. |
| `IngestionControllerTest`, `DashboardControllerTest` | Web-layer slice tests: request mapping, validation, exact JSON schema. |
| `SecurityIntegrationTest` | Full Spring context + real filter chain: confirms each endpoint is actually gated by the right auth scheme. |
| `EndToEndIngestionFlowTest` | Full "whole module" flow: ingest → AI engine (stubbed) → alert persisted → visible on the dashboard, plus the AI-outage fallback path, over the real HTTP + security + database stack. |

## Note on the AI engine contract

This service assumes the Python AI microservice exposes `POST /predict`
accepting the JSON shape built by `LogProcessingService#buildAiRequest` and
responding with:

```json
{
  "risk_score": 0.96,
  "anomaly_type": "Lateral Movement",
  "explainability_factors": ["..."]
}
```

Building that Python service is outside the scope of this sub-problem (the
Java "Middle Layer Orchestrator"), but `AiPredictionRequest`/
`AiPredictionResponse` fully document the expected contract in code.
