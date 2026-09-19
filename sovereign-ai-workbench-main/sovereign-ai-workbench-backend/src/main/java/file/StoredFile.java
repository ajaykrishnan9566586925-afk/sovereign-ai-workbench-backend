package com.mrpl.saiw.file;

import java.time.Instant;
import java.util.UUID;

public record StoredFile(
        UUID fileId,
        String ownerUserId,
        String originalFilename,
        String storedFilename,
        String contentType,
        long size,
        Instant uploadedAt
) {
}