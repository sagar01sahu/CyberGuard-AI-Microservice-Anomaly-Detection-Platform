package com.security.anomalydetection;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

/**
 * Entry point for the Middle Layer Orchestrator.
 *
 * @EnableScheduling powers PendingAnalysisRetryScheduler, which
 * periodically retries AccessLog rows that failed AI analysis due to a
 * transient outage of the Python AI engine.
 */
@SpringBootApplication
@EnableScheduling
public class AnomalyDetectionApplication {
    public static void main(String[] args) {
        SpringApplication.run(AnomalyDetectionApplication.class, args);
    }
}
