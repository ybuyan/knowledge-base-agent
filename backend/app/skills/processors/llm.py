from typing import Dict, Any, AsyncGenerator
from app.skills.base import BaseProcessor, ProcessorRegistry
from app.core.llm import get_llm, call_llm, stream_llm
from app.core.config_loader import config_loader


@ProcessorRegistry.register("LLMGenerator")
class LLMGenerator(BaseProcessor):
    
    @property
    def name(self) -> str:
        return "LLMGenerator"
    
    async def process(self, context: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        prompt_template_id = params.get("prompt_template", "qa_rag")
        stream = params.get("stream", False)
        
        prompt_config = config_loader.get_prompt(prompt_template_id)
        if not prompt_config:
            raise ValueError(f"Prompt template not found: {prompt_template_id}")
        
        template = prompt_config["template"]
        system_prompt = template.get("system", "")
        user_template = template.get("user", "")
        
        variables = prompt_config.get("variables", [])
        defaults = prompt_config.get("defaults", {})
        
        prompt_vars = {}
        for var in variables:
            prompt_vars[var] = context.get(var, defaults.get(var, ""))
        
        user_prompt = user_template.format(**prompt_vars)
        
        if stream:
            context["_stream"] = True
            context["_system_prompt"] = system_prompt
            context["_user_prompt"] = user_prompt
            return {"answer": "", "streaming": True}
        
        answer = await call_llm(user_prompt, system_prompt)
        
        # from app.config import settings
        
        return {
            "answer": answer,
            # "model": settings.llm_model
        }
    
    async def stream(self, context: Dict[str, Any]) -> AsyncGenerator[str, None]:
        system_prompt = context.get("_system_prompt", "")
        user_prompt = context.get("_user_prompt", "")
        
        async for chunk in stream_llm(user_prompt, system_prompt):
            yield chunk
