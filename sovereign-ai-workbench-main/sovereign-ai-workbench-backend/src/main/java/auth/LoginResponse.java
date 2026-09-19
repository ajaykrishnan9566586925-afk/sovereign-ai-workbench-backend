package com.mrpl.saiw.auth;

import java.time.Instant;
import java.util.List;

public record LoginResponse(
        String accessToken,
        String tokenType,
        Instant expiresAt,
        String userId,
        String username,
        List<String> roles
) {
}