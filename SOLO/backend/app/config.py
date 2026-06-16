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
    # 基础地址，实际对话接口为 POST {LLM_ENDPOINT}/chat
    LLM_ENDPOINT: str = "http://127.0.0.1:8802"
    LLM_API_KEY: Optional[str] = None
    LLM_MODEL: str = "medical-large"
    # 单位：毫秒（LLMService 内部会除以 1000 传给 httpx）
    LLM_TIMEOUT: int = 300000  # 300秒
    
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
