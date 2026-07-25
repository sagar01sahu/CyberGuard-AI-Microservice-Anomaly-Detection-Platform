package com.security.anomalydetection.security;

import com.auth0.jwt.exceptions.JWTVerificationException;
import com.auth0.jwt.interfaces.DecodedJWT;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class JwtServiceTest {

    private final JwtService jwtService =
            new JwtService("a-sufficiently-long-test-secret-key", "test-issuer", 60);

    @Test
    void generatesAndVerifiesATokenRoundTrip() {
        String token = jwtService.generateToken("user-42");

        DecodedJWT decoded = jwtService.verifyToken(token);

        assertThat(decoded.getSubject()).isEqualTo("user-42");
        assertThat(decoded.getIssuer()).isEqualTo("test-issuer");
    }

    @Test
    void rejectsATokenSignedWithADifferentSecret() {
        JwtService otherService = new JwtService("a-completely-different-secret-key", "test-issuer", 60);
        String token = otherService.generateToken("user-42");

        assertThatThrownBy(() -> jwtService.verifyToken(token))
                .isInstanceOf(JWTVerificationException.class);
    }

    @Test
    void rejectsATokenWithTheWrongIssuer() {
        JwtService otherIssuerService = new JwtService("a-sufficiently-long-test-secret-key", "someone-else", 60);
        String token = otherIssuerService.generateToken("user-42");

        assertThatThrownBy(() -> jwtService.verifyToken(token))
                .isInstanceOf(JWTVerificationException.class);
    }

    @Test
    void anExpiredTokenFailsVerification() throws InterruptedException {
        JwtService shortLivedService = new JwtService("a-sufficiently-long-test-secret-key", "test-issuer", 0);
        String token = shortLivedService.generateToken("user-42");

        // expiration-minutes = 0 means the token expires at issue time;
        // give the clock a moment to move past "now" before verifying.
        Thread.sleep(50);

        assertThatThrownBy(() -> shortLivedService.verifyToken(token))
                .isInstanceOf(JWTVerificationException.class);
    }
}
