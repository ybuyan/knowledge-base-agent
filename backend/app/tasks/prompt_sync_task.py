"""
提示词配置定时同步任务

定期从数据库同步提示词配置到内存
"""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
from app.prompts.manager import prompt_manager

logger = logging.getLogger(__name__)


class PromptSyncTask:
    """提示词配置同步任务"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
    
    async def sync_prompts(self):
        """同步提示词配置"""
        try:
            logger.info("开始同步提示词配置...")
            
            # 重新加载配置（会从数据库加载）
            prompt_manager.reload()
            
            logger.info(f"提示词配置同步完成: {datetime.now()}")
            
        except Exception as e:
            logger.error(f"同步提示词配置失败: {e}")
    
    def start(self, interval_minutes: int = 5):
        """
        启动定时任务
        
        Args:
            interval_minutes: 同步间隔（分钟），默认5分钟
        """
        if self.is_running:
            logger.warning("提示词同步任务已在运行")
            return
        
        # 添加定时任务
        self.scheduler.add_job(
            self.sync_prompts,
            trigger=IntervalTrigger(minutes=interval_minutes),
            id="prompt_sync_task",
            name="提示词配置同步任务",
            replace_existing=True
        )
        
        # 启动调度器
        self.scheduler.start()
        self.is_running = True
        
        logger.info(f"提示词同步任务已启动，间隔: {interval_minutes} 分钟")
    
    def stop(self):
        """停止定时任务"""
        if not self.is_running:
            return
        
        self.scheduler.shutdown()
        self.is_running = False
        logger.info("提示词同步任务已停止")
    
    def trigger_sync(self):
        """手动触发同步"""
        if not self.is_running:
            logger.warning("调度器未运行，无法触发同步")
            return False
        
        try:
            self.scheduler.add_job(
                self.sync_prompts,
                id="manual_prompt_sync",
                replace_existing=True
            )
            logger.info("已触发手动同步")
            return True
        except Exception as e:
            logger.error(f"触发手动同步失败: {e}")
            return False


# 全局实例
prompt_sync_task = PromptSyncTask()
