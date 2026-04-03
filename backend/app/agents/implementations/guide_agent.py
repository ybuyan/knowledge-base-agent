"""
GuideAgent - 流程指引 Agent

通过多轮对话收集信息，然后生成流程操作指引
"""
import logging
from typing import Dict, Any
from app.agents.base import BaseAgent, agent_engine
from app.skills.engine import SkillEngine

logger = logging.getLogger(__name__)


class GuideAgent(BaseAgent):
    
    @property
    def agent_id(self) -> str:
        return "guide_agent"
    
    @property
    def name(self) -> str:
        return "流程指引Agent"
    
    def __init__(self):
        self.skill_engine = SkillEngine()
    
    def _match_guide_skill(self, query: str, history: list = None) -> str:
        """
        根据 triggers 匹配对应的指引 skill
        
        Args:
            query: 用户查询
            history: 对话历史
            
        Returns:
            匹配到的 skill_id，如果没有匹配则返回 None
        """
        logger.info("🔍 [GUIDE] 开始匹配 guide skill | query='%s'", query)
        logger.info("🔍 [GUIDE] history 长度: %d", len(history) if history else 0)
        if history:
            logger.info("🔍 [GUIDE] history 内容: %s", [f"{msg.get('role')}:{msg.get('content', '')[:20]}" for msg in history[-4:]])
        
        # 获取所有 guide 类型的 skills
        for skill_id, skill_def in self.skill_engine.skill_loader._cache.items():
            skill_type = skill_def.frontmatter.get("skill_type", "qa")
            
            # 只匹配 guide 类型的 skills
            if skill_type != "guide":
                continue
            
            logger.debug("   检查 skill: %s (type=%s)", skill_id, skill_type)
            
            # 检查 triggers
            triggers = skill_def.frontmatter.get("triggers", [])
            
            # 首先检查当前查询
            for trigger in triggers:
                if trigger in query:
                    logger.info("✅ [GUIDE] 匹配成功 | skill_id='%s' | trigger='%s' | query='%s'", 
                               skill_id, trigger, query)
                    return skill_id
            
            # 如果当前查询没有匹配，检查历史记录（最近3轮）
            if history:
                recent_history = history[-6:]  # 最近3轮对话（每轮2条消息）
                for msg in recent_history:
                    # 检查用户和助手的消息（助手消息中也可能包含关键词）
                    content = msg.get("content", "")
                    for trigger in triggers:
                        if trigger in content:
                            logger.info("✅ [GUIDE] 通过历史记录匹配成功 | skill_id='%s' | trigger='%s' | history_role='%s' | history_content='%s' | current_query='%s'", 
                                       skill_id, trigger, msg.get("role"), content[:30], query)
                            return skill_id
        
        logger.warning("❌ [GUIDE] 未匹配到任何 guide skill | query='%s'", query)
        return None
    
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行流程指引
        
        Args:
            input_data: 包含 query, session_id, history 等
            
        Returns:
            包含 answer 的字典
        """
        query: str = input_data.get("query", "")
        session_id: str = input_data.get("session_id", "")
        history: list = input_data.get("history", [])
        
        logger.info("🚀 [GUIDE] GuideAgent 开始执行 | query='%s' | session_id='%s'", 
                   query, session_id)
        logger.info("🚀 [GUIDE] 接收到的 history 长度: %d", len(history))
        
        if not query:
            return {"answer": "请问您需要什么帮助？", "intent": "guide"}
        
        # 匹配对应的指引 skill（使用历史记录辅助匹配）
        skill_id = self._match_guide_skill(query, history=history)
        
        if not skill_id:
            logger.warning("⚠️  [GUIDE] 未找到匹配的 skill，返回默认回复")
            return {
                "answer": "抱歉，我暂时无法提供该流程的指引。请联系管理员。",
                "intent": "guide",
            }
        
        logger.info("📋 [GUIDE] 准备执行 skill | skill_id='%s'", skill_id)
        
        # 构建上下文
        context = {
            "query": query,
            "question": query,  # LLMGenerator 需要 question 变量
            "session_id": session_id,
            "history": history,
        }
        
        try:
            # 执行 skill
            logger.info("⚙️  [GUIDE] 开始执行 SkillEngine | skill_id='%s' | context_keys=%s", 
                       skill_id, list(context.keys()))
            result = await self.skill_engine.execute(skill_id, context)
            
            answer = result.get("answer", "")
            logger.info("✅ [GUIDE] Skill 执行成功 | skill_id='%s' | answer_length=%d", 
                       skill_id, len(answer))
            
            # 调试：如果 answer 为空，记录详细信息
            if not answer or len(answer.strip()) == 0:
                logger.error("⚠️  [GUIDE] 警告：返回的 answer 为空！| result=%s", result)
            
            return {
                "answer": answer,
                "session_id": session_id,
                "intent": "guide",  # 标记为 guide 意图，防止 chat API 再次调用 QA Agent
            }
            
        except Exception as e:
            logger.error("❌ [GUIDE] Skill 执行失败 | skill_id='%s' | error=%s", skill_id, str(e))
            import traceback
            logger.error(traceback.format_exc())
            return {
                "answer": "抱歉，生成指引时出现错误。请稍后再试。",
                "session_id": session_id,
                "intent": "guide",
            }


agent_engine.register(GuideAgent())
