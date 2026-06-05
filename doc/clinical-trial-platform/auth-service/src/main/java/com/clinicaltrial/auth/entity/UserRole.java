package com.clinicaltrial.auth.entity;

/**
 * 用户角色枚举
 */
public enum UserRole {
    
    /**
     * 系统管理员
     */
    ADMIN,
    
    /**
     * 平台管理员
     */
    PLATFORM_ADMIN,
    
    /**
     * 申办方用户
     */
    SPONSOR,
    
    /**
     * CRO 用户
     */
    CRO,
    
    /**
     * 研究中心管理员
     */
    SITE_ADMIN,
    
    /**
     * 主要研究者 (PI)
     */
    PRINCIPAL_INVESTIGATOR,
    
    /**
     * 研究协调员 (CRC)
     */
    COORDINATOR,
    
    /**
     * 数据管理员
     */
    DATA_MANAGER,
    
    /**
     * 监查员 (CRA)
     */
    CRA,
    
    /**
     * 普通用户
     */
    USER
}
