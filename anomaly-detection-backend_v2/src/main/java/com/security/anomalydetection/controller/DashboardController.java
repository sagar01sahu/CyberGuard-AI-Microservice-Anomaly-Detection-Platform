package com.security.anomalydetection.controller;

import com.security.anomalydetection.dto.outgoing.AlertResponseDTO;
import com.security.anomalydetection.entity.AccessLog;
import com.security.anomalydetection.entity.RiskAlert;
import com.security.anomalydetection.repository.AccessLogRepository;
import com.security.anomalydetection.repository.RiskAlertRepository;
import com.security.anomalydetection.service.TelemetryService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Serves live risk alert data, telemetry, system statistics, and log feeds
 * to the React dashboard.
 */
@RestController
@RequestMapping("/api/v1")
@RequiredArgsConstructor
public class DashboardController {

    private final RiskAlertRepository riskAlertRepository;
    private final AccessLogRepository accessLogRepository;
    private final TelemetryService telemetryService;

    @GetMapping("/alerts/live")
    public List<AlertResponseDTO> getLiveAlerts() {
        return riskAlertRepository.findTop20ByOrderByTimestampDesc()
                .stream()
                .map(this::toDto)
                .toList();
    }

    @GetMapping("/dashboard/telemetry")
    public List<TelemetryService.MicroservicePacket> getTelemetryPackets() {
        return telemetryService.getRecentPackets();
    }

    @GetMapping("/dashboard/stats")
    public Map<String, Object> getDashboardStats() {
        long totalLogs = accessLogRepository.count();
        long totalAlerts = riskAlertRepository.count();
        List<RiskAlert> alerts = riskAlertRepository.findAll();

        Map<String, Long> severityCounts = new HashMap<>();
        Map<String, Long> anomalyTypeCounts = new HashMap<>();

        for (RiskAlert a : alerts) {
            severityCounts.merge(a.getSeverity() != null ? a.getSeverity() : "UNKNOWN", 1L, Long::sum);
            anomalyTypeCounts.merge(a.getAnomalyType() != null ? a.getAnomalyType() : "UNKNOWN", 1L, Long::sum);
        }

        Map<String, Object> stats = new HashMap<>();
        stats.put("totalLogsIngested", totalLogs);
        stats.put("totalAlertsGenerated", totalAlerts);
        stats.put("severityBreakdown", severityCounts);
        stats.put("anomalyTypeBreakdown", anomalyTypeCounts);
        stats.put("systemStatus", "HEALTHY");
        return stats;
    }

    @GetMapping("/dashboard/logs")
    public List<AccessLog> getRecentLogs() {
        return accessLogRepository.findAll()
                .stream()
                .sorted((a, b) -> b.getTimestamp().compareTo(a.getTimestamp()))
                .limit(30)
                .toList();
    }

    private AlertResponseDTO toDto(RiskAlert alert) {
        AccessLog log = accessLogRepository.findById(alert.getAccessLogId()).orElse(null);
        return AlertResponseDTO.builder()
                .alertId(alert.getAlertId())
                .timestamp(alert.getTimestamp())
                .entityId(alert.getEntityId())
                .riskScore(alert.getRiskScore())
                .severity(alert.getSeverity())
                .anomalyType(alert.getAnomalyType())
                .explainabilityFactors(alert.getExplainabilityFactors())
                .sourceIp(log != null ? log.getSourceIp() : "192.168.1.100")
                .deviceId(log != null ? log.getDeviceId() : "device-unknown")
                .resourceAccessed(log != null ? log.getResourceAccessed() : "/api/v1/resource")
                .build();
    }
}

