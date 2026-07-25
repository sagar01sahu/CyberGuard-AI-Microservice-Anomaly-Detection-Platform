package com.security.anomalydetection;

import com.security.anomalydetection.repository.AccessLogRepository;
import com.security.anomalydetection.repository.RiskAlertRepository;
import com.security.anomalydetection.security.JwtService;
import okhttp3.mockwebserver.MockResponse;
import okhttp3.mockwebserver.MockWebServer;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.test.web.servlet.MockMvc;

import java.io.IOException;

import static org.hamcrest.Matchers.hasSize;
import static org.hamcrest.Matchers.is;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/**
 * Full "whole module" integration test: real HTTP layer (MockMvc), real
 * Spring Security filter chain, real JPA/H2 database, and a fake HTTP
 * server standing in for the Python AI engine (MockWebServer) so the
 * complete workflow described in the spec is exercised end-to-end:
 *
 *   ingest (API key) -> LogProcessingService -> AI engine call
 *     -> RiskAlert persisted -> visible on GET /alerts/live (JWT)
 *
 * and the fallback path:
 *
 *   AI engine outage -> AccessLog kept with processing_status = pending_analysis
 */
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.MOCK)
@AutoConfigureMockMvc
@ActiveProfiles("test")
class EndToEndIngestionFlowTest {

    private static MockWebServer mockAiEngine;

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private JwtService jwtService;

    @Autowired
    private AccessLogRepository accessLogRepository;

    @Autowired
    private RiskAlertRepository riskAlertRepository;

    @DynamicPropertySource
    static void aiEngineProps(DynamicPropertyRegistry registry) throws IOException {
        mockAiEngine = new MockWebServer();
        mockAiEngine.start();
        registry.add("ai-engine.base-url", () -> "http://localhost:" + mockAiEngine.getPort());
    }

    @AfterAll
    static void tearDownServer() throws IOException {
        mockAiEngine.shutdown();
    }

    @BeforeEach
    void cleanDb() {
        riskAlertRepository.deleteAll();
        accessLogRepository.deleteAll();
    }

    private static final String INGEST_PAYLOAD_TEMPLATE = """
            {
              "entity_id": "%s",
              "auth_method": "password",
              "auth_status": "SUCCESS",
              "timestamp": "2026-07-25T08:15:00Z",
              "source_ip": "10.0.0.5",
              "geo_location": { "lat": 37.77, "lon": -122.41 },
              "device_id": "device-1",
              "os_version": "Windows 11",
              "user_agent": "Mozilla/5.0",
              "resource_accessed": "%s"
            }
            """;

    @Test
    void highRiskLogEndsUpAsAnAlertOnTheDashboard() throws Exception {
        mockAiEngine.enqueue(new MockResponse()
                .setResponseCode(200)
                .setHeader("Content-Type", "application/json")
                .setBody("""
                        {
                          "risk_score": 0.97,
                          "anomaly_type": "Lateral Movement",
                          "explainability_factors": [
                            "Access to /marketing/budget.pdf was 4 standard deviations from normal."
                          ]
                        }
                        """));

        String payload = INGEST_PAYLOAD_TEMPLATE.formatted("user_4589", "/marketing/budget.pdf");

        mockMvc.perform(post("/api/v1/logs/ingest")
                        .header("X-API-Key", "test-api-key")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(payload))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.processing_status", is("ANALYZED")));

        String token = jwtService.generateToken("test-dashboard-user");

        mockMvc.perform(get("/api/v1/alerts/live")
                        .header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].entity_id", is("user_4589")))
                .andExpect(jsonPath("$[0].severity", is("CRITICAL")))
                .andExpect(jsonPath("$[0].anomaly_type", is("Lateral Movement")))
                .andExpect(jsonPath("$[0].explainability_factors", hasSize(1)));
    }

    @Test
    void lowRiskLogIsStoredButDoesNotCreateAnAlert() throws Exception {
        mockAiEngine.enqueue(new MockResponse()
                .setResponseCode(200)
                .setHeader("Content-Type", "application/json")
                .setBody("{\"risk_score\": 0.2, \"anomaly_type\": \"None\", \"explainability_factors\": []}"));

        String payload = INGEST_PAYLOAD_TEMPLATE.formatted("user_0001", "/home");

        mockMvc.perform(post("/api/v1/logs/ingest")
                        .header("X-API-Key", "test-api-key")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(payload))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.processing_status", is("ANALYZED")));

        String token = jwtService.generateToken("test-dashboard-user");
        mockMvc.perform(get("/api/v1/alerts/live")
                        .header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(0)));
    }

    @Test
    void aiEngineOutageMarksTheLogPendingInsteadOfLosingIt() throws Exception {
        mockAiEngine.enqueue(new MockResponse().setResponseCode(500).setBody("boom"));

        String payload = INGEST_PAYLOAD_TEMPLATE.formatted("user_9999", "/home");

        mockMvc.perform(post("/api/v1/logs/ingest")
                        .header("X-API-Key", "test-api-key")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(payload))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.processing_status", is("PENDING_ANALYSIS")));

        org.assertj.core.api.Assertions.assertThat(accessLogRepository.findAll()).hasSize(1);
        org.assertj.core.api.Assertions.assertThat(riskAlertRepository.findAll()).isEmpty();
    }

    @Test
    void ingestWithoutTheApiKeyNeverReachesTheAiEngineOrTheDatabase() throws Exception {
        String payload = INGEST_PAYLOAD_TEMPLATE.formatted("user_intruder", "/secret");

        mockMvc.perform(post("/api/v1/logs/ingest")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(payload))
                .andExpect(status().isUnauthorized());

        org.assertj.core.api.Assertions.assertThat(accessLogRepository.findAll()).isEmpty();
    }
}
