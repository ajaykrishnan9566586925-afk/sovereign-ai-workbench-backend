package com.mrpl.saiw.security;

import java.time.Instant;
import java.util.UUID;

public record SecurityEvent(
        UUID eventId,
        String type,
        String message,
        String requestId,
        Instant timestamp
) {
}