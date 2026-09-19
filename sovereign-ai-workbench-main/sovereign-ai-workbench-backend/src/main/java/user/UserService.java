package com.mrpl.saiw.user;

import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;

@Service
public class UserService {

    public UserProfile getCurrentUser(Jwt jwt) {
        String userId = jwt.getSubject();
        String username = jwt.getClaimAsString("username");

        List<String> roles = jwt.getClaimAsStringList("roles");

        return new UserProfile(
                userId,
                username,
                roles
        );
    }

    public record UserProfile(
            String userId,
            String username,
            List<String> roles
    ) {
    }
}