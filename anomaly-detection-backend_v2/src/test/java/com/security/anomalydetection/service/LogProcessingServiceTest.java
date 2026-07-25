package com.security.anomalydetection.service;

import com.security.anomalydetection.client.AiEngineClient;
import com.security.anomalydetection.dto.ai.AiPredictionResponse;
import com.security.anomalydetection.dto.incoming.GeoLocationDTO;
import com.security.anomalydetection.dto.incoming.IncomingLogRequest;
import com.security.anomalydetection.entity.AccessLog;
import com.security.anomalydetection.entity.RiskAlert;
import com.security.anomalydetection.exception.AiEngineUnavailableException;
import com.security.anomalydetection.repository.AccessLogRepository;
import com.security.anomalydetection.repository.RiskAlertRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.time.Instant;
import java.util.Collections;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

/**
 * Pure unit tests for the orchestration brain of the backend. All
 * collaborators are mocked so these tests run in milliseconds and
 * exercise every branch of processIncomingLog / reanalyzeExistingLog.
 */
@ExtendWith(MockitoExtension.class)
class LogProcessingServiceTest {

    @Mock
    private AccessLogRepository accessLogRepository;

    @Mock
    private RiskAlertRepository riskAlertRepository;

    @Mock
    private AiEngineClient aiEngineClient;

    private LogProcessingService service;

    @BeforeEach
    void setUp() {
        service = new LogProcessingService(accessLogRepository, riskAlertRepository, aiEngineClient);
    }

    private IncomingLogRequest sampleRequest() {
        IncomingLogRequest request = new IncomingLogRequest();
        request.setEntityId("user_123");
        request.setAuthMethod("password");
        request.setAuthStatus("SUCCESS");
        request.setTimestamp(Instant.parse("2026-07-25T08:15:00Z"));
        request.setSourceIp("10.0.0.1");
        request.setGeoLocation(new GeoLocationDTO(37.77, -122.41));
        request.setDeviceId("device-1");
        request.setOsVersion("Windows 11");
        request.setUserAgent("Mozilla/5.0");
        request.setResourceAccessed("/finance/report.pdf");
        return request;
    }

    @Test
    void savesAccessLogAndCallsTheAiEngine() {
        AccessLog saved = AccessLog.builder().id(1L).entityId("user_123").build();
        when(accessLogRepository.save(any(AccessLog.class))).thenReturn(saved);
        when(accessLogRepository.findTop5ByEntityIdOrderByTimestampDesc("user_123"))
                .thenReturn(Collections.emptyList());
        when(aiEngineClient.predict(any())).thenReturn(new AiPredictionResponse(0.1f, "None", List.of()));

        AccessLog result = service.processIncomingLog(sampleRequest());

        assertThat(result.getProcessingStatus()).isEqualTo("ANALYZED");
        verify(accessLogRepository, atLeast(2)).save(any(AccessLog.class));
        verify(aiEngineClient).predict(any());
    }

    @Test
    void createsAlertWhenRiskScoreExceedsThreshold() {
        AccessLog saved = AccessLog.builder().id(1L).entityId("user_123")
                .timestamp(Instant.parse("2026-07-25T08:15:00Z")).build();
        when(accessLogRepository.save(any(AccessLog.class))).thenReturn(saved);
        when(accessLogRepository.findTop5ByEntityIdOrderByTimestampDesc("user_123"))
                .thenReturn(Collections.emptyList());
        when(aiEngineClient.predict(any())).thenReturn(
                new AiPredictionResponse(0.96f, "Lateral Movement", List.of("factor A")));

        service.processIncomingLog(sampleRequest());

        ArgumentCaptor<RiskAlert> captor = ArgumentCaptor.forClass(RiskAlert.class);
        verify(riskAlertRepository).save(captor.capture());

        assertThat(captor.getValue().getSeverity()).isEqualTo("CRITICAL");
        assertThat(captor.getValue().getAnomalyType()).isEqualTo("Lateral Movement");
        assertThat(captor.getValue().getAccessLogId()).isEqualTo(1L);
        assertThat(captor.getValue().getRiskScore()).isEqualTo(0.96f);
    }

