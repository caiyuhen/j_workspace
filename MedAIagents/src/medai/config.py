"""
配置管理模块
Configuration Management Module
"""

import os
import copy
import yaml
from typing import Any, Dict, Optional
from dotenv import load_dotenv


class Config:
    """全局配置管理类"""
    
    _instance: Optional['Config'] = None
    _config: Dict[str, Any] = {}
    _config_path: str = ""
    
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
        
        self._config_path = config_path
        
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
    
    def save(self):
        """将当前内存配置保存回 config.yaml，api_key 脱敏为环境变量占位符"""
        if not self._config_path:
            return False
        
        # 深拷贝，避免修改内存中的真实 api_key
        save_config = copy.deepcopy(self._config)
        providers = save_config.get('llm', {}).get('providers', {})
        known_env_map = {
            'cherryin': 'CHERRYIN_API_KEY',
            'openai': 'OPENAI_API_KEY',
            'anthropic': 'ANTHROPIC_API_KEY',
            'deepseek': 'DEEPSEEK_API_KEY',
            'qwen': 'DASHSCOPE_API_KEY',
            'siliconflow': 'SILICONFLOW_API_KEY',
            'fireworks': 'FIREWORKS_API_KEY',
            'together': 'TOGETHER_API_KEY',
            'groq': 'GROQ_API_KEY',
        }
        for pname, pconfig in providers.items():
            if isinstance(pconfig, dict) and 'api_key' in pconfig:
                key_val = pconfig['api_key']
                if key_val and isinstance(key_val, str):
                    env_var = known_env_map.get(pname)
                    if env_var and not (key_val.startswith('${') and key_val.endswith('}')):
                        pconfig['api_key'] = '${' + env_var + '}'
        
        with open(self._config_path, 'w', encoding='utf-8') as f:
            yaml.dump(save_config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        return True
    
    def delete(self, key: str) -> bool:
        """删除配置项
        
        Args:
            key: 配置键名，支持点号分隔 (如 'llm.providers.myprovider')
        
        Returns:
            是否成功删除
        """
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if isinstance(config, dict) and k in config:
                config = config[k]
            else:
                return False
        
        if isinstance(config, dict) and keys[-1] in config:
            del config[keys[-1]]
            return True
        return False
