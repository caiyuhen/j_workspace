"""
临床研究项目：代理/Skill Task 验收脚本

目标：
验证在“临床研究项目”场景下，系统是否能通过编排代理自动触发医学专用 Skill（medical_api）来完成任务，
并输出可交付的验收结果文件（JSON）。

前置：
- 后端 API 已启动（默认 http://127.0.0.1:8000）
- 可使用内置账号登录：
  - admin@medical.ai / admin123
  - doctor@medical.ai / doctor123
- 若希望 medical_api 真正执行成功，需要医学后端服务可用（LLM_ENDPOINT 指向的服务，包含 /clinical_trial /write /clinical 等）

用法：
  py -3 clinical_research_task_runner.py --api http://127.0.0.1:8000 --email admin@medical.ai --password admin123
  py -3 clinical_research_task_runner.py --cases clinical_research_task_cases.json
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
        with urllib.request.urlopen(req, timeout=60) as resp:
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
    status, data = http_json("POST", f"{api_base}/api/v1/auth/login", {"email": email, "password": password})
    if status != 200 or "access_token" not in data:
        raise RuntimeError(f"登录失败: http={status}, body={data}")
    return data["access_token"]


def submit_task(api_base: str, token: str, text: str) -> str:
    # 走 /agents/tasks => 编排代理自动路由，便于验证“代理/skill 能否实现 task”
    status, data = http_json(
        "POST",
        f"{api_base}/api/v1/agents/tasks",
        {"task_type": "chat", "priority": "normal", "input": {"text": text}, "config": {}},
        headers={"Authorization": f"Bearer {token}"},
    )
    if status != 200 or "task_id" not in data:
        raise RuntimeError(f"提交任务失败: http={status}, body={data}")
    return data["task_id"]


def get_task(api_base: str, token: str, task_id: str) -> Dict[str, Any]:
    status, data = http_json("GET", f"{api_base}/api/v1/agents/tasks/{task_id}", headers={"Authorization": f"Bearer {token}"})
    if status != 200:
        raise RuntimeError(f"获取任务失败: http={status}, body={data}")
    return data


def wait_task_done(api_base: str, token: str, task_id: str, timeout_s: int = 120) -> Dict[str, Any]:
    start = time.time()
    while True:
        task = get_task(api_base, token, task_id)
        if task.get("status") in {"completed", "failed"}:
            return task
        if time.time() - start > timeout_s:
            return {"status": "timeout", "task_id": task_id, "task": task}
        time.sleep(0.5)


def load_cases(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", default="http://127.0.0.1:8000")
    ap.add_argument("--email", default="admin@medical.ai")
    ap.add_argument("--password", default="admin123")
    ap.add_argument("--cases", default="clinical_research_task_cases.json")
    ap.add_argument("--out", default="clinical_research_task_results.json")
    args = ap.parse_args()

    cases_doc = load_cases(args.cases)
    cases: List[Dict[str, Any]] = cases_doc.get("cases", [])
    if not cases:
        raise RuntimeError("cases 文件为空或格式不正确")

    token = login(args.api, args.email, args.password)

    results: Dict[str, Any] = {
        "api": args.api,
        "user": args.email,
        "project": cases_doc.get("project"),
        "description": cases_doc.get("description"),
        "cases": [],
    }

    for c in cases:
        text = c["text"]
        task_id = submit_task(args.api, token, text)
        task = wait_task_done(args.api, token, task_id)

        out = {
            "name": c.get("name"),
            "task_id": task_id,
            "status": task.get("status"),
            "expect_skill_id": c.get("expect_skill_id"),
            "result": task.get("result"),
            "error": task.get("error"),
        }

        # 从 orchestrator 输出中提取关键字段（若本用例触发了 tool/skill）
        if isinstance(task.get("result"), dict):
            out["actual_skill_id"] = task["result"].get("skill_id")
            out["quality_gate"] = task["result"].get("quality_gate")
            out["content_preview"] = (task["result"].get("content") or "")[:400]

        results["cases"].append(out)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"✅ 已生成交付物: {args.out}")


if __name__ == "__main__":
    main()

