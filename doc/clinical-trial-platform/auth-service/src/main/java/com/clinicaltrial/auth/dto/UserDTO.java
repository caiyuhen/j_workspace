package com.clinicaltrial.auth.dto;

import com.clinicaltrial.auth.entity.UserRole;
import lombok.*;

import java.time.LocalDateTime;
import java.util.List;

/**
 * 用户信息 DTO
 * 
 * @author Cai Yuheng
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class UserDTO {
    
    private String id;
    private String username;
    private String email;
    private String phoneNumber;
    private String realName;
    private String department;
    private String position;
    private UserRole role;
    private List<String> roleNames;
    private LocalDateTime createdAt;
    private LocalDateTime lastLoginAt;
}
