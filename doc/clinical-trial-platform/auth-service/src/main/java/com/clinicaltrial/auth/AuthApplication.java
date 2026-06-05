package com.clinicaltrial.auth;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity;

/**
 * 认证服务主启动类
 * 
 * @author Cai Yuheng
 * @version 1.0.0
 */
@SpringBootApplication
@EnableDiscoveryClient
@EnableMethodSecurity(prePostEnabled = true)
public class AuthApplication {
    
    public static void main(String[] args) {
        SpringApplication.run(AuthApplication.class, args);
    }
}
