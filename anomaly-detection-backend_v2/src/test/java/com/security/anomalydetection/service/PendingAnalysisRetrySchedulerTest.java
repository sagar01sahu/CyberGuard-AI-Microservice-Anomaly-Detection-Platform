package com.security.anomalydetection.service;

import com.security.anomalydetection.entity.AccessLog;
import com.security.anomalydetection.repository.AccessLogRepository;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.time.Instant;
import java.util.List;

import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class PendingAnalysisRetrySchedulerTest {

    @Mock
    private AccessLogRepository accessLogRepository;

    @Mock
    private LogProcessingService logProcessingService;

    @Test
    void reanalyzesEveryPendingLogFound() {
        AccessLog pending1 = AccessLog.builder().id(1L).entityId("user_1")
                .timestamp(Instant.now()).processingStatus("PENDING_ANALYSIS").build();
        AccessLog pending2 = AccessLog.builder().id(2L).entityId("user_2")
                .timestamp(Instant.now()).processingStatus("PENDING_ANALYSIS").build();

        when(accessLogRepository.findTop50ByProcessingStatusOrderByTimestampAsc("PENDING_ANALYSIS"))
                .thenReturn(List.of(pending1, pending2));

        PendingAnalysisRetryScheduler scheduler =
                new PendingAnalysisRetryScheduler(accessLogRepository, logProcessingService);
        scheduler.retryPendingLogs();

        verify(logProcessingService).reanalyzeExistingLog(pending1);
        verify(logProcessingService).reanalyzeExistingLog(pending2);
    }

    @Test
    void doesNothingWhenThereAreNoPendingLogs() {
        when(accessLogRepository.findTop50ByProcessingStatusOrderByTimestampAsc("PENDING_ANALYSIS"))
                .thenReturn(List.of());

        PendingAnalysisRetryScheduler scheduler =
                new PendingAnalysisRetryScheduler(accessLogRepository, logProcessingService);
        scheduler.retryPendingLogs();

        verifyNoInteractions(logProcessingService);
    }
}
