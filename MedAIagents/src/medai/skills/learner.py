"""
Skill 学习器

从用户对话中自动提取和生成可复用的 Skill。
"""

import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
from loguru import logger

from .models import Skill, SkillStep, SkillParameter, StepType


class SkillLearner:
    """Skill 学习器 - 从对话中提取可复用工作流"""
    
    def __init__(self, llm_router=None):
        self.llm_router = llm_router
        self._extract_patterns = self._build_extract_patterns()
    
    def _build_extract_patterns(self) -> Dict[str, Any]:
        """构建 Skill 提取模式"""
        return {
            "step_indicators": [
                r"第[一二三四五六七八九十\d]+步",
                r"Step\s*\d+",
                r"首先",
                r"然后",
                r"接着",
                r"最后",
                r"第一步",
                r"第二步",
                r"第三步",
            ],
            "workflow_keywords": [
                "流程", "步骤", "流程图", "workflow", "procedure",
                "protocol", "guideline", "SOP", "标准操作",
            ],
            "condition_keywords": [
                "如果", "若", "当", "当...时", "if", "when", "depending on",
                "否则", "else",
            ],
            "loop_keywords": [
                "重复", "循环", "直到", "for each", "while", "iterate",
            ]
        }
    
    def learn_from_conversation(
        self,
        conversation: List[Dict[str, str]],
        skill_name: str = None,
        skill_description: str = None
    ) -> Optional[Skill]:
        """从对话中学习 Skill
        
        Args:
            conversation: 对话历史，每项为 {"role": "user/assistant", "content": "..."}
            skill_name: Skill 名称（如未提供则自动生成）
            skill_description: Skill 描述
        
        Returns:
            提取的 Skill 或 None
        """
        # 合并对话内容
        full_text = self._merge_conversation(conversation)
        
        # 检测是否包含工作流
        if not self._contains_workflow(full_text):
            logger.info("对话中未检测到可提取的工作流")
            return None
        
        # 提取步骤
        steps = self._extract_steps(full_text)
        if not steps:
            logger.warning("未能提取到有效步骤")
            return None
        
        # 提取参数
        parameters = self._extract_parameters(full_text)
        
        # 生成名称和描述
        if not skill_name:
            skill_name = self._generate_skill_name(full_text)
        if not skill_description:
            skill_description = self._generate_description(full_text)
        
        skill = Skill(
            name=skill_name,
            description=skill_description,
            parameters=parameters,
            steps=steps,
            tags=self._extract_tags(full_text),
            author="learner",
            is_builtin=False
        )
        
        logger.info(f"从对话中提取 Skill: {skill.name} ({len(steps)} 个步骤)")
        return skill
    
    async def learn_with_llm(
        self,
        conversation: List[Dict[str, str]],
        skill_name: str = None
    ) -> Optional[Skill]:
        """使用 LLM 辅助从对话中提取 Skill"""
        if not self.llm_router:
            return self.learn_from_conversation(conversation, skill_name)
        
        # 构建提取提示词
        conversation_text = "\n".join([
            f"{'用户' if msg['role'] == 'user' else '助手'}: {msg['content']}"
            for msg in conversation[-10:]  # 最近10轮
        ])
        
        prompt = f"""请从以下对话中提取一个可复用的工作流（Skill）。

对话内容：
{conversation_text}

请分析对话中是否包含可复用的多步骤工作流程。如果包含，请以JSON格式输出：

{{
    "name": "skill_name",
    "description": "简短的技能描述",
    "parameters": [
        {{
            "name": "参数名",
            "description": "参数描述",
            "type": "string|number|boolean",
            "required": true
        }}
    ],
    "steps": [
        {{
            "name": "步骤名称",
            "step_type": "llm_call|tool_call|condition|output",
            "description": "步骤描述",
            "config": {{}},
            "output_var": "变量名"
        }}
    ],
    "tags": ["tag1", "tag2"]
}}

如果对话中不包含可复用的工作流程，请输出 null。
只输出JSON，不要其他解释。"""

        try:
            messages = [{"role": "user", "content": prompt}]
            response = await self.llm_router.chat(messages)
            
            # 解析 JSON
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return self._parse_skill_from_dict(data)
            
            if "null" in response.lower():
                return None
                
        except Exception as e:
            logger.warning(f"LLM Skill 提取失败: {e}")
        
        # 回退到规则提取
        return self.learn_from_conversation(conversation, skill_name)
    
    def _merge_conversation(self, conversation: List[Dict[str, str]]) -> str:
        """合并对话内容"""
        texts = []
        for msg in conversation:
            role = msg.get('role', '')
            content = msg.get('content', '')
            texts.append(f"[{role}] {content}")
        return "\n".join(texts)
    
    def _contains_workflow(self, text: str) -> bool:
        """检测文本是否包含工作流"""
        patterns = self._extract_patterns["step_indicators"]
        for pattern in patterns:
            if re.search(pattern, text):
                return True
        
        keywords = self._extract_patterns["workflow_keywords"]
        text_lower = text.lower()
        for kw in keywords:
            if kw in text_lower:
                return True
        
        return False
    
    def _extract_steps(self, text: str) -> List[SkillStep]:
        """从文本中提取步骤"""
        steps = []
        
        # 尝试匹配 "第X步" 或 "Step X" 格式
        step_pattern = r'(?:第[一二三四五六七八九十\d]+步|Step\s*\d+)[：:.\s]*(.+?)(?=(?:第[一二三四五六七八九十\d]+步|Step\s*\d+)|$)'
        matches = list(re.finditer(step_pattern, text, re.DOTALL))
        
        if matches:
            for i, match in enumerate(matches):
                step_content = match.group(1).strip()
                step = self._parse_step_content(step_content, i)
                if step:
                    steps.append(step)
        else:
            # 尝试按顺序词分割
            steps = self._extract_steps_by_keywords(text)
        
        return steps
    
    def _extract_steps_by_keywords(self, text: str) -> List[SkillStep]:
        """按顺序关键词提取步骤"""
        steps = []
        keywords = ["首先", "第一步", "先", "接着", "然后", "第二步", "随后", 
                    "再", "之后", "最后", "第三步", "最终"]
        
        # 构建分割模式
        pattern = '(' + '|'.join(keywords) + ')'
        parts = re.split(pattern, text)
        
        if len(parts) > 1:
            for i in range(1, len(parts), 2):
                if i + 1 < len(parts):
                    keyword = parts[i]
                    content = parts[i + 1].strip()
                    if content:
                        step = self._parse_step_content(f"{keyword}{content}", len(steps))
                        if step:
                            steps.append(step)
        
        return steps
    
    def _parse_step_content(self, content: str, index: int) -> Optional[SkillStep]:
        """解析步骤内容"""
        content = content.strip()
        if len(content) < 5:
            return None
        
        # 检测步骤类型
        step_type = self._detect_step_type(content)
        
        # 提取配置
        config = self._extract_step_config(content, step_type)
        
        return SkillStep(
            name=f"步骤{index + 1}",
            description=content[:100],
            step_type=step_type,
            config=config,
            output_var=f"step_{index + 1}_result"
        )
    
    def _detect_step_type(self, content: str) -> StepType:
        """检测步骤类型"""
        content_lower = content.lower()
        
        # 检测条件
        for kw in self._extract_patterns["condition_keywords"]:
            if kw in content_lower:
                return StepType.CONDITION
        
        # 检测循环
        for kw in self._extract_patterns["loop_keywords"]:
            if kw in content_lower:
                return StepType.LOOP
        
        # 检测工具调用（需要较明确的动词）
        tool_keywords = ["查询", "搜索", "计算", "调用工具", "使用工具", "执行工具", "tool_call"]
        for kw in tool_keywords:
            if kw in content_lower:
                return StepType.TOOL_CALL
        
        # 检测输出
        output_keywords = ["输出", "生成", "返回", "给出", "输出结果", "produce", "generate output"]
        for kw in output_keywords:
            if kw in content_lower:
                return StepType.OUTPUT
        
        # 默认 LLM 调用
        return StepType.LLM_CALL
    
    def _extract_step_config(self, content: str, step_type: StepType) -> Dict[str, Any]:
        """提取步骤配置"""
        config = {}
        
        if step_type == StepType.LLM_CALL:
            config["prompt_template"] = content
            config["system_prompt"] = "你是一个专业的医学AI助手。"
        
        elif step_type == StepType.TOOL_CALL:
            # 尝试提取工具名
            tool_match = re.search(r'(?:使用|调用)\s*["\']?(\w+)["\']?', content)
            if tool_match:
                config["tool_name"] = tool_match.group(1)
            else:
                config["tool_name"] = "search"
            config["arguments"] = {"query": content}
        
        elif step_type == StepType.CONDITION:
            config["condition_expression"] = self._extract_condition(content)
            config["true_branch"] = "next"
            config["false_branch"] = "skip"
        
        elif step_type == StepType.OUTPUT:
            config["output_template"] = "${" + content + "}"
        
        return config
    
    def _extract_condition(self, content: str) -> str:
        """从文本中提取条件表达式"""
        # 简单的条件提取
        patterns = [
            r'如果\s*(.+?)\s*则',
            r'若\s*(.+?)\s*则',
            r'当\s*(.+?)\s*时',
        ]
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1).strip()
        return "true"
    
    def _extract_parameters(self, text: str) -> List[SkillParameter]:
        """从文本中提取参数"""
        parameters = []
        
        # 查找 "参数名: 描述" 格式
        param_pattern = r'[\n\s](\w+)[：:]\s*(.+?)(?=[\n,，;；]|$)'
        matches = re.findall(param_pattern, text)
        
        seen = set()
        for name, desc in matches:
            name = name.strip()
            if name in seen or len(name) > 20:
                continue
            seen.add(name)
            
            # 推断类型
            param_type = self._infer_param_type(desc)
            
            parameters.append(SkillParameter(
                name=name,
                description=desc.strip()[:100],
                type=param_type,
                required=True
            ))
        
        return parameters
    
    def _infer_param_type(self, description: str) -> str:
        """推断参数类型"""
        desc_lower = description.lower()
        
        if any(kw in desc_lower for kw in ["数量", "数值", "数字", "年龄", "大小", "number"]):
            return "number"
        elif any(kw in desc_lower for kw in ["是否", "真假", "boolean", "true/false"]):
            return "boolean"
        elif any(kw in desc_lower for kw in ["列表", "数组", "多个", "array", "list"]):
            return "array"
        elif any(kw in desc_lower for kw in ["对象", "字典", "object", "dict"]):
            return "object"
        
        return "string"
    
    def _generate_skill_name(self, text: str) -> str:
        """生成 Skill 名称"""
        # 尝试从文本中提取主题
        patterns = [
            r'(?:关于|针对|用于)?(.+?)(?:流程|步骤|workflow|protocol|指南)',
            r'如何(.+?)(?:的|之)?',
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                name = match.group(1).strip()
                if 2 < len(name) < 30:
                    return name + "_workflow"
        
        return f"learned_skill_{datetime.now().strftime('%m%d_%H%M')}"
    
    def _generate_description(self, text: str) -> str:
        """生成描述"""
        # 取前100字符作为描述
        desc = text[:150].replace('\n', ' ')
        return desc
    
    def _extract_tags(self, text: str) -> List[str]:
        """提取标签"""
        tags = ["auto_learned"]
        
        medical_tags = {
            "诊断": "diagnosis",
            "治疗": "treatment",
            "影像": "imaging",
            "药物": "medication",
            "手术": "surgery",
            "科研": "research",
            "写作": "writing",
            "分析": "analysis",
            "临床": "clinical",
            "病理": "pathology",
        }
        
        for cn, en in medical_tags.items():
            if cn in text:
                tags.append(en)
        
        return tags
    
    def _parse_skill_from_dict(self, data: Dict[str, Any]) -> Optional[Skill]:
        """从字典解析 Skill"""
        try:
            steps_data = data.get("steps", [])
            steps = []
            for i, step_data in enumerate(steps_data):
                step_data["step_type"] = StepType(step_data.get("step_type", "llm_call"))
                steps.append(SkillStep(**step_data))
            
            params_data = data.get("parameters", [])
            parameters = [SkillParameter(**p) for p in params_data]
            
            return Skill(
                name=data["name"],
                description=data.get("description", ""),
                parameters=parameters,
                steps=steps,
                tags=data.get("tags", ["llm_extracted"]),
                author="llm_learner",
                is_builtin=False
            )
        except Exception as e:
            logger.warning(f"解析 Skill JSON 失败: {e}")
            return None
    
    def suggest_skills(self, conversation: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """建议可能可以提取 Skill 的对话片段"""
        suggestions = []
        
        # 滑动窗口检查
        window_size = 4
        for i in range(0, len(conversation) - window_size + 1):
            window = conversation[i:i + window_size]
            text = self._merge_conversation(window)
            
            if self._contains_workflow(text):
                suggestions.append({
                    "start_index": i,
                    "end_index": i + window_size,
                    "preview": text[:200] + "...",
                    "confidence": self._estimate_confidence(text)
                })
        
        return suggestions
    
    def _estimate_confidence(self, text: str) -> float:
        """评估提取置信度"""
        score = 0.0
        
        # 步骤指示器数量
        step_count = 0
        for pattern in self._extract_patterns["step_indicators"]:
            step_count += len(re.findall(pattern, text))
        score += min(step_count * 0.2, 0.6)
        
        # 工作流关键词
        for kw in self._extract_patterns["workflow_keywords"]:
            if kw in text.lower():
                score += 0.1
                break
        
        # 长度适中
        if 100 < len(text) < 2000:
            score += 0.2
        
        return min(score, 1.0)
