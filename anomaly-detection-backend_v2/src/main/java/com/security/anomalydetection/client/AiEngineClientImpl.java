package com.security.anomalydetection.client;

import com.security.anomalydetection.dto.ai.AiPredictionRequest;
import com.security.anomalydetection.dto.ai.AiPredictionResponse;
import com.security.anomalydetection.exception.AiEngineUnavailableException;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientRequestException;
import org.springframework.web.reactive.function.client.WebClientResponseException;

import java.time.Duration;


@Slf4j
@Component
public class AiEngineClientImpl implements AiEngineClient {

    private final WebClient webClient;
    private final Duration responseTimeout;

    public AiEngineClientImpl(@Qualifier("aiEngineWebClient") WebClient webClient,
                               @Value("${ai-engine.timeout-ms:3000}") long timeoutMs) {
        this.webClient = webClient;
        this.responseTimeout = Duration.ofMillis(timeoutMs);
    }

    @Override
    public AiPredictionResponse predict(AiPredictionRequest request) {
        try {
            return webClient.post()
                    .uri("/predict")
                    .bodyValue(request)
                    .retrieve()
                    .bodyToMono(AiPredictionResponse.class)
                    .block(responseTimeout);
        } catch (WebClientResponseException e) {
            log.error("AI engine returned an error status {}: {}", e.getStatusCode(), e.getResponseBodyAsString());
            throw new AiEngineUnavailableException("AI engine responded with error status " + e.getStatusCode(), e);
        } catch (WebClientRequestException e) {
            log.error("Could not reach AI engine: {}", e.getMessage());
            throw new AiEngineUnavailableException("AI engine unreachable", e);
        } catch (Exception e) {
            log.error("Unexpected error calling AI engine", e);
            throw new AiEngineUnavailableException("Unexpected error calling AI engine", e);
        }
    }
}
