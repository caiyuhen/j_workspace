import asyncio
import os
import sys

# 确保能找到 backend 模块
sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))

from app.db.session import AsyncSessionLocal
from app.models.models import Patient, SubjectRandomization
from sqlalchemy import select

async def get_randomization():
    async with AsyncSessionLocal() as db:
        # 查询受试者
        result = await db.execute(select(Patient).where(Patient.patient_no == 'P-001229090'))
        patient = result.scalar_one_or_none()
        
        if not patient:
            print("未找到受试者 P-001229090")
            return
            
        print(f"找到受试者: {patient.id}")
        
        # 查询随机化记录
        result = await db.execute(
            select(SubjectRandomization).where(SubjectRandomization.patient_id == patient.id)
        )
        records = result.scalars().all()
        
        if not records:
            print("该受试者暂无随机化记录")
            return
            
        print(f"受试者 P-001229090 共有 {len(records)} 条随机化记录：")
        for i, r in enumerate(records):
            print(f"[{i+1}] 随机号: {r.randomization_code}")
            print(f"    分配组别: {r.treatment_name} (组 {r.treatment_arm})")
            print(f"    受试者编号: {r.subject_code}")
            print(f"    是否盲态: {'是' if r.is_blinded else '否'}")
            print(f"    药品编码: {r.drug_code}")
            print(f"    状态: {r.status}")
            print("-" * 30)

if __name__ == "__main__":
    asyncio.run(get_randomization())