"""后台任务执行辅助服务 - 纯同步版本，完全不用 asyncio。"""
from __future__ import annotations

import json
import logging
import re
import threading
import time
import traceback
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional

import requests

from app.config import settings
from app.models import Task, TaskStatus, SubTask, AgentType
from app.services.artifact_service import artifact_service

logger = logging.getLogger(__name__)


def _sync_db_url(database_url: str) -> str:
    if database_url.startswith("sqlite+aiosqlite://"):
        return database_url.replace("sqlite+aiosqlite://", "sqlite://", 1)
    return database_url


def build_task_started_result(task_id: str) -> Dict[str, Any]:
    """构造任务已启动的非阻塞响应。"""
    return {
        "content": "任务已创建，正在后台执行。",
        "task_id": task_id,
        "task_status": TaskStatus.RUNNING.value,
        "async_execution": True,
        "waiting_for_skill": False,
        "skill_resolution": None,
        "subtasks": [],
        "artifacts": [],
    }


def should_poll_task(status: str) -> bool:
    """判断前端是否应继续轮询任务。"""
    return (status or "").lower() in {TaskStatus.PENDING.value, TaskStatus.RUNNING.value}


def _load_model_configs() -> list:
    """读取模型配置。"""
    config_path = Path(__file__).resolve().parents[2] / "model_configs.json"
    if not config_path.exists():
        return []
    try:
        with config_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception as exc:
        logger.warning("读取模型配置失败: %s", exc)
        return []


def _resolve_sync_llm_request(model: Optional[str]) -> Dict[str, Any]:
    """解析同步后台任务应使用的 LLM 端点、真实模型名和密钥。"""
    configs = _load_model_configs()
    selected = None
    if model:
        selected = next((cfg for cfg in configs if cfg.get("name") == model), None)
    if not selected:
        selected = next((cfg for cfg in configs if cfg.get("default")), None)

    if selected:
        endpoint = (selected.get("endpoint") or settings.LLM_ENDPOINT).rstrip("/")
        if endpoint.endswith("/chat/completions"):
            endpoint = endpoint[:-len("/chat/completions")]
        if endpoint.endswith("/chat"):
            endpoint = endpoint[:-5]
        return {
            "selected_name": selected.get("name") or model,
            "api_type": selected.get("type", "openai"),
            "endpoint": endpoint,
            "payload_model": selected.get("model") or selected.get("name") or settings.LLM_MODEL,
            "api_key": selected.get("api_key") or settings.LLM_API_KEY,
        }

    endpoint = settings.LLM_ENDPOINT.rstrip("/")
    if endpoint.endswith("/chat/completions"):
        endpoint = endpoint[:-len("/chat/completions")]
    if endpoint.endswith("/chat"):
        endpoint = endpoint[:-5]
    return {
        "selected_name": model or settings.LLM_MODEL,
        "api_type": "openai",
        "endpoint": endpoint,
        "payload_model": model or settings.LLM_MODEL,
        "api_key": settings.LLM_API_KEY,
    }


