import httpx

from ctms_common.config import load_config


def call_service(service_name: str, method: str, path: str, payload: dict | None = None) -> dict | list:
    config = load_config()
    port = config.get(service_name, "port")
    url = f"http://127.0.0.1:{port}{path}"
    with httpx.Client(timeout=15) as client:
        response = client.request(method=method, url=url, json=payload)
        data = response.json()
        if response.status_code >= 400:
            message = data.get("detail") if isinstance(data, dict) else str(data)
            raise RuntimeError(message)
        return data
