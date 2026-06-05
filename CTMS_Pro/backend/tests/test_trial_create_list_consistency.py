import pytest
import uuid
from types import SimpleNamespace

from sqlalchemy import select, delete

from app.api.v1.endpoints.trials import create_trial, list_trials, TrialCreate
from app.db.session import AsyncSessionLocal
from app.models.models import User, Trial


@pytest.mark.skip(reason="Windows asyncpg connection pool teardown issue")
@pytest.mark.asyncio
async def test_create_then_list_should_contain_new_trial_immediately():
    created_trial_id = None
    trial_no = f"UT-CONSIST-{uuid.uuid4().hex[:10].upper()}"

    async with AsyncSessionLocal() as db:
        user_id = (await db.execute(select(User.id).limit(1))).scalar_one()
        current_user = SimpleNamespace(id=user_id, is_superuser=True)

        payload = TrialCreate(
            trial_no=trial_no,
            short_name="一致性测试试验",
            full_name="一致性测试试验-创建后立即列表可见",
            phase="III",
            indication="测试适应症",
            sponsor="CTMS QA",
            target_enrollment=100,
        )

        created = await create_trial(body=payload, db=db, current_user=current_user)
        created_trial_id = created["data"]["id"]

        listed = await list_trials(
            page=1,
            page_size=300,
            status=None,
            phase=None,
            keyword=trial_no,
            db=db,
            current_user=current_user,
        )

        assert any(item["id"] == created_trial_id for item in listed["items"])

    if created_trial_id:
        async with AsyncSessionLocal() as db:
            await db.execute(delete(Trial).where(Trial.id == uuid.UUID(created_trial_id)))
            await db.commit()
