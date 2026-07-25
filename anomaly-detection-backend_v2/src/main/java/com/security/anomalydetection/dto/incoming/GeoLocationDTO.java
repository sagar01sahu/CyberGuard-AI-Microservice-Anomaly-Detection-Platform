package com.security.anomalydetection.dto.incoming;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class GeoLocationDTO {

    @JsonProperty("lat")
    private Double lat;

    @JsonProperty("lon")
    private Double lon;
}
