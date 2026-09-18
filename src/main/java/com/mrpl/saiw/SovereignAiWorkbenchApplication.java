package com.mrpl.saiw;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.ConfigurationPropertiesScan;

@SpringBootApplication
@ConfigurationPropertiesScan
public class SovereignAiWorkbenchApplication {

    public static void main(String[] args) {
        SpringApplication.run(SovereignAiWorkbenchApplication.class, args);
    }
}