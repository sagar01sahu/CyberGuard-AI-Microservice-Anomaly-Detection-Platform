package com.security.anomalydetection.dto.incoming;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.Instant;


@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class IncomingLogRequest {

    @NotBlank
    @JsonProperty("entity_id")
    private String entityId;


    // ADD THIS FIELD
    @JsonProperty("role")
    private String role;
    @JsonProperty("auth_method")
    private String authMethod;

    @JsonProperty("auth_status")
    private String authStatus;

    @NotNull
    @JsonProperty("timestamp")
    private Instant timestamp;

    @JsonProperty("source_ip")
    private String sourceIp;

    @Valid
    @NotNull
    @JsonProperty("geo_location")
    private GeoLocationDTO geoLocation;

    @JsonProperty("device_id")
    private String deviceId;

    @JsonProperty("os_version")
    private String osVersion;

    @JsonProperty("user_agent")
    private String userAgent;

    @JsonProperty("resource_accessed")
    private String resourceAccessed;
}
