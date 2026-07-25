package com.security.anomalydetection.security;

import com.auth0.jwt.JWT;
import com.auth0.jwt.algorithms.Algorithm;
import com.auth0.jwt.interfaces.DecodedJWT;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.Date;

/**
 * Thin wrapper around Auth0's java-jwt library for issuing and verifying
 * HMAC-signed JWTs used by the React dashboard.
 */
@Service
public class JwtService {

    private final Algorithm algorithm;
    private final String issuer;
    private final long expirationMinutes;

    public JwtService(@Value("${security.jwt.secret}") String secret,
                       @Value("${security.jwt.issuer:anomaly-detection-backend}") String issuer,
                       @Value("${security.jwt.expiration-minutes:60}") long expirationMinutes) {
        this.algorithm = Algorithm.HMAC256(secret);
        this.issuer = issuer;
        this.expirationMinutes = expirationMinutes;
    }

    public String generateToken(String subject) {
        Instant now = Instant.now();
        return JWT.create()
                .withIssuer(issuer)
                .withSubject(subject)
                .withIssuedAt(Date.from(now))
                .withExpiresAt(Date.from(now.plusSeconds(expirationMinutes * 60)))
                .sign(algorithm);
    }

    public DecodedJWT verifyToken(String token) {
        return JWT.require(algorithm)
                .withIssuer(issuer)
                .build()
                .verify(token);
    }
}
