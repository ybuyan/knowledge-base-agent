"""
SkillEngine - Skill 执行引擎

Skill 定义完全来自 SKILL.md 文件（skills/definitions/ 目录）。
遵循 Agent Skills 开放标准。
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

from app.skills.skill_loader import SkillLoader

logger = logging.getLogger(__name__)

_DEFINITIONS_DIR = Path(__file__).parent / "definitions"


class SkillEngine:
    """Skill 执行引擎"""

    def __init__(self):
        from app.skills.registry import ProcessorRegistry
        self.registry = ProcessorRegistry
        self.skill_loader = SkillLoader(_DEFINITIONS_DIR)
        self.skill_loader.load_all()

    def get_skill(self, skill_id: str) -> Optional[Dict[str, Any]]:
        skill_def = self.skill_loader.get(skill_id)
        if not skill_def:
            raise ValueError(f"Skill not found: '{skill_id}'。请在 skills/definitions/ 下创建对应的 SKILL.md")
        return skill_def.to_dict()

    def list_skills(self) -> List[Dict[str, Any]]:
        """列出所有可用 skill 摘要（仅 name + description，避免 context bloat）"""
        return self.skill_loader.list_skills()

    def reload(self, skill_id: Optional[str] = None):
        """热重载 skill 定义"""
        self.skill_loader.reload(skill_id)

    def resolve_params(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """解析参数中的 ${var} 变量引用"""
        resolved = {}
        for key, value in params.items():
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                resolved[key] = context.get(value[2:-1], value)
            elif isinstance(value, dict):
                resolved[key] = self.resolve_params(value, context)
            else:
                resolved[key] = value
        return resolved

    async def execute(self, skill_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        skill = self.get_skill(skill_id)

        if not skill.get("enabled", True):
            raise ValueError(f"Skill is disabled: {skill_id}")

        logger.info("🎬 [SKILL] 开始执行 Skill | skill_id='%s' | version='%s' | type='%s'", 
                   skill_id, skill.get("version", "?"), skill.get("skill_type", "qa"))

        context = input_data.copy()
        context["_skill"] = skill

        pipeline = skill.get("pipeline", [])
        logger.info("📝 [SKILL] Pipeline 步骤数: %d | skill_id='%s'", len(pipeline), skill_id)

        for i, step in enumerate(pipeline, 1):
            processor_name = step.get("processor")
            step_name = step.get("step", processor_name)
            params = step.get("params", {})

            processor = self.registry.get(processor_name)
            resolved_params = self.resolve_params(params, context)

            logger.info("   [%d/%d] 执行步骤 | step='%s' | processor='%s' | params=%s", 
                       i, len(pipeline), step_name, processor_name, resolved_params)
            
            result = await processor.process(context, resolved_params)
            context.update(result)
            context[f"_step_{step_name}"] = result
            
            logger.debug("   [%d/%d] 步骤完成 | result_keys=%s", i, len(pipeline), list(result.keys()))

        output = self._extract_output(context, skill.get("output", {}))
        logger.info("✅ [SKILL] Skill 执行完成 | skill_id='%s' | output_keys=%s", 
                   skill_id, list(output.keys()))
        
        return output

    def _extract_output(self, context: Dict[str, Any], output_config: Dict[str, Any]) -> Dict[str, Any]:
        if not output_config:
            return context
        return {key: context[key] for key in output_config.get("return", []) if key in context}
