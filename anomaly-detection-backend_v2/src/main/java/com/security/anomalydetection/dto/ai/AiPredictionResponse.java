package com.security.anomalydetection.dto.ai;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.List;

/**
 * Response returned by the AI engine's POST /predict endpoint.
 * Unknown fields are ignored so the AI engine can evolve its response
 * shape without breaking this orchestrator.
 */
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@JsonIgnoreProperties(ignoreUnknown = true)
public class AiPredictionResponse {

    @JsonProperty("risk_score")
    private Float riskScore;

    @JsonProperty("anomaly_type")
    private String anomalyType;

    @JsonProperty("explainability_factors")
    private List<String> explainabilityFactors;
}