def _call_llm_sync(messages: list, model: Optional[str], conversation_id: str, timeout: int = 60) -> str:
    """同步调用前端所选 LLM 模型，返回响应内容。

    若环境变量 ``SOLO_LLM_GATEWAY`` 已配置，则优先走 LLMGateway（cherryin / inner）；
    任何网关层错误都会回退到原 _resolve_sync_llm_request 路径，避免单点故障。
    """
    try:
        from app.services.llm_gateway import LLMGatewayError, build_llm_gateway
        gateway = build_llm_gateway()
    except Exception as exc:  # noqa: BLE001
        logger.warning("LLM 网关初始化失败，回退默认调用: %s", exc)
        gateway = None
    if gateway is not None:
        try:
            text = gateway.chat(messages, timeout=timeout)
            logger.info("🤖 LLM 网关[%s] 响应长度：%d 字符", gateway.name, len(text or ""))
            return text or ""
        except LLMGatewayError as exc:
            logger.warning("LLM 网关调用失败，回退默认调用: %s", exc)

    request_cfg = _resolve_sync_llm_request(model)
    endpoint = request_cfg["endpoint"]
    url = f"{endpoint}/chat/completions"
    payload = {
        "model": request_cfg["payload_model"],
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 8000,
    }

    # 重试机制：最多重试 2 次
    last_error = None
    for attempt in range(3):
        logger.info(
            "🤖 调用所选 LLM (尝试 %d/3): selected=%s, payload_model=%s",
            attempt + 1,
            request_cfg["selected_name"],
            request_cfg["payload_model"],
        )
        try:
            headers = {"Content-Type": "application/json"}
            if request_cfg.get("api_key"):
                headers["Authorization"] = f"Bearer {request_cfg['api_key']}"
            resp = requests.post(url, json=payload, headers=headers, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            choice = data.get("choices", [{}])[0]
            message = choice.get("message", {})
            content = message.get("content", "")
            # 如果 content 为空，尝试从 reasoning_content 中提取
            if not content:
                reasoning_content = message.get("reasoning_content", "")
                content = reasoning_content
            logger.info("🤖 LLM 响应长度：%d 字符", len(content))
            return content
        except requests.exceptions.Timeout:
            last_error = f"LLM 调用超时 ({timeout}s)"
            logger.warning("🤖 %s (尝试 %d/3)", last_error, attempt + 1)
            time.sleep(2 ** attempt)
        except Exception as exc:
            last_error = f"LLM 调用失败：{exc}"
            logger.warning("🤖 %s (尝试 %d/3)", last_error, attempt + 1)
            time.sleep(2 ** attempt)

    logger.error("🤖 LLM 调用最终失败：%s", last_error)
    raise RuntimeError(last_error or "LLM 调用失败，未返回有效内容")


def _require_generated_content(content: str, step_name: str) -> str:
    """校验 LLM 子任务必须返回有效内容。"""
    normalized = (content or "").strip()
    if not normalized:
        raise RuntimeError(f"{step_name}未返回有效内容，任务已终止，未生成交付物。请重试或更换模型。")
    return normalized


def _select_artifact_content(final_content: str, outline_content: str, prompt: str) -> str:
    """选择交付物内容；禁止用原始提示词生成正式交付物。"""
    if (final_content or "").strip():
        return final_content.strip()
    if (outline_content or "").strip():
        return outline_content.strip()
    raise RuntimeError("正文生成失败，未生成有效交付物。系统已阻止使用原始提示词生成空壳文件。")


DEFAULT_TASK_PLAN = [
    {"name": "理解任务", "type": "planning", "description": "分析任务目标和需求"},
    {"name": "生成大纲", "type": "llm", "description": "生成结构化大纲"},
    {"name": "生成完整正文", "type": "llm", "description": "基于大纲生成完整正文"},
    {"name": "生成交付物", "type": "artifact", "description": "生成最终交付文件"},
]

_ALLOWED_STEP_TYPES = {"planning", "llm", "tool", "artifact"}


def _list_installed_skill_ids() -> list:
    """返回当前已安装/已注册的 skill_id 列表，供规划与校验使用。"""
    try:
        from app.services.skill_registry import skill_registry
        return sorted(skill_registry._skills.keys())
    except Exception as exc:
        logger.warning("读取已安装技能列表失败: %s", exc)
        return []


def _list_installed_skills_with_schema() -> List[Dict[str, Any]]:
    """返回每个已安装 skill 的 {id, display_name, description, required, optional} 摘要，供规划提示词注入。"""
    try:
        from app.services.skill_registry import skill_registry
    except Exception as exc:
        logger.warning("读取已安装技能详情失败: %s", exc)
        return []

    summary: List[Dict[str, Any]] = []
    for skill_id in sorted(skill_registry._skills.keys()):
        skill = skill_registry._skills[skill_id]
        schema = skill.get("input_schema") or {}
        properties = (schema.get("properties") or {}) if isinstance(schema, dict) else {}
        required = list((schema.get("required") or [])) if isinstance(schema, dict) else []
        optional = [name for name in properties.keys() if name not in required]
        summary.append({
            "id": skill_id,
            "display_name": skill.get("display_name") or skill.get("name") or skill_id,
            "description": (skill.get("description") or "").strip(),
            "required": required,
            "optional": optional,
        })
    return summary


def _format_skills_for_prompt(skills: List[Dict[str, Any]]) -> str:
    """把已安装技能详情格式化为规划提示词中的 Markdown 列表。"""
    if not skills:
        return "(当前没有已安装技能，禁止使用 type=tool)"
    lines = []
    for s in skills:
        required_text = ", ".join(s["required"]) if s["required"] else "(无)"
        optional_text = ", ".join(s["optional"]) if s["optional"] else "(无)"
        desc = s["description"] or "(无描述)"
        lines.append(
            f"- id: {s['id']}\n"
            f"  display_name: {s['display_name']}\n"
            f"  description: {desc}\n"
            f"  input_schema:\n"
            f"    required: {required_text}\n"
            f"    optional: {optional_text}"
        )
    return "\n".join(lines)


def _normalize_plan_step(step: Any, installed_skill_ids: Optional[set] = None) -> Optional[Dict[str, Any]]:
    """把 LLM 输出的单个步骤规范化为可执行 step；不合法返回 None。

    如果 step 是 type=tool 但 skill_id 不在已安装列表里，先尝试调用 SkillResolver 解析：
    - 命中本地匹配 → 改写 skill_id；
    - 通过远程仓库自动安装成功 → 改写 skill_id；
    - 否则降级为 type=llm 普通步骤，不阻断任务。
    """
    if not isinstance(step, dict):
        return None
    name = (step.get("name") or "").strip()
    step_type = (step.get("type") or "").strip().lower()
    if not name or step_type not in _ALLOWED_STEP_TYPES:
        return None

    normalized: Dict[str, Any] = {
        "name": name,
        "type": step_type,
        "description": (step.get("description") or "").strip() or name,
    }
    if step_type == "tool":
        skill_id = (step.get("skill_id") or "").strip()
        if not skill_id:
            return None
        if installed_skill_ids is not None and skill_id not in installed_skill_ids:
            # 先尝试 SkillResolver；命中即改写 skill_id 并继续作为 tool 执行
            from app.services.skill_resolver import skill_resolver

            resolution = skill_resolver.resolve(name=name, description=normalized["description"])
            if resolution.skill_id and resolution.status in {"local", "auto_installed"}:
                logger.info(
                    "规划阶段未安装 skill_id=%s 已被 resolver 改写为 %s（%s）",
                    skill_id, resolution.skill_id, resolution.status,
                )
                installed_skill_ids.add(resolution.skill_id)
                normalized["skill_id"] = resolution.skill_id
                normalized["input"] = step.get("input") or {}
                normalized["config"] = step.get("config") or {}
                normalized["resolver_status"] = resolution.status
                normalized["resolver_message"] = resolution.message
                return normalized

            # 兜底：降级为 llm 步骤，避免任务因“技能不存在”失败
            logger.info(
                "规划阶段杜撰的未安装 skill_id=%s 已降级为 llm 步骤: %s（resolver: %s）",
                skill_id, name, resolution.message,
            )
            normalized["type"] = "llm"
            normalized["resolver_status"] = "not_available"
            normalized["resolver_message"] = resolution.message
            return normalized
        normalized["skill_id"] = skill_id
        normalized["input"] = step.get("input") or {}
        normalized["config"] = step.get("config") or {}
    return normalized


def _parse_llm_plan(text: str, installed_skill_ids: Optional[set] = None) -> Optional[list]:
    """解析 LLM 返回的 JSON 计划，返回规范化后的步骤列表。"""
    if not text:
        return None
    payload = text.strip()
    fence_match = re.search(r"```(?:json)?\s*(.*?)```", payload, flags=re.DOTALL | re.IGNORECASE)
    if fence_match:
        payload = fence_match.group(1).strip()
    array_match = re.search(r"\[.*\]", payload, flags=re.DOTALL)
    if array_match:
        payload = array_match.group(0)
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, list) or not data:
        return None
    normalized: list = []
    for item in data:
        step = _normalize_plan_step(item, installed_skill_ids=installed_skill_ids)
        if step:
            normalized.append(step)
    return normalized or None


