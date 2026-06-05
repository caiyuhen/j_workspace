import json
import uuid
import sys
from datetime import datetime

import requests

BASE = "http://127.0.0.1:8898/api/v1"

def dump_req_resp(tag, req, resp):
    print(f"\n===== {tag} =====")
    print("request_line:", req.method, req.url)
    print("status_code:", resp.status_code)
    try:
        print("response_body:", resp.json())
    except:
        print("response_body:", resp.text)

def main():
    s = requests.Session()

    # 1. Login
    login_payload = {"username": "admin@ctms-pro.com", "password": "Admin@CTMS2026!"}
    login_req = requests.Request("POST", f"{BASE}/auth/login", json=login_payload).prepare()
    login_resp = s.send(login_req, timeout=20)
    dump_req_resp("LOGIN", login_req, login_resp)
    if login_resp.status_code != 200:
        print("Login failed, skipping E2E test")
        return

    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # 2. Get Trial ID
    trial_req = requests.Request("GET", f"{BASE}/trials?page=1&page_size=10", headers=headers).prepare()
    trial_resp = s.send(trial_req, timeout=20)
    dump_req_resp("GET_TRIALS", trial_req, trial_resp)
    
    items = trial_resp.json().get("items", [])
    if not items:
        print("No trials found, cannot proceed")
        return
    trial_id = items[0]["id"]

    # 3. Create a Patient
    patient_no = f"E2E-P-{uuid.uuid4().hex[:4].upper()}"
    patient_payload = {
        "trial_id": trial_id,
        "patient_no": patient_no,
        "status": "ENROLLED"
    }
    patient_req = requests.Request("POST", f"{BASE}/patients", headers=headers, json=patient_payload).prepare()
    patient_resp = s.send(patient_req, timeout=20)
    dump_req_resp("CREATE_PATIENT", patient_req, patient_resp)
    patient_resp.raise_for_status()
    patient_id = patient_resp.json()["data"]["id"]

    # 4. Get or Create a Randomization Scheme
    scheme_req = requests.Request("GET", f"{BASE}/iwrs/schemes", headers=headers).prepare()
    scheme_resp = s.send(scheme_req, timeout=20)
    dump_req_resp("GET_SCHEMES", scheme_req, scheme_resp)
    schemes = scheme_resp.json()
    
    active_scheme = next((s for s in schemes if s["status"] in ["ACTIVE", "DRAFT"]), None)
    
    if not active_scheme:
        # Create one
        scheme_payload = {
            "scheme_name": f"E2E-Scheme-{uuid.uuid4().hex[:4]}",
            "scheme_type": "SIMPLE",
            "trial_id": trial_id,
            "total_subjects": 10,
            "is_blinded": True
        }
        create_scheme_req = requests.Request("POST", f"{BASE}/iwrs/schemes", headers=headers, json=scheme_payload).prepare()
        create_scheme_resp = s.send(create_scheme_req, timeout=20)
        dump_req_resp("CREATE_SCHEME", create_scheme_req, create_scheme_resp)
        active_scheme = create_scheme_resp.json()
        
        # Activate it
        activate_req = requests.Request("POST", f"{BASE}/iwrs/schemes/{active_scheme['id']}/activate", headers=headers).prepare()
        activate_resp = s.send(activate_req, timeout=20)
        dump_req_resp("ACTIVATE_SCHEME", activate_req, activate_resp)
        active_scheme = activate_resp.json()

    scheme_id = active_scheme["id"]

    # 5. Assign Randomization
    assign_payload = {
        "scheme_id": scheme_id,
        "patient_id": patient_id,
        "strata_values": {}
    }
    assign_req = requests.Request("POST", f"{BASE}/iwrs/assign", headers=headers, json=assign_payload).prepare()
    assign_resp = s.send(assign_req, timeout=20)
    dump_req_resp("ASSIGN_RANDOMIZATION", assign_req, assign_resp)
    assign_resp.raise_for_status()

    # 6. Verify Patient state
    verify_req = requests.Request("GET", f"{BASE}/patients/{patient_id}", headers=headers).prepare()
    verify_resp = s.send(verify_req, timeout=20)
    dump_req_resp("VERIFY_PATIENT", verify_req, verify_resp)
    
    patient_data = verify_resp.json().get("data", {})
    arm = patient_data.get("arm")
    
    print(f"\nFinal Check - Patient {patient_no} arm is: {arm}")
    
    assert arm is not None, "Patient arm is None after assignment"
    if active_scheme.get("is_blinded"):
        assert arm == "盲态", f"Expected arm '盲态', got '{arm}'"
    else:
        assert arm in ["A", "B", "试验组", "对照组"], f"Expected specific arm, got '{arm}'"
        
    print("E2E Test Passed Successfully!")

if __name__ == "__main__":
    main()
