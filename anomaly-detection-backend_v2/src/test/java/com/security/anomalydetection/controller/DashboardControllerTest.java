package com.security.anomalydetection.controller;

import com.security.anomalydetection.entity.RiskAlert;
import com.security.anomalydetection.repository.RiskAlertRepository;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.test.web.servlet.MockMvc;

import java.time.Instant;
import java.util.List;

import static org.hamcrest.Matchers.containsString;
import static org.hamcrest.Matchers.hasSize;
import static org.hamcrest.Matchers.is;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/**
 * Verifies GET /api/v1/alerts/live returns the exact JSON schema the
 * React frontend expects, per the spec's payload contract.
 */
@WebMvcTest(controllers = DashboardController.class)
@AutoConfigureMockMvc(addFilters = false)
class DashboardControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private RiskAlertRepository riskAlertRepository;

    @Test
    void returnsAlertsInTheExactSchemaTheFrontendExpects() throws Exception {
        RiskAlert alert = RiskAlert.builder()
                .alertId(1045L)
                .timestamp(Instant.parse("2026-07-25T08:15:00Z"))
                .entityId("user_4589")
                .riskScore(0.96f)
                .severity("CRITICAL")
                .anomalyType("Lateral Movement")
                .explainabilityFactors(List.of(
                        "Access to /marketing/budget.pdf was 4 standard deviations from normal.",
                        "Graph edge probability for this resource is 0.012."))
                .accessLogId(99L)
                .build();

        when(riskAlertRepository.findTop20ByOrderByTimestampDesc()).thenReturn(List.of(alert));

        mockMvc.perform(get("/api/v1/alerts/live"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].alert_id", is(1045)))
                .andExpect(jsonPath("$[0].entity_id", is("user_4589")))
                .andExpect(jsonPath("$[0].risk_score", is(0.96)))
                .andExpect(jsonPath("$[0].severity", is("CRITICAL")))
                .andExpect(jsonPath("$[0].anomaly_type", is("Lateral Movement")))
                .andExpect(jsonPath("$[0].explainability_factors", hasSize(2)))
                .andExpect(jsonPath("$[0].explainability_factors[0]", containsString("4 standard deviations")));
    }

    @Test
    void returnsAnEmptyArrayWhenThereAreNoAlerts() throws Exception {
        when(riskAlertRepository.findTop20ByOrderByTimestampDesc()).thenReturn(List.of());

        mockMvc.perform(get("/api/v1/alerts/live"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(0)));
    }
}
