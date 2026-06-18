"""对话中安装 Skill 的意图识别与执行服务。"""
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from app.services.skill_registry import skill_registry as default_skill_registry
from app.services.skill_resolver import skill_resolver as default_skill_resolver


class ChatSkillInstaller:
    """识别“安装 Skill”类对话，并复用 SkillHub 安装链路完成安装。"""

    INSTALL_PREFIX_RE = re.compile(r"^(?:请)?(?:帮我)?(?:搜索并安装|搜索安装|安装|添加|启用)\s+(.+?)\s*$", re.I)
    SKILLHUB_URL_RE = re.compile(r"https?://skillhub\.cn/skills/[A-Za-z0-9_-]+", re.I)
    SLUG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{2,}$")

    def __init__(self, registry=None, resolver=None):
        self.registry = registry or default_skill_registry
        self.resolver = resolver or default_skill_resolver

    def handle(self, message: str) -> Optional[Dict[str, Any]]:
        """处理对话安装请求；非安装意图返回 None。"""
        text = (message or "").strip()
        match = self.INSTALL_PREFIX_RE.match(text)
        if not match:
            return None

        target = match.group(1).strip().strip("`'\"")
        url_match = self.SKILLHUB_URL_RE.search(target)
        if url_match:
            return self._install_url(url_match.group(0))

        if self.SLUG_RE.match(target) and ("-" in target or "_" in target):
            slug = target.replace("_", "-")
            return self._install_url(f"https://skillhub.cn/skills/{slug}")

        return self._search_then_install(target)

    def _install_url(self, url: str) -> Dict[str, Any]:
        try:
            skill = self.registry.install_by_url(url)
            installed_now = True
        except ValueError as exc:
            existing = self._find_existing_by_url(url)
            if not existing:
                raise
            skill = existing
            installed_now = False

        local_pack = None
        if getattr(self.registry, "_ensure_skillhub_local_pack", None):
            try:
                local_pack = str(self.registry._ensure_skillhub_local_pack(skill))
            except Exception as exc:  # noqa: BLE001
                local_pack = f"本地包预安装失败：{exc}"

        display_name = skill.get("display_name") or skill.get("name") or skill.get("id")
        status_line = "已安装 Skill" if installed_now else "该 Skill 已安装，无需重复安装"
        content = f"{status_line}：{display_name}\n\n来源：{url}"
        if local_pack:
            content += f"\n\n本地包：{local_pack}"
        return {
            "handled": True,
            "status": "installed" if installed_now else "already_installed",
            "content": content,
            "skill": self._skill_payload(skill),
        }

    def _search_then_install(self, query: str) -> Dict[str, Any]:
        remote = getattr(self.resolver, "remote_strategy", None)
        if remote is None:
            return {
                "handled": True,
                "status": "not_found",
                "content": "当前无法访问远程 SkillHub 搜索。请提供完整 SkillHub 链接，例如：https://skillhub.cn/skills/ppt-generator-skill",
                "skill_install_candidates": [],
            }

        results = remote.search(query, "") or []
        candidates = [self._candidate_payload(item) for item in results if (item or {}).get("url")]
        if len(candidates) == 1:
            return self._install_url(candidates[0]["url"])
        if len(candidates) > 1:
            return {
                "handled": True,
                "status": "candidates",
                "content": "找到多个候选 Skill，请选择要安装的一个：",
                "skill_install_candidates": candidates,
            }
        return {
            "handled": True,
            "status": "not_found",
            "content": f"没有找到匹配的 Skill：{query}\n你可以提供 SkillHub 链接，或换一个关键词。",
            "skill_install_candidates": [],
        }

    def _find_existing_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        normalized = urlparse(url).geturl()
        for skill in getattr(self.registry, "_skills", {}).values():
            if skill.get("source_url") == normalized or (skill.get("config") or {}).get("endpoint") == normalized:
                return skill
        return None

    @staticmethod
    def _skill_payload(skill: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": skill.get("id"),
            "name": skill.get("name"),
            "display_name": skill.get("display_name"),
            "protocol": skill.get("protocol"),
            "source_url": skill.get("source_url") or (skill.get("config") or {}).get("endpoint"),
        }

    @staticmethod
    def _candidate_payload(item: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "title": item.get("title") or item.get("name") or item.get("display_name") or "未命名 Skill",
            "description": item.get("description") or "",
            "url": item.get("url"),
            "source": item.get("source") or "skillhub",
        }


chat_skill_installer = ChatSkillInstaller()
