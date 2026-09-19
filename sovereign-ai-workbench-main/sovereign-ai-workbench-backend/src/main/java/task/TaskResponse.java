package com.mrpl.saiw.task;

import java.time.Instant;
import java.util.List;
import java.util.UUID;

public record TaskResponse(
        UUID taskId,
        TaskStatus status,
        String message,
        String result,
        List<UUID> files,
        int progress,
        Instant timestamp
) {
    public static TaskResponse from(Task task) {
        return new TaskResponse(
                task.getTaskId(),
                task.getStatus(),
                task.getMessage(),
                task.getResult(),
                List.of(),
                task.getProgress(),
                Instant.now()
        );
    }
}