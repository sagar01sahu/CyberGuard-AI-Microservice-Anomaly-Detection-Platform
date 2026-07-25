package com.security.anomalydetection.config;

import io.netty.channel.ChannelOption;
import io.netty.handler.timeout.ReadTimeoutHandler;
import io.netty.handler.timeout.WriteTimeoutHandler;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.reactive.ReactorClientHttpConnector;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.netty.http.client.HttpClient;

import java.util.concurrent.TimeUnit;

/**
 * Configures the WebClient bean used to talk to the external Python AI
 * microservice.
 *
 * A dedicated, bounded connect timeout plus read/write timeouts are set
 * so a slow or hanging AI engine can never block an ingestion request
 * indefinitely -- this keeps the ingestion endpoint's throughput
 * predictable even under AI engine degradation, and works together with
 * the fallback path in LogProcessingService (mark PENDING_ANALYSIS and
 * move on) rather than ever hanging the caller.
 */
@Configuration
public class WebClientConfig {

    @Bean
    public WebClient aiEngineWebClient(
            @Value("${ai-engine.base-url:http://localhost:8000}") String baseUrl,
            @Value("${ai-engine.connect-timeout-ms:2000}") int connectTimeoutMs,
            @Value("${ai-engine.timeout-ms:3000}") int readWriteTimeoutMs) {

        HttpClient httpClient = HttpClient.create()
                .option(ChannelOption.CONNECT_TIMEOUT_MILLIS, connectTimeoutMs)
                .doOnConnected(conn -> conn
                        .addHandlerLast(new ReadTimeoutHandler(readWriteTimeoutMs, TimeUnit.MILLISECONDS))
                        .addHandlerLast(new WriteTimeoutHandler(readWriteTimeoutMs, TimeUnit.MILLISECONDS)));

        return WebClient.builder()
                .baseUrl(baseUrl)
                .clientConnector(new ReactorClientHttpConnector(httpClient))
                .build();
    }
}
