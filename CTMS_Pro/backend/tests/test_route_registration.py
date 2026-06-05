import re
from pathlib import Path

from fastapi import FastAPI
from fastapi.routing import APIRoute

from app.api.v1.router import api_router


ENDPOINT_PREFIXES = {
    "auth.py": "/auth",
    "users.py": "/users",
    "trials.py": "/trials",
    "patients.py": "/patients",
    "visits.py": "/visits",
    "adverse_events.py": "/adverse-events",
    "drugs.py": "/drugs",
    "contracts.py": "/contracts",
    "documents.py": "/documents",
    "monitoring.py": "/monitoring",
    "reports.py": "/reports",
    "notifications.py": "/notifications",
    "iwrs.py": "",
}


def _extract_expected_routes():
    base_dir = Path(__file__).resolve().parents[1] / "app" / "api" / "v1" / "endpoints"
    pattern = re.compile(r'@router\.(get|post|put|delete)\("([^"]*)"')
    router_prefix_pattern = re.compile(r'APIRouter\(\s*prefix="([^"]*)"')
    expected = set()

    for filename, prefix in ENDPOINT_PREFIXES.items():
        source = (base_dir / filename).read_text(encoding="utf-8")
        router_prefix_match = router_prefix_pattern.search(source)
        router_prefix = router_prefix_match.group(1) if router_prefix_match else ""
        for method, route_path in pattern.findall(source):
            full_path = f"/api/v1{prefix}{router_prefix}{route_path}"
            expected.add((full_path, method.upper()))
    return expected


def test_all_endpoint_decorators_are_registered_in_api_router():
    app = FastAPI()
    app.include_router(api_router, prefix="/api/v1")

    actual = set()
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        for method in route.methods:
            if method in {"GET", "POST", "PUT", "DELETE"}:
                actual.add((route.path, method))

    expected = _extract_expected_routes()
    missing = sorted(expected - actual)

    assert not missing, f"以下路由未注册到主路由: {missing}"
