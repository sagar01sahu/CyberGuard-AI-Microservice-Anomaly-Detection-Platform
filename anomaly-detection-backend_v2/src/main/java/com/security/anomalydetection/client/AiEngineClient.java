package com.security.anomalydetection.client;

import com.security.anomalydetection.dto.ai.AiPredictionRequest;
import com.security.anomalydetection.dto.ai.AiPredictionResponse;


public interface AiEngineClient {
    AiPredictionResponse predict(AiPredictionRequest request);
}