def _ensure_artifact_step(plan: list) -> list:
    """确保计划末尾一定有 artifact 步骤，否则任务无法产出交付物。"""
    if any(step.get("type") == "artifact" for step in plan):
        return plan
    plan = list(plan)
    plan.append({
        "name": "生成交付物",
        "type": "artifact",
        "description": "生成最终交付文件",
    })
    return plan


def _build_task_plan(prompt: str, model: Optional[str], conversation_id: str) -> list:
    """构造任务计划：调用 LLM 生成 → JSON 校验 → 强制注入 artifact 步骤；失败回退默认计划。"""
    skills_with_schema = _list_installed_skills_with_schema()
    installed_skill_ids = {s["id"] for s in skills_with_schema}
    skills_hint = _format_skills_for_prompt(skills_with_schema)
    plan_request_messages = [
        {
            "role": "system",
            "content": (
                "你是医学研究任务规划助手。根据用户任务，输出一个 JSON 数组作为执行计划。"
                "每一步是 {name, type, description} 对象，可选字段 skill_id、input、config。"
                "type 仅限 planning/llm/tool/artifact。"
                "type=tool 必须包含 skill_id，且 skill_id 只能从下面这份“已安装技能列表”里选；不要发明新的 skill_id。"
                "type=tool 的 input 字段必须包含该技能 input_schema 中所有 required 字段；"
                "input 不允许是空对象 {}；如果你无法填齐所有必填字段，请改用 type=llm。"
                "如果没有合适的已安装技能，请使用 type=llm 而不是 type=tool。"
                "最后一步必须是 type=artifact。步数 3 到 10。"
                "只输出 JSON 数组，不要解释，不要 Markdown 之外的文字。\n\n"
                f"已安装技能列表（含 input_schema）:\n{skills_hint}"
            ),
        },
        {"role": "user", "content": f"任务: {prompt}\n请直接给出 JSON 计划数组。"},
    ]
    try:
        response = _call_llm_sync(plan_request_messages, model, conversation_id, timeout=60)
    except Exception as exc:
        logger.warning("规划阶段 LLM 调用失败，回退默认计划: %s", exc)
        return list(DEFAULT_TASK_PLAN)

    parsed = _parse_llm_plan(response, installed_skill_ids=installed_skill_ids)
    if not parsed:
        logger.info("LLM 计划解析失败或为空，回退默认计划。原始响应=%s", (response or "")[:200])
        return list(DEFAULT_TASK_PLAN)
    return _ensure_artifact_step(parsed)