    @Test
    void doesNotCreateAlertWhenRiskScoreIsAtOrBelowThreshold() {
        AccessLog saved = AccessLog.builder().id(2L).entityId("user_123")
                .timestamp(Instant.now()).build();
        when(accessLogRepository.save(any(AccessLog.class))).thenReturn(saved);
        when(accessLogRepository.findTop5ByEntityIdOrderByTimestampDesc("user_123"))
                .thenReturn(Collections.emptyList());
        when(aiEngineClient.predict(any())).thenReturn(new AiPredictionResponse(0.85f, "None", List.of()));

        service.processIncomingLog(sampleRequest());

        verify(riskAlertRepository, never()).save(any());
    }

    @Test
    void marksLogAsPendingAnalysisWhenAiEngineFailsButNeverLosesTheLog() {
        AccessLog saved = AccessLog.builder().id(3L).entityId("user_123")
                .timestamp(Instant.now()).processingStatus("ANALYZED").build();
        when(accessLogRepository.save(any(AccessLog.class))).thenReturn(saved);
        when(accessLogRepository.findTop5ByEntityIdOrderByTimestampDesc("user_123"))
                .thenReturn(Collections.emptyList());
        when(aiEngineClient.predict(any())).thenThrow(new AiEngineUnavailableException("timeout", null));

        AccessLog result = service.processIncomingLog(sampleRequest());

        assertThat(result.getProcessingStatus()).isEqualTo("PENDING_ANALYSIS");
        verify(riskAlertRepository, never()).save(any());
        // The original write is never lost -- save() is still called on
        // both the initial persist and the final status update.
        verify(accessLogRepository, atLeast(2)).save(any(AccessLog.class));
    }

    @Test
    void excludesTheJustSavedLogFromItsOwnHistoricalContext() {
        AccessLog saved = AccessLog.builder().id(5L).entityId("user_123").timestamp(Instant.now()).build();
        AccessLog olderLog = AccessLog.builder().id(4L).entityId("user_123")
                .timestamp(Instant.now().minusSeconds(60)).build();

        when(accessLogRepository.save(any(AccessLog.class))).thenReturn(saved);
        // The repository query naturally includes the row just committed
        // within the same transaction.
        when(accessLogRepository.findTop5ByEntityIdOrderByTimestampDesc("user_123"))
                .thenReturn(List.of(saved, olderLog));
        when(aiEngineClient.predict(any())).thenReturn(new AiPredictionResponse(0.1f, "None", List.of()));

        service.processIncomingLog(sampleRequest());

        verify(aiEngineClient).predict(argThat(req -> req.getHistoricalEvents().size() == 1));
    }

    @Test
    void reanalyzeExistingLogFlipsStatusBackToAnalyzedOnSuccess() {
        AccessLog pending = AccessLog.builder().id(9L).entityId("user_9")
                .timestamp(Instant.now()).processingStatus("PENDING_ANALYSIS").build();

        when(accessLogRepository.findTop5ByEntityIdOrderByTimestampDesc("user_9"))
                .thenReturn(Collections.emptyList());
        when(aiEngineClient.predict(any())).thenReturn(new AiPredictionResponse(0.2f, "None", List.of()));
        when(accessLogRepository.save(any(AccessLog.class))).thenReturn(pending);

        AccessLog result = service.reanalyzeExistingLog(pending);

        assertThat(result.getProcessingStatus()).isEqualTo("ANALYZED");
    }

    @Test
    void reanalyzeExistingLogStaysPendingIfTheRetryAlsoFails() {
        AccessLog pending = AccessLog.builder().id(9L).entityId("user_9")
                .timestamp(Instant.now()).processingStatus("PENDING_ANALYSIS").build();

        when(accessLogRepository.findTop5ByEntityIdOrderByTimestampDesc("user_9"))
                .thenReturn(Collections.emptyList());
        when(aiEngineClient.predict(any())).thenThrow(new AiEngineUnavailableException("still down", null));
        when(accessLogRepository.save(any(AccessLog.class))).thenReturn(pending);

        AccessLog result = service.reanalyzeExistingLog(pending);

        assertThat(result.getProcessingStatus()).isEqualTo("PENDING_ANALYSIS");
    }
}
