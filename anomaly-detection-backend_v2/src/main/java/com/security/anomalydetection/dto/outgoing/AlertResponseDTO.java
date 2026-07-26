package com.security.anomalydetection.dto.outgoing;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.Instant;
import java.util.List;


@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class AlertResponseDTO {

    @JsonProperty("alert_id")
    private Long alertId;

    @JsonProperty("timestamp")
    private Instant timestamp;

    @JsonProperty("entity_id")
    private String entityId;

    @JsonProperty("risk_score")
    private Float riskScore;

    @JsonProperty("severity")
    private String severity;

    @JsonProperty("anomaly_type")
    private String anomalyType;

    @JsonProperty("explainability_factors")
    private List<String> explainabilityFactors;

    @JsonProperty("source_ip")
    private String sourceIp;

    @JsonProperty("device_id")
    private String deviceId;

    @JsonProperty("resource_accessed")
    private String resourceAccessed;
}
