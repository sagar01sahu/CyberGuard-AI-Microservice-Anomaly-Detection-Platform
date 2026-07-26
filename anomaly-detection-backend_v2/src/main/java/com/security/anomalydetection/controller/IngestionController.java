package com.security.anomalydetection.controller;

import com.security.anomalydetection.dto.incoming.IncomingLogRequest;
import com.security.anomalydetection.entity.AccessLog;
import com.security.anomalydetection.service.LogProcessingService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;


@RestController
@RequestMapping("/api/v1/logs")
@RequiredArgsConstructor
public class IngestionController {

    private final LogProcessingService logProcessingService;

    @PostMapping("/ingest")
    public ResponseEntity<Map<String, Object>> ingest(@Valid @RequestBody IncomingLogRequest request) {
        AccessLog savedLog = logProcessingService.processIncomingLog(request);

        return ResponseEntity.status(HttpStatus.CREATED).body(Map.of(
                "id", savedLog.getId(),
                "processing_status", savedLog.getProcessingStatus()
        ));
    }
}
