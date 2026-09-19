package com.mrpl.saiw.security;

import org.slf4j.MDC;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.List;
import java.util.UUID;
import java.util.concurrent.CopyOnWriteArrayList;

@Service
public class SecurityMonitorService {

    private final List<SecurityEvent> events = new CopyOnWriteArrayList<>();

    public void record(String type, String message) {
        events.add(new SecurityEvent(
                UUID.randomUUID(),
                type,
                message,
                MDC.get("requestId"),
                Instant.now()
        ));
    }

    public List<SecurityEvent> findAll() {
        return List.copyOf(events);
    }
}