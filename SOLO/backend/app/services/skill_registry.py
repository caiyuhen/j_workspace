"""
Skill 注册与执行中心（单例）

目标：
1) 让 Skills API 与 ToolAgent 共用同一套技能注册/执行逻辑，避免重复与偏差
2) 统一 Skill 的协议执行：builtin / skillhub / mcp
3) MCP 协议改为真实 HTTP 调用（基于 skill.config.endpoint），未配置则明确报错
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
from app.config import settings

logger = logging.getLogger(__name__)


class SkillRegistry:
    def __init__(self):
        self._skills: Dict[str, Dict[str, Any]] = {}
        self._executions: Dict[str, Dict[str, Any]] = {}
        self._init_builtin_skills()

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
        return skill

    def update_skill(self, skill_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        skill = self._skills.get(skill_id)
        if not skill:
            raise ValueError(f"技能不存在: {skill_id}")

        for k in ["display_name", "description", "config", "is_active"]:
            if k in updates and updates[k] is not None:
                skill[k] = updates[k]
        skill["updated_at"] = datetime.now()
        return skill

    def delete_skill(self, skill_id: str) -> None:
        skill = self._skills.get(skill_id)
        if not skill:
            raise ValueError(f"技能不存在: {skill_id}")
        if skill.get("is_builtin"):
            raise ValueError("内置技能不能删除")
        del self._skills[skill_id]

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
        builtin_skills: List[Dict[str, Any]] = [
            {
                "id": "skill_medical_diagnosis",
                "name": "medical_diagnosis",
                "display_name": "医学诊断",
                "description": "基于症状进行疾病诊断分析，提供可能的诊断结果和建议",
                "category": "diagnosis",
                "protocol": "builtin",
                "is_active": True,
                "is_builtin": True,
                "config": {},
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "symptoms": {"type": "array", "items": {"type": "string"}},
                        "patient_info": {"type": "object"},
                    },
                    "required": ["symptoms"],
                },
                "output_schema": {"type": "object", "properties": {"diagnoses": {"type": "array"}, "recommendations": {"type": "array"}}},
                "usage_count": 0,
                "created_at": datetime.now(),
            },
            {
                "id": "skill_drug_interaction",
                "name": "drug_interaction",
                "display_name": "药物相互作用检查",
                "description": "检查多种药物之间的相互作用，提供用药安全建议",
                "category": "pharmacy",
                "protocol": "builtin",
                "is_active": True,
                "is_builtin": True,
                "config": {},
                "input_schema": {"type": "object", "properties": {"drugs": {"type": "array", "items": {"type": "string"}}}, "required": ["drugs"]},
                "output_schema": {"type": "object", "properties": {"interactions": {"type": "array"}, "recommendations": {"type": "array"}}},
                "usage_count": 0,
                "created_at": datetime.now(),
            },
            {
                "id": "skill_literature_search",
                "name": "literature_search",
                "display_name": "医学文献检索",
                "description": "检索PubMed、知网等医学文献数据库",
                "category": "research",
                "protocol": "skillhub",
                "is_active": True,
                "is_builtin": False,
                "config": {"endpoint": "https://api.skillhub.cn/skills/literature"},
                "input_schema": {
                    "type": "object",
                    "properties": {"query": {"type": "string"}, "sources": {"type": "array", "items": {"type": "string"}}, "limit": {"type": "integer", "default": 10}},
                    "required": ["query"],
                },
                "output_schema": {},
                "usage_count": 0,
                "created_at": datetime.now(),
            },
            {
                "id": "skill_clinical_guideline",
                "name": "clinical_guideline",
                "display_name": "临床指南查询",
                "description": "查询临床诊疗指南和专家共识",
                "category": "reference",
                "protocol": "skillhub",
                "is_active": True,
                "is_builtin": False,
                "config": {"endpoint": "https://api.skillhub.cn/skills/guideline"},
                "input_schema": {"type": "object", "properties": {"disease": {"type": "string"}, "type": {"type": "string", "enum": ["guideline", "consensus", "all"]}}, "required": ["disease"]},
                "output_schema": {},
                "usage_count": 0,
                "created_at": datetime.now(),
            },
            {
                "id": "skill_lab_interpretation",
                "name": "lab_interpretation",
                "display_name": "检验结果解读",
                "description": "解读临床检验报告，提供异常指标分析和建议",
                "category": "diagnosis",
                "protocol": "builtin",
                "is_active": True,
                "is_builtin": True,
                "config": {},
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string"},
                        "lab_results": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "value": {"type": "number"},
                                    "unit": {"type": "string"},
                                    "ref_range": {"type": "string"}
                                }
                            }
                        }
                    },
                    "required": []
                },
                "output_schema": {},
                "usage_count": 0,
                "created_at": datetime.now(),
            },
            {
                "id": "skill_medical_api_health",
                "name": "medical_api_health",
                "display_name": "医学服务健康检查",
                "description": "检查医学大模型后端服务健康状态（GET /health）",
                "category": "system",
                "protocol": "medical_api",
                "is_active": True,
                "is_builtin": True,
                "config": {"path": "/health", "method": "GET"},
                "input_schema": {"type": "object", "properties": {}, "required": []},
                "output_schema": {"type": "object"},
                "usage_count": 0,
                "created_at": datetime.now(),
            },
            {
                "id": "skill_medical_api_triage",
                "name": "medical_api_triage",
                "display_name": "智能分诊",
                "description": "多轮分诊（POST /triage），支持 session_id 上下文",
                "category": "triage",
                "protocol": "medical_api",
                "is_active": True,
                "is_builtin": True,
                "config": {"path": "/triage", "method": "POST"},
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "prompt": {"type": "string"},
                        "session_id": {"type": "string"},
                        "use_rag": {"type": "boolean"},
                    },
                    "required": ["prompt"],
                },
                "output_schema": {"type": "object"},
                "usage_count": 0,
                "created_at": datetime.now(),
            },
            {
                "id": "skill_medical_api_write",
                "name": "medical_api_write",
                "display_name": "医学写作",
                "description": "医学写作（POST /write），输出偏 Markdown",
                "category": "writing",
                "protocol": "medical_api",
                "is_active": True,
                "is_builtin": True,
                "config": {"path": "/write", "method": "POST"},
                "input_schema": {"type": "object", "properties": {"prompt": {"type": "string"}, "use_rag": {"type": "boolean"}}, "required": ["prompt"]},
                "output_schema": {"type": "object"},
                "usage_count": 0,
                "created_at": datetime.now(),
            },
            {
                "id": "skill_medical_api_clinical",
                "name": "medical_api_clinical",
                "display_name": "临床建议",
                "description": "循证临床建议（POST /clinical）",
                "category": "clinical",
                "protocol": "medical_api",
                "is_active": True,
                "is_builtin": True,
                "config": {"path": "/clinical", "method": "POST"},
                "input_schema": {"type": "object", "properties": {"prompt": {"type": "string"}, "use_rag": {"type": "boolean"}}, "required": ["prompt"]},
                "output_schema": {"type": "object"},
                "usage_count": 0,
                "created_at": datetime.now(),
            },
            {
                "id": "skill_medical_api_management_plan",
                "name": "medical_api_management_plan",
                "display_name": "个案管理计划",
                "description": "患者个案管理计划（POST /management_plan），支持 session_id",
                "category": "management",
                "protocol": "medical_api",
                "is_active": True,
                "is_builtin": True,
                "config": {"path": "/management_plan", "method": "POST"},
                "input_schema": {
                    "type": "object",
                    "properties": {"prompt": {"type": "string"}, "session_id": {"type": "string"}, "use_rag": {"type": "boolean"}, "return_rag_info": {"type": "boolean"}},
                    "required": ["prompt"],
                },
                "output_schema": {"type": "object"},
                "usage_count": 0,
                "created_at": datetime.now(),
            },
            {
                "id": "skill_medical_api_clinical_trial",
                "name": "medical_api_clinical_trial",
                "display_name": "临床实验设计",
                "description": "临床实验设计建议（POST /clinical_trial）",
                "category": "research",
                "protocol": "medical_api",
                "is_active": True,
                "is_builtin": True,
                "config": {"path": "/clinical_trial", "method": "POST"},
                "input_schema": {"type": "object", "properties": {"prompt": {"type": "string"}, "use_rag": {"type": "boolean"}}, "required": ["prompt"]},
                "output_schema": {"type": "object"},
                "usage_count": 0,
                "created_at": datetime.now(),
            },
            {
                "id": "skill_image_analysis",
                "name": "image_analysis",
                "display_name": "医学影像分析",
                "description": "分析X光、CT、MRI等医学影像（需要配置 MCP endpoint）",
                "category": "imaging",
                "protocol": "mcp",
                "is_active": True,
                "is_builtin": False,
                "config": {
                    "mcp_server": "medical-imaging-mcp",
                    # 真实 MCP/工具服务地址需部署后填写，例如：http://127.0.0.1:9001/invoke
                    # "endpoint": "http://127.0.0.1:9001/invoke"
                },
                "input_schema": {"type": "object", "properties": {"image_url": {"type": "string"}, "image_type": {"type": "string"}}, "required": ["image_url", "image_type"]},
                "output_schema": {},
                "usage_count": 0,
                "created_at": datetime.now(),
            },
            {
                "id": "skill_symptom_checker",
                "name": "symptom_checker",
                "display_name": "症状自查",
                "description": "根据症状进行初步健康评估",
                "category": "consultation",
                "protocol": "builtin",
                "is_active": True,
                "is_builtin": True,
                "config": {},
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string"},
                        "symptoms": {"type": "array", "items": {"type": "string"}},
                        "duration": {"type": "string"}
                    },
                    "required": []
                },
                "output_schema": {},
                "usage_count": 0,
                "created_at": datetime.now(),
            },
            {
                "id": "skill_dosage_calculator",
                "name": "dosage_calculator",
                "display_name": "用药剂量计算",
                "description": "根据患者信息计算药物剂量",
                "category": "pharmacy",
                "protocol": "builtin",
                "is_active": True,
                "is_builtin": True,
                "config": {},
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string"},
                        "drug_name": {"type": "string"},
                        "patient_weight": {"type": "number"},
                        "patient_age": {"type": "integer"},
                        "indication": {"type": "string"}
                    },
                    "required": []
                },
                "output_schema": {},
                "usage_count": 0,
                "created_at": datetime.now(),
            },
        ]

        for s in builtin_skills:
            self._skills[s["id"]] = s

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

    async def _execute_skillhub(self, skill: Dict[str, Any], input_data: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        endpoint = (skill.get("config") or {}).get("endpoint")
        if not endpoint:
            raise ValueError("SkillHub endpoint未配置")
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(endpoint, json={"input": input_data, "config": config or {}})
            r.raise_for_status()
            return r.json()

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
