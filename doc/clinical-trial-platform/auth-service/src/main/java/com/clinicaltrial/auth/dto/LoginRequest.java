package com.clinicaltrial.auth.dto;

import jakarta.validation.constraints.*;
import lombok.*;

/**
 * 登录请求 DTO
 * 
 * @author Cai Yuheng
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class LoginRequest {
    
    @NotBlank(message = "用户名不能为空")
    private String username;
    
    @NotBlank(message = "密码不能为空")
    private String password;
    
    private Boolean rememberMe;
}
