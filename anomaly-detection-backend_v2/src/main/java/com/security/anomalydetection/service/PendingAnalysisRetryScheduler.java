package com.security.anomalydetection.service;

import com.security.anomalydetection.entity.AccessLog;
import com.security.anomalydetection.repository.AccessLogRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

import java.util.List;


@Slf4j
@Service
@RequiredArgsConstructor
public class PendingAnalysisRetryScheduler {

    private static final String STATUS_PENDING = "PENDING_ANALYSIS";

    private final AccessLogRepository accessLogRepository;
    private final LogProcessingService logProcessingService;

    @Scheduled(fixedDelayString = "${ai-engine.retry-interval-ms:60000}")
    public void retryPendingLogs() {
        List<AccessLog> pending = accessLogRepository
                .findTop50ByProcessingStatusOrderByTimestampAsc(STATUS_PENDING);

        if (pending.isEmpty()) {
            return;
        }

        log.info("Retrying AI analysis for {} pending access logs", pending.size());
        pending.forEach(logProcessingService::reanalyzeExistingLog);
    }
}
