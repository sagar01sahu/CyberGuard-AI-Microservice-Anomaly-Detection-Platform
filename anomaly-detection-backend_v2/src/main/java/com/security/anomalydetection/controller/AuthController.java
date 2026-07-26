package com.security.anomalydetection.controller;

import com.security.anomalydetection.security.JwtService;
import lombok.RequiredArgsConstructor;
import org.springframework.context.annotation.Profile;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;


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
