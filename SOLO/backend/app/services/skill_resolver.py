"""任务执行所需 Skill 解析服务。

支持两种调用：

1. 旧调用（保留向后兼容）：
   ``resolver.resolve(prompt)`` -> ``dict``
   按关键词规则识别"提示词需要哪些技能"，并报告缺失。

2. 新调用（动态计划链路使用）：
   ``resolver.resolve(name=step_name, description=step_description)`` -> ``SkillResolution``
   - 先在本地 skill_registry 中按关键字匹配；
   - 命中 → ``status='local'``；
   - 未命中 → 调用可注入的 ``remote_strategy`` 在线检索 Skill 仓库（如 clawhub.ai），
     拿到 URL 后调用 ``skill_registry.install_by_url`` 自动安装。
   - 远程未配置 / 失败 → ``status='not_available'``，附带明确中文提示，**绝不发假 HTTP**。
"""
from __future__ import annotations

import logging
import os
import requests
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from app.config import settings
from app.services.skill_registry import skill_registry as default_skill_registry

logger = logging.getLogger(__name__)


class RemoteSearchUnavailable(RuntimeError):
    """远程 Skill 仓库未配置或调用失败时抛出，用于告知调用方："""


@dataclass
class SkillResolution:
    """解析结果。"""

    status: str  # 'local' | 'auto_installed' | 'not_available'
    skill_id: Optional[str]
    source: str  # 'local' | 'clawhub' | 'none'
    message: str
    candidate_url: Optional[str] = None


class ClawhubSearchStrategy:
    """远程 Skill 检索策略。

    - 如果配置了 ``SOLO_CLAWHUB_API_BASE``，优先请求远程搜索接口；
    - 如果未配置或远程不可用，回退到内置 SkillHub 公开目录，保证“在线搜索”功能可用；
    - 返回结果必须包含可安装 URL，后续由 install_by_url 真正安装并持久化。
    """

    DEFAULT_SKILLHUB_CATALOG: List[Dict[str, Any]] = [
        {
            "title": "Ppt Generator Skill",
            "description": "通过 SkillHub 安装的 PPT/演示文稿生成技能",
            "url": "https://skillhub.cn/skills/ppt-generator-skill",
            "keywords": "ppt powerpoint presentation deck slides 演示文稿 幻灯片 汇报",
        },
        {
            "title": "Clinical Trial Protocol Synopsis",
            "description": "生成临床试验方案摘要和研究设计草案",
            "url": "https://skillhub.cn/skills/clinical-trial-protocol-synopsis",
            "keywords": "clinical trial protocol synopsis 临床试验 方案 研究设计 医学",
        },
    ]

    def __init__(
        self,
        api_base: Optional[str] = None,
        api_key: Optional[str] = None,
        http_post: Optional[Callable[..., Any]] = None,
        http_get: Optional[Callable[..., Any]] = None,
    ):
        self.api_base = (api_base or "").strip().rstrip("/")
        self.api_key = api_key
        self._http_post = http_post or requests.post
        self._http_get = http_get or requests.get

    @staticmethod
    def _normalize_results(payload: Any) -> List[Dict[str, Any]]:
        if isinstance(payload, dict):
            items = payload.get("items") or payload.get("results") or payload.get("data") or []
        elif isinstance(payload, list):
            items = payload
        else:
            items = []

        normalized: List[Dict[str, Any]] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            url = item.get("url") or item.get("install_url") or item.get("homepage") or item.get("source_url")
            title = item.get("title") or item.get("name") or item.get("display_name") or url
            if not url or not title:
                continue
            normalized.append({
                "title": title,
                "description": item.get("description") or item.get("summary") or "",
                "url": url,
            })
        return normalized

    def _search_builtin_catalog(self, name: str, description: str) -> List[Dict[str, Any]]:
        query = f"{name or ''} {description or ''}".lower().strip()
        if not query:
            return [
                {"title": i["title"], "description": i["description"], "url": i["url"]}
                for i in self.DEFAULT_SKILLHUB_CATALOG
            ]
        results = []
        for item in self.DEFAULT_SKILLHUB_CATALOG:
            haystack = f"{item['title']} {item['description']} {item.get('keywords', '')} {item['url']}".lower()
            if any(token and token in haystack for token in query.split()):
                results.append({"title": item["title"], "description": item["description"], "url": item["url"]})
        return results

    def search(self, name: str, description: str) -> List[Dict[str, Any]]:
        if not self.api_base:
            return self._search_builtin_catalog(name, description)

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {"q": name, "query": name, "description": description}
        errors: List[str] = []

        # 兼容不同部署可能暴露的搜索路径/方法：优先 POST /search，失败后尝试 GET。
        attempts = [
            ("POST", f"{self.api_base}/search"),
            ("GET", f"{self.api_base}/search"),
            ("GET", f"{self.api_base}/skills/search"),
            ("GET", f"{self.api_base}/skills"),
        ]
        for method, url in attempts:
            try:
                if method == "POST":
                    response = self._http_post(url, json=payload, headers=headers, timeout=10)
                else:
                    response = self._http_get(url, params=payload, headers=headers, timeout=10)
                if hasattr(response, "raise_for_status"):
                    response.raise_for_status()
                response_payload = response.json() if hasattr(response, "json") else response
                results = self._normalize_results(response_payload)
                if results:
                    return results
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{method} {url}: {exc}")
                continue

        if errors:
            logger.warning("远程 Skill 搜索失败，回退到内置 SkillHub 目录: %s", " | ".join(errors[:3]))
        return self._search_builtin_catalog(name, description)



