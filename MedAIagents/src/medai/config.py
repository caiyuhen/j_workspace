"""
配置管理模块
Configuration Management Module
"""

import os
import yaml
from typing import Any, Dict, Optional
from dotenv import load_dotenv


class Config:
    """全局配置管理类"""
    
    _instance: Optional['Config'] = None
    _config: Dict[str, Any] = {}
    
    def __new__(cls, config_path: str = None):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config(config_path)
        return cls._instance
    
    def _load_config(self, config_path: str = None):
        """加载配置文件"""
        # 加载环境变量
        load_dotenv()
        
        # 默认配置文件路径
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                'config.yaml'
            )
        
        # 加载YAML配置
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f) or {}
        
        # 替换环境变量占位符
        self._replace_env_vars(self._config)
    
    def _replace_env_vars(self, obj: Any):
        """递归替换配置中的环境变量占位符"""
        if isinstance(obj, dict):
            for key, value in obj.items():
                obj[key] = self._replace_env_vars(value)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                obj[i] = self._replace_env_vars(item)
        elif isinstance(obj, str) and obj.startswith('${') and obj.endswith('}'):
            # 提取环境变量名
            env_var = obj[2:-1]
            return os.getenv(env_var, obj)
        return obj
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            key: 配置键名，支持点号分隔 (如 'llm.default_provider')
            default: 默认值
        
        Returns:
            配置值
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """设置配置值
        
        Args:
            key: 配置键名，支持点号分隔
            value: 配置值
        """
        keys = key.split('.')
        config = self._config
        
        # 遍历创建嵌套字典
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def get_llm_config(self, provider: str = None) -> Dict[str, Any]:
        """获取LLM提供商配置
        
        Args:
            provider: 提供商名称，如不指定则使用默认提供商
        
        Returns:
            LLM配置字典
        """
        if provider is None:
            provider = self.get('llm.default_provider', 'openai')
        
        return self.get(f'llm.providers.{provider}', {})
    
    def get_medical_knowledge_config(self) -> Dict[str, Any]:
        """获取医学知识库配置"""
        return self.get('medical_knowledge', {})
    
    def get_cdss_config(self) -> Dict[str, Any]:
        """获取CDSS配置"""
        return self.get('cdss', {})
    
    def get_security_config(self) -> Dict[str, Any]:
        """获取安全配置"""
        return self.get('security', {})
    
    @property
    def all_config(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self._config.copy()
