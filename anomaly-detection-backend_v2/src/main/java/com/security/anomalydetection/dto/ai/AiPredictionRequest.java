package com.security.anomalydetection.dto.ai;

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
public class AiPredictionRequest {

    private CurrentEvent currentEvent;
    private List<HistoricalEvent> historicalEvents;

    @Getter
    @Setter
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class CurrentEvent {
        private String entityId;
        private String role; // <--- MUST BE HERE
        private String authMethod;
        private String authStatus;
        private Instant timestamp;
        private String sourceIp;
        private Double geoLat;
        private Double geoLon;
        private String deviceId;
        private String osVersion;
        private String userAgent;
        private String resourceAccessed;
    }

    @Getter
    @Setter
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class HistoricalEvent {
        private String role; // <--- MUST BE HERE
        private String authMethod;
        private String authStatus;
        private Instant timestamp;
        private String sourceIp;
        private Double geoLat;
        private Double geoLon;
        private String deviceId;
        private String osVersion;
        private String resourceAccessed;
    }
}