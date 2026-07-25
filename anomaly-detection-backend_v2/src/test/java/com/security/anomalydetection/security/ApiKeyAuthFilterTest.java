package com.security.anomalydetection.security;

import jakarta.servlet.FilterChain;
import jakarta.servlet.http.HttpServletRequest;
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

@ExtendWith(MockitoExtension.class)
class ApiKeyAuthFilterTest {

    @Mock
    private HttpServletRequest request;

    @Mock
    private FilterChain filterChain;

    private ApiKeyAuthFilter filter;

    @BeforeEach
    void setUp() {
        filter = new ApiKeyAuthFilter("correct-key");
    }

    @AfterEach
    void clearContext() {
        SecurityContextHolder.clearContext();
    }

    @Test
    void onlyAppliesToTheIngestionPath() {
        when(request.getRequestURI()).thenReturn("/api/v1/alerts/live");
        assertThat(filter.shouldNotFilter(request)).isTrue();

        when(request.getRequestURI()).thenReturn("/api/v1/logs/ingest");
        assertThat(filter.shouldNotFilter(request)).isFalse();
    }

    @Test
    void rejectsAMissingApiKey() throws Exception {
        when(request.getHeader("X-API-Key")).thenReturn(null);
        MockHttpServletResponse response = new MockHttpServletResponse();

        filter.doFilterInternal(request, response, filterChain);

        assertThat(response.getStatus()).isEqualTo(401);
        verifyNoInteractions(filterChain);
    }

    @Test
    void rejectsAWrongApiKey() throws Exception {
        when(request.getHeader("X-API-Key")).thenReturn("wrong-key");
        when(request.getRemoteAddr()).thenReturn("127.0.0.1");
        MockHttpServletResponse response = new MockHttpServletResponse();

        filter.doFilterInternal(request, response, filterChain);

        assertThat(response.getStatus()).isEqualTo(401);
        verifyNoInteractions(filterChain);
    }

    @Test
    void allowsTheCorrectApiKeyThroughAndPopulatesTheSecurityContext() throws Exception {
        when(request.getHeader("X-API-Key")).thenReturn("correct-key");
        MockHttpServletResponse response = new MockHttpServletResponse();

        filter.doFilterInternal(request, response, filterChain);

        verify(filterChain).doFilter(request, response);
        assertThat(SecurityContextHolder.getContext().getAuthentication().getName())
                .isEqualTo("log-generator-service");
    }
}
