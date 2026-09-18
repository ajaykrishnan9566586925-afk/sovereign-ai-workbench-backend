package com.mrpl.saiw.file;

import org.springframework.core.io.Resource;
import org.springframework.core.io.UrlResource;
import org.springframework.http.*;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.net.MalformedURLException;
import java.nio.file.Path;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/files")
public class FileController {

    private final FileService fileService;

    public FileController(FileService fileService) {
        this.fileService = fileService;
    }

    @PostMapping(consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    @PreAuthorize("hasAnyRole('USER', 'ANALYST', 'ADMIN')")
    public FileMetadataResponse upload(
            @RequestPart("file") MultipartFile file,
            @AuthenticationPrincipal Jwt jwt
    ) {
        return fileService.upload(file, jwt.getSubject());
    }

    @GetMapping("/{fileId}/download")
    @PreAuthorize("hasAnyRole('USER', 'ANALYST', 'ADMIN')")
    public ResponseEntity<Resource> download(
            @PathVariable UUID fileId,
            @AuthenticationPrincipal Jwt jwt
    ) throws MalformedURLException {

        boolean admin = jwt.getClaimAsStringList("roles").contains("ADMIN");

        StoredFile storedFile = fileService.getAuthorizedFile(
                fileId,
                jwt.getSubject(),
                admin
        );

        Path path = fileService.physicalPath(storedFile);
        Resource resource = new UrlResource(path.toUri());

        if (!resource.exists() || !resource.isReadable()) {
            return ResponseEntity.notFound().build();
        }

        return ResponseEntity.ok()
                .contentType(MediaType.APPLICATION_OCTET_STREAM)
                .header(
                        HttpHeaders.CONTENT_DISPOSITION,
                        ContentDisposition.attachment()
                                .filename(storedFile.originalFilename())
                                .build()
                                .toString()
                )
                .header("X-Content-Type-Options", "nosniff")
                .body(resource);
    }
}