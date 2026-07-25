package com.security.anomalydetection.security;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.List;

/**
 * Guards the log ingestion endpoint with a simple static API key
 * (shared secret) instead of JWT, since the caller is a trusted
 * synthetic-data generator service, not an interactive dashboard user.
 *
 * Uses a constant-time comparison (MessageDigest.isEqual) to avoid
 * leaking timing information about the correct key.
 */
@Slf4j
@Component
public class ApiKeyAuthFilter extends OncePerRequestFilter {

    private static final String API_KEY_HEADER = "X-API-Key";
    private static final String INGEST_PATH = "/api/v1/logs/ingest";

    private final String expectedApiKey;

    public ApiKeyAuthFilter(@Value("${security.ingest.api-key}") String expectedApiKey) {
        this.expectedApiKey = expectedApiKey;
    }

    @Override
    protected boolean shouldNotFilter(HttpServletRequest request) {
        return !request.getRequestURI().startsWith(INGEST_PATH);
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                     HttpServletResponse response,
                                     FilterChain filterChain) throws ServletException, IOException {

        String providedKey = request.getHeader(API_KEY_HEADER);

        if (providedKey == null || !constantTimeEquals(providedKey, expectedApiKey)) {
            log.warn("Rejected ingestion request with invalid API key from {}", request.getRemoteAddr());
            response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
            response.setContentType("application/json");
            response.getWriter().write("{\"error\":\"Invalid or missing API key\"}");
            return;
        }

        // Authenticate as a system principal so downstream
        // authorizeHttpRequests() rules (permitAll on this path) are
        // satisfied without requiring a JWT.
        var authentication = new UsernamePasswordAuthenticationToken(
                "log-generator-service", null, List.of(new SimpleGrantedAuthority("ROLE_INGESTION_SERVICE")));
        SecurityContextHolder.getContext().setAuthentication(authentication);

        filterChain.doFilter(request, response);
    }

    private boolean constantTimeEquals(String a, String b) {
        return MessageDigest.isEqual(
                a.getBytes(StandardCharsets.UTF_8),
                b.getBytes(StandardCharsets.UTF_8));
    }
}
