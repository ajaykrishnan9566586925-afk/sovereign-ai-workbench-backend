package com.mrpl.saiw.security;

import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/v1/security/events")
public class SecurityMonitorController {

    private final SecurityMonitorService service;

    public SecurityMonitorController(SecurityMonitorService service) {
        this.service = service;
    }

    @GetMapping
    @PreAuthorize("hasAnyRole('ADMIN', 'SECURITY_OFFICER')")
    public List<SecurityEvent> getEvents() {
        return service.findAll();
    }
}