"""
Skill 注册与执行中心（单例）

目标：
1) 让 Skills API 与 ToolAgent 共用同一套技能注册/执行逻辑，避免重复与偏差
2) 统一 Skill 的协议执行：builtin / skillhub / mcp
3) MCP 协议改为真实 HTTP 调用（基于 skill.config.endpoint），未配置则明确报错
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import httpx
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.core.database import engine
from app.models.models import Skill as SkillModel

logger = logging.getLogger(__name__)


# LLM-only 域名（仅允许作为 LLM 网关，不允许当 skill 工具 endpoint）。
# 之所以做这层硬屏蔽：cherryin/v1 是 OpenAI 兼容 LLM 网关；192.168.0.214:8802 是内网 LLM 网关。
# 它们都不是"医疗工具 API"，过去多次出现把它们填进 skill endpoint 然后 404/405 的问题，统一在这里阻止。
_LLM_ONLY_HOST_SUFFIXES = (
    "cherryin.cc",
    "192.168.0.214:8802",
)


def _host_is_llm_only(netloc: str) -> bool:
    netloc = (netloc or "").strip().lower()
    return any(netloc == suffix or netloc.endswith("." + suffix) or netloc == suffix
               for suffix in _LLM_ONLY_HOST_SUFFIXES)


class SkillRegistry:
    def __init__(self):
        self._skills: Dict[str, Dict[str, Any]] = {}
        self._executions: Dict[str, Dict[str, Any]] = {}
        self._candidate_skills: Dict[str, Dict[str, Any]] = {}
        self._db_session_factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)
        self._skillhub_store_dir = Path(os.getenv("SOLO_SKILLHUB_STORE_DIR", r"d:\workspace\SOLO\backend\skillhub_skills"))
        self._init_builtin_skills()
        self._init_candidate_skills()
        self._load_installed_skills_from_db()

    def _skill_to_dict(self, row: SkillModel) -> Dict[str, Any]:
        return {
            "id": row.id,
            "name": row.name,
            "display_name": row.display_name,
            "description": row.description,
            "category": row.category,
            "protocol": row.protocol,
            "config": row.config or {},
            "input_schema": row.input_schema or {},
            "output_schema": row.output_schema or {},
            "is_active": bool(row.is_active),
            "is_builtin": bool(row.is_builtin),
            "usage_count": row.usage_count or 0,
            "created_at": row.created_at or datetime.now(),
            "updated_at": row.updated_at,
            "last_used_at": row.last_used_at,
        }

    def _load_installed_skills_from_db(self) -> None:
        """把数据库中已安装的 Skill 加载进运行时 registry。"""
        session = self._db_session_factory()
        try:
            for row in session.query(SkillModel).all():
                self._skills[row.id] = self._skill_to_dict(row)
        finally:
            session.close()

    def _persist_skill_to_db(self, skill: Dict[str, Any]) -> None:
        """把运行时 Skill 写入数据库，保证重启后仍然安装。"""
        session = self._db_session_factory()
        try:
            row = session.get(SkillModel, skill["id"])
            if row is None:
                row = SkillModel(id=skill["id"], name=skill["name"], display_name=skill["display_name"], protocol=skill["protocol"])
                session.add(row)
            row.name = skill["name"]
            row.display_name = skill.get("display_name") or skill["name"]
            row.description = skill.get("description")
            row.category = skill.get("category")
            row.protocol = skill.get("protocol") or "skillhub"
            row.config = skill.get("config") or {}
            row.input_schema = skill.get("input_schema") or {}
            row.output_schema = skill.get("output_schema") or {}
            row.is_active = bool(skill.get("is_active", True))
            row.is_builtin = bool(skill.get("is_builtin", False))
            row.usage_count = int(skill.get("usage_count") or 0)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def _delete_skill_from_db(self, skill_id: str) -> None:
        session = self._db_session_factory()
        try:
            row = session.get(SkillModel, skill_id)
            if row is not None:
                session.delete(row)
                session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # --------- candidate discovery / explicit install ----------
    def _init_candidate_skills(self) -> None:
        """初始化可发现但不会自动安装的候选技能。"""
        self._candidate_skills = {
            "candidate_pubmed_search": {
                "id": "candidate_pubmed_search",
                "target_skill_id": "skill_pubmed_search",
                "name": "pubmed_search",
                "display_name": "PubMed 文献检索",
                "description": "基于 PubMed 的医学文献检索候选技能，需要用户确认后安装。",
                "category": "research",
                "protocol": "skillhub",
                "source": "trusted_catalog",
                "install_requires_confirmation": True,
                "config": {"endpoint": "https://api.skillhub.cn/skills/pubmed_search"},
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "limit": {"type": "integer", "default": 10}
                    },
                    "required": ["query"],
                },
                "output_schema": {},
            },
            "candidate_clinical_guideline_search": {
                "id": "candidate_clinical_guideline_search",
                "target_skill_id": "skill_guideline_search",
                "name": "guideline_search",
                "display_name": "临床指南检索",
                "description": "检索临床指南、专家共识和诊疗规范的候选技能，需要用户确认后安装。",
                "category": "reference",
                "protocol": "skillhub",
                "source": "trusted_catalog",
                "install_requires_confirmation": True,
                "config": {"endpoint": "https://api.skillhub.cn/skills/guideline_search"},
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "disease": {"type": "string"},
                        "query": {"type": "string"},
                        "limit": {"type": "integer", "default": 10}
                    },
                    "required": ["query"],
                },
                "output_schema": {},
            },
            "candidate_semantic_scholar_search": {
                "id": "candidate_semantic_scholar_search",
                "target_skill_id": "skill_semantic_scholar_search",
                "name": "semantic_scholar_search",
                "display_name": "Semantic Scholar 文献检索",
                "description": "基于 Semantic Scholar 的论文检索候选技能，需要用户确认后安装。",
                "category": "research",
                "protocol": "skillhub",
                "source": "trusted_catalog",
                "install_requires_confirmation": True,
                "config": {"endpoint": "https://api.skillhub.cn/skills/semantic_scholar_search"},
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "limit": {"type": "integer", "default": 10}
                    },
                    "required": ["query"],
                },
                "output_schema": {},
            },
        }

    def discover_skill_candidates(
        self,
        query: Optional[str] = None,
        required_skill_id: Optional[str] = None,
        category: Optional[str] = None,
    ) -> Dict[str, Any]:
        """发现候选技能，但不自动安装。"""
        q = (query or "").lower()
        candidates = list(self._candidate_skills.values())

        if required_skill_id:
            candidates = [
                c for c in candidates
                if c.get("target_skill_id") == required_skill_id or c.get("id") == required_skill_id
            ]
        if category:
            candidates = [c for c in candidates if c.get("category") == category]
        if q:
            candidates = [
                c for c in candidates
                if q in c.get("name", "").lower()
                or q in c.get("display_name", "").lower()
                or q in (c.get("description") or "").lower()
                or any(token and token in (c.get("description") or "").lower() for token in q.split())
                or any(token and token in c.get("name", "").lower() for token in q.split())
            ]

        return {
            "installed": False,
            "required_skill_id": required_skill_id,
            "query": query,
            "candidates": candidates,
            "message": "已发现候选技能，但不会自动安装；请确认后调用安装接口。"
        }

    def install_candidate(self, candidate_id: str) -> Dict[str, Any]:
        """显式安装候选技能。调用此方法代表用户/管理员已确认安装。"""
        candidate = self._candidate_skills.get(candidate_id)
        if not candidate:
            raise ValueError(f"候选技能不存在: {candidate_id}")

        target_skill_id = candidate["target_skill_id"]
        if target_skill_id in self._skills:
            raise ValueError(f"技能已安装: {target_skill_id}")

        skill = {
            "id": target_skill_id,
            "name": candidate["name"],
            "display_name": candidate["display_name"],
            "description": candidate.get("description"),
            "category": candidate.get("category") or "general",
            "protocol": candidate.get("protocol") or "skillhub",
            "is_active": True,
            "is_builtin": False,
            "config": candidate.get("config") or {},
            "input_schema": candidate.get("input_schema") or {},
            "output_schema": candidate.get("output_schema") or {},
            "usage_count": 0,
            "created_at": datetime.now(),
            "installed_from_candidate": candidate_id,
            "source": candidate.get("source"),
        }
        self._skills[target_skill_id] = skill
        self._persist_skill_to_db(skill)
        return skill

    def install_by_url(self, url: str) -> Dict[str, Any]:
        """通过 URL 真实安装一个外部技能。"""
        if not isinstance(url, str) or not url.strip():
            raise ValueError("URL 不能为空")

        parsed = urlparse(url.strip())
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("URL 必须是合法的 http/https 地址")

        # 屏蔽 LLM-only 域名：cherryin.cc 与内网 192.168.0.214:8802，仅允许做 LLM 网关
        if _host_is_llm_only(parsed.netloc):
            raise ValueError(
                f"该 URL 仅作为 LLM 网关，禁止注册为 skill 工具 endpoint: {parsed.netloc}"
            )

        normalized_url = parsed.geturl()
        for existing in self._skills.values():
            if existing.get("source_url") == normalized_url or (existing.get("config") or {}).get("endpoint") == normalized_url:
                raise ValueError(f"该 URL 对应的技能已安装: {existing.get('id')}")

        path_parts = [p for p in parsed.path.split("/") if p]
        slug = path_parts[-1] if path_parts else parsed.netloc.replace(".", "_")
        skill_name = re.sub(r"[^a-zA-Z0-9_]+", "_", slug).strip("_") or "external_skill"

        base_skill_id = f"skill_{skill_name}"
        skill_id = base_skill_id
        suffix = 2
        while skill_id in self._skills:
            skill_id = f"{base_skill_id}_{suffix}"
            suffix += 1

        display_name = slug.replace("-", " ").replace("_", " ").strip().title() or skill_name
        skill = {
            "id": skill_id,
            "name": skill_name,
            "display_name": display_name,
            "description": f"通过 URL 安装的外部技能：{normalized_url}",
            "category": "external",
            "protocol": "skillhub",
            "is_active": True,
            "is_builtin": False,
            "config": {"endpoint": normalized_url},
            "input_schema": {},
            "output_schema": {},
            "usage_count": 0,
            "created_at": datetime.now(),
            "source": "url",
            "source_url": normalized_url,
        }
        self._skills[skill_id] = skill
        self._persist_skill_to_db(skill)
        return skill

    # --------- skills CRUD ----------
    def list_skills(
        self,
        category: Optional[str] = None,
        protocol: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        skills = list(self._skills.values())

        if category:
            skills = [s for s in skills if s.get("category") == category]
        if protocol:
            skills = [s for s in skills if s.get("protocol") == protocol]
        if is_active is not None:
            skills = [s for s in skills if s.get("is_active") == is_active]
        if search:
            q = search.lower()
            skills = [
                s
                for s in skills
                if q in (s.get("name", "").lower())
                or q in (s.get("display_name", "").lower())
                or q in ((s.get("description") or "").lower())
            ]

        return skills

    def get_skill(self, skill_id: str) -> Optional[Dict[str, Any]]:
        return self._skills.get(skill_id)

    def create_skill(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # payload expects: name, display_name, description, category, protocol, config, input_schema, output_schema
        for s in self._skills.values():
            if s.get("name") == payload["name"]:
                raise ValueError("技能名称已存在")

        skill_id = f"skill_{payload['name']}"
        skill = {
            "id": skill_id,
            "name": payload["name"],
            "display_name": payload["display_name"],
            "description": payload.get("description"),
            "category": payload.get("category") or "general",
            "protocol": payload.get("protocol") or "builtin",
            "is_active": True,
            "is_builtin": False,
            "config": payload.get("config") or {},
            "input_schema": payload.get("input_schema") or {},
            "output_schema": payload.get("output_schema") or {},
            "usage_count": 0,
            "created_at": datetime.now(),
        }
        self._skills[skill_id] = skill
        self._persist_skill_to_db(skill)
        return skill

    def update_skill(self, skill_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        skill = self._skills.get(skill_id)
        if not skill:
            raise ValueError(f"技能不存在: {skill_id}")

        for k in ["display_name", "description", "config", "is_active"]:
            if k in updates and updates[k] is not None:
                skill[k] = updates[k]
        skill["updated_at"] = datetime.now()
        self._persist_skill_to_db(skill)
        return skill

    def delete_skill(self, skill_id: str) -> None:
        skill = self._skills.get(skill_id)
        if not skill:
            raise ValueError(f"技能不存在: {skill_id}")
        if skill.get("is_builtin"):
            raise ValueError("内置技能不能删除")
        del self._skills[skill_id]
        self._delete_skill_from_db(skill_id)

    # --------- executions ----------
    def get_execution(self, execution_id: str) -> Optional[Dict[str, Any]]:
        return self._executions.get(execution_id)

    async def execute_skill(
        self,
        skill_id: str,
        input_data: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        skill = self._skills.get(skill_id)
        if not skill:
            raise ValueError(f"技能不存在: {skill_id}")
        if not skill.get("is_active"):
            raise ValueError("技能未启用")

        execution_id = str(uuid.uuid4())
        start_time = datetime.now()
        self._executions[execution_id] = {
            "execution_id": execution_id,
            "skill_id": skill_id,
            "user_id": user_id,
            "input": input_data,
            "config": config or {},
            "conversation_id": conversation_id,
            "status": "running",
            "started_at": start_time,
        }

        try:
            protocol = skill.get("protocol")

            # 输入 schema 校验（轻量实现）
            self._validate_input_schema(skill, input_data)

            if protocol == "builtin":
                result = await self._execute_builtin(skill, input_data, conversation_id=conversation_id)
            elif protocol == "skillhub":
                result = await self._execute_skillhub(skill, input_data, config=config)
            elif protocol == "mcp":
                result = await self._execute_mcp(skill, input_data, config=config)
            elif protocol == "medical_api":
                result = await self._execute_medical_api(skill, input_data)
            else:
                raise ValueError(f"不支持的协议: {protocol}")

            duration = (datetime.now() - start_time).total_seconds()
            self._executions[execution_id].update(
                {
                    "status": "completed",
                    "result": result,
                    "duration_seconds": duration,
                    "completed_at": datetime.now(),
                }
            )
            skill["usage_count"] = skill.get("usage_count", 0) + 1
            skill["last_used_at"] = datetime.now()

            return {
                "skill_id": skill_id,
                "execution_id": execution_id,
                "success": True,
                "result": result,
                "duration_seconds": duration,
            }

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            self._executions[execution_id].update(
                {
                    "status": "failed",
                    "error": str(e),
                    "duration_seconds": duration,
                    "completed_at": datetime.now(),
                }
            )
            return {
                "skill_id": skill_id,
                "execution_id": execution_id,
                "success": False,
                "error": str(e),
                "duration_seconds": duration,
            }

    # --------- builtins ----------
    def _init_builtin_skills(self) -> None:
        """默认不再内置安装任何 Skill。

        用户需要在 Skills 页面通过在线发现、候选安装或 URL 手动安装所需 Skill。
        """
        return

    @staticmethod
    def _build_skill_prompt(skill_name: str, input_data: Dict[str, Any]) -> str:
        prompts = {
            "medical_diagnosis": f"请根据以下症状进行诊断分析：{input_data}",
            "drug_interaction": f"请检查以下药物的相互作用：{input_data}",
            "lab_interpretation": f"请解读以下检验结果：{input_data}",
            "symptom_checker": f"请分析以下症状：{input_data}",
            "dosage_calculator": f"请计算用药剂量：{input_data}",
        }
        return prompts.get(skill_name, f"请处理以下请求：{input_data}")

    async def _execute_builtin(self, skill: Dict[str, Any], input_data: Dict[str, Any], conversation_id: Optional[str] = None) -> Dict[str, Any]:
        from app.services.llm_service import llm_service

        prompt = self._build_skill_prompt(skill.get("name"), input_data)
        response = await llm_service.chat(
            [
                {"role": "system", "content": f"你是一个专业的医学{skill.get('display_name')}助手。"},
                {"role": "user", "content": prompt},
            ],
            session_id=conversation_id,
        )
        return {"skill": skill.get("name"), "output": response.get("content", ""), "raw_response": response}

    @staticmethod
    def _skillhub_slug_from_skill(skill: Dict[str, Any]) -> str:
        config = skill.get("config") or {}
        explicit_slug = config.get("slug") or skill.get("slug")
        if explicit_slug:
            return str(explicit_slug).strip()
        endpoint = config.get("endpoint") or skill.get("source_url") or ""
        if endpoint:
            parsed = urlparse(endpoint)
            parts = [p for p in parsed.path.split("/") if p]
            if parts:
                return parts[-1]
        return str(skill.get("name") or skill.get("id") or "").replace("skill_", "").replace("_", "-").strip()

    @staticmethod
    def _skillhub_cmd() -> str:
        configured = os.getenv("SOLO_SKILLHUB_CLI")
        if configured:
            return configured
        default_cmd = Path.home() / ".local" / "bin" / "skillhub.cmd"
        if default_cmd.exists():
            return str(default_cmd)
        return "skillhub"

    def _ensure_skillhub_local_pack(self, skill: Dict[str, Any]) -> Path:
        slug = self._skillhub_slug_from_skill(skill)
        if not slug:
            raise ValueError("SkillHub skill 无法解析 slug")
        target_dir = self._skillhub_store_dir / slug
        skill_md = target_dir / "SKILL.md"
        if skill_md.exists():
            return target_dir

        self._skillhub_store_dir.mkdir(parents=True, exist_ok=True)
        cmd = [
            self._skillhub_cmd(),
            "install",
            slug,
            "--dir",
            str(self._skillhub_store_dir),
            "--json",
            "--force",
        ]
        env = os.environ.copy()
        token = settings.SOLO_CLAWHUB_API_KEY or settings.SKILLHUB_API_KEY
        if token:
            env["SKILLHUB_SECRET"] = token
        completed = subprocess.run(cmd, capture_output=True, text=True, timeout=90, env=env)
        if completed.returncode != 0:
            raise ValueError(f"SkillHub CLI 安装失败: {completed.stderr or completed.stdout}")
        if not skill_md.exists():
            raise ValueError(f"SkillHub CLI 已运行但未找到本地 SKILL.md: {skill_md}")
        return target_dir

    async def _run_skillhub_markdown_with_llm(
        self,
        skill: Dict[str, Any],
        input_data: Dict[str, Any],
        skill_markdown: str,
        conversation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        from app.services.llm_service import llm_service

        response = await llm_service.chat(
            [
                {
                    "role": "system",
                    "content": (
                        f"你正在执行本地 SkillHub Skill：{skill.get('display_name') or skill.get('name')}。\n"
                        "严格遵循以下 SKILL.md 指令，但不要要求多轮澄清；如果输入不足，基于已知信息输出草案并标注假设与待确认项。\n\n"
                        f"{skill_markdown}"
                    ),
                },
                {
                    "role": "user",
                    "content": f"请执行该 Skill。输入 JSON：\n{json.dumps(input_data, ensure_ascii=False, indent=2)}",
                },
            ],
            session_id=conversation_id,
        )
        return {
            "skill": skill.get("name"),
            "output": response.get("content", ""),
            "raw_response": response,
            "execution_mode": "local_skillhub_pack",
        }

    async def _execute_skillhub(self, skill: Dict[str, Any], input_data: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        skill_dir = await asyncio.to_thread(self._ensure_skillhub_local_pack, skill)
        skill_md = skill_dir / "SKILL.md"
        skill_markdown = await asyncio.to_thread(skill_md.read_text, encoding="utf-8")
        merged_input = {**(input_data or {})}
        if config:
            merged_input["config"] = config
        return await self._run_skillhub_markdown_with_llm(skill, merged_input, skill_markdown)

    async def _execute_mcp(self, skill: Dict[str, Any], input_data: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        MCP/工具服务真实调用：
        - 约定 skill.config.endpoint 为可访问的 HTTP 地址
        - 请求体沿用 {input, config} 结构，便于与 SkillHub 统一
        """
        skill_config = skill.get("config") or {}
        endpoint = skill_config.get("endpoint")
        if not endpoint:
            raise ValueError("MCP endpoint未配置（请在技能 config 中设置 endpoint）")

        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(endpoint, json={"input": input_data, "config": config or {}, "skill_id": skill.get("id")})
            r.raise_for_status()
            return r.json()

    async def _execute_medical_api(self, skill: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        直接调用“医疗大模型后端”HTTP API（附件文档定义的 /chat /triage /write /clinical ...）

        约定：
        - 基础地址使用 settings.LLM_ENDPOINT（已规范为 base url，如 http://127.0.0.1:8802）
        - skill.config.path 指定路径
        - GET 直接返回 raw json
        - POST 返回 raw json，同时提供 output 字段便于聊天展示
        """
        cfg = skill.get("config") or {}
        path = cfg.get("path")
        method = (cfg.get("method") or "POST").upper()
        if not path:
            raise ValueError("medical_api skill 未配置 path")

        base = (settings.LLM_ENDPOINT or "").rstrip("/")
        url = f"{base}{path}"

        async with httpx.AsyncClient(timeout=60) as client:
            if method == "GET":
                r = await client.get(url)
                r.raise_for_status()
                return r.json()

            r = await client.post(url, json=input_data)
            r.raise_for_status()
            raw = r.json()

            # 统一输出字段，便于 ToolAgent → Orchestrator 聚合
            output = raw.get("response")
            if output is None:
                output = str(raw)

            return {"output": output, "raw_response": raw}

    # --------- schema validation (lightweight) ----------
    def _validate_input_schema(self, skill: Dict[str, Any], input_data: Dict[str, Any]) -> None:
        schema = skill.get("input_schema")
        if not schema:
            return
        self._validate_schema(input_data, schema, where=f"skill={skill.get('id')}")

    def _validate_schema(self, data: Any, schema: Dict[str, Any], where: str = "") -> None:
        """
        轻量 JSON Schema 校验（只覆盖本项目会用到的 subset）。
        支持：type/object/properties/required/array/items/string/number/integer/boolean
        """
        schema_type = schema.get("type")
        if not schema_type:
            return

        def err(msg: str) -> None:
            raise ValueError(f"输入不符合 schema: {msg}{(' (' + where + ')') if where else ''}")

        if schema_type == "object":
            if not isinstance(data, dict):
                err("期望 object")
            required = schema.get("required") or []
            for k in required:
                if k not in data:
                    err(f"缺少必填字段: {k}")
            props = schema.get("properties") or {}
            for k, prop_schema in props.items():
                if k in data and prop_schema:
                    self._validate_schema(data[k], prop_schema, where=f"{where}.{k}" if where else k)
            return

        if schema_type == "array":
            if not isinstance(data, list):
                err("期望 array")
            item_schema = schema.get("items") or {}
            for idx, item in enumerate(data):
                self._validate_schema(item, item_schema, where=f"{where}[{idx}]")
            return

        if schema_type == "string":
            if not isinstance(data, str):
                err("期望 string")
            return
        if schema_type == "boolean":
            if not isinstance(data, bool):
                err("期望 boolean")
            return
        if schema_type == "integer":
            if not isinstance(data, int):
                err("期望 integer")
            return
        if schema_type == "number":
            if not isinstance(data, (int, float)):
                err("期望 number")
            return

        # 未覆盖的类型直接放行
        return


# 全局单例
skill_registry = SkillRegistry()
