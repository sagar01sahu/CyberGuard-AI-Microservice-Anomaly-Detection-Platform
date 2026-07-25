package com.security.anomalydetection.client;

import com.security.anomalydetection.dto.ai.AiPredictionRequest;
import com.security.anomalydetection.dto.ai.AiPredictionResponse;
import com.security.anomalydetection.exception.AiEngineUnavailableException;
import okhttp3.mockwebserver.MockResponse;
import okhttp3.mockwebserver.MockWebServer;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.web.reactive.function.client.WebClient;

import java.io.IOException;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

/**
 * Exercises the real WebClient wiring (headers, JSON (de)serialization,
 * error-status handling, connection failures) against a fake HTTP
 * server playing the role of the Python AI engine -- no Spring context
 * needed, so this runs fast.
 */
class AiEngineClientImplTest {

    private MockWebServer mockWebServer;
    private AiEngineClientImpl client;

    @BeforeEach
    void setUp() throws IOException {
        mockWebServer = new MockWebServer();
        mockWebServer.start();

        WebClient webClient = WebClient.builder()
                .baseUrl(mockWebServer.url("/").toString())
                .build();

        client = new AiEngineClientImpl(webClient, 2000);
    }

    @AfterEach
    void tearDown() {
        try {
            mockWebServer.shutdown();
        } catch (IOException ignored) {
            // already shut down by a test that intentionally kills the server
        }
    }

    @Test
    void parsesASuccessfulPredictionResponse() {
        mockWebServer.enqueue(new MockResponse()
                .setResponseCode(200)
                .setHeader("Content-Type", "application/json")
                .setBody("""
                        {"risk_score": 0.87, "anomaly_type": "Impossible Travel", "explainability_factors": ["far apart logins"]}
                        """));

        AiPredictionResponse response = client.predict(AiPredictionRequest.builder().build());

        assertThat(response.getRiskScore()).isEqualTo(0.87f);
        assertThat(response.getAnomalyType()).isEqualTo("Impossible Travel");
        assertThat(response.getExplainabilityFactors()).containsExactly("far apart logins");
    }

    @Test
    void wrapsA5xxResponseInAiEngineUnavailableException() {
        mockWebServer.enqueue(new MockResponse().setResponseCode(503).setBody("service unavailable"));

        assertThatThrownBy(() -> client.predict(AiPredictionRequest.builder().build()))
                .isInstanceOf(AiEngineUnavailableException.class);
    }

    @Test
    void wrapsAConnectionFailureInAiEngineUnavailableException() throws IOException {
        // Shut the server down entirely so the connection is refused.
        mockWebServer.shutdown();

        assertThatThrownBy(() -> client.predict(AiPredictionRequest.builder().build()))
                .isInstanceOf(AiEngineUnavailableException.class);
    }

    @Test
    void ignoresUnknownFieldsInTheAiResponse() {
        mockWebServer.enqueue(new MockResponse()
                .setResponseCode(200)
                .setHeader("Content-Type", "application/json")
                .setBody("""
                        {"risk_score": 0.3, "anomaly_type": "None", "explainability_factors": [], "model_version": "v7"}
                        """));

        AiPredictionResponse response = client.predict(AiPredictionRequest.builder().build());

        assertThat(response.getRiskScore()).isEqualTo(0.3f);
    }
}
