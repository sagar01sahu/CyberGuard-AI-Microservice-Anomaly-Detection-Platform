package com.security.anomalydetection.client;

import com.security.anomalydetection.dto.ai.AiPredictionRequest;
import com.security.anomalydetection.dto.ai.AiPredictionResponse;

/**
 * Abstraction over the call to the external Python AI microservice.
 * Kept as an interface (rather than injecting WebClient directly into
 * LogProcessingService) so the orchestration logic can be unit tested
 * with a plain Mockito mock instead of standing up a fake HTTP server
 * for every test.
 */
public interface AiEngineClient {
    AiPredictionResponse predict(AiPredictionRequest request);
}
