"""
Skill 执行器
"""

import asyncio
import re
from typing import Dict, List, Any, Optional
from loguru import logger

from .models import Skill, SkillStep, StepType, SkillExecutionResult
from .registry import SkillRegistry


class SkillExecutor:
    """Skill 执行器 - 按步骤执行 Skill"""
    
    def __init__(self, skill_registry: SkillRegistry, 
                 llm_router=None, tool_executor=None, agent_orchestrator=None):
        self.skill_registry = skill_registry
        self.llm_router = llm_router
        self.tool_executor = tool_executor
        self.agent_orchestrator = agent_orchestrator
    
    async def execute(self, skill_name: str, arguments: Dict[str, Any],
                      context: Dict[str, Any] = None) -> SkillExecutionResult:
        """执行 Skill"""
        skill = self.skill_registry.get(skill_name)
        if not skill:
            return SkillExecutionResult(
                skill_id="", skill_name=skill_name,
                success=False, error=f"Skill '{skill_name}' 未找到"
            )
        
        # 验证参数
        valid, errors = skill.validate_parameters(arguments)
        if not valid:
            return SkillExecutionResult(
                skill_id=skill.id, skill_name=skill.name,
                success=False, error=f"参数验证失败: {', '.join(errors)}"
            )
        
        # 初始化变量上下文
        variables = dict(arguments)
        if context:
            variables.update(context)
        
        result = SkillExecutionResult(
            skill_id=skill.id,
            skill_name=skill.name,
            success=True,
            variables=variables
        )
        
        logger.info(f"开始执行 Skill: {skill.name}，共 {len(skill.steps)} 个步骤")
        
        try:
            for step in skill.steps:
                # 检查执行条件
                if step.condition and not self._evaluate_condition(step.condition, variables):
                    logger.debug(f"步骤 '{step.name}' 条件不满足，跳过")
                    continue
                
                # 执行步骤（带重试）
                step_result = await self._execute_step_with_retry(step, variables)
                
                result.step_results[step.id] = step_result
                
                if step.output_var:
                    variables[step.output_var] = step_result
                
                # 检查是否失败
                if step_result is None or (isinstance(step_result, dict) and not step_result.get('success', True)):
                    if step.on_error == "stop":
                        result.success = False
                        result.error = f"步骤 '{step.name}' 执行失败"
                        result.failed_step_id = step.id
                        break
                    elif step.on_error == "continue":
                        logger.warning(f"步骤 '{step.name}' 失败，继续执行")
                        continue
                    elif step.fallback_step_id:
                        # 执行 fallback 步骤
                        fallback_step = skill.get_step_by_id(step.fallback_step_id)
                        if fallback_step:
                            fallback_result = await self._execute_step(fallback_step, variables)
                            variables[fallback_step.output_var or "fallback_result"] = fallback_result
            
            # 最终输出
            if result.success:
                result.output = variables.get("output", variables)
            
        except Exception as e:
            logger.error(f"Skill 执行异常: {e}")
            result.success = False
            result.error = str(e)
        
        from datetime import datetime
        result.end_time = datetime.now()
        
        # 更新统计
        self.skill_registry.update_usage_stats(skill.name, result.success)
        
        logger.info(f"Skill '{skill.name}' 执行完成，耗时 {result.duration_ms}ms，成功: {result.success}")
        return result
    
    async def _execute_step_with_retry(self, step: SkillStep, variables: Dict[str, Any]) -> Any:
        """带重试的步骤执行"""
        last_error = None
        
        for attempt in range(step.retry_count + 1):
            try:
                return await self._execute_step(step, variables)
            except Exception as e:
                last_error = e
                logger.warning(f"步骤 '{step.name}' 第 {attempt + 1} 次尝试失败: {e}")
                if attempt < step.retry_count:
                    await asyncio.sleep(step.retry_delay)
        
        raise last_error
    
    async def _execute_step(self, step: SkillStep, variables: Dict[str, Any]) -> Any:
        """执行单个步骤"""
        config = self._resolve_variables(step.config, variables)
        
        if step.step_type == StepType.LLM_CALL:
            return await self._execute_llm_call(config, variables)
        
        elif step.step_type == StepType.TOOL_CALL:
            return await self._execute_tool_call(config, variables)
        
        elif step.step_type == StepType.AGENT_CALL:
            return await self._execute_agent_call(config, variables)
        
        elif step.step_type == StepType.SKILL_CALL:
            return await self._execute_skill_call(config, variables)
        
        elif step.step_type == StepType.CONDITION:
            return self._execute_condition(config, variables)
        
        elif step.step_type == StepType.LOOP:
            return await self._execute_loop(config, variables)
        
        elif step.step_type == StepType.USER_INPUT:
            return await self._execute_user_input(config, variables)
        
        elif step.step_type == StepType.OUTPUT:
            return self._execute_output(config, variables)
        
        else:
            raise ValueError(f"未知的步骤类型: {step.step_type}")
    
    async def _execute_llm_call(self, config: Dict, variables: Dict) -> str:
        """执行 LLM 调用"""
        prompt = config.get('prompt_template', '')
        system_prompt = config.get('system_prompt', '')
        model = config.get('model', None)
        
        # 渲染提示词模板
        prompt = self._render_template(prompt, variables)
        
        if self.llm_router:
            messages = []
            if system_prompt:
                messages.append({'role': 'system', 'content': system_prompt})
            messages.append({'role': 'user', 'content': prompt})
            
            response = await self.llm_router.chat(messages, model=model)
            return response
        
        return f"[LLM Mock] {prompt[:50]}..."
    
    async def _execute_tool_call(self, config: Dict, variables: Dict) -> Any:
        """执行工具调用"""
        tool_name = config.get('tool_name', '')
        arguments = config.get('arguments', {})
        
        # 解析参数映射
        resolved_args = {}
        for key, value in arguments.items():
            if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                var_name = value[2:-1]
                resolved_args[key] = variables.get(var_name)
            else:
                resolved_args[key] = value
        
        if self.tool_executor:
            return await self.tool_executor.execute(tool_name, resolved_args)
        
        return {"tool": tool_name, "args": resolved_args, "mock": True}
    
    async def _execute_agent_call(self, config: Dict, variables: Dict) -> str:
        """执行 Agent 调用"""
        agent_role = config.get('agent_role', '')
        task = config.get('task', '')
        task = self._render_template(task, variables)
        
        if self.agent_orchestrator:
            result = await self.agent_orchestrator.delegate(task, [agent_role])
            return result.get(agent_role, '')
        
        return f"[Agent Mock] {agent_role}: {task[:50]}..."
    
    async def _execute_skill_call(self, config: Dict, variables: Dict) -> Any:
        """执行嵌套 Skill 调用"""
        skill_name = config.get('skill_name', '')
        arguments = config.get('arguments', {})
        
        resolved_args = {}
        for key, value in arguments.items():
            if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                var_name = value[2:-1]
                resolved_args[key] = variables.get(var_name)
            else:
                resolved_args[key] = value
        
        return await self.execute(skill_name, resolved_args, variables)
    
    def _execute_condition(self, config: Dict, variables: Dict) -> bool:
        """执行条件判断"""
        expression = config.get('condition_expression', 'true')
        return self._evaluate_condition(expression, variables)
    
    async def _execute_loop(self, config: Dict, variables: Dict) -> List[Any]:
        """执行循环"""
        max_iterations = config.get('max_iterations', 10)
        body_steps = config.get('body_steps', [])
        results = []
        
        for i in range(max_iterations):
            variables['_iteration'] = i
            
            # 检查循环条件
            condition = config.get('loop_condition', '')
            if condition and not self._evaluate_condition(condition, variables):
                break
            
            # 执行循环体
            for step_data in body_steps:
                step = SkillStep(**step_data)
                step_result = await self._execute_step(step, variables)
                results.append(step_result)
        
        return results
    
    async def _execute_user_input(self, config: Dict, variables: Dict) -> str:
        """等待用户输入（在异步环境中返回占位符）"""
        prompt = config.get('prompt', '请输入:')
        # 在 CLI 环境中可以实际等待输入
        # 在 Web/桌面环境中需要特殊处理
        return f"[等待用户输入] {prompt}"
    
    def _execute_output(self, config: Dict, variables: Dict) -> Any:
        """执行输出"""
        output_template = config.get('output_template', '')
        return self._render_template(output_template, variables)
    
    def _render_template(self, template: str, variables: Dict) -> str:
        """渲染模板变量 ${var_name}"""
        def replace_var(match):
            var_name = match.group(1)
            value = variables.get(var_name, match.group(0))
            return str(value) if value is not None else match.group(0)
        
        return re.sub(r'\$\{([^}]+)\}', replace_var, template)
    
    def _evaluate_condition(self, expression: str, variables: Dict) -> bool:
        """安全地评估条件表达式"""
        try:
            # 简单的表达式求值，只允许变量和基本运算符
            # 替换变量引用
            def replace_var(match):
                var_name = match.group(1)
                value = variables.get(var_name)
                if isinstance(value, str):
                    return repr(value)
                return str(value) if value is not None else 'None'
            
            expr = re.sub(r'\$\{([^}]+)\}', replace_var, expression)
            
            # 处理 true/false 关键字（JSON 风格 -> Python 风格）
            expr = expr.replace("true", "True").replace("false", "False")
            
            # 安全求值：只允许白名单字符
            allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.=<>!&|"\' +-*/()[]{}:,% ')
            if not all(c in allowed_chars for c in expr):
                logger.warning(f"条件表达式包含不安全字符: {expression}")
                return False
            
            result = eval(expr, {"__builtins__": {}}, {})
            return bool(result)
        except Exception as e:
            logger.warning(f"条件表达式求值失败 '{expression}': {e}")
            return False
    
    def _resolve_variables(self, config: Dict, variables: Dict) -> Dict:
        """解析配置中的变量引用"""
        resolved = {}
        for key, value in config.items():
            if isinstance(value, str):
                resolved[key] = self._render_template(value, variables)
            elif isinstance(value, dict):
                resolved[key] = self._resolve_variables(value, variables)
            elif isinstance(value, list):
                resolved[key] = [
                    self._render_template(v, variables) if isinstance(v, str) else v
                    for v in value
                ]
            else:
                resolved[key] = value
        return resolved
