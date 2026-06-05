import json
import uuid
from datetime import datetime

import requests


BASE = "http://127.0.0.1:8000/api/v1"


def dump_req_resp(tag, req, resp):
    print(f"\n===== {tag} =====")
    print("timestamp:", datetime.now().isoformat())
    print("request_line:", req.method, req.url)
    print("request_headers:", json.dumps(dict(req.headers), ensure_ascii=False, indent=2))
    body = req.body.decode("utf-8") if isinstance(req.body, (bytes, bytearray)) else (req.body or "")
    print("request_body:", body)
    print("status_code:", resp.status_code)
    print("response_headers:", json.dumps(dict(resp.headers), ensure_ascii=False, indent=2))
    print("response_body:", resp.text)


def main():
    s = requests.Session()

    login_payload = {"username": "admin@ctms-pro.com", "password": "Admin@CTMS2026!"}
    login_req = requests.Request("POST", f"{BASE}/auth/login", json=login_payload).prepare()
    login_resp = s.send(login_req, timeout=20)
    dump_req_resp("LOGIN", login_req, login_resp)
    login_resp.raise_for_status()

    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    trial_no = f"E2E-{uuid.uuid4().hex[:8].upper()}"
    create_payload = {
        "trial_no": trial_no,
        "short_name": "E2E一致性",
        "full_name": "E2E一致性测试试验",
        "phase": "III",
        "indication": "非小细胞肺癌",
        "sponsor": "CTMS E2E",
        "target_enrollment": 120,
    }
    create_req = requests.Request("POST", f"{BASE}/trials", headers=headers, json=create_payload).prepare()
    create_resp = s.send(create_req, timeout=20)
    dump_req_resp("CREATE_TRIAL", create_req, create_resp)
    create_resp.raise_for_status()
    created_id = create_resp.json().get("data", {}).get("id")

    list_req = requests.Request(
        "GET",
        f"{BASE}/trials",
        headers=headers,
        params={"page": 1, "page_size": 100, "keyword": trial_no},
    ).prepare()
    list_resp = s.send(list_req, timeout=20)
    dump_req_resp("LIST_TRIALS", list_req, list_resp)
    list_resp.raise_for_status()

    items = list_resp.json().get("items", [])
    assert created_id, "create 接口未返回新建ID"
    assert any(i.get("id") == created_id for i in items), "列表未返回刚创建记录"
    print("\nASSERTION: PASS")
    print("created_id:", created_id)


if __name__ == "__main__":
    main()
