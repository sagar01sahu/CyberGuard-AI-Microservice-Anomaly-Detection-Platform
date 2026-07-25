package com.security.anomalydetection.security;

import com.auth0.jwt.exceptions.JWTVerificationException;
import com.auth0.jwt.interfaces.DecodedJWT;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.List;

/**
 * Validates the Bearer JWT on every request that isn't explicitly
 * bypassed (see shouldNotFilter). On success, populates the
 * SecurityContext with an authenticated principal so downstream
 * authorizeHttpRequests() rules let the request through.
 *
 * The dashboard (React) must present this token on every GET endpoint;
 * the log ingestion endpoint is intentionally bypassed here since it
 * is authenticated via a separate static API key (see ApiKeyAuthFilter).
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    private static final String AUTH_HEADER = "Authorization";
    private static final String BEARER_PREFIX = "Bearer ";

    private final JwtService jwtService;

    @Override
    protected boolean shouldNotFilter(HttpServletRequest request) {
        String path = request.getRequestURI();
        return path.startsWith("/api/v1/logs/ingest")
                || path.startsWith("/actuator/health")
                || path.startsWith("/api/v1/auth/")
                || path.startsWith("/api/v1/dashboard/")
                || path.startsWith("/api/v1/alerts/");
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                     HttpServletResponse response,
                                     FilterChain filterChain) throws ServletException, IOException {

        String header = request.getHeader(AUTH_HEADER);

        if (header == null || !header.startsWith(BEARER_PREFIX)) {
            respondUnauthorized(response, "Missing or malformed Authorization header");
            return;
        }

        String token = header.substring(BEARER_PREFIX.length());

        try {
            DecodedJWT decoded = jwtService.verifyToken(token);

            UsernamePasswordAuthenticationToken authentication = new UsernamePasswordAuthenticationToken(
                    decoded.getSubject(), null, List.of(new SimpleGrantedAuthority("ROLE_DASHBOARD_USER")));

            SecurityContextHolder.getContext().setAuthentication(authentication);
            filterChain.doFilter(request, response);

        } catch (JWTVerificationException e) {
            log.warn("JWT verification failed: {}", e.getMessage());
            respondUnauthorized(response, "Invalid or expired token");
        }
    }

    private void respondUnauthorized(HttpServletResponse response, String message) throws IOException {
        response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
        response.setContentType("application/json");
        response.getWriter().write("{\"error\":\"" + message + "\"}");
    }
}
