import logging
from typing import Dict, Any, AsyncGenerator
from app.skills.base import BaseProcessor, ProcessorRegistry
from app.core.llm import get_llm, call_llm, stream_llm
from app.core.config_loader import config_loader

logger = logging.getLogger(__name__)


@ProcessorRegistry.register("LLMGenerator")
class LLMGenerator(BaseProcessor):
    
    @property
    def name(self) -> str:
        return "LLMGenerator"
    
    async def process(self, context: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        prompt_template_id = params.get("prompt_template", "qa_rag")
        stream = params.get("stream", False)
        
        logger.info("🤖 [LLM] 开始处理 | prompt_template='%s' | stream=%s", 
                   prompt_template_id, stream)
        
        prompt_config = config_loader.get_prompt(prompt_template_id)
        if not prompt_config:
            logger.error("❌ [LLM] Prompt 模板未找到 | template_id='%s'", prompt_template_id)
            raise ValueError(f"Prompt template not found: {prompt_template_id}")
        
        logger.info("📄 [LLM] 加载 Prompt 配置 | template_id='%s' | name='%s'", 
                   prompt_template_id, prompt_config.get("name", ""))
        
        template = prompt_config["template"]
        system_prompt = template.get("system", "")
        user_template = template.get("user", "")
        
        variables = prompt_config.get("variables", [])
        defaults = prompt_config.get("defaults", {})
        
        prompt_vars = {}
        for var in variables:
            prompt_vars[var] = context.get(var, defaults.get(var, ""))
        
        logger.debug("   变量映射: %s", {k: f"{str(v)[:50]}..." if len(str(v)) > 50 else v 
                                        for k, v in prompt_vars.items()})
        
        user_prompt = user_template.format(**prompt_vars) if user_template else ""
        # system_prompt 也支持变量替换（用于动态注入流程数据等场景）
        if system_prompt and prompt_vars:
            try:
                system_prompt = system_prompt.format(**prompt_vars)
            except (KeyError, ValueError):
                pass  # 模板中有未定义变量时保持原样
        
        # 获取对话历史
        history = context.get("history", [])
        
        logger.info("💬 [LLM] 准备调用 LLM | system_prompt_length=%d | user_prompt_length=%d | history_length=%d", 
                   len(system_prompt), len(user_prompt), len(history))
        
        if stream:
            context["_stream"] = True
            context["_system_prompt"] = system_prompt
            context["_user_prompt"] = user_prompt
            context["_history"] = history
            logger.info("🌊 [LLM] 流式模式已启用")
            return {"answer": "", "streaming": True}
        
        answer = await call_llm(user_prompt, system_prompt, history=history)
        
        logger.info("✅ [LLM] LLM 调用完成 | answer_length=%d | prompt_template='%s'", 
                   len(answer), prompt_template_id)
        
        # 调试：如果 answer 为空，记录详细信息
        if not answer or len(answer.strip()) == 0:
            logger.error("⚠️  [LLM] 警告：LLM 返回空内容！| user_prompt='%s' | system_prompt_length=%d | history_length=%d", 
                        user_prompt[:100], len(system_prompt), len(history))
        
        # from app.config import settings
        
        return {
            "answer": answer,
            # "model": settings.llm_model
        }
    
    async def stream(self, context: Dict[str, Any]) -> AsyncGenerator[str, None]:
        system_prompt = context.get("_system_prompt", "")
        user_prompt = context.get("_user_prompt", "")
        history = context.get("_history", [])
        
        async for chunk in stream_llm(user_prompt, system_prompt, history=history):
            yield chunk
