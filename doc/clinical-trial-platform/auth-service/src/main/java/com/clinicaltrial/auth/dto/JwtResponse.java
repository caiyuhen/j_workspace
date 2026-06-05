package com.clinicaltrial.auth.dto;

import lombok.*;

/**
 * JWT 响应 DTO
 * 
 * @author Cai Yuheng
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class JwtResponse {
    
    private String token;
    private String refreshToken;
    private String tokenType;
    private Long expiresIn;
    private UserDTO user;
}
