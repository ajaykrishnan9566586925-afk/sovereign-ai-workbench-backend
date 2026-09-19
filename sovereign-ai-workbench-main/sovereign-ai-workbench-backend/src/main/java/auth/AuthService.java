
package com.mrpl.saiw.auth;

import org.springframework.security.oauth2.jose.jws.SignatureAlgorithm;
import org.springframework.security.oauth2.jwt.*;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.List;

@Service
public class AuthService {

    private final JwtEncoder jwtEncoder;

    public AuthService(JwtEncoder jwtEncoder) {
        this.jwtEncoder = jwtEncoder;
    }

    public LoginResponse login(LoginRequest request) {
        if (!"demo".equals(request.username()) || !"demo123".equals(request.password())) {
            throw new RuntimeException("Invalid username or password");
        }

        Instant now = Instant.now();
        Instant expiresAt = now.plusSeconds(3600);

        JwtClaimsSet claims = JwtClaimsSet.builder()
                .issuer("self")
                .issuedAt(now)
                .expiresAt(expiresAt)
                .subject("user123")
                .claim("username", request.username())
                .claim("roles", List.of("ROLE_USER"))
                .build();

        JwsHeader jwsHeader = JwsHeader.with(SignatureAlgorithm.RS256).build();

        String token = jwtEncoder.encode(
                JwtEncoderParameters.from(jwsHeader, claims)
        ).getTokenValue();

        return new LoginResponse(
                token,
                "Bearer",
                expiresAt,
                "user123",
                request.username(),
                List.of("ROLE_USER")
        );
    }
}

