import json
import os
from typing import Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

DEFAULT_CONSTRAINTS = {
    "constraints": {
        "retrieval": {
            "enabled": True,
            "min_similarity_score": 0.7,
            "min_relevant_docs": 1,
            "max_relevant_docs": 5,
            "content_coverage_threshold": 0.3
        },
        "generation": {
            "strict_mode": True,
            "allow_general_knowledge": False,
            "require_citations": True,
            "max_answer_length": 1000,
            "forbidden_topics": [],
            "forbidden_keywords": []
        },
        "validation": {
            "enabled": True,
            "check_source_attribution": True,
            "min_confidence_score": 0.6,
            "hallucination_detection": True
        },
        "fallback": {
            "no_result_message": "抱歉，我在知识库中没有找到相关信息。",
            "suggest_similar": True,
            "suggest_contact": True,
            "contact_info": "如有其他问题，请联系管理员。"
        },
        "suggest_questions": {
            "enabled": True,
            "count": 3,
            "types": ["相关追问", "深入探索", "对比分析"]
        }
    },
    "logging": {
        "enabled": True,
        "log_file": "data/logs/constraints.log",
        "log_level": "INFO"
    }
}


class ConstraintConfig:
    """Constraint configuration manager"""
    
    _instance: Optional['ConstraintConfig'] = None
    _config: Dict[str, Any] = {}
    _config_path: str = ""
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._config:
            self._load_config()
    
    def _get_config_path(self) -> str:
        """Get config file path"""
        backend_dir = Path(__file__).parent.parent.parent
        return str(backend_dir / "config" / "constraints.json")
    
    def _load_config(self):
        """Load configuration from file"""
        self._config_path = self._get_config_path()
        
        if os.path.exists(self._config_path):
            try:
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                self._config = loaded_config
                logger.info(f"Loaded constraints config from {self._config_path}")
                return True
            except Exception as e:
                logger.error(f"Failed to load constraints config: {e}")
                if not self._config:  # 只有在首次加载时才使用默认配置
                    self._config = DEFAULT_CONSTRAINTS
                return False
        else:
            logger.warning(f"Constraints config not found at {self._config_path}, using defaults")
            self._config = DEFAULT_CONSTRAINTS
            self._save_config()
            return True
    
    def _save_config(self):
        """Save configuration to file"""
        os.makedirs(os.path.dirname(self._config_path), exist_ok=True)
        with open(self._config_path, 'w', encoding='utf-8') as f:
            json.dump(self._config, f, indent=2, ensure_ascii=False)
    
    @property
    def retrieval(self) -> Dict[str, Any]:
        return self._config.get("constraints", {}).get("retrieval", DEFAULT_CONSTRAINTS["constraints"]["retrieval"])
    
    @property
    def generation(self) -> Dict[str, Any]:
        return self._config.get("constraints", {}).get("generation", DEFAULT_CONSTRAINTS["constraints"]["generation"])
    
    @property
    def validation(self) -> Dict[str, Any]:
        return self._config.get("constraints", {}).get("validation", DEFAULT_CONSTRAINTS["constraints"]["validation"])
    
    @property
    def fallback(self) -> Dict[str, Any]:
        return self._config.get("constraints", {}).get("fallback", DEFAULT_CONSTRAINTS["constraints"]["fallback"])
    
    @property
    def suggest_questions(self) -> Dict[str, Any]:
        return self._config.get("constraints", {}).get("suggest_questions", DEFAULT_CONSTRAINTS["constraints"]["suggest_questions"])
    
    def reload(self) -> bool:
        """
        重新加载配置文件
        
        用于在配置文件被外部修改后重新加载配置。
        
        Returns:
            bool: 是否成功重新加载
        """
        try:
            success = self._load_config()
            if success:
                logger.info("Constraints config reloaded successfully")
            else:
                logger.warning("Constraints config reload failed, keeping current config")
            return success
        except Exception as e:
            logger.error(f"Failed to reload constraints config: {e}")
            return False
    
    def get_all(self) -> Dict[str, Any]:
        """Get all constraints"""
        return self._config.get("constraints", DEFAULT_CONSTRAINTS["constraints"])
    
    def update(self, constraints: Dict[str, Any]) -> bool:
        """Update constraints"""
        try:
            self._config["constraints"] = constraints
            self._save_config()
            logger.info("Constraints updated successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to update constraints: {e}")
            return False
    
    def reset(self) -> bool:
        """Reset to default constraints"""
        try:
            self._config["constraints"] = DEFAULT_CONSTRAINTS["constraints"]
            self._save_config()
            logger.info("Constraints reset to defaults")
            return True
        except Exception as e:
            logger.error(f"Failed to reset constraints: {e}")
            return False


def get_constraint_config() -> ConstraintConfig:
    """Get constraint config instance"""
    return ConstraintConfig()
