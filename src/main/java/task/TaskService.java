package com.mrpl.saiw.task;

import com.mrpl.saiw.file.FileService;
import com.mrpl.saiw.file.StoredFile;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

import java.util.Map;
import java.util.NoSuchElementException;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

@Service
public class TaskService {

    private final Map<UUID, Task> tasks = new ConcurrentHashMap<>();
    private final FileService fileService;
    private final AgentClient agentClient;

    public TaskService(
            FileService fileService,
            AgentClient agentClient
    ) {
        this.fileService = fileService;
        this.agentClient = agentClient;
    }

    public TaskResponse submit(
            SubmitTaskRequest request,
            String userId
    ) {
        StoredFile file = fileService.getAuthorizedFile(
                request.fileId(),
                userId,
                false
        );

        Task task = new Task(
                UUID.randomUUID(),
                userId,
                file.fileId(),
                request.instruction()
        );

        tasks.put(task.getTaskId(), task);
        submitToAgentAsync(task);

        return TaskResponse.from(task);
    }

    @Async
    protected void submitToAgentAsync(Task task) {
        try {
            task.processing();

            agentClient.submit(
                    task.getTaskId(),
                    task.getFileId(),
                    task.getUserId(),
                    task.getInstruction()
            );

            task.updateProgress(
                    20,
                    "Task accepted by Python LangGraph agent"
            );

        } catch (Exception ex) {
            task.fail("Python agent service is unavailable");
        }
    }

    public Task getAuthorizedTask(UUID taskId, String userId) {
        Task task = tasks.get(taskId);

        if (task == null) {
            throw new NoSuchElementException("Task not found");
        }

        if (!task.getUserId().equals(userId)) {
            throw new AccessDeniedException("Task access denied");
        }

        return task;
    }

    public TaskResponse getStatus(UUID taskId, String userId) {
        return TaskResponse.from(getAuthorizedTask(taskId, userId));
    }

    public TaskResponse getProgress(UUID taskId, String userId) {
        return TaskResponse.from(getAuthorizedTask(taskId, userId));
    }

    public TaskResponse getResult(UUID taskId, String userId) {
        Task task = getAuthorizedTask(taskId, userId);

        if (task.getStatus() != TaskStatus.COMPLETED) {
            throw new IllegalArgumentException("Task result is not ready");
        }

        return TaskResponse.from(task);
    }

    public boolean isHealthy() {
        try {
            AgentClient.AgentHealthResponse response = agentClient.health();
            return response != null && "UP".equalsIgnoreCase(response.status());
        } catch (Exception ex) {
            return false;
        }
    }
}