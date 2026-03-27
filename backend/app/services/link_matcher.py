"""
链接匹配服务

基于关键词匹配相关的外部链接。
"""

from typing import List, Dict, Any, Optional
import logging

from app.services.link_service import get_link_service

logger = logging.getLogger(__name__)


class LinkMatcher:
    """链接匹配器"""
    
    def __init__(self):
        self.link_service = get_link_service()
        self._cached_links: Optional[List[Dict]] = None
    
    async def match_links(self, query: str) -> List[Dict[str, Any]]:
        """
        匹配查询相关的链接
        
        Args:
            query: 用户查询文本
            
        Returns:
            List[Dict]: 匹配的链接列表
        """
        try:
            links = await self.link_service.get_enabled_links()
            
            logger.info(f"[LinkMatcher] 获取到 {len(links)} 个启用的链接")
            
            if not links:
                logger.warning("[LinkMatcher] 没有启用的链接")
                return []
            
            matched_links = []
            query_lower = query.lower()
            
            for link in links:
                keywords = link.get("keywords", [])
                logger.debug(f"[LinkMatcher] 检查链接 '{link.get('title')}' 关键词: {keywords}")
                for keyword in keywords:
                    if keyword.lower() in query_lower:
                        matched_links.append({
                            "id": link.get("id"),
                            "title": link.get("title"),
                            "url": link.get("url"),
                            "description": link.get("description", "")
                        })
                        logger.info(f"[LinkMatcher] 匹配到链接: {link.get('title')} (关键词: {keyword})")
                        break
            
            if matched_links:
                logger.info(f"[LinkMatcher] 查询 '{query[:20]}...' 匹配到 {len(matched_links)} 个链接")
            else:
                logger.info(f"[LinkMatcher] 查询 '{query[:20]}...' 没有匹配到任何链接")
            
            return matched_links
            
        except Exception as e:
            logger.error(f"[LinkMatcher] 匹配链接失败: {e}", exc_info=True)
            return []
    
    async def refresh_cache(self):
        """刷新缓存"""
        self._cached_links = None
        logger.info("[LinkMatcher] 缓存已刷新")


_link_matcher_instance: Optional[LinkMatcher] = None


def get_link_matcher() -> LinkMatcher:
    """获取链接匹配器实例"""
    global _link_matcher_instance
    if _link_matcher_instance is None:
        _link_matcher_instance = LinkMatcher()
    return _link_matcher_instance
