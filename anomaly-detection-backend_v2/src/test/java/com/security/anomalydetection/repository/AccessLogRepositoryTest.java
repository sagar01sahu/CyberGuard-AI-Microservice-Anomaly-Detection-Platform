package com.security.anomalydetection.repository;

import com.security.anomalydetection.entity.AccessLog;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.test.context.ActiveProfiles;

import java.time.Instant;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

@DataJpaTest
@ActiveProfiles("test")
class AccessLogRepositoryTest {

    @Autowired
    private AccessLogRepository accessLogRepository;

    @Test
    void findsTheFiveMostRecentLogsForAnEntityInDescendingOrder() {
        Instant base = Instant.parse("2026-07-25T08:00:00Z");
        for (int i = 0; i < 8; i++) {
            accessLogRepository.save(AccessLog.builder()
                    .entityId("user_1")
                    .authMethod("password")
                    .authStatus("SUCCESS")
                    .timestamp(base.plusSeconds(i * 60L))
                    .sourceIp("10.0.0." + i)
                    .resourceAccessed("/resource" + i)
                    .build());
        }
        // A log for a different entity should never leak into user_1's history.
        accessLogRepository.save(AccessLog.builder()
                .entityId("user_2")
                .timestamp(base.plusSeconds(999))
                .build());

        List<AccessLog> result = accessLogRepository.findTop5ByEntityIdOrderByTimestampDesc("user_1");

        assertThat(result).hasSize(5);
        assertThat(result).allMatch(entry -> entry.getEntityId().equals("user_1"));
        assertThat(result.get(0).getResourceAccessed()).isEqualTo("/resource7"); // most recent first
        assertThat(result.get(4).getResourceAccessed()).isEqualTo("/resource3");
    }

    @Test
    void returnsAnEmptyListWhenTheEntityHasNoHistory() {
        List<AccessLog> result = accessLogRepository.findTop5ByEntityIdOrderByTimestampDesc("nobody");
        assertThat(result).isEmpty();
    }

    @Test
    void findsPendingAnalysisLogsOldestFirst() {
        Instant base = Instant.parse("2026-07-25T08:00:00Z");
        accessLogRepository.save(AccessLog.builder()
                .entityId("user_1").timestamp(base).processingStatus("PENDING_ANALYSIS").build());
        accessLogRepository.save(AccessLog.builder()
                .entityId("user_1").timestamp(base.plusSeconds(60)).processingStatus("PENDING_ANALYSIS").build());
        accessLogRepository.save(AccessLog.builder()
                .entityId("user_1").timestamp(base.plusSeconds(120)).processingStatus("ANALYZED").build());

        List<AccessLog> pending = accessLogRepository
                .findTop50ByProcessingStatusOrderByTimestampAsc("PENDING_ANALYSIS");

        assertThat(pending).hasSize(2);
        assertThat(pending.get(0).getTimestamp()).isEqualTo(base);
    }

    @Test
    void defaultsProcessingStatusToAnalyzedWhenNotExplicitlySet() {
        AccessLog saved = accessLogRepository.save(AccessLog.builder()
                .entityId("user_5")
                .timestamp(Instant.now())
                .build());

        assertThat(saved.getProcessingStatus()).isEqualTo("ANALYZED");
    }
}
