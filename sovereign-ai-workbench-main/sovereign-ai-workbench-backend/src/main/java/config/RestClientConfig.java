package com.mrpl.saiw.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.JdkClientHttpRequestFactory;
import org.springframework.web.client.RestClient;

import java.net.http.HttpClient;
import java.time.Duration;

@Configuration
public class RestClientConfig {

    @Bean
    RestClient restClient(
            RestClient.Builder builder,
            AppProperties properties
    ) {
        AppProperties.Agent agent = properties.getAgent();

        HttpClient httpClient = HttpClient.newBuilder()
                .connectTimeout(Duration.ofMillis(
                        agent.getConnectTimeoutMs()
                ))
                .build();

        JdkClientHttpRequestFactory requestFactory =
                new JdkClientHttpRequestFactory(httpClient);

        requestFactory.setReadTimeout(
                Duration.ofMillis(agent.getReadTimeoutMs())
        );

        return builder
                .requestFactory(requestFactory)
                .build();
    }
}