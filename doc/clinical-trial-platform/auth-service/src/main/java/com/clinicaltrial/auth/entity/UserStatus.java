package com.clinicaltrial.auth.entity;

/**
 * 用户状态枚举
 */
public enum UserStatus {
    
    /**
     * 活跃
     */
    ACTIVE,
    
    /**
     * 已禁用
     */
    DISABLED,
    
    /**
     * 待验证
     */
    PENDING_VERIFICATION,
    
    /**
     * 已注销
     */
    DEACTIVATED
}
