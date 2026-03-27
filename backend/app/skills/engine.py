import re
from typing import Dict, Any, List, Optional
from app.core.config_loader import config_loader


class SkillEngine:
    """Skill 执行引擎"""
    
    def __init__(self):
        from app.skills.registry import ProcessorRegistry
        self.registry = ProcessorRegistry
    
    def get_skill(self, skill_id: str) -> Optional[Dict[str, Any]]:
        return config_loader.get_skill(skill_id)
    
    def resolve_params(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """解析参数中的变量引用"""
        resolved = {}
        for key, value in params.items():
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                var_name = value[2:-1]
                resolved[key] = context.get(var_name, value)
            elif isinstance(value, dict):
                resolved[key] = self.resolve_params(value, context)
            else:
                resolved[key] = value
        return resolved
    
    async def execute(self, skill_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        skill = self.get_skill(skill_id)
        if not skill:
            raise ValueError(f"Skill not found: {skill_id}")
        
        if not skill.get("enabled", True):
            raise ValueError(f"Skill is disabled: {skill_id}")
        
        context = input_data.copy()
        context["_skill"] = skill
        
        pipeline = skill.get("pipeline", [])
        
        for step in pipeline:
            processor_name = step.get("processor")
            params = step.get("params", {})
            
            processor = self.registry.get(processor_name)
            resolved_params = self.resolve_params(params, context)
            
            result = await processor.process(context, resolved_params)
            context.update(result)
            context[f"_step_{step.get('step')}"] = result
        
        output_config = skill.get("output", {})
        return self.extract_output(context, output_config)
    
    def extract_output(self, context: Dict[str, Any], output_config: Dict[str, Any]) -> Dict[str, Any]:
        """提取输出"""
        if not output_config:
            return context
        
        result = {}
        for key in output_config.get("return", []):
            if key in context:
                result[key] = context[key]
        
        return result
