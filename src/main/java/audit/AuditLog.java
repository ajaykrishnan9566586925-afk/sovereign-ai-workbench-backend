package com.mrpl.saiw.audit;

import java.time.Instant;
import java.util.UUID;

public record AuditLog(
        UUID auditId,
        String userId,
        String role,
        String operation,
        String resourceId,
        String requestId,
        boolean success,
        Instant timestamp
) {
}