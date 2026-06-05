"""
IWRS 随机化服务
实现分层随机、区组随机、简单随机算法
"""
import random
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_


class RandomizationService:
    """随机化算法服务"""
    
    @staticmethod
    def parse_ratio(ratio: str) -> List[int]:
        """解析分配比例，如 '1:1' -> [1, 1], '2:1' -> [2, 1]"""
        return [int(x) for x in ratio.split(':')]
    
    @staticmethod
    def generate_block(block_size: int, ratio: str) -> List[int]:
        """
        生成一个区组
        例如 block_size=4, ratio='1:1' -> [0, 1, 1, 0] (随机顺序)
        """
        arms = RandomizationService.parse_ratio(ratio)
        total = sum(arms)
        if block_size % total != 0:
            raise ValueError(f"区组大小 {block_size} 必须能被分配比例 {ratio} 整除")
        
        # 构建区组
        block = []
        for arm_idx, count in enumerate(arms):
            block.extend([arm_idx] * count)
        
        # Fisher-Yates 洗牌
        random.shuffle(block)
        return block
    
    @staticmethod
    def generate_code_pool(
        scheme_type: str,
        total_subjects: int,
        block_sizes: List[int],
        ratio: str,
        strata_factors: List[str],
        arms: List[Dict]
    ) -> List[Dict]:
        """
        生成随机编码池
        
        Returns:
            List[Dict]: 编码列表，每项包含:
                - block_id: 区组ID
                - sequence: 区组内序号
                - treatment_arm: 组别代码
                - treatment_name: 组别名称
                - strata_values: 分层因素值（分层随机时使用）
        """
        codes = []
        
        if scheme_type in ("RANDOM", "SIMPLE"):
            # 简单随机：直接按比例随机分配
            arm_indices = RandomizationService.parse_ratio(ratio)
            arm_list = []
            for idx, count in enumerate(arm_indices):
                arm_list.extend([idx] * count)
            
            for i in range(total_subjects):
                arm_idx = random.choice(arm_list)
                codes.append({
                    "block_id": f"B{i+1}",
                    "sequence": 1,
                    "treatment_arm": arms[arm_idx]["code"],
                    "treatment_name": arms[arm_idx]["name"],
                    "strata_values": {}
                })
        
        elif scheme_type in ("BLOCK", "STRATIFIED"):
            # 区组随机或分层随机
            if not block_sizes:
                block_sizes = [4]
            
            # 计算每个区组的subjects数量
            ratio_sum = sum(RandomizationService.parse_ratio(ratio))
            
            for block_size in block_sizes:
                num_full_blocks = (total_subjects // block_size) * block_size // ratio_sum
                
                for _ in range(num_full_blocks):
                    block = RandomizationService.generate_block(block_size, ratio)
                    
                    for seq_idx, arm_idx in enumerate(block):
                        codes.append({
                            "block_id": str(uuid.uuid4())[:8].upper(),
                            "sequence": seq_idx + 1,
                            "treatment_arm": arms[arm_idx]["code"],
                            "treatment_name": arms[arm_idx]["name"],
                            "strata_values": {}
                        })
            
            # 处理剩余的subjects
            remaining = total_subjects - len(codes)
            if remaining > 0:
                # 使用最小的block_size
                block_size = min(block_sizes)
                if remaining >= ratio_sum:
                    block = RandomizationService.generate_block(block_size, ratio)
                    for seq_idx, arm_idx in enumerate(block[:remaining]):
                        codes.append({
                            "block_id": str(uuid.uuid4())[:8].upper(),
                            "sequence": seq_idx + 1,
                            "treatment_arm": arms[arm_idx]["code"],
                            "treatment_name": arms[arm_idx]["name"],
                            "strata_values": {}
                        })
        
        return codes
    
    @staticmethod
    def assign_random(
        scheme: "RandomizationScheme",
        strata_values: Optional[Dict] = None,
        db: Optional[AsyncSession] = None
    ) -> Tuple[str, str, str]:
        """
        为受试者分配随机号
        
        Args:
            scheme: 随机化方案
            strata_values: 分层因素值，如 {"性别": "男", "年龄段": "45-65"}
            db: 数据库会话（可选）
            
        Returns:
            (randomization_code, treatment_arm, treatment_name)
        """
        # 生成随机号
        timestamp = datetime.now().strftime("%Y%m%d")
        random_part = str(random.randint(1000, 9999))
        randomization_code = f"R{timestamp}{random_part}"
        
        # 根据方案类型分配组别
        if scheme.scheme_type in ("RANDOM", "SIMPLE"):
            arms = scheme.arms
            ratio_arms = RandomizationService.parse_ratio(scheme.ratio)
            arm_list = []
            for idx, count in enumerate(ratio_arms):
                arm_list.extend([idx] * count)
            arm_idx = random.choice(arm_list)
        
        elif scheme.scheme_type in ("BLOCK", "STRATIFIED"):
            # 简单起见，这里用随机分配演示
            # 实际应该从code_pool中获取可用编码
            arms = scheme.arms
            ratio_arms = RandomizationService.parse_ratio(scheme.ratio)
            arm_list = []
            for idx, count in enumerate(ratio_arms):
                arm_list.extend([idx] * count)
            arm_idx = random.choice(arm_list)
        
        treatment_arm = arms[arm_idx]["code"]
        treatment_name = arms[arm_idx]["name"]
        
        return randomization_code, treatment_arm, treatment_name
    
    @staticmethod
    def unblind(
        randomization_id: uuid.UUID,
        reason: str,
        unblinded_by: uuid.UUID,
        db: AsyncSession
    ) -> "SubjectRandomization":
        """
        执行解盲操作
        
        Args:
            randomization_id: 随机化记录ID
            reason: 解盲原因
            unblinded_by: 解盲操作人
            db: 数据库会话
            
        Returns:
            更新后的 SubjectRandomization 记录
        """
        # 实际实现需要查询数据库更新记录
        # 这里返回模拟结果
        pass


# 导出服务实例
randomization_service = RandomizationService()
