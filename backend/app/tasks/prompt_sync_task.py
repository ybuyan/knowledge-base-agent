"""
提示词配置定时同步任务

启动时：将 config.json 写入数据库（仅当数据库为空时）
定时：每 N 分钟从数据库拉取最新配置，刷新 config_loader 内存缓存
"""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)


class PromptSyncTask:
    """提示词配置同步任务"""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.is_running = False

    async def _ensure_db_initialized(self) -> None:
        """
        启动时检查：如果数据库中没有 prompt 数据，
        则将 config.json 的内容写入数据库作为初始数据。
        """
        from app.services.prompt_config_service import prompt_config_service
        from app.core.mongodb import mongodb

        if not mongodb.is_connected or mongodb.database is None:
            logger.warning("[PromptSync] 数据库未连接，跳过初始化")
            return

        try:
            existing = await prompt_config_service.get_all(enabled_only=False)
            if existing:
                logger.info("[PromptSync] 数据库已有 %d 个 prompt，跳过初始化写入", len(existing))
                return

            logger.info("[PromptSync] 数据库为空，从 config.json 初始化写入...")
            result = await prompt_config_service.sync_from_file()
            if result.get("success"):
                stats = result.get("stats", {})
                logger.info("[PromptSync] 初始化写入完成: 新增 %d 个", stats.get("created", 0))
            else:
                logger.error("[PromptSync] 初始化写入失败: %s", result.get("error"))
        except Exception as e:
            logger.error("[PromptSync] 初始化检查失败: %s", e)

    async def sync_prompts(self) -> None:
        """从数据库拉取最新 prompt，刷新 config_loader 内存缓存"""
        from app.services.prompt_config_service import prompt_config_service
        from app.core.mongodb import mongodb
        from app.core.config_loader import config_loader

        if not mongodb.is_connected or mongodb.database is None:
            logger.debug("[PromptSync] 数据库未连接，跳过同步")
            return

        try:
            prompts = await prompt_config_service.get_all(enabled_only=False)
            if not prompts:
                logger.warning("[PromptSync] 数据库中没有 prompt 配置")
                return

            # 转换为 {prompt_id: prompt_dict} 格式，刷新到 config_loader 缓存
            cache = {
                p["id"]: {
                    "name": p["name"],
                    "description": p.get("description"),
                    "enabled": p["enabled"],
                    "category": p["category"],
                    "template": p["template"],
                    "variables": p["variables"],
                }
                for p in prompts
            }
            config_loader.refresh_prompt_cache(cache)
            logger.info("[PromptSync] 同步完成，共 %d 个 prompt", len(cache))

        except Exception as e:
            logger.error("[PromptSync] 同步失败: %s", e)

    async def startup(self, interval_minutes: int = 5) -> None:
        """
        应用启动时调用：
        1. 初始化数据库（如果为空则写入 config.json）
        2. 立即执行一次同步，加载到内存缓存
        3. 启动定时任务
        """
        await self._ensure_db_initialized()
        await self.sync_prompts()
        self.start(interval_minutes)

    def start(self, interval_minutes: int = 5) -> None:
        """启动定时同步任务"""
        if self.is_running:
            return

        self.scheduler.add_job(
            self.sync_prompts,
            trigger=IntervalTrigger(minutes=interval_minutes),
            id="prompt_sync",
            name="Prompt 定时同步",
            replace_existing=True,
        )
        self.scheduler.start()
        self.is_running = True
        logger.info("[PromptSync] 定时任务已启动，间隔 %d 分钟", interval_minutes)

    def stop(self) -> None:
        """停止定时任务"""
        if not self.is_running:
            return
        self.scheduler.shutdown(wait=False)
        self.is_running = False
        logger.info("[PromptSync] 定时任务已停止")


# 全局实例
prompt_sync_task = PromptSyncTask()