_endpoint_probe_cache: Dict[str, Dict[str, Any]] = {}
_PROBE_CACHE_TTL_SECONDS = 300  # 5 分钟


def _probe_endpoint_supports_post(url: str) -> Dict[str, Any]:
    """探测 endpoint 是否真的接受 POST。

    - 仅发 OPTIONS（不带 body），获取 Allow 头判断；
    - 5 分钟内相同 url 命中缓存；
    - 任何异常均判定为不支持 POST，避免反复尝试。
    返回：{post_supported: bool, status: int|None, allow: str|None, error: str|None}
    """
    import urllib.request
    import urllib.error

    now = time.time()
    cached = _endpoint_probe_cache.get(url)
    if cached and now - cached.get("_at", 0) < _PROBE_CACHE_TTL_SECONDS:
        return cached["data"]

    inner = globals().get("_probe_endpoint_supports_post_inner")
    if callable(inner):
        result = inner(url)
    else:
        result = {"post_supported": False, "status": None, "allow": None, "error": None}
        try:
            req = urllib.request.Request(url, method="OPTIONS")
            with urllib.request.urlopen(req, timeout=5) as resp:
                allow = (resp.headers.get("Allow") or "").upper()
                result["status"] = resp.status
                result["allow"] = allow
                result["post_supported"] = "POST" in allow
        except urllib.error.HTTPError as e:
            allow = (e.headers.get("Allow") if e.headers else "" or "").upper()
            result["status"] = e.code
            result["allow"] = allow
            # OPTIONS 405 时仍可能允许 POST，保守按 Allow 头判断；缺失即视为不支持
            result["post_supported"] = "POST" in allow
        except Exception as exc:  # noqa: BLE001
            result["error"] = str(exc)
            result["post_supported"] = False

    _endpoint_probe_cache[url] = {"_at": now, "data": result}
    return result


_AUTO_FILL_FIELD_ALIASES = {
    "query": ("prompt", "description", "topic"),
    "topic": ("prompt", "description"),
    "question": ("prompt", "description"),
    "prompt": ("prompt", "description"),
    "context": ("previous_outputs", "prompt"),
    "study_topic": ("prompt", "description"),
    "research_topic": ("prompt", "description"),
    "disease": ("prompt", "description"),
    "input_text": ("prompt", "description"),
    "text": ("prompt", "description"),
}


