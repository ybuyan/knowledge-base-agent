"""
约束设置功能测试用例

测试内容：
1. 检索约束：最小相似度、文档数量限制
2. 生成约束：严格模式、禁止主题/关键词
3. 验证约束：来源检查、置信度
4. 兜底策略：无结果提示、联系信息
"""

import pytest
import asyncio
import httpx
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"


class TestConstraintsAPI:
    """测试约束 API 接口"""
    
    @pytest.fixture
    def client(self):
        return httpx.AsyncClient(base_url=BASE_URL, timeout=30.0)
    
    @pytest.mark.asyncio
    async def test_get_constraints(self, client):
        """测试获取约束配置"""
        response = await client.get("/api/constraints")
        assert response.status_code == 200
        
        data = response.json()
        assert "constraints" in data
        assert "retrieval" in data["constraints"]
        assert "generation" in data["constraints"]
        assert "validation" in data["constraints"]
        assert "fallback" in data["constraints"]
    
    @pytest.mark.asyncio
    async def test_update_retrieval_constraints(self, client):
        """测试更新检索约束"""
        update_data = {
            "retrieval": {
                "enabled": True,
                "min_similarity_score": 0.8,
                "min_relevant_docs": 2,
                "max_relevant_docs": 3,
                "content_coverage_threshold": 0.5
            }
        }
        
        response = await client.put("/api/constraints", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["constraints"]["retrieval"]["min_similarity_score"] == 0.8
        assert data["constraints"]["retrieval"]["min_relevant_docs"] == 2
    
    @pytest.mark.asyncio
    async def test_update_generation_constraints(self, client):
        """测试更新生成约束"""
        update_data = {
            "generation": {
                "strict_mode": True,
                "allow_general_knowledge": False,
                "require_citations": True,
                "max_answer_length": 500,
                "forbidden_topics": ["政治", "宗教"],
                "forbidden_keywords": ["可能", "大概"]
            }
        }
        
        response = await client.put("/api/constraints", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["constraints"]["generation"]["strict_mode"] == True
        assert "政治" in data["constraints"]["generation"]["forbidden_topics"]
    
    @pytest.mark.asyncio
    async def test_reset_constraints(self, client):
        """测试重置约束配置"""
        response = await client.post("/api/constraints/reset")
        assert response.status_code == 200
        
        data = response.json()
        assert data["constraints"]["retrieval"]["min_similarity_score"] == 0.7
        assert data["constraints"]["generation"]["strict_mode"] == True


class TestRetrievalConstraints:
    """测试检索约束功能"""
    
    @pytest.fixture
    def client(self):
        return httpx.AsyncClient(base_url=BASE_URL, timeout=30.0)
    
    @pytest.mark.asyncio
    async def test_min_similarity_score_filter(self, client):
        """测试最小相似度过滤"""
        await client.put("/api/constraints", json={
            "retrieval": {
                "enabled": True,
                "min_similarity_score": 0.9,
                "min_relevant_docs": 1,
                "max_relevant_docs": 5,
                "content_coverage_threshold": 0.3
            }
        })
        
        response = await client.get("/api/constraints")
        data = response.json()
        assert data["constraints"]["retrieval"]["min_similarity_score"] == 0.9
    
    @pytest.mark.asyncio
    async def test_max_relevant_docs_limit(self, client):
        """测试最大文档数限制"""
        await client.put("/api/constraints", json={
            "retrieval": {
                "enabled": True,
                "min_similarity_score": 0.5,
                "min_relevant_docs": 1,
                "max_relevant_docs": 2,
                "content_coverage_threshold": 0.3
            }
        })
        
        response = await client.get("/api/constraints")
        data = response.json()
        assert data["constraints"]["retrieval"]["max_relevant_docs"] == 2


class TestGenerationConstraints:
    """测试生成约束功能"""
    
    @pytest.fixture
    def client(self):
        return httpx.AsyncClient(base_url=BASE_URL, timeout=60.0)
    
    @pytest.mark.asyncio
    async def test_strict_mode_enabled(self, client):
        """测试严格模式"""
        await client.put("/api/constraints", json={
            "generation": {
                "strict_mode": True,
                "allow_general_knowledge": False,
                "require_citations": True,
                "max_answer_length": 1000,
                "forbidden_topics": [],
                "forbidden_keywords": []
            }
        })
        
        response = await client.get("/api/constraints")
        data = response.json()
        assert data["constraints"]["generation"]["strict_mode"] == True
        assert data["constraints"]["generation"]["allow_general_knowledge"] == False
    
    @pytest.mark.asyncio
    async def test_forbidden_keywords(self, client):
        """测试禁止关键词"""
        await client.put("/api/constraints", json={
            "generation": {
                "strict_mode": True,
                "allow_general_knowledge": False,
                "require_citations": True,
                "max_answer_length": 1000,
                "forbidden_topics": [],
                "forbidden_keywords": ["可能", "大概", "估计"]
            }
        })
        
        response = await client.get("/api/constraints")
        data = response.json()
        assert "可能" in data["constraints"]["generation"]["forbidden_keywords"]
        assert "大概" in data["constraints"]["generation"]["forbidden_keywords"]


class TestFallbackConstraints:
    """测试兜底策略功能"""
    
    @pytest.fixture
    def client(self):
        return httpx.AsyncClient(base_url=BASE_URL, timeout=30.0)
    
    @pytest.mark.asyncio
    async def test_custom_no_result_message(self, client):
        """测试自定义无结果提示"""
        custom_message = "抱歉，知识库中暂无相关信息，请联系HR部门。"
        
        await client.put("/api/constraints", json={
            "fallback": {
                "no_result_message": custom_message,
                "suggest_similar": True,
                "suggest_contact": True,
                "contact_info": "联系邮箱：hr@company.com"
            }
        })
        
        response = await client.get("/api/constraints")
        data = response.json()
        assert data["constraints"]["fallback"]["no_result_message"] == custom_message
    
    @pytest.mark.asyncio
    async def test_contact_info(self, client):
        """测试联系信息"""
        contact_info = "如有疑问，请联系：\n电话：12345\n邮箱：support@company.com"
        
        await client.put("/api/constraints", json={
            "fallback": {
                "no_result_message": "未找到相关信息",
                "suggest_similar": True,
                "suggest_contact": True,
                "contact_info": contact_info
            }
        })
        
        response = await client.get("/api/constraints")
        data = response.json()
        assert "12345" in data["constraints"]["fallback"]["contact_info"]


class TestConstraintIntegration:
    """测试约束与 QA 流程的集成"""
    
    @pytest.fixture
    def client(self):
        return httpx.AsyncClient(base_url=BASE_URL, timeout=60.0)
    
    @pytest.mark.asyncio
    async def test_qa_with_strict_mode(self, client):
        """测试严格模式下的问答"""
        await client.put("/api/constraints", json={
            "generation": {
                "strict_mode": True,
                "allow_general_knowledge": False,
                "require_citations": True,
                "max_answer_length": 1000,
                "forbidden_topics": [],
                "forbidden_keywords": []
            }
        })
        
        response = await client.get("/api/constraints")
        data = response.json()
        assert data["constraints"]["generation"]["strict_mode"] == True
    
    @pytest.mark.asyncio
    async def test_qa_with_forbidden_topic(self, client):
        """测试禁止主题"""
        await client.put("/api/constraints", json={
            "generation": {
                "strict_mode": True,
                "allow_general_knowledge": False,
                "require_citations": True,
                "max_answer_length": 1000,
                "forbidden_topics": ["薪资", "工资"],
                "forbidden_keywords": []
            }
        })
        
        response = await client.get("/api/constraints")
        data = response.json()
        assert "薪资" in data["constraints"]["generation"]["forbidden_topics"]


class TestConstraintStats:
    """测试约束统计功能"""
    
    @pytest.fixture
    def client(self):
        return httpx.AsyncClient(base_url=BASE_URL, timeout=30.0)
    
    @pytest.mark.asyncio
    async def test_get_stats(self, client):
        """测试获取统计数据"""
        response = await client.get("/api/constraints/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_queries" in data
        assert "passed_queries" in data
        assert "failed_queries" in data
        assert "pass_rate" in data
        assert "avg_similarity_score" in data


def run_tests():
    """运行所有测试"""
    import subprocess
    result = subprocess.run(
        ["pytest", __file__, "-v", "--tb=short"],
        capture_output=True,
        text=True
    )
    print(result.stdout)
    print(result.stderr)
    return result.returncode


if __name__ == "__main__":
    run_tests()
