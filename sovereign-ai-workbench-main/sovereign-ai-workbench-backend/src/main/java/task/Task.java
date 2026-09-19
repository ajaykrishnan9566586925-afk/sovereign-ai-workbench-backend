package com.mrpl.saiw.task;

import java.time.Instant;
import java.util.UUID;

public class Task {

    private final UUID taskId;
    private final String userId;
    private final UUID fileId;
    private final String instruction;
    private final Instant createdAt;

    private volatile TaskStatus status;
    private volatile int progress;
    private volatile String message;
    private volatile String result;

    public Task(
            UUID taskId,
            String userId,
            UUID fileId,
            String instruction
    ) {
        this.taskId = taskId;
        this.userId = userId;
        this.fileId = fileId;
        this.instruction = instruction;
        this.createdAt = Instant.now();
        this.status = TaskStatus.QUEUED;
        this.progress = 0;
        this.message = "Task queued";
    }

    public UUID getTaskId() {
        return taskId;
    }

    public String getUserId() {
        return userId;
    }

    public UUID getFileId() {
        return fileId;
    }

    public String getInstruction() {
        return instruction;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }

    public TaskStatus getStatus() {
        return status;
    }

    public int getProgress() {
        return progress;
    }

    public String getMessage() {
        return message;
    }

    public String getResult() {
        return result;
    }

    public void processing() {
        this.status = TaskStatus.PROCESSING;
        this.message = "Agent processing started";
        this.progress = 10;
    }

    public void updateProgress(int progress, String message) {
        this.progress = Math.max(0, Math.min(100, progress));
        this.message = message;
    }

    public void complete(String result) {
        this.status = TaskStatus.COMPLETED;
        this.progress = 100;
        this.message = "Task completed";
        this.result = result;
    }

    public void fail(String message) {
        this.status = TaskStatus.FAILED;
        this.message = message;
    }
}