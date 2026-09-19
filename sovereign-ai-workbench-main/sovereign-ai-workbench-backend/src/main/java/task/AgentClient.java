package com.mrpl.saiw.task;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

import java.util.UUID;

@Component
public class AgentClient {

    private final RestClient restClient;
    private final String baseUrl;

    public AgentClient(
            RestClient restClient,
            @Value("${app.agent.base-url}") String baseUrl
    ) {
        this.restClient = restClient;
        this.baseUrl = baseUrl;
    }

    public AgentTaskResponse submit(
            UUID taskId,
            UUID fileId,
            String userId,
            String instruction
    ) {
        AgentTaskRequest request = new AgentTaskRequest(
                taskId,
                fileId,
                userId,
                instruction
        );

        return restClient.post()
                .uri(baseUrl + "/internal/tasks")
                .contentType(MediaType.APPLICATION_JSON)
                .body(request)
                .retrieve()
                .body(AgentTaskResponse.class);
    }

    public AgentHealthResponse health() {
        return restClient.get()
                .uri(baseUrl + "/internal/health")
                .retrieve()
                .body(AgentHealthResponse.class);
    }

    public record AgentTaskRequest(
            UUID taskId,
            UUID fileId,
            String userId,
            String instruction
    ) {
    }

    public record AgentTaskResponse(
            UUID taskId,
            String status,
            String message
    ) {
    }

    public record AgentHealthResponse(
            String status,
            String service
    ) {
    }
}