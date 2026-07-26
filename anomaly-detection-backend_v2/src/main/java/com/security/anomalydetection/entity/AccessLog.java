package com.security.anomalydetection.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.Instant;

/**
 * A single synthetic access event ingested from the log generator.
 */
@Entity
@Table(name = "access_logs", indexes = {
        @Index(name = "idx_access_logs_entity_id_timestamp", columnList = "entityId, timestamp"),
        @Index(name = "idx_access_logs_processing_status", columnList = "processingStatus")
})
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class AccessLog {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String entityId;

    private String authMethod;

    private String authStatus;

    @Column(nullable = false)
    private Instant timestamp;

    private String sourceIp;

    private Double geoLat;

    private Double geoLon;

    private String deviceId;

    private String osVersion;

    @Column(length = 1024)
    private String userAgent;

    private String resourceAccessed;
    private String role;


    @Builder.Default
    @Column(nullable = false)
    private String processingStatus = "ANALYZED";
}
