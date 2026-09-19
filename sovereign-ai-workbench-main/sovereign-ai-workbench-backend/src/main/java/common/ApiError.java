package com.mrpl.saiw.common;

import java.time.Instant;
import java.util.Map;

public record ApiError(
        String requestId,
        Instant timestamp,
        int status,
        String error,
        String message,
        Map<String, String> validationErrors
) {
}