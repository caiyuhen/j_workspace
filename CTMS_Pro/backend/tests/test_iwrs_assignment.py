import pytest
import pytest_asyncio
from uuid import uuid4
from unittest.mock import MagicMock
from fastapi import HTTPException
from app.api.v1.endpoints.iwrs import assign_randomization
from app.models.models import RandomizationScheme, RandomizationCode, SubjectRandomization, Patient
from app.api.v1.endpoints.iwrs import RandomizationAssignRequest

@pytest.mark.asyncio
async def test_assign_randomization_success():
    """测试分配随机号成功且状态落库同步更新 Patient.arm"""
    mock_db = MagicMock()
    mock_user = MagicMock()
    mock_user.id = uuid4()

    scheme_id = uuid4()
    patient_id = uuid4()
    
    mock_scheme = RandomizationScheme(
        id=scheme_id,
        scheme_code="RS-2026-TEST",
        scheme_name="Test Scheme",
        scheme_type="SIMPLE",
        status="ACTIVE",
        is_blinded=True
    )
    
    mock_code = RandomizationCode(
        id=uuid4(),
        scheme_id=scheme_id,
        is_used=False,
        randomization_code="R12345",
        treatment_arm="A",
        treatment_name="Test Drug",
        block_id="B1",
        sequence=1
    )
    
    mock_patient = Patient(
        id=patient_id,
        patient_no="P-001",
        status="ENROLLED",
        arm=None
    )

    # 模拟 db.execute() 根据调用顺序返回不同的结果
    # 1. 查找 scheme
    # 2. count(可用code)
    # 3. 获取可用 code
    # 4. count(SubjectRandomization) 生成受试者编号
    # 5. 查找 patient

    call_count = 0
    def mock_execute_side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        
        mock_result = MagicMock()
        if call_count == 1: # Scheme
            mock_result.scalar_one_or_none.return_value = mock_scheme
        elif call_count == 2: # Available count
            mock_result.scalar.return_value = 10
        elif call_count == 3: # Code
            mock_result.scalar_one_or_none.return_value = mock_code
        elif call_count == 4: # Subject count
            mock_result.scalar.return_value = 0
        elif call_count == 5: # Patient
            mock_result.scalar_one_or_none.return_value = mock_patient
            
        # 封装异步返回
        async def async_return():
            return mock_result
        return async_return()

    mock_db.execute = mock_execute_side_effect
    
    # 模拟异步方法
    async def mock_async_method(*args, **kwargs):
        pass

    mock_db.commit = mock_async_method
    mock_db.refresh = mock_async_method
    mock_db.add = MagicMock()
    mock_db.rollback = mock_async_method

    request = RandomizationAssignRequest(
        scheme_id=scheme_id,
        patient_id=patient_id,
        strata_values={}
    )

    response = await assign_randomization(request=request, db=mock_db, current_user=mock_user)
    
    # 验证响应
    assert response.randomization_code == "R12345"
    assert response.is_blinded is True
    
    # 验证 Patient.arm 被更新
    assert mock_patient.arm == "盲态"
    
    # 验证 db.add 被调用插入了 SubjectRandomization
    assert mock_db.add.called
