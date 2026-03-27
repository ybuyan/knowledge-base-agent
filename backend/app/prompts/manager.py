"""
提示词管理器

统一管理所有提示词模板，支持：
- 从配置文件加载提示词
- 动态渲染模板变量
- 分类管理提示词
"""

from typing import Dict, Any, Optional, List
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class PromptManager:
    """
    提示词管理器
    
    功能：
    1. 从配置文件加载提示词
    2. 渲染模板变量
    3. 分类管理提示词
    4. 支持运行时修改
    """
    
    _instance = None
    _config: Dict[str, Any] = {}
    _config_path: Path = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self) -> None:
        """加载配置文件"""
        self._config_path = Path(__file__).parent / "config.json"
        
        try:
            with open(self._config_path, "r", encoding="utf-8") as f:
                self._config = json.load(f)
            logger.info(f"提示词配置加载成功: {len(self._config.get('prompts', {}))} 个提示词")
        except Exception as e:
            logger.error(f"加载提示词配置失败: {e}")
            self._config = {"prompts": {}, "categories": {}}
    
    def get(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        """
        获取提示词配置
        
        Args:
            prompt_id: 提示词ID
            
        Returns:
            提示词配置字典，不存在返回None
        """
        return self._config.get("prompts", {}).get(prompt_id)
    
    def render(
        self, 
        prompt_id: str, 
        variables: Dict[str, Any] = None,
        template_key: str = None
    ) -> Dict[str, str]:
        """
        渲染提示词模板
        
        Args:
            prompt_id: 提示词ID
            variables: 模板变量
            template_key: 模板键名（用于多模板提示词）
            
        Returns:
            渲染后的提示词字典 {"system": ..., "user": ...}
            
        Raises:
            ValueError: 提示词不存在或已禁用
        """
        prompt_config = self.get(prompt_id)
        if not prompt_config:
            raise ValueError(f"提示词不存在: {prompt_id}")
        
        if not prompt_config.get("enabled", True):
            raise ValueError(f"提示词已禁用: {prompt_id}")
        
        template = prompt_config.get("template", {})
        variables = variables or {}
        
        result = {}
        
        # 处理不同的模板结构
        if template_key:
            # 多模板提示词（如 query_enhance）
            content = template.get(template_key, "")
            if isinstance(content, str):
                result["content"] = content.format(**variables) if variables else content
        else:
            # 标准 system/user 结构
            if "system" in template:
                result["system"] = template["system"]
            if "user" in template:
                result["user"] = template["user"].format(**variables) if variables else template["user"]
            if "content" in template:
                result["content"] = template["content"].format(**variables) if variables else template["content"]
        
        return result
    
    def get_system_prompt(self, prompt_id: str) -> Optional[str]:
        """获取系统提示词"""
        prompt_config = self.get(prompt_id)
        if prompt_config:
            return prompt_config.get("template", {}).get("system")
        return None
    
    def get_template(self, prompt_id: str, template_key: str = None) -> Optional[str]:
        """
        获取模板内容
        
        Args:
            prompt_id: 提示词ID
            template_key: 模板键名
            
        Returns:
            模板字符串
        """
        prompt_config = self.get(prompt_id)
        if not prompt_config:
            return None
        
        template = prompt_config.get("template", {})
        
        if template_key:
            return template.get(template_key)
        
        return template.get("user") or template.get("content")
    
    def list_all(self) -> List[Dict[str, Any]]:
        """列出所有提示词"""
        prompts = self._config.get("prompts", {})
        return [
            {**v, "id": k}
            for k, v in prompts.items()
        ]
    
    def list_by_category(self, category: str) -> List[Dict[str, Any]]:
        """按分类列出提示词"""
        prompts = self._config.get("prompts", {})
        return [
            {**v, "id": k}
            for k, v in prompts.items()
            if v.get("category") == category
        ]
    
    def get_categories(self) -> Dict[str, str]:
        """获取所有分类"""
        return self._config.get("categories", {})
    
    def get_variables(self, prompt_id: str) -> List[str]:
        """获取提示词所需的变量列表"""
        prompt_config = self.get(prompt_id)
        if prompt_config:
            return prompt_config.get("variables", [])
        return []
    
    def update(self, prompt_id: str, updates: Dict[str, Any]) -> bool:
        """
        更新提示词配置
        
        Args:
            prompt_id: 提示词ID
            updates: 更新内容
            
        Returns:
            是否更新成功
        """
        if prompt_id not in self._config.get("prompts", {}):
            return False
        
        try:
            self._config["prompts"][prompt_id].update(updates)
            self._save_config()
            logger.info(f"提示词已更新: {prompt_id}")
            return True
        except Exception as e:
            logger.error(f"更新提示词失败: {e}")
            return False
    
    def _save_config(self) -> None:
        """保存配置到文件"""
        try:
            with open(self._config_path, "w", encoding="utf-8") as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存提示词配置失败: {e}")
    
    def reload(self) -> None:
        """重新加载配置"""
        self._load_config()
        logger.info("提示词配置已重新加载")


# 单例实例
prompt_manager = PromptManager()


# 便捷函数
def get_prompt(prompt_id: str) -> Optional[Dict[str, Any]]:
    """获取提示词配置"""
    return prompt_manager.get(prompt_id)


def render_prompt(prompt_id: str, variables: Dict[str, Any] = None) -> Dict[str, str]:
    """渲染提示词"""
    return prompt_manager.render(prompt_id, variables)


def get_system_prompt(prompt_id: str) -> Optional[str]:
    """获取系统提示词"""
    return prompt_manager.get_system_prompt(prompt_id)
