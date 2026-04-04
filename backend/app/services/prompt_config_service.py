"""
提示词配置服务

负责提示词配置的数据库操作和同步
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
from app.core.mongodb import get_mongo_db

logger = logging.getLogger(__name__)


class PromptConfigService:
    """提示词配置服务"""
    
    @staticmethod
    def _get_collection():
        """获取 MongoDB 集合"""
        from app.core.mongodb import mongodb
        
        if not mongodb.is_connected or mongodb.database is None:
            raise Exception("数据库未连接")
        
        return mongodb.database.prompts
    
    @staticmethod
    async def sync_from_file(config_path: str = None) -> Dict[str, Any]:
        """
        从配置文件同步到数据库
        
        Args:
            config_path: 配置文件路径，默认为 prompts/config.json
            
        Returns:
            同步结果统计
        """
        if not config_path:
            config_path = Path(__file__).parent.parent / "prompts" / "config.json"
        else:
            config_path = Path(config_path)
        
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception as e:
            logger.error(f"读取配置文件失败: {e}")
            return {"success": False, "error": str(e)}
        
        prompts = config.get("prompts", {})
        stats = {"created": 0, "updated": 0, "skipped": 0, "errors": 0}
        
        collection = PromptConfigService._get_collection()
        
        for prompt_id, prompt_data in prompts.items():
            try:
                # 查询是否已存在
                existing = await collection.find_one({"prompt_id": prompt_id})
                
                # 准备数据
                data = {
                    "prompt_id": prompt_id,
                    "name": prompt_data.get("name", ""),
                    "description": prompt_data.get("description"),
                    "enabled": prompt_data.get("enabled", True),
                    "category": prompt_data.get("category", ""),
                    "template": prompt_data.get("template", {}),
                    "variables": prompt_data.get("variables", []),
                    "version": config.get("version", "1.0"),
                    "updated_at": datetime.utcnow()
                }
                
                if existing:
                    # 更新
                    await collection.update_one(
                        {"prompt_id": prompt_id},
                        {"$set": data}
                    )
                    stats["updated"] += 1
                else:
                    # 创建
                    data["created_at"] = datetime.utcnow()
                    await collection.insert_one(data)
                    stats["created"] += 1
                
            except Exception as e:
                logger.error(f"同步提示词 {prompt_id} 失败: {e}")
                stats["errors"] += 1
        
        logger.info(f"配置同步完成: {stats}")
        return {"success": True, "stats": stats}
    
    @staticmethod
    async def get_all(enabled_only: bool = False) -> List[Dict[str, Any]]:
        """
        获取所有提示词配置
        
        Args:
            enabled_only: 是否只返回启用的配置
            
        Returns:
            提示词配置列表
        """
        collection = PromptConfigService._get_collection()
        
        query = {}
        if enabled_only:
            query["enabled"] = True
        
        cursor = collection.find(query)
        prompts = await cursor.to_list(length=None)
        
        return [
            {
                "id": p["prompt_id"],
                "name": p["name"],
                "description": p.get("description"),
                "enabled": p["enabled"],
                "category": p["category"],
                "template": p["template"],
                "variables": p["variables"],
                "version": p.get("version", "1.0"),
                "updated_at": p.get("updated_at").isoformat() if p.get("updated_at") else None
            }
            for p in prompts
        ]
    
    @staticmethod
    async def get_by_id(prompt_id: str) -> Optional[Dict[str, Any]]:
        """
        根据ID获取提示词配置
        
        Args:
            prompt_id: 提示词ID
            
        Returns:
            提示词配置字典
        """
        collection = PromptConfigService._get_collection()
        prompt = await collection.find_one({"prompt_id": prompt_id})
        
        if not prompt:
            return None
        
        return {
            "id": prompt["prompt_id"],
            "name": prompt["name"],
            "description": prompt.get("description"),
            "enabled": prompt["enabled"],
            "category": prompt["category"],
            "template": prompt["template"],
            "variables": prompt["variables"],
            "version": prompt.get("version", "1.0"),
            "updated_at": prompt.get("updated_at").isoformat() if prompt.get("updated_at") else None
        }
    
    @staticmethod
    async def get_by_category(category: str, enabled_only: bool = True) -> List[Dict[str, Any]]:
        """
        根据分类获取提示词配置
        
        Args:
            category: 分类名称
            enabled_only: 是否只返回启用的配置
            
        Returns:
            提示词配置列表
        """
        collection = PromptConfigService._get_collection()
        
        query = {"category": category}
        if enabled_only:
            query["enabled"] = True
        
        cursor = collection.find(query)
        prompts = await cursor.to_list(length=None)
        
        return [
            {
                "id": p["prompt_id"],
                "name": p["name"],
                "description": p.get("description"),
                "enabled": p["enabled"],
                "category": p["category"],
                "template": p["template"],
                "variables": p["variables"],
                "version": p.get("version", "1.0")
            }
            for p in prompts
        ]
    
    @staticmethod
    async def update(prompt_id: str, updates: Dict[str, Any], updated_by: str = None) -> bool:
        """
        更新提示词配置
        
        Args:
            prompt_id: 提示词ID
            updates: 更新内容
            updated_by: 更新人
            
        Returns:
            是否更新成功
        """
        collection = PromptConfigService._get_collection()
        
        try:
            # 添加更新时间和更新人
            updates["updated_at"] = datetime.utcnow()
            if updated_by:
                updates["updated_by"] = updated_by
            
            result = await collection.update_one(
                {"prompt_id": prompt_id},
                {"$set": updates}
            )
            
            if result.modified_count > 0:
                logger.info(f"提示词配置已更新: {prompt_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"更新提示词配置失败: {e}")
            return False
    
    @staticmethod
    async def create(prompt_data: Dict[str, Any], created_by: str = None) -> Optional[str]:
        """
        创建新的提示词配置
        
        Args:
            prompt_data: 提示词数据
            created_by: 创建人
            
        Returns:
            创建的提示词ID，失败返回None
        """
        collection = PromptConfigService._get_collection()
        
        try:
            # 检查是否已存在
            existing = await collection.find_one({"prompt_id": prompt_data["prompt_id"]})
            if existing:
                logger.error(f"提示词ID已存在: {prompt_data['prompt_id']}")
                return None
            
            # 准备数据
            data = {
                "prompt_id": prompt_data["prompt_id"],
                "name": prompt_data["name"],
                "description": prompt_data.get("description"),
                "enabled": prompt_data.get("enabled", True),
                "category": prompt_data.get("category", ""),
                "template": prompt_data.get("template", {}),
                "variables": prompt_data.get("variables", []),
                "version": prompt_data.get("version", "1.0"),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            if created_by:
                data["updated_by"] = created_by
            
            await collection.insert_one(data)
            
            logger.info(f"提示词配置已创建: {data['prompt_id']}")
            return data["prompt_id"]
            
        except Exception as e:
            logger.error(f"创建提示词配置失败: {e}")
            return None
    
    @staticmethod
    async def delete(prompt_id: str) -> bool:
        """
        删除提示词配置
        
        Args:
            prompt_id: 提示词ID
            
        Returns:
            是否删除成功
        """
        collection = PromptConfigService._get_collection()
        
        try:
            result = await collection.delete_one({"prompt_id": prompt_id})
            
            if result.deleted_count > 0:
                logger.info(f"提示词配置已删除: {prompt_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"删除提示词配置失败: {e}")
            return False
    
    @staticmethod
    async def export_to_file(output_path: str = None) -> bool:
        """
        导出配置到文件
        
        Args:
            output_path: 输出文件路径
            
        Returns:
            是否导出成功
        """
        if not output_path:
            output_path = Path(__file__).parent.parent / "prompts" / "config_export.json"
        else:
            output_path = Path(output_path)
        
        try:
            prompts = await PromptConfigService.get_all()
            
            # 转换为配置文件格式
            config = {
                "version": prompts[0]["version"] if prompts else "1.0",
                "description": "从数据库导出的提示词配置",
                "prompts": {
                    p["id"]: {
                        "id": p["id"],
                        "name": p["name"],
                        "description": p["description"],
                        "enabled": p["enabled"],
                        "category": p["category"],
                        "template": p["template"],
                        "variables": p["variables"]
                    }
                    for p in prompts
                }
            }
            
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            logger.info(f"配置已导出到: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"导出配置失败: {e}")
            return False


# 便捷实例
prompt_config_service = PromptConfigService()
