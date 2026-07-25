package com.security.anomalydetection.repository;

import com.security.anomalydetection.entity.RiskAlert;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.test.context.ActiveProfiles;

import java.time.Instant;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

@DataJpaTest
@ActiveProfiles("test")
class RiskAlertRepositoryTest {

    @Autowired
    private RiskAlertRepository riskAlertRepository;

    @Test
    void returnsTheTwentyMostRecentAlertsNewestFirst() {
        Instant base = Instant.parse("2026-07-25T08:00:00Z");
        for (int i = 0; i < 25; i++) {
            riskAlertRepository.save(RiskAlert.builder()
                    .entityId("user_" + i)
                    .timestamp(base.plusSeconds(i * 60L))
                    .riskScore(0.9f)
                    .severity("HIGH")
                    .anomalyType("Test Anomaly")
                    .explainabilityFactors(List.of("factor 1", "factor 2"))
                    .accessLogId((long) i)
                    .build());
        }

        List<RiskAlert> result = riskAlertRepository.findTop20ByOrderByTimestampDesc();

        assertThat(result).hasSize(20);
        assertThat(result.get(0).getEntityId()).isEqualTo("user_24"); // newest first
        assertThat(result.get(19).getEntityId()).isEqualTo("user_5");
        assertThat(result.get(0).getExplainabilityFactors()).containsExactly("factor 1", "factor 2");
    }

    @Test
    void returnsAnEmptyListWhenThereAreNoAlerts() {
        assertThat(riskAlertRepository.findTop20ByOrderByTimestampDesc()).isEmpty();
    }
}
