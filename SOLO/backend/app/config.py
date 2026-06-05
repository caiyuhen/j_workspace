"""
应用配置管理
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用配置
    APP_NAME: str = "Medical Agent System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # 数据库配置
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/medical_agent"
    
    # Redis配置
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # LLM服务配置（内置RAG）
    # 大模型服务地址: 192.168.0.214:8802/chat/
    # LLM服务配置（内置RAG）
    LLM_ENDPOINT: str = "http://192.168.0.214:8802"
    LLM_MODEL: str = "medical-large"
    LLM_TIMEOUT: int = 300000  # 增加到300秒
    
    # JWT配置
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Skill配置
    SKILLHUB_API_KEY: Optional[str] = None
    SKILLHUB_ENDPOINT: str = "https://api.skillhub.cn"
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 全局配置实例
settings = Settings()
