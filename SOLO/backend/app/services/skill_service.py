"""
Skill服务

管理Skill的注册、发现和调用
支持skillhub.cn和MCP双协议
"""
import httpx
from typing import Dict, List, Optional
from enum import Enum
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class SkillProtocol(Enum):
    """Skill协议类型"""
    SKILLHUB = "skillhub"
    MCP = "mcp"
    LOCAL = "local"


class SkillService:
    """
    Skill服务
    
    管理Skill的生命周期，支持多协议调用
    """
    
    def __init__(self):
        self.skills: Dict[str, Dict] = {}
        self._setup_default_skills()
    
    def _setup_default_skills(self):
        """初始化默认Skill列表"""
        self.skills = {
            # 诊断类Skill
            "symptom_analyzer": {
                "skill_id": "symptom_analyzer",
                "name": "症状分析器",
                "description": "分析患者症状，提取关键信息",
                "category": "diagnosis",
                "protocol": SkillProtocol.SKILLHUB.value,
                "status": "active",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "症状描述文本"}
                    },
                    "required": ["text"]
                }
            },
            "lab_interpretation": {
                "skill_id": "lab_interpretation",
                "name": "检验结果解读",
                "description": "解读临床检验结果",
                "category": "diagnosis",
                "protocol": SkillProtocol.SKILLHUB.value,
                "status": "active"
            },
            "imaging_analysis": {
                "skill_id": "imaging_analysis",
                "name": "影像辅助分析",
                "description": "辅助分析医学影像",
                "category": "diagnosis",
                "protocol": SkillProtocol.SKILLHUB.value,
                "status": "active"
            },
            
            # 药学类Skill
            "drug_interaction": {
                "skill_id": "drug_interaction",
                "name": "药物相互作用检查",
                "description": "检查药物之间的相互作用",
                "category": "pharmacy",
                "protocol": SkillProtocol.MCP.value,
                "status": "active"
            },
            "dosage_calculator": {
                "skill_id": "dosage_calculator",
                "name": "药物剂量计算",
                "description": "计算药物剂量",
                "category": "pharmacy",
                "protocol": SkillProtocol.LOCAL.value,
                "status": "active"
            },
            
            # 检索类Skill
            "clinical_trial_search": {
                "skill_id": "clinical_trial_search",
                "name": "临床试验检索",
                "description": "检索相关临床试验",
                "category": "research",
                "protocol": SkillProtocol.MCP.value,
                "status": "active"
            },
            "guideline_search": {
                "skill_id": "guideline_search",
                "name": "临床指南检索",
                "description": "检索临床指南",
                "category": "knowledge",
                "protocol": SkillProtocol.MCP.value,
                "status": "active"
            },
            
            # 计算类Skill
            "risk_score": {
                "skill_id": "risk_score",
                "name": "风险评分计算",
                "description": "计算各种医学风险评分",
                "category": "calculation",
                "protocol": SkillProtocol.LOCAL.value,
                "status": "active"
            }
        }
    
    async def list_skills(
        self,
        category: Optional[str] = None,
        protocol: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict]:
        """
        列出Skill
        
        Args:
            category: 按类别过滤
            protocol: 按协议过滤
            status: 按状态过滤
            
        Returns:
            List[Dict]: Skill列表
        """
        skills = list(self.skills.values())
        
        if category:
            skills = [s for s in skills if s.get("category") == category]
        if protocol:
            skills = [s for s in skills if s.get("protocol") == protocol]
        if status:
            skills = [s for s in skills if s.get("status") == status]
        
        return skills
    
    async def get_skill(self, skill_id: str) -> Optional[Dict]:
        """
        获取Skill详情
        
        Args:
            skill_id: Skill ID
            
        Returns:
            Dict: Skill信息
        """
        return self.skills.get(skill_id)
    
    async def invoke(
        self,
        skill_id: str,
        input_data: Dict,
        config: Optional[Dict] = None
    ) -> Dict:
        """
        调用Skill
        
        Args:
            skill_id: Skill ID
            input_data: 输入数据
            config: 配置参数
            
        Returns:
            Dict: 调用结果
        """
        skill = self.skills.get(skill_id)
        if not skill:
            raise ValueError(f"Skill not found: {skill_id}")
        
        if skill.get("status") != "active":
            raise ValueError(f"Skill is not active: {skill_id}")
        
        protocol = skill.get("protocol")
        
        try:
            if protocol == SkillProtocol.SKILLHUB.value:
                result = await self._invoke_skillhub(skill, input_data, config)
            elif protocol == SkillProtocol.MCP.value:
                result = await self._invoke_mcp(skill, input_data, config)
            else:
                result = await self._invoke_local(skill, input_data, config)
            
            return {
                "skill_id": skill_id,
                "success": True,
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Skill invocation failed: {skill_id}, error: {e}")
            return {
                "skill_id": skill_id,
                "success": False,
                "error": str(e)
            }
    
    async def _invoke_skillhub(
        self,
        skill: Dict,
        input_data: Dict,
        config: Optional[Dict] = None
    ) -> Dict:
        """
        调用SkillHub Skill
        
        TODO: 实现实际的SkillHub API调用
        """
        # 模拟调用
        logger.info(f"Invoking SkillHub skill: {skill['skill_id']}")
        
        # 实际实现应该调用skillhub.cn API
        # async with httpx.AsyncClient() as client:
        #     response = await client.post(
        #         f"{settings.SKILLHUB_ENDPOINT}/skills/{skill['skill_id']}/invoke",
        #         json={"input": input_data, "config": config},
        #         headers={"Authorization": f"Bearer {settings.SKILLHUB_API_KEY}"}
        #     )
        #     return response.json()
        
        return {
            "message": "SkillHub调用成功",
            "skill": skill["name"],
            "input": input_data
        }
    
    async def _invoke_mcp(
        self,
        skill: Dict,
        input_data: Dict,
        config: Optional[Dict] = None
    ) -> Dict:
        """
        调用MCP工具
        
        TODO: 实现实际的MCP协议调用
        """
        logger.info(f"Invoking MCP tool: {skill['skill_id']}")
        
        return {
            "message": "MCP调用成功",
            "skill": skill["name"],
            "input": input_data
        }
    
    async def _invoke_local(
        self,
        skill: Dict,
        input_data: Dict,
        config: Optional[Dict] = None
    ) -> Dict:
        """
        调用本地工具
        """
        logger.info(f"Invoking local skill: {skill['skill_id']}")
        
        return {
            "message": "本地工具调用成功",
            "skill": skill["name"],
            "input": input_data
        }
    
    def register_skill(self, skill: Dict) -> bool:
        """
        注册新Skill
        
        Args:
            skill: Skill配置
            
        Returns:
            bool: 是否成功
        """
        skill_id = skill.get("skill_id")
        if not skill_id:
            return False
        
        self.skills[skill_id] = skill
        logger.info(f"Skill registered: {skill_id}")
        return True
    
    def unregister_skill(self, skill_id: str) -> bool:
        """
        注销Skill
        
        Args:
            skill_id: Skill ID
            
        Returns:
            bool: 是否成功
        """
        if skill_id in self.skills:
            del self.skills[skill_id]
            logger.info(f"Skill unregistered: {skill_id}")
            return True
        return False
    
    def update_skill_status(self, skill_id: str, status: str) -> bool:
        """
        更新Skill状态
        
        Args:
            skill_id: Skill ID
            status: 新状态
            
        Returns:
            bool: 是否成功
        """
        if skill_id in self.skills:
            self.skills[skill_id]["status"] = status
            return True
        return False


# 全局单例实例
skill_service = SkillService()
