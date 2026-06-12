"""
代理/Skill Task 验收脚本（无需前端）

用途：
1) 验证“任务 -> 编排代理 -> tool/skill 自动触发”的链路是否可用
2) 输出可留存的交付物：agent_skill_task_results.json

运行前置：
- 后端 API 已启动（默认 http://127.0.0.1:8000）
- 可使用内置账号登录：
  - admin@medical.ai / admin123
  - doctor@medical.ai / doctor123

可选前置（会影响执行是否真正成功）：
- 医疗大模型后端服务可用（LLM_ENDPOINT 指向的服务，包括 /chat 及 medical_api 的 /triage /clinical 等）

用法示例：
  py -3 agent_skill_task_runner.py --api http://127.0.0.1:8000 --email admin@medical.ai --password admin123
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.request
import urllib.error
from typing import Any, Dict, Optional, Tuple, List


def http_json(method: str, url: str, payload: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Tuple[int, Dict[str, Any]]:
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url=url, data=data, method=method.upper())
    req.add_header("Content-Type", "application/json")
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8") if hasattr(e, "read") else ""
        try:
            return e.code, json.loads(body) if body else {"error": body}
        except Exception:
            return e.code, {"error": body}
    except Exception as e:
        return 0, {"error": str(e)}


def login(api_base: str, email: str, password: str) -> str:
    status, data = http_json(
        "POST",
        f"{api_base}/api/v1/auth/login",
        {"email": email, "password": password},
    )
    if status != 200 or "access_token" not in data:
        raise RuntimeError(f"登录失败: http={status}, body={data}")
    return data["access_token"]


def submit_task(api_base: str, token: str, text: str) -> str:
    status, data = http_json(
        "POST",
        f"{api_base}/api/v1/agents/tasks",
        {
            "task_type": "chat",
            "priority": "normal",
            "input": {"text": text},
            "config": {},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    if status != 200 or "task_id" not in data:
        raise RuntimeError(f"提交任务失败: http={status}, body={data}")
    return data["task_id"]


def get_task(api_base: str, token: str, task_id: str) -> Dict[str, Any]:
    status, data = http_json(
        "GET",
        f"{api_base}/api/v1/agents/tasks/{task_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    if status != 200:
        raise RuntimeError(f"获取任务失败: http={status}, body={data}")
    return data


def wait_task_done(api_base: str, token: str, task_id: str, timeout_s: int = 60) -> Dict[str, Any]:
    start = time.time()
    while True:
        task = get_task(api_base, token, task_id)
        if task.get("status") in {"completed", "failed"}:
            return task
        if time.time() - start > timeout_s:
            return {"status": "timeout", "task_id": task_id, "task": task}
        time.sleep(0.5)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", default="http://127.0.0.1:8000", help="后端 API 基地址，如 http://127.0.0.1:8000")
    ap.add_argument("--email", default="admin@medical.ai")
    ap.add_argument("--password", default="admin123")
    ap.add_argument("--out", default="agent_skill_task_results.json")
    args = ap.parse_args()

    token = login(args.api, args.email, args.password)

    cases: List[Dict[str, Any]] = [
        {
            "name": "化验单解读(应触发skill_lab_interpretation)",
            "text": "请帮我解读化验单：ALT 80 U/L (0-40)；AST 60 U/L (0-40)；TBIL 25 umol/L (5-21)。",
            "expect_skill_id": "skill_lab_interpretation",
        },
        {
            "name": "分诊(应触发skill_medical_api_triage)",
            "text": "我胸口很闷已经三天了，有时候恶心，应该挂什么科？需要急诊吗？",
            "expect_skill_id": "skill_medical_api_triage",
        },
        {
            "name": "临床建议(应触发skill_medical_api_clinical)",
            "text": "2型糖尿病，二甲双胍控制不佳，HbA1c 8.5%，下一步治疗方案推荐？",
            "expect_skill_id": "skill_medical_api_clinical",
        },
        {
            "name": "个案管理计划(应触发skill_medical_api_management_plan)",
            "text": "我去年做过乳腺癌手术，未来一周每天的康复/运动/饮食任务怎么安排？",
            "expect_skill_id": "skill_medical_api_management_plan",
        },
    ]

    results: Dict[str, Any] = {"api": args.api, "user": args.email, "cases": []}

    for c in cases:
        task_id = submit_task(args.api, token, c["text"])
        task = wait_task_done(args.api, token, task_id)
        out = {
            "name": c["name"],
            "task_id": task_id,
            "status": task.get("status"),
            "expect_skill_id": c["expect_skill_id"],
            "result": task.get("result"),
            "error": task.get("error"),
        }
        # 尝试从 orchestrator 输出中提取 skill_id / quality_gate
        if isinstance(task.get("result"), dict):
            out["actual_skill_id"] = task["result"].get("skill_id")
            out["quality_gate"] = task["result"].get("quality_gate")
            out["content_preview"] = (task["result"].get("content") or "")[:300]
        results["cases"].append(out)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"✅ 已生成交付物: {args.out}")


if __name__ == "__main__":
    main()