def _autofill_skill_input(skill_id: str, given: Dict[str, Any], description: str,
                          prompt: str, previous_outputs: List[str]) -> Dict[str, Any]:
    """根据 skill 的 input_schema 自动补全 input 中缺失的必填字段。

    优先策略：
    1. 已有值不覆盖。
    2. 常见字段（query/topic/prompt 等）→ 任务提示词或本步描述。
    3. 上下文相关字段（context）→ 上一步输出。
    4. 仍补不齐的字段保持缺失，由调用方决定是否降级。
    """
    try:
        from app.services.skill_registry import skill_registry
    except Exception:
        return given
    skill = skill_registry.get_skill(skill_id)
    if not isinstance(skill, dict):
        return given
    schema = skill.get("input_schema") or {}
    required = list(schema.get("required") or []) if isinstance(schema, dict) else []
    if not required:
        return given

    filled = dict(given or {})
    sources = {
        "prompt": (prompt or "").strip(),
        "description": (description or "").strip(),
        "topic": (description or prompt or "").strip(),
        "previous_outputs": "\n\n".join(p for p in (previous_outputs or []) if p)[-2000:],
    }
    for field in required:
        if field in filled and filled[field] not in (None, "", [], {}):
            continue
        for alias in _AUTO_FILL_FIELD_ALIASES.get(field, ()):
            value = sources.get(alias)
            if value:
                filled[field] = value
                break
        if field in filled:
            continue
        # 通用兜底：用任务提示词补字符串型字段
        properties = (schema.get("properties") or {}) if isinstance(schema, dict) else {}
        prop = properties.get(field) or {}
        if prop.get("type") in (None, "string"):
            fallback = sources["prompt"] or sources["description"]
            if fallback:
                filled[field] = fallback
    return filled


def _execute_skill_step(step: dict, user_id: str, conversation_id: str,
                         prompt: str = "", previous_outputs: Optional[List[str]] = None) -> dict:
    """同步执行 type=tool 的子任务，调用 skill_registry.execute_skill。

    在调用前会按 input_schema 做最小预校验：
    - input 缺必填字段 → 用任务提示词/上一步输出自动补全
    - 仍缺必填字段 → 抛 RuntimeError，由上层按 A 策略降级处理
    """
    import asyncio
    from app.services.skill_registry import skill_registry

    skill_id = step.get("skill_id")
    if not skill_id:
        raise RuntimeError("tool 步骤缺少 skill_id，无法调用已安装的技能。")

    skill_input = step.get("input") or {}
    skill_config = step.get("config") or {}

    skill_input = _autofill_skill_input(
        skill_id=skill_id,
        given=skill_input,
        description=step.get("description") or "",
        prompt=prompt,
        previous_outputs=previous_outputs or [],
    )
    step["input"] = skill_input  # 把补全后的入参写回 step，方便审计/前端展示

    skill = skill_registry.get_skill(skill_id) or {}
    schema = skill.get("input_schema") or {}
    required = list(schema.get("required") or []) if isinstance(schema, dict) else []
    missing = [field for field in required if not skill_input.get(field)]
    if missing:
        raise RuntimeError(
            f"技能 {skill_id} 缺少必填字段 {missing}，已尝试自动补全仍不完整，按 A 策略降级处理。"
        )

    # 选项 3：调用前探测 endpoint 是否支持 POST；不支持时不发起业务请求，直接抛错以便上层 LLM 兑底
    endpoint_url = ""
    config_dict = skill.get("config") or {}
    if isinstance(config_dict, dict):
        endpoint_url = (config_dict.get("endpoint") or "").strip()
    protocol = (skill.get("protocol") or "").lower()

    # 第一道防线：LLM-only 域名禁止作为 skill 工具 endpoint
    if endpoint_url:
        try:
            from urllib.parse import urlparse
            from app.services.skill_registry import _host_is_llm_only
            netloc = urlparse(endpoint_url).netloc
            if _host_is_llm_only(netloc):
                raise RuntimeError(
                    f"技能 {skill_id} 的 endpoint host={netloc} 仅作为 LLM 网关，禁止当作工具 API 调用。"
                )
        except RuntimeError:
            raise
        except Exception:  # noqa: BLE001
            pass

    if endpoint_url and protocol in {"skillhub", "openapi", "http", "openai"}:
        probe = _probe_endpoint_supports_post(endpoint_url)
        if not probe.get("post_supported"):
            allow = probe.get("allow") or "(未知)"
            status = probe.get("status")
            err = probe.get("error")
            detail = f"OPTIONS={status} Allow={allow}"
            if err:
                detail += f" error={err}"
            raise RuntimeError(
                f"技能 {skill_id} 的远程 endpoint 不支持 POST（{detail}），已跳过远程调用。"
            )


    coro = skill_registry.execute_skill(
        skill_id=skill_id,
        input_data=skill_input,
        config=skill_config,
        user_id=user_id,
        conversation_id=conversation_id,
    )
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            response = loop.run_until_complete(coro)
        finally:
            loop.close()
            asyncio.set_event_loop(None)
    except Exception as exc:
        raise RuntimeError(f"调用技能 {skill_id} 异常: {exc}") from exc

    if not response.get("success"):
        raise RuntimeError(f"技能 {skill_id} 执行失败: {response.get('error') or '未知错误'}")
    return response


