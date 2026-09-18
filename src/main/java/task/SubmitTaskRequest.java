package com.mrpl.saiw.task;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

import java.util.UUID;

public record SubmitTaskRequest(
        @NotNull UUID fileId,
        @NotBlank String instruction
) {
}