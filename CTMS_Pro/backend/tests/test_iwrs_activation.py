import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from uuid import uuid4
from unittest.mock import patch, MagicMock

# 模拟 SQLAlchemy 和依赖
from app.api.v1.endpoints.iwrs import activate_scheme
from app.models.models import RandomizationScheme, RandomizationCode
from app.services.randomization import RandomizationService
from fastapi import HTTPException

# ======== 单元测试 ========

@pytest.mark.asyncio
async def test_activate_scheme_success():
    """测试激活草稿状态的随机化方案"""
    mock_db = MagicMock()
    mock_user = MagicMock()
    mock_user.id = uuid4()
    
    scheme_id = uuid4()
    mock_scheme = RandomizationScheme(
        id=scheme_id,
        scheme_code="RS-2026-TEST",
        scheme_name="Test Scheme",
        scheme_type="SIMPLE",
        status="DRAFT",
        total_subjects=10,
        block_sizes=[4],
        ratio="1:1",
        strata_factors=[],
        arms=[{"code": "A", "name": "A"}, {"code": "B", "name": "B"}],
        is_blinded=True,
        blinding_method="DOUBLE"
    )
    
    # 模拟 db.execute(...).scalar_one_or_none()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_scheme
    
    # 异步方法的 mock
    async def mock_execute(*args, **kwargs):
        return mock_result
        
    mock_db.execute = mock_execute
    from unittest.mock import AsyncMock
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()
    mock_db.add_all = MagicMock()

    response = await activate_scheme(scheme_id=scheme_id, db=mock_db, current_user=mock_user)
    
    assert response.status == "ACTIVE"
    assert response.scheme_code == "RS-2026-TEST"
    assert response.activated_at is not None
    # 验证添加了随机码
    assert mock_db.add_all.called

@pytest.mark.asyncio
async def test_activate_scheme_not_found():
    """测试方案不存在时的错误处理"""
    mock_db = MagicMock()
    
    # 模拟找不到
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    
    async def mock_execute(*args, **kwargs):
        return mock_result
        
    mock_db.execute = mock_execute

    with pytest.raises(HTTPException) as exc_info:
        await activate_scheme(scheme_id=uuid4(), db=mock_db, current_user=MagicMock())
    
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "随机化方案不存在"

@pytest.mark.asyncio
async def test_activate_scheme_wrong_status():
    """测试激活非草稿状态方案时的错误处理"""
    mock_db = MagicMock()
    
    mock_scheme = RandomizationScheme(status="ACTIVE")
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_scheme
    
    async def mock_execute(*args, **kwargs):
        return mock_result
        
    mock_db.execute = mock_execute

    with pytest.raises(HTTPException) as exc_info:
        await activate_scheme(scheme_id=uuid4(), db=mock_db, current_user=MagicMock())
    
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "只能激活草稿状态的方案"


# ======== 集成测试 (依赖测试客户端) ========
def test_integration_activate_scheme_api():
    """集成测试: 测试 API 路由是否能正确处理序列化和错误"""
    from app.main import app
    client = TestClient(app)
    
    # 假设未授权访问
    response = client.post(f"/api/v1/iwrs/schemes/{uuid4()}/activate")
    assert response.status_code == 401
    assert "Not authenticated" in response.text or "Not authenticated" in response.json().get("detail", "")
