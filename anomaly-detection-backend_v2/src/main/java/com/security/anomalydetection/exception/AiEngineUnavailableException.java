package com.security.anomalydetection.exception;

/**
 * Raised whenever the Python AI engine cannot be reached, times out, or
 * returns an error/empty response. Caught by LogProcessingService so the
 * originating AccessLog write is never lost -- it is marked
 * PENDING_ANALYSIS instead of failing the whole ingestion request.
 */
public class AiEngineUnavailableException extends RuntimeException {
    public AiEngineUnavailableException(String message, Throwable cause) {
        super(message, cause);
    }
}
