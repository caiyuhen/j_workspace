"""
Skill 注册表
"""

import json
import os
from typing import Dict, List, Optional, Any
from loguru import logger

from .models import Skill


class SkillRegistry:
    """Skill 注册表 - 管理所有可用 Skills"""
    
    def __init__(self, storage_path: str = "./data/skills"):
        self.storage_path = storage_path
        self._skills: Dict[str, Skill] = {}
        os.makedirs(storage_path, exist_ok=True)
        
        # 加载已保存的 Skills
        self._load_from_disk()
    
    def register(self, skill: Skill) -> bool:
        """注册 Skill"""
        if skill.name in self._skills:
            logger.warning(f"Skill '{skill.name}' 已存在，将覆盖")
        
        self._skills[skill.name] = skill
        
        # 持久化保存
        self._save_skill(skill)
        
        logger.info(f"Skill 注册成功: {skill.name} (v{skill.version})")
        return True
    
    def unregister(self, name: str) -> bool:
        """注销 Skill"""
        if name not in self._skills:
            return False
        
        del self._skills[name]
        
        # 删除持久化文件
        file_path = os.path.join(self.storage_path, f"{name}.json")
        if os.path.exists(file_path):
            os.remove(file_path)
        
        logger.info(f"Skill 已注销: {name}")
        return True
    
    def get(self, name: str) -> Optional[Skill]:
        """获取 Skill"""
        return self._skills.get(name)
    
    def has(self, name: str) -> bool:
        """检查是否存在"""
        return name in self._skills
    
    def list_skills(self, tag: str = None, builtin_only: bool = False) -> List[Skill]:
        """列出所有 Skills"""
        skills = list(self._skills.values())
        
        if tag:
            skills = [s for s in skills if tag in s.tags]
        
        if builtin_only:
            skills = [s for s in skills if s.is_builtin]
        
        return skills
    
    def list_skill_names(self) -> List[str]:
        """列出所有 Skill 名称"""
        return list(self._skills.keys())
    
    def search(self, query: str) -> List[Skill]:
        """搜索 Skills"""
        query = query.lower()
        results = []
        
        for skill in self._skills.values():
            if (query in skill.name.lower() or
                query in skill.description.lower() or
                any(query in t.lower() for t in skill.tags)):
                results.append(skill)
        
        return results
    
    def to_openai_functions(self) -> List[Dict[str, Any]]:
        """转换为 OpenAI Function Calling 格式"""
        return [skill.to_openai_function() for skill in self._skills.values()]
    
    def update_usage_stats(self, name: str, success: bool):
        """更新使用统计"""
        skill = self._skills.get(name)
        if skill:
            skill.usage_count += 1
            # 更新成功率
            total = skill.usage_count
            current_success = int(skill.success_rate * (total - 1))
            if success:
                current_success += 1
            skill.success_rate = current_success / total if total > 0 else 1.0
            skill.updated_at = __import__('datetime').datetime.now()
            self._save_skill(skill)
    
    def _save_skill(self, skill: Skill):
        """保存 Skill 到磁盘"""
        file_path = os.path.join(self.storage_path, f"{skill.name}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(skill.dict(), f, ensure_ascii=False, indent=2, default=str)
    
    def _load_from_disk(self):
        """从磁盘加载 Skills"""
        if not os.path.exists(self.storage_path):
            return
        
        for filename in os.listdir(self.storage_path):
            if filename.endswith('.json'):
                file_path = os.path.join(self.storage_path, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    skill = Skill(**data)
                    self._skills[skill.name] = skill
                    logger.debug(f"已加载 Skill: {skill.name}")
                except Exception as e:
                    logger.warning(f"加载 Skill 文件失败 {filename}: {e}")
    
    def export_skill(self, name: str, file_path: str) -> bool:
        """导出 Skill 到文件"""
        skill = self._skills.get(name)
        if not skill:
            return False
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(skill.dict(), f, ensure_ascii=False, indent=2, default=str)
        return True
    
    def import_skill(self, file_path: str) -> Optional[Skill]:
        """从文件导入 Skill"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        skill = Skill(**data)
        self.register(skill)
        return skill
