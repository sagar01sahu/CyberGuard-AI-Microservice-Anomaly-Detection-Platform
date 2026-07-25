package com.security.anomalydetection.service;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.ConcurrentLinkedQueue;

/**
 * Captures live microservice data transfer packets for UI visualization
 * in the React Microservice Data Flow tab.
 */
@Service
public class TelemetryService {

    private final ConcurrentLinkedQueue<MicroservicePacket> packetHistory = new ConcurrentLinkedQueue<>();
    private static final int MAX_PACKETS = 50;

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class MicroservicePacket {
        private String packetId;
        private String timestamp;
        private String sourceService;     // e.g. "Microservice 1: Synthetic Log Generator"
        private String targetService;     // e.g. "Microservice 2: Spring Boot Backend"
        private String endpoint;          // e.g. "POST /api/v1/logs/ingest"
        private String protocol;          // e.g. "HTTP/1.1 REST (X-API-Key)"
        private String entityId;
        private String payloadType;       // "Log Ingestion", "AI Feature Vector", "Risk Score Output"
        private Object requestBody;
        private Object responseBody;
        private String status;            // "SUCCESS", "ANOMALY_DETECTED", "PENDING"
        private Long latencyMs;
    }

    public void recordPacket(MicroservicePacket packet) {
        if (packet.getTimestamp() == null) {
            packet.setTimestamp(Instant.now().toString());
        }
        packetHistory.add(packet);
        while (packetHistory.size() > MAX_PACKETS) {
            packetHistory.poll();
        }
    }

    public List<MicroservicePacket> getRecentPackets() {
        List<MicroservicePacket> list = new ArrayList<>(packetHistory);
        Collections.reverse(list);
        return list;
    }
}
