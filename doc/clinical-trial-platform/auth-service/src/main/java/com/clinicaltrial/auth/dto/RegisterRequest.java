package com.clinicaltrial.auth.dto;

import jakarta.validation.constraints.*;
import lombok.*;

/**
 * 注册请求 DTO
 * 
 * @author Cai Yuheng
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class RegisterRequest {
    
    @NotBlank(message = "用户名不能为空")
    @Size(min = 3, max = 50, message = "用户名长度必须在 3-50 之间")
    private String username;
    
    @NotBlank(message = "密码不能为空")
    @Size(min = 6, max = 100, message = "密码长度必须在 6-100 之间")
    private String password;
    
    @NotBlank(message = "邮箱不能为空")
    @Email(message = "邮箱格式不正确")
    private String email;
    
    @Size(max = 100, message = "真实姓名长度不能超过 100")
    private String realName;
    
    @Size(max = 100, message = "部门长度不能超过 100")
    private String department;
    
    @Size(max = 100, message = "职位长度不能超过 100")
    private String position;
    
    private String phoneNumber;
    
    private String inviteCode;
}
