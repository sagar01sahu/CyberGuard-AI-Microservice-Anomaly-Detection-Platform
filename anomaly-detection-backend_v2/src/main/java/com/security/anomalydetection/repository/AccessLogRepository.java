package com.security.anomalydetection.repository;

import com.security.anomalydetection.entity.AccessLog;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface AccessLogRepository extends JpaRepository<AccessLog, Long> {

    /**
     * Historical context lookup used by LogProcessingService to give the
     * AI engine behavioral history for an entity.
     */
    List<AccessLog> findTop5ByEntityIdOrderByTimestampDesc(String entityId);

    /**
     * Used by PendingAnalysisRetryScheduler to find logs whose AI
     * analysis failed and needs to be retried, oldest first.
     */
    List<AccessLog> findTop50ByProcessingStatusOrderByTimestampAsc(String processingStatus);
}
