"""任务执行所需 Skill 解析服务。"""
from __future__ import annotations

from typing import Any, Dict, List

from app.services.skill_registry import skill_registry as default_skill_registry


class SkillResolver:
    """根据任务提示语识别所需 Skill，并检查是否已安装。"""

    RULES = [
        {
            "required_skill_id": "skill_pubmed_search",
            "keywords": ["pubmed", "文献", "论文", "检索", "综述", "meta分析", "meta-analysis"],
            "query": "PubMed 文献检索",
            "category": "research",
        },
        {
            "required_skill_id": "skill_clinical_trials_search",
            "keywords": ["clinicaltrials", "临床试验", "clinical trial", "试验登记"],
            "query": "ClinicalTrials 临床试验检索",
            "category": "research",
        },
        {
            "required_skill_id": "skill_fda_drug_search",
            "keywords": ["fda", "药品审评", "说明书", "批准", "label"],
            "query": "FDA 药品信息检索",
            "category": "tool",
        },
    ]

    def __init__(self, skill_registry=None):
        self.skill_registry = skill_registry or default_skill_registry

    @staticmethod
    def _is_active(skill: Any) -> bool:
        if not skill:
            return False
        if isinstance(skill, dict):
            return skill.get("is_active", True) is not False
        return getattr(skill, "is_active", True) is not False

    @staticmethod
    def _skill_payload(skill: Any) -> Dict[str, Any]:
        if isinstance(skill, dict):
            return skill
        return {
            "id": getattr(skill, "id", None),
            "name": getattr(skill, "name", None),
            "display_name": getattr(skill, "display_name", None),
            "description": getattr(skill, "description", None),
            "category": getattr(skill, "category", None),
            "is_active": getattr(skill, "is_active", None),
        }

    def detect_required_skills(self, prompt: str) -> List[Dict[str, Any]]:
        text = (prompt or "").lower()
        required = []
        seen = set()
        for rule in self.RULES:
            if rule["required_skill_id"] in seen:
                continue
            if any(keyword.lower() in text for keyword in rule["keywords"]):
                required.append(rule)
                seen.add(rule["required_skill_id"])
        return required

    def resolve(self, prompt: str) -> Dict[str, Any]:
        installed_skills: List[Dict[str, Any]] = []
        missing_skills: List[Dict[str, Any]] = []
        required_skills = self.detect_required_skills(prompt)

        for required in required_skills:
            skill = self.skill_registry.get_skill(required["required_skill_id"])
            if self._is_active(skill):
                installed_skills.append(self._skill_payload(skill))
                continue

            discovery = self.skill_registry.discover_skill_candidates(
                query=required["query"],
                required_skill_id=required["required_skill_id"],
                category=required.get("category"),
            )
            missing_skills.append({
                "required_skill_id": required["required_skill_id"],
                "query": required["query"],
                "category": required.get("category"),
                "candidates": discovery.get("candidates", []),
                "message": discovery.get("message", "需要安装或启用 Skill 后继续执行"),
            })

        return {
            "ready": len(missing_skills) == 0,
            "required_skills": required_skills,
            "installed_skills": installed_skills,
            "missing_skills": missing_skills,
        }


skill_resolver = SkillResolver()
