package com.security.anomalydetection;

import com.security.anomalydetection.security.JwtService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/**
 * Full application context, real security filter chain. Confirms the
 * two authentication schemes described in the spec actually gate the
 * right endpoints:
 *   - POST /api/v1/logs/ingest -> static API key
 *   - GET  /api/v1/alerts/live -> Bearer JWT
 *
 * These requests never reach the AI engine (they're rejected by the
 * filter chain before hitting the controller/service), so no AI engine
 * stub is required here -- see EndToEndIngestionFlowTest for the happy
 * path that does call through to a stubbed AI engine.
 */
@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
class SecurityIntegrationTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private JwtService jwtService;

    @Test
    void ingestWithoutApiKeyIsRejected() throws Exception {
        mockMvc.perform(post("/api/v1/logs/ingest")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{}"))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void ingestWithWrongApiKeyIsRejected() throws Exception {
        mockMvc.perform(post("/api/v1/logs/ingest")
                        .header("X-API-Key", "totally-wrong-key")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{}"))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void dashboardWithoutJwtIsRejected() throws Exception {
        mockMvc.perform(get("/api/v1/alerts/live"))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void dashboardWithAMalformedBearerHeaderIsRejected() throws Exception {
        mockMvc.perform(get("/api/v1/alerts/live")
                        .header("Authorization", "Token something"))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void dashboardWithInvalidJwtIsRejected() throws Exception {
        mockMvc.perform(get("/api/v1/alerts/live")
                        .header("Authorization", "Bearer not-a-real-token"))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void dashboardWithValidJwtIsAccepted() throws Exception {
        String token = jwtService.generateToken("qa-user");
        mockMvc.perform(get("/api/v1/alerts/live")
                        .header("Authorization", "Bearer " + token))
                .andExpect(status().isOk());
    }
}
