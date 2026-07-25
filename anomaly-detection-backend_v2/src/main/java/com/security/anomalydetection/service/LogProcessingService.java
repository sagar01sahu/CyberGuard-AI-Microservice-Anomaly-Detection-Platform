package com.security.anomalydetection.service;

import com.security.anomalydetection.client.AiEngineClient;
import com.security.anomalydetection.dto.ai.AiPredictionRequest;
import com.security.anomalydetection.dto.ai.AiPredictionResponse;
import com.security.anomalydetection.dto.incoming.IncomingLogRequest;
import com.security.anomalydetection.entity.AccessLog;
import com.security.anomalydetection.entity.RiskAlert;
import com.security.anomalydetection.exception.AiEngineUnavailableException;
import com.security.anomalydetection.repository.AccessLogRepository;
import com.security.anomalydetection.repository.RiskAlertRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Isolation;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.util.List;

/**
 * Orchestrates the full lifecycle of an incoming access-log event:
 * persist -> pull historical context -> score via the AI engine -> alert.
 *
 * <p><b>Concurrency &amp; isolation notes</b></p>
 * The synthetic data generator pushes logs for many different entities
 * concurrently and at high throughput. Two things matter here:
 *
 * <ol>
 *   <li>{@code Isolation.READ_COMMITTED} (Postgres' default) is enough:
 *       we only ever need to see <i>committed</i> rows when pulling the
 *       "last 5" historical logs for an entity. We deliberately do NOT
 *       need REPEATABLE_READ/SERIALIZABLE guarantees because each
 *       incoming log is independent -- there is no read-modify-write
 *       cycle on a row shared between concurrent requests. READ_COMMITTED
 *       avoids dirty reads while keeping throughput high, since it
 *       doesn't hold long-lived locks across the AI engine round trip.</li>
 *   <li>The AI engine call happens inside the transaction boundary so a
 *       RiskAlert and its parent AccessLog are always committed
 *       atomically. Because that call is blocking network I/O, the DB
 *       connection is held for its duration -- for very high throughput
 *       deployments this should be tuned via (a) a connection pool sized
 *       for the workload and (b) the tight AI-engine timeout configured
 *       in WebClientConfig, so a slow AI engine can never exhaust the
 *       pool.</li>
 * </ol>
 *
 * <p><b>Fallback / rollback</b></p>
 * If the AI engine call fails or times out, the AccessLog write is never
 * lost: it is committed with processingStatus = PENDING_ANALYSIS instead
 * of failing the whole ingestion request, and PendingAnalysisRetryScheduler
 * retries it later.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class LogProcessingService {

    private static final float ALERT_THRESHOLD = 0.85f;
    private static final String STATUS_ANALYZED = "ANALYZED";
    private static final String STATUS_PENDING = "PENDING_ANALYSIS";

    private final AccessLogRepository accessLogRepository;
    private final RiskAlertRepository riskAlertRepository;
    private final AiEngineClient aiEngineClient;
    private final TelemetryService telemetryService;

    /**
     * Main ingestion workflow, invoked by IngestionController for every
     * incoming access log.
     */
    @Transactional(isolation = Isolation.READ_COMMITTED)
    public AccessLog processIncomingLog(IncomingLogRequest request) {

        long startTime = System.currentTimeMillis();

        // Step 1: persist the incoming log FIRST so the event is never
        // lost, even if everything downstream (AI call, alerting) fails.
        AccessLog currentLog = toEntity(request);
        currentLog = accessLogRepository.save(currentLog);

        // Record Microservice 1 -> Microservice 2 packet
        telemetryService.recordPacket(TelemetryService.MicroservicePacket.builder()
                .packetId("INGEST-" + currentLog.getId())
                .sourceService("Microservice 1: Synthetic Log Generator")
                .targetService("Microservice 2: Spring Boot Backend")
                .endpoint("POST /api/v1/logs/ingest")
                .protocol("HTTP/1.1 REST (X-API-Key)")
                .entityId(currentLog.getEntityId())
                .payloadType("Access Log Payload")
                .requestBody(request)
                .responseBody(java.util.Map.of("id", currentLog.getId(), "status", "INGESTED"))
                .status("SUCCESS")
                .latencyMs(System.currentTimeMillis() - startTime)
                .build());

        try {
            runAiAnalysisAndMaybeAlert(currentLog);
            currentLog.setProcessingStatus(STATUS_ANALYZED);
        } catch (AiEngineUnavailableException e) {
            log.error("AI engine unavailable while processing log id={} for entity={}. " +
                            "Marking as pending_analysis for later retry. Reason: {}",
                    currentLog.getId(), currentLog.getEntityId(), e.getMessage());
            currentLog.setProcessingStatus(STATUS_PENDING);
        }

        return accessLogRepository.save(currentLog);
    }

    /**
     * Re-runs AI analysis for an AccessLog that previously failed
     * (PENDING_ANALYSIS). Used by PendingAnalysisRetryScheduler.
     */
    @Transactional(isolation = Isolation.READ_COMMITTED)
    public AccessLog reanalyzeExistingLog(AccessLog existingLog) {
        try {
            runAiAnalysisAndMaybeAlert(existingLog);
            existingLog.setProcessingStatus(STATUS_ANALYZED);
        } catch (AiEngineUnavailableException e) {
            log.warn("Retry still failing for access log id={}: {}", existingLog.getId(), e.getMessage());
        }
        return accessLogRepository.save(existingLog);
    }

    private void runAiAnalysisAndMaybeAlert(AccessLog accessLog) {
        long startTime = System.currentTimeMillis();
        List<AccessLog> historicalLogs = accessLogRepository
                .findTop5ByEntityIdOrderByTimestampDesc(accessLog.getEntityId());
        historicalLogs.removeIf(historyEntry ->
                historyEntry.getId() != null && historyEntry.getId().equals(accessLog.getId()));

        AiPredictionRequest aiRequest = buildAiRequest(accessLog, historicalLogs);
        AiPredictionResponse aiResponse = aiEngineClient.predict(aiRequest);

        long aiLatency = System.currentTimeMillis() - startTime;

        if (aiResponse == null) {
            telemetryService.recordPacket(TelemetryService.MicroservicePacket.builder()
                    .packetId("AI-PREDICT-FAIL-" + accessLog.getId())
                    .sourceService("Microservice 2: Spring Boot Backend")
                    .targetService("Microservice 3: Python HGNN AI Engine")
                    .endpoint("POST /predict")
                    .protocol("HTTP/1.1 JSON REST")
                    .entityId(accessLog.getEntityId())
                    .payloadType("AiPredictionRequest -> NULL")
                    .requestBody(aiRequest)
                    .responseBody("NULL_RESPONSE")
                    .status("FAILED")
                    .latencyMs(aiLatency)
                    .build());
            throw new AiEngineUnavailableException("AI engine returned an empty response", null);
        }

        boolean isAnomaly = aiResponse.getRiskScore() != null && aiResponse.getRiskScore() > ALERT_THRESHOLD;

        // Record Microservice 2 -> Microservice 3 packet
        telemetryService.recordPacket(TelemetryService.MicroservicePacket.builder()
                .packetId("AI-PREDICT-" + accessLog.getId())
                .sourceService("Microservice 2: Spring Boot Backend")
                .targetService("Microservice 3: Python HGNN AI Engine")
                .endpoint("POST /predict")
                .protocol("HTTP/1.1 JSON REST")
                .entityId(accessLog.getEntityId())
                .payloadType("Graph Feature Vector & Historical Baseline")
                .requestBody(aiRequest)
                .responseBody(aiResponse)
                .status(isAnomaly ? "ANOMALY_DETECTED (" + aiResponse.getAnomalyType() + ")" : "NORMAL")
                .latencyMs(aiLatency)
                .build());

        if (isAnomaly) {
            RiskAlert alert = RiskAlert.builder()
                    .entityId(accessLog.getEntityId())
                    .timestamp(accessLog.getTimestamp())
                    .riskScore(aiResponse.getRiskScore())
                    .severity(severityFor(aiResponse.getRiskScore()))
                    .anomalyType(aiResponse.getAnomalyType())
                    .explainabilityFactors(aiResponse.getExplainabilityFactors())
                    .accessLogId(accessLog.getId())
                    .build();
            riskAlertRepository.save(alert);
            log.info("Risk alert created for entity {} with score {}", accessLog.getEntityId(), aiResponse.getRiskScore());
        }
    }

    private String severityFor(float riskScore) {
        if (riskScore >= 0.95f) return "CRITICAL";
        if (riskScore >= 0.85f) return "HIGH";
        if (riskScore >= 0.6f) return "MEDIUM";
        return "LOW";
    }

    private AccessLog toEntity(IncomingLogRequest r) {
        return AccessLog.builder()
                .entityId(r.getEntityId())
                .role(r.getRole()) // ADD THIS LINE
                .authMethod(r.getAuthMethod())
                .authStatus(r.getAuthStatus())
                .timestamp(r.getTimestamp() != null ? r.getTimestamp() : Instant.now())
                .sourceIp(r.getSourceIp())
                .geoLat(r.getGeoLocation() != null ? r.getGeoLocation().getLat() : null)
                .geoLon(r.getGeoLocation() != null ? r.getGeoLocation().getLon() : null)
                .deviceId(r.getDeviceId())
                .osVersion(r.getOsVersion())
                .userAgent(r.getUserAgent())
                .resourceAccessed(r.getResourceAccessed())
                .build();
    }

    private AiPredictionRequest buildAiRequest(AccessLog current, List<AccessLog> historical) {
        AiPredictionRequest.CurrentEvent currentEvent = AiPredictionRequest.CurrentEvent.builder()
                .entityId(current.getEntityId())
                .role(current.getRole())
                .authMethod(current.getAuthMethod())
                .authStatus(current.getAuthStatus())
                .timestamp(current.getTimestamp())
                .sourceIp(current.getSourceIp())
                .geoLat(current.getGeoLat())
                .geoLon(current.getGeoLon())
                .deviceId(current.getDeviceId())
                .osVersion(current.getOsVersion())
                .userAgent(current.getUserAgent())
                .resourceAccessed(current.getResourceAccessed())
                .build();

        List<AiPredictionRequest.HistoricalEvent> historicalEvents = historical.stream()
                .map(h -> AiPredictionRequest.HistoricalEvent.builder()
                        .role(h.getRole())
                        .authMethod(h.getAuthMethod())
                        .authStatus(h.getAuthStatus())
                        .timestamp(h.getTimestamp())
                        .sourceIp(h.getSourceIp())
                        .geoLat(h.getGeoLat())
                        .geoLon(h.getGeoLon())
                        .deviceId(h.getDeviceId())
                        .osVersion(h.getOsVersion())
                        .resourceAccessed(h.getResourceAccessed())
                        .build()) // <--- This .build() is crucial for the compiler
                .toList();

        return AiPredictionRequest.builder()
                .currentEvent(currentEvent)
                .historicalEvents(historicalEvents)
                .build();
    }
}
