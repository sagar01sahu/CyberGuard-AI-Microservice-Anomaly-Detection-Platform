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
        private String sourceService;
        private String targetService;
        private String endpoint;
        private String protocol;
        private String entityId;
        private String payloadType;
        private Object requestBody;
        private Object responseBody;
        private String status;
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