class SkillResolver:
    """既支持旧的"提示词关键字检测"，也支持新的"动态计划 step 解析"。"""

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

    def __init__(self, skill_registry=None, remote_strategy: Optional[Any] = None):
        self.skill_registry = skill_registry or default_skill_registry
        self.remote_strategy = remote_strategy

    # -------- 旧调用（保持原有签名，不改） --------

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

    def _resolve_legacy(self, prompt: str) -> Dict[str, Any]:
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

    # -------- 新调用：按 step 名称/描述解析具体 skill_id --------

    def _local_match(self, name: str, description: str) -> Optional[Dict[str, Any]]:
        haystacks: List[tuple] = []
        for skill in self.skill_registry._skills.values():
            tokens = " ".join(
                str(skill.get(field) or "")
                for field in ("id", "name", "display_name", "description", "category")
            ).lower()
            haystacks.append((skill, tokens))

        keywords = [
            token
            for token in (name + " " + (description or "")).lower().split()
            if len(token) >= 2
        ]
        if not keywords:
            return None

        best: Optional[Dict[str, Any]] = None
        best_score = 0
        for skill, tokens in haystacks:
            score = sum(1 for kw in keywords if kw in tokens)
            if score > best_score:
                best = skill
                best_score = score
        return best

    def search_local(self, name: str, description: str = "") -> List[Dict[str, Any]]:
        """供前端"在线搜索"前先做的本地搜索。"""
        match = self._local_match(name, description)
        return [match] if match else []

    def _resolve_for_step(self, name: str, description: str) -> SkillResolution:
        match = self._local_match(name, description)
        if match and self._is_active(match):
            return SkillResolution(
                status="local",
                skill_id=match.get("id"),
                source="local",
                message=f"在本地技能库中匹配到：{match.get('display_name') or match.get('id')}",
            )

        if self.remote_strategy is None:
            return SkillResolution(
                status="not_available",
                skill_id=None,
                source="none",
                message="未启用远程技能搜索；当前没有匹配的本地技能，已自动降级为普通 LLM 步骤。",
            )

        try:
            results = self.remote_strategy.search(name, description) or []
        except RemoteSearchUnavailable as exc:
            return SkillResolution(
                status="not_available",
                skill_id=None,
                source="none",
                message=f"远程技能仓库不可用：{exc}",
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("远程技能检索异常，已降级: %s", exc)
            return SkillResolution(
                status="not_available",
                skill_id=None,
                source="none",
                message=f"远程技能仓库调用异常：{exc}",
            )

        for item in results:
            url = (item or {}).get("url") or ""
            if not url:
                continue
            try:
                installed = self.skill_registry.install_by_url(url)
            except ValueError as exc:
                logger.info("远程候选 %s 安装失败：%s", url, exc)
                continue
            return SkillResolution(
                status="auto_installed",
                skill_id=installed["id"],
                source="clawhub",
                message=f"已从远程技能仓库自动安装并入库：{installed.get('display_name') or installed['id']}",
                candidate_url=url,
            )

        return SkillResolution(
            status="not_available",
            skill_id=None,
            source="none",
            message="远程仓库未返回可用候选，已自动降级为普通 LLM 步骤。",
        )

    def resolve(self, prompt: Optional[str] = None, *, name: Optional[str] = None,
                description: Optional[str] = None):
        """同时支持两种语义。"""
        if name is not None:
            return self._resolve_for_step(name=name, description=description or "")
        return self._resolve_legacy(prompt or "")


def _build_default_remote_strategy() -> Optional[ClawhubSearchStrategy]:
    """构造默认远程策略。

    兼容两套变量：
    - SOLO_CLAWHUB_API_BASE / SOLO_CLAWHUB_API_KEY
    - SKILLHUB_ENDPOINT / SKILLHUB_API_KEY
    """
    api_base = (
        os.getenv("SOLO_CLAWHUB_API_BASE", "").strip()
        or os.getenv("SKILLHUB_ENDPOINT", "").strip()
        or (settings.SOLO_CLAWHUB_API_BASE or "").strip()
        or (settings.SKILLHUB_ENDPOINT or "").strip()
    )
    api_key = (
        os.getenv("SOLO_CLAWHUB_API_KEY", "")
        or os.getenv("SKILLHUB_API_KEY", "")
        or settings.SOLO_CLAWHUB_API_KEY
        or settings.SKILLHUB_API_KEY
        or None
    )
    return ClawhubSearchStrategy(
        api_base=api_base,
        api_key=api_key,
    )


skill_resolver = SkillResolver(remote_strategy=_build_default_remote_strategy())
