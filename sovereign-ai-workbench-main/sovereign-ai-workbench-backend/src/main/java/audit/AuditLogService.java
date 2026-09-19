package com.mrpl.saiw.audit;

import org.slf4j.MDC;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.List;
import java.util.UUID;
import java.util.concurrent.CopyOnWriteArrayList;

@Service
public class AuditLogService {

    private final List<AuditLog> logs = new CopyOnWriteArrayList<>();

    public void record(
            String userId,
            String role,
            String operation,
            String resourceId,
            boolean success
    ) {
        logs.add(new AuditLog(
                UUID.randomUUID(),
                userId,
                role,
                operation,
                resourceId,
                MDC.get("requestId"),
                success,
                Instant.now()
        ));
    }

    public List<AuditLog> findAll() {
        return List.copyOf(logs);
    }
}