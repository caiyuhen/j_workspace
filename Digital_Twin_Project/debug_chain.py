import requests
import json

PATIENT_SERVICE = "http://localhost:8003"
SIMULATION_SERVICE = "http://localhost:8001"
VISUALIZATION_SERVICE = "http://localhost:8002"
PATIENT_NAME = "倪欣然"

def run_debug():
    # 1. 获取患者数据
    print("--- 1. 正在获取患者数据 ---")
    resp = requests.get(f"{PATIENT_SERVICE}/patients/{PATIENT_NAME}")
    if resp.status_code != 200:
        print(f"获取患者失败: {resp.text}")
        return
    patient_data = resp.json()
    print("患者数据 (部分):")
    print(json.dumps(patient_data['metrics'], indent=2))
    print(f"Rotation len: {len(patient_data['curve_data']['vertebral_rotation'])}")
    print(f"Offsets len: {len(patient_data['curve_data']['coronal_offsets'])}")

    # 2. 运行模拟
    print("\n--- 2. 正在运行模拟 ---")
    payload = {
        "patient_name": PATIENT_NAME,
        "initial_state": {
            "metrics": patient_data['metrics'],
            "curve_data": patient_data['curve_data']
        },
        "treatment_plan": {
            "type": "Brace",
            "duration": 24,
            "compliance": 0.9
        }
    }
    resp = requests.post(f"{SIMULATION_SERVICE}/simulate", json=payload)
    if resp.status_code != 200:
        print(f"模拟失败: {resp.text}")
        return
    sim_result = resp.json()
    print("模拟结果键:", sim_result.keys())
    print(f"时间轴长度: {len(sim_result['timeline'])}")
    if len(sim_result['timeline']) > 0:
        t0 = sim_result['timeline'][0]
        print("T0 Rotation len:", len(t0['control']['curve_data']['vertebral_rotation']))

    # 3. 运行可视化
    print("\n--- 3. 正在运行可视化 ---")
    try:
        resp = requests.post(f"{VISUALIZATION_SERVICE}/render/evolution", json=sim_result)
        if resp.status_code != 200:
            print(f"可视化失败: {resp.status_code}")
            print(resp.text)
        else:
            print("可视化成功!")
    except Exception as e:
        print(f"可视化请求错误: {e}")

if __name__ == "__main__":
    run_debug()
