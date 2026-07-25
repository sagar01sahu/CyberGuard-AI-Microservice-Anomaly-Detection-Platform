package com.security.anomalydetection.controller;

import com.security.anomalydetection.entity.AccessLog;
import com.security.anomalydetection.service.LogProcessingService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import static org.hamcrest.Matchers.is;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/**
 * Web-layer slice test: verifies request mapping, JSON (de)serialization,
 * and bean validation for the ingestion endpoint. Security filters are
 * disabled here (covered separately by SecurityIntegrationTest) so this
 * stays focused purely on controller behavior.
 */
@WebMvcTest(controllers = IngestionController.class)
@AutoConfigureMockMvc(addFilters = false)
class IngestionControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private LogProcessingService logProcessingService;

    @Test
    void validPayloadIsAcceptedAndReturnsTheProcessingStatus() throws Exception {
        AccessLog persisted = AccessLog.builder()
                .id(10L)
                .entityId("user_1")
                .processingStatus("ANALYZED")
                .build();
        when(logProcessingService.processIncomingLog(any())).thenReturn(persisted);

        String payload = """
                {
                  "entity_id": "user_1",
                  "auth_method": "password",
                  "auth_status": "SUCCESS",
                  "timestamp": "2026-07-25T08:15:00Z",
                  "source_ip": "10.0.0.5",
                  "geo_location": { "lat": 1.0, "lon": 2.0 },
                  "device_id": "device-1",
                  "os_version": "Windows 11",
                  "user_agent": "Mozilla/5.0",
                  "resource_accessed": "/home"
                }
                """;

        mockMvc.perform(post("/api/v1/logs/ingest")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(payload))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.id", is(10)))
                .andExpect(jsonPath("$.processing_status", is("ANALYZED")));
    }

    @Test
    void missingEntityIdIsRejectedWithBadRequest() throws Exception {
        String payload = """
                {
                  "auth_method": "password",
                  "timestamp": "2026-07-25T08:15:00Z",
                  "geo_location": { "lat": 1.0, "lon": 2.0 }
                }
                """;

        mockMvc.perform(post("/api/v1/logs/ingest")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(payload))
                .andExpect(status().isBadRequest());
    }

    @Test
    void missingTimestampIsRejectedWithBadRequest() throws Exception {
        String payload = """
                {
                  "entity_id": "user_1",
                  "geo_location": { "lat": 1.0, "lon": 2.0 }
                }
                """;

        mockMvc.perform(post("/api/v1/logs/ingest")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(payload))
                .andExpect(status().isBadRequest());
    }
}