def _run_task_in_thread(
    task_id: str,
    user_id: str,
    conversation_id: str,
    prompt: str,
    model: Optional[str],
    deliverable_format: str,
) -> None:
    """在独立线程中纯同步执行任务。"""
    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import sessionmaker

    sync_url = _sync_db_url(settings.DATABASE_URL)
    logger.info("🚀 后台线程启动: task_id=%s", task_id)

    engine = create_engine(sync_url, connect_args={"check_same_thread": False})
    Session = sessionmaker(bind=engine)

    with Session() as db:
        try:
            task = db.execute(select(Task).where(Task.id == task_id)).scalar_one_or_none()
            if not task:
                logger.error("❌ 后台任务不存在: %s", task_id)
                return

            logger.info("✅ 找到任务: %s", task.title[:60])

            # Plan
            plan_steps = _build_task_plan(prompt, model, conversation_id)

            task.config = {**(task.config or {}), "model": model, "deliverable_format": deliverable_format}
            task.started_at = task.started_at or datetime.now()
            task.status = TaskStatus.RUNNING
            db.flush()
            db.commit()
            logger.info("📝 任务配置已保存: %d 步", len(plan_steps))

            # Create subtasks
            subtask_records = []
            for index, step in enumerate(plan_steps, 1):
                step_input: Dict[str, Any] = {"step_type": step["type"], "order": index, "prompt": prompt}
                if step.get("skill_id"):
                    step_input["skill_id"] = step["skill_id"]
                    step_input["input"] = step.get("input") or {}
                if step.get("resolver_status"):
                    step_input["resolver_status"] = step["resolver_status"]
                    step_input["resolver_message"] = step.get("resolver_message")
                subtask = SubTask(
                    id=f"{task_id}-sub-{index}",
                    task_id=task_id,
                    name=step["name"],
                    description=step.get("description"),
                    status=TaskStatus.PENDING,
                    input_data=step_input,
                    depends_on=[],
                )
                db.add(subtask)
                subtask_records.append(subtask)
            db.flush()
            db.commit()
            logger.info("📋 子任务已创建: %d 个", len(subtask_records))

            outline_content = ""
            final_content = ""
            artifacts = []
            previous_outputs: List[str] = []

            for subtask, step in zip(subtask_records, plan_steps):
                logger.info("▶️ 开始: %s", step["name"])
                subtask.status = TaskStatus.RUNNING
                subtask.started_at = datetime.now()
                db.flush()
                db.commit()

                try:
                    if step["type"] == "planning":
                        subtask.output_data = {"goal": prompt, "plan": plan_steps}
                        time.sleep(0.1)

                    elif step["type"] == "llm" and step["name"] == "生成大纲":
                        outline_prompt = f"""请为下面任务生成结构化大纲，输出 Markdown。

任务：{prompt}
交付物格式：{deliverable_format}"""
                        response = _call_llm_sync(
                            [{"role": "user", "content": outline_prompt}],
                            model=model,
                            conversation_id=conversation_id,
                        )
                        outline_content = _require_generated_content(response, "生成大纲")
                        subtask.output_data = {"content": outline_content}
                        previous_outputs.append(outline_content)

                    elif step["type"] == "llm" and step["name"] == "生成完整正文":
                        body_prompt = f"""请基于任务和大纲生成完整正文，输出可直接转换为 {deliverable_format} 文件的 Markdown 内容。

任务：{prompt}

大纲：
{outline_content}

要求：
1. 内容完整，不要只给建议。
2. 包含标题、目标、主体内容、结论/下一步。
3. 如适合表格，请使用 Markdown 表格。"""
                        response = _call_llm_sync(
                            [{"role": "user", "content": body_prompt}],
                            model=model,
                            conversation_id=conversation_id,
                        )
                        final_content = _require_generated_content(response, "生成完整正文")
                        subtask.output_data = {"content": final_content}
                        previous_outputs.append(final_content)

                    elif step["type"] == "llm":
                        # 通用 llm 步骤：把任务+本步描述+上一步输出喂给模型，作为补充内容
                        section_prompt = (
                            f"任务：{prompt}\n\n"
                            f"当前步骤：{step.get('name')}\n"
                            f"步骤说明：{step.get('description') or step.get('name')}\n"
                            f"已有大纲：\n{outline_content or '(尚未生成大纲)'}\n\n"
                            "请用 Markdown 输出本步骤的内容，不要只给建议；如适合可包含表格。"
                        )
                        response = _call_llm_sync(
                            [{"role": "user", "content": section_prompt}],
                            model=model,
                            conversation_id=conversation_id,
                        )
                        section_text = (response or "").strip()
                        subtask.output_data = {"content": section_text}
                        if section_text:
                            previous_outputs.append(section_text)
                            if final_content:
                                final_content = final_content.rstrip() + f"\n\n## {step.get('name')}\n\n{section_text}\n"
                            else:
                                final_content = section_text

                    elif step["type"] == "tool":
                        try:
                            skill_response = _execute_skill_step(
                                step,
                                user_id=user_id,
                                conversation_id=conversation_id,
                                prompt=prompt,
                                previous_outputs=previous_outputs,
                            )
                            subtask.output_data = {
                                "skill_id": skill_response.get("skill_id"),
                                "execution_id": skill_response.get("execution_id"),
                                "result": skill_response.get("result"),
                                "duration_seconds": skill_response.get("duration_seconds"),
                                "input": step.get("input") or {},
                            }
                            result_text = skill_response.get("result")
                            if isinstance(result_text, str) and result_text.strip():
                                previous_outputs.append(result_text)
                        except Exception as tool_exc:
                            # 方案 B：tool 步骤失败时自动用 LLM 重做该步骤，子任务最终 COMPLETED 但保留原始错误
                            logger.warning(
                                "tool 步骤失败，按 B 策略尝试 LLM 兜底: name=%s, skill_id=%s, err=%s",
                                step.get("name"), step.get("skill_id"), tool_exc,
                            )
                            fallback_prompt = (
                                f"任务：{prompt}\n\n"
                                f"当前步骤：{step.get('name')}\n"
                                f"步骤说明：{step.get('description') or step.get('name')}\n"
                                f"原计划调用技能：{step.get('skill_id')}（已失败，错误：{tool_exc}）\n"
                                f"已有上下文：\n{outline_content or '(尚未生成大纲)'}\n\n"
                                "请用 Markdown 输出本步骤的内容，等同于该技能本应给出的结果；"
                                "不要解释失败原因，直接给出可用的内容；如适合可包含表格。"
                            )
                            try:
                                fallback_response = _call_llm_sync(
                                    [{"role": "user", "content": fallback_prompt}],
                                    model=model,
                                    conversation_id=conversation_id,
                                )
                            except Exception as llm_exc:
                                # 兜底 LLM 也失败 → 退回 A 策略：仅该子任务 FAILED，后续步骤继续
                                logger.warning(
                                    "B 策略中 LLM 兜底也失败，退回 A 策略：name=%s, llm_err=%s",
                                    step.get("name"), llm_exc,
                                )
                                subtask.status = TaskStatus.FAILED
                                subtask.error_message = f"{tool_exc}（LLM 兜底也失败：{llm_exc}）"
                                subtask.completed_at = datetime.now()
                                subtask.output_data = {
                                    "skill_id": step.get("skill_id"),
                                    "input": step.get("input") or {},
                                    "error": str(tool_exc),
                                    "fallback": "llm_fallback_also_failed",
                                }
                                db.flush()
                                db.commit()
                                continue

                            fallback_text = (fallback_response or "").strip()
                            if not fallback_text:
                                # LLM 给空 → 视作失败，按 A 策略继续
                                logger.warning("B 策略中 LLM 兜底返回空文本，退回 A 策略：name=%s", step.get("name"))
                                subtask.status = TaskStatus.FAILED
                                subtask.error_message = f"{tool_exc}（LLM 兜底返回空内容）"
                                subtask.completed_at = datetime.now()
                                subtask.output_data = {
                                    "skill_id": step.get("skill_id"),
                                    "input": step.get("input") or {},
                                    "error": str(tool_exc),
                                    "fallback": "llm_fallback_empty",
                                }
                                db.flush()
                                db.commit()
                                continue

                            # 成功兜底：累计到 final_content，便于 artifact 使用
                            previous_outputs.append(fallback_text)
                            if final_content:
                                final_content = final_content.rstrip() + f"\n\n## {step.get('name')}\n\n{fallback_text}\n"
                            else:
                                final_content = fallback_text

                            subtask.status = TaskStatus.COMPLETED
                            subtask.completed_at = datetime.now()
                            subtask.output_data = {
                                "skill_id": step.get("skill_id"),
                                "input": step.get("input") or {},
                                "error": str(tool_exc),
                                "fallback": "llm_after_skill_error",
                                "content": fallback_text,
                            }
                            db.flush()
                            db.commit()
                            continue

                    elif step["type"] == "artifact":
                        content = _select_artifact_content(final_content, outline_content, prompt)
                        artifact = artifact_service.create_artifact(
                            user_id=user_id,
                            conversation_id=conversation_id,
                            task_id=task_id,
                            title=task.title or prompt[:80] or "任务交付物",
                            content=content,
                            artifact_format=deliverable_format,
                        )
                        artifacts = [_serialize_artifact(artifact)]
                        subtask.output_data = {"content": content, "format": deliverable_format, "artifacts": artifacts}

                    subtask.status = TaskStatus.COMPLETED
                    subtask.completed_at = datetime.now()
                    db.flush()
                    db.commit()
                    logger.info("✅ 完成: %s", step["name"])

                except Exception as exc:
                    subtask.status = TaskStatus.FAILED
                    subtask.error_message = str(exc)
                    subtask.completed_at = datetime.now()
                    task.status = TaskStatus.FAILED
                    task.error_message = str(exc)
                    task.completed_at = datetime.now()
                    task.result = {
                        "content": final_content,
                        "plan": plan_steps,
                        "subtasks": [
                            {
                                "id": s.id,
                                "name": s.name,
                                "status": _enum_value(s.status),
                            }
                            for s in subtask_records
                        ],
                        "artifacts": artifacts,
                        "error": str(exc),
                    }
                    db.flush()
                    db.commit()
                    raise

            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            if task.started_at:
                task.duration_seconds = int((task.completed_at - task.started_at).total_seconds())
            task.result = {
                "content": final_content,
                "plan": plan_steps,
                "subtasks": [
                    {
                        "id": s.id,
                        "name": s.name,
                        "status": _enum_value(s.status),
                    }
                    for s in subtask_records
                ],
                "artifacts": artifacts,
            }
            db.commit()
            logger.info("🎉 任务完成: %s，耗时 %d 秒", task_id, task.duration_seconds or 0)

        except Exception as exc:
            db.rollback()
            logger.error("❌ 后台任务异常: %s\n%s", task_id, traceback.format_exc())
            try:
                with Session() as fail_db:
                    task = fail_db.execute(select(Task).where(Task.id == task_id)).scalar_one_or_none()
                    if task:
                        task.status = TaskStatus.FAILED
                        task.error_message = str(exc)
                        task.completed_at = datetime.now()
                        fail_db.commit()
                        logger.info("💀 已标记任务失败: %s", task_id)
            except Exception as fail_exc:
                logger.error("标记任务失败也出错: %s", fail_exc)


def _enum_value(v) -> str:
    return v.value if hasattr(v, "value") else str(v)


def _serialize_artifact(artifact: Dict[str, Any]) -> Dict[str, Any]:
    """转换交付物元数据为可 JSON 序列化结构。"""
    created_at = artifact.get("created_at")
    return {
        "artifact_id": artifact.get("artifact_id"),
        "task_id": artifact.get("task_id"),
        "filename": artifact.get("filename"),
        "format": artifact.get("format"),
        "download_url": artifact.get("download_url"),
        "created_at": created_at.isoformat() if hasattr(created_at, "isoformat") else created_at,
    }


def launch_task_in_background(
    task_id: str,
    user_id: str,
    conversation_id: str,
    prompt: str,
    model: Optional[str],
    deliverable_format: str,
) -> None:
    """启动 daemon 线程执行任务。"""
    logger.info("🧵 启动任务线程: task_id=%s", task_id)
    thread = threading.Thread(
        target=_run_task_in_thread,
        args=(task_id, user_id, conversation_id, prompt, model, deliverable_format),
        daemon=True,
    )
    thread.start()
    logger.info("✅ 线程已启动: %s", thread.name)
