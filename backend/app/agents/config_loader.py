"""
Agent 配置加载器
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

_CONFIG_FILE = Path(__file__).parent / "config.json"


class AgentConfigLoader:
    """Agent 配置加载器"""
    
    def __init__(self):
        self._config: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        try:
            if _CONFIG_FILE.exists():
                with open(_CONFIG_FILE, "r", encoding="utf-8") as f:
                    self._config = json.load(f)
                logger.info("✅ Agent 配置加载成功 | version=%s", 
                           self._config.get("version", "unknown"))
            else:
                logger.warning("⚠️  Agent 配置文件不存在，使用默认配置")
                self._config = self._get_default_config()
        except Exception as e:
            logger.error("❌ Agent 配置加载失败: %s，使用默认配置", str(e))
            self._config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "version": "1.0",
            "orchestrator": {
                "intent_detection": {
                    "method": "llm",
                    "fallback_to_keyword": True
                }
            },
            "guide_agent": {
                "skill_matching": {
                    "method": "trigger"
                }
            }
        }
    
    def get_intent_detection_method(self) -> str:
        """获取意图识别方法"""
        return self._config.get("orchestrator", {}).get("intent_detection", {}).get("method", "llm")
    
    def should_fallback_to_keyword(self) -> bool:
        """是否回退到关键词匹配"""
        return self._config.get("orchestrator", {}).get("intent_detection", {}).get("fallback_to_keyword", True)
    
    def get_skill_matching_method(self) -> str:
        """获取 Skill 匹配方法"""
        return self._config.get("guide_agent", {}).get("skill_matching", {}).get("method", "trigger")
    
    def reload(self):
        """重新加载配置"""
        logger.info("🔄 重新加载 Agent 配置")
        self._load_config()


# 全局配置实例
agent_config = AgentConfigLoader()
