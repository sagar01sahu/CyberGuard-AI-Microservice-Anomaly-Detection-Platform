package com.security.anomalydetection.security;

import com.auth0.jwt.exceptions.JWTVerificationException;
import com.auth0.jwt.interfaces.DecodedJWT;
import jakarta.servlet.FilterChain;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.mock.web.MockHttpServletResponse;
import org.springframework.security.core.context.SecurityContextHolder;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.*;

/**
 * Exercises JwtAuthenticationFilter directly (no Spring context) so the
 * pass/reject logic and shouldNotFilter bypass rules are covered fast
 * and in isolation from the rest of the security chain.
 */
@ExtendWith(MockitoExtension.class)
class JwtAuthenticationFilterTest {

    @Mock
    private JwtService jwtService;

    @Mock
    private HttpServletRequest request;

    @Mock
    private FilterChain filterChain;

    @Mock
    private DecodedJWT decodedJWT;

    private JwtAuthenticationFilter filter;

    @BeforeEach
    void setUp() {
        filter = new JwtAuthenticationFilter(jwtService);
    }

    @AfterEach
    void clearContext() {
        SecurityContextHolder.clearContext();
    }

    @Test
    void bypassesTheIngestionEndpoint() {
        when(request.getRequestURI()).thenReturn("/api/v1/logs/ingest");
        assertThat(filter.shouldNotFilter(request)).isTrue();
    }

    @Test
    void bypassesTheDevAuthEndpoint() {
        when(request.getRequestURI()).thenReturn("/api/v1/auth/dev-token");
        assertThat(filter.shouldNotFilter(request)).isTrue();
    }

    @Test
    void doesNotBypassTheDashboardEndpoint() {
        when(request.getRequestURI()).thenReturn("/api/v1/alerts/live");
        assertThat(filter.shouldNotFilter(request)).isFalse();
    }

    @Test
    void rejectsRequestsMissingTheAuthorizationHeader() throws Exception {
        when(request.getHeader("Authorization")).thenReturn(null);
        MockHttpServletResponse response = new MockHttpServletResponse();

        filter.doFilterInternal(request, response, filterChain);

        assertThat(response.getStatus()).isEqualTo(HttpServletResponse.SC_UNAUTHORIZED);
        verifyNoInteractions(filterChain);
    }

    @Test
    void rejectsAMalformedAuthorizationHeader() throws Exception {
        when(request.getHeader("Authorization")).thenReturn("Basic abc123");
        MockHttpServletResponse response = new MockHttpServletResponse();

        filter.doFilterInternal(request, response, filterChain);

        assertThat(response.getStatus()).isEqualTo(HttpServletResponse.SC_UNAUTHORIZED);
        verifyNoInteractions(filterChain);
    }

    @Test
    void rejectsAnInvalidToken() throws Exception {
        when(request.getHeader("Authorization")).thenReturn("Bearer bad-token");
        when(jwtService.verifyToken("bad-token")).thenThrow(new JWTVerificationException("invalid"));
        MockHttpServletResponse response = new MockHttpServletResponse();

        filter.doFilterInternal(request, response, filterChain);

        assertThat(response.getStatus()).isEqualTo(HttpServletResponse.SC_UNAUTHORIZED);
        verifyNoInteractions(filterChain);
    }

    @Test
    void allowsAValidTokenThroughAndPopulatesTheSecurityContext() throws Exception {
        when(request.getHeader("Authorization")).thenReturn("Bearer good-token");
        when(jwtService.verifyToken("good-token")).thenReturn(decodedJWT);
        when(decodedJWT.getSubject()).thenReturn("user-42");
        MockHttpServletResponse response = new MockHttpServletResponse();

        filter.doFilterInternal(request, response, filterChain);

        verify(filterChain).doFilter(request, response);
        assertThat(SecurityContextHolder.getContext().getAuthentication().getName()).isEqualTo("user-42");
    }
}
