package com.mrpl.saiw.task;

import jakarta.validation.Valid;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.web.bind.annotation.*;

import java.util.UUID;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/tasks")
public class TaskController {

    private final TaskService taskService;

    public TaskController(TaskService taskService) {
        this.taskService = taskService;
    }

    @PostMapping
    @PreAuthorize("hasAnyRole('USER', 'ANALYST', 'ADMIN')")
    public TaskResponse submit(
            @Valid @RequestBody SubmitTaskRequest request,
            @AuthenticationPrincipal Jwt jwt
    ) {
        return taskService.submit(request, jwt.getSubject());
    }

    @GetMapping("/{taskId}")
    @PreAuthorize("hasAnyRole('USER', 'ANALYST', 'ADMIN')")
    public TaskResponse status(
            @PathVariable UUID taskId,
            @AuthenticationPrincipal Jwt jwt
    ) {
        return taskService.getStatus(taskId, jwt.getSubject());
    }

    @GetMapping("/{taskId}/progress")
    @PreAuthorize("hasAnyRole('USER', 'ANALYST', 'ADMIN')")
    public TaskResponse progress(
            @PathVariable UUID taskId,
            @AuthenticationPrincipal Jwt jwt
    ) {
        return taskService.getProgress(taskId, jwt.getSubject());
    }

    @GetMapping("/{taskId}/result")
    @PreAuthorize("hasAnyRole('USER', 'ANALYST', 'ADMIN')")
    public TaskResponse result(
            @PathVariable UUID taskId,
            @AuthenticationPrincipal Jwt jwt
    ) {
        return taskService.getResult(taskId, jwt.getSubject());
    }

    @GetMapping("/{taskId}/files")
    @PreAuthorize("hasAnyRole('USER', 'ANALYST', 'ADMIN')")
    public Map<String, Object> generatedFiles(
            @PathVariable UUID taskId,
            @AuthenticationPrincipal Jwt jwt
    ) {
        Task task = taskService.getAuthorizedTask(taskId, jwt.getSubject());

        return Map.of(
                "taskId", task.getTaskId(),
                "files", java.util.List.of()
        );
    }
}