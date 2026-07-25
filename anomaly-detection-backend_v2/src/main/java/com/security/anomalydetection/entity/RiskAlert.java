package com.security.anomalydetection.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.Instant;
import java.util.List;

/**
 * A risk alert raised when the AI engine's risk score for an AccessLog
 * crosses the alerting threshold.
 */
@Entity
@Table(name = "risk_alerts", indexes = {
        @Index(name = "idx_risk_alerts_timestamp", columnList = "timestamp")
})
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class RiskAlert {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long alertId;

    @Column(nullable = false)
    private String entityId;

    @Column(nullable = false)
    private Instant timestamp;

    private Float riskScore;

    private String severity;

    private String anomalyType;

    @ElementCollection(fetch = FetchType.EAGER)
    @CollectionTable(name = "risk_alert_explainability_factors", joinColumns = @JoinColumn(name = "alert_id"))
    @Column(name = "factor", length = 2048)
    @OrderColumn(name = "factor_order")
    private List<String> explainabilityFactors;

    @Column(nullable = false)
    private Long accessLogId;
}
