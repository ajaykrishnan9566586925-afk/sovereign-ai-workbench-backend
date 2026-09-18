package com.mrpl.saiw.file;

import java.time.Instant;
import java.util.UUID;

public record FileMetadataResponse(
        UUID fileId,
        String filename,
        String contentType,
        long size,
        Instant uploadedAt
) {
}