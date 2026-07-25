package com.security.anomalydetection.controller;

import com.security.anomalydetection.security.JwtService;
import lombok.RequiredArgsConstructor;
import org.springframework.context.annotation.Profile;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

/**
 * DEV/TEST-ONLY endpoint for minting dashboard JWTs.
 *
 * The original spec does not define a login/identity flow for the React
 * dashboard. In a real deployment, JWTs would be issued by an existing
 * IdP/SSO provider (Okta, Cognito, Auth0, etc.) or a dedicated auth
 * service, and JwtAuthenticationFilter would simply verify tokens signed
 * by that provider's key. This controller exists only so the API can be
 * exercised end-to-end locally without standing up a full identity
 * provider. It is registered ONLY under the "dev" profile and MUST NOT
 * be enabled in production.
 */
@RestController
@Profile("dev")
@RequiredArgsConstructor
public class AuthController {

    private final JwtService jwtService;

    @PostMapping("/api/v1/auth/dev-token")
    public Map<String, String> issueDevToken(@RequestParam(defaultValue = "dev-user") String subject) {
        return Map.of("token", jwtService.generateToken(subject));
    }
}
