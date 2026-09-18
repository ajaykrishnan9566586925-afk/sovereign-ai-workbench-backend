package com.mrpl.saiw.file;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.nio.file.*;
import java.time.Instant;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

@Service
public class FileService {

    private final Path uploadDirectory;
    private final long maxFileSize;
    private final Set<String> allowedExtensions;
    private final Map<UUID, StoredFile> files = new ConcurrentHashMap<>();

    public FileService(
            @Value("${app.storage.upload-directory}") String uploadDirectory,
            @Value("${app.security.max-file-size-bytes}") long maxFileSize,
            @Value("${app.security.allowed-extensions}") List<String> allowedExtensions
    ) throws IOException {
        this.uploadDirectory = Paths.get(uploadDirectory).toAbsolutePath().normalize();
        this.maxFileSize = maxFileSize;
        this.allowedExtensions = new HashSet<>(
                allowedExtensions.stream()
                        .map(String::toLowerCase)
                        .toList()
        );

        Files.createDirectories(this.uploadDirectory);
    }

    public FileMetadataResponse upload(MultipartFile file, String userId) {
        validate(file);

        UUID fileId = UUID.randomUUID();
        String extension = extension(file.getOriginalFilename());
        String storedFilename = fileId + "." + extension;
        Path target = uploadDirectory.resolve(storedFilename).normalize();

        if (!target.getParent().equals(uploadDirectory)) {
            throw new IllegalArgumentException("Invalid file path");
        }

        try {
            Files.copy(file.getInputStream(), target, StandardCopyOption.REPLACE_EXISTING);
        } catch (IOException ex) {
            throw new IllegalStateException("Unable to store file");
        }

        StoredFile storedFile = new StoredFile(
                fileId,
                userId,
                safeOriginalName(file.getOriginalFilename()),
                storedFilename,
                file.getContentType(),
                file.getSize(),
                Instant.now()
        );

        files.put(fileId, storedFile);

        return toResponse(storedFile);
    }

    public StoredFile getAuthorizedFile(UUID fileId, String userId, boolean admin) {
        StoredFile file = files.get(fileId);

        if (file == null) {
            throw new NoSuchElementException("File not found");
        }

        if (!admin && !file.ownerUserId().equals(userId)) {
            throw new AccessDeniedException("File access denied");
        }

        return file;
    }

    public Path physicalPath(StoredFile file) {
        return uploadDirectory.resolve(file.storedFilename()).normalize();
    }

    private void validate(MultipartFile file) {
        if (file == null || file.isEmpty()) {
            throw new IllegalArgumentException("File is required");
        }

        if (file.getSize() > maxFileSize) {
            throw new IllegalArgumentException("File exceeds maximum allowed size");
        }

        String extension = extension(file.getOriginalFilename());

        if (!allowedExtensions.contains(extension)) {
            throw new IllegalArgumentException("File type is not allowed");
        }

        if (file.getOriginalFilename() != null &&
                file.getOriginalFilename().contains("..")) {
            throw new IllegalArgumentException("Invalid filename");
        }
    }

    private String extension(String name) {
        if (name == null || !name.contains(".")) {
            throw new IllegalArgumentException("File extension is required");
        }

        return name.substring(name.lastIndexOf('.') + 1)
                .toLowerCase(Locale.ROOT);
    }

    private String safeOriginalName(String name) {
        return Paths.get(Objects.requireNonNullElse(name, "file"))
                .getFileName()
                .toString();
    }

    private FileMetadataResponse toResponse(StoredFile file) {
        return new FileMetadataResponse(
                file.fileId(),
                file.originalFilename(),
                file.contentType(),
                file.size(),
                file.uploadedAt()
        );
    }
}