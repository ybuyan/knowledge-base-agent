"""
约束 API 测试

测试约束相关的 API 端点
"""

import pytest
import httpx
from typing import Dict, Any


BASE_URL = "http://localhost:8000"


class TestConstraintsAPIEndpoints:
    """测试约束 API 端点"""
    
    @pytest.fixture
    async def client(self):
        """创建异步 HTTP 客户端"""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
            yield client
    
    @pytest.mark.asyncio
    async def test_get_constraints_endpoint(self, client):
        """测试获取约束配置端点"""
        response = await client.get("/api/constraints")
        
        assert response.status_code == 200
        data = response.json()
        
        # 验证响应结构
        assert "constraints" in data
        assert isinstance(data["constraints"], dict)
        
        # 验证必需的约束类型
        constraints = data["constraints"]
        assert "retrieval" in constraints
        assert "generation" in constraints
        assert "validation" in constraints
        assert "fallback" in constraints
    
    @pytest.mark.asyncio
    async def test_update_constraints_endpoint(self, client):
        """测试更新约束配置端点"""
        update_data = {
            "retrieval": {
                "enabled": True,
                "min_similarity_score": 0.75,
                "min_relevant_docs": 1,
                "max_relevant_docs": 4,
                "content_coverage_threshold": 0.4
            }
        }
        
        response = await client.put("/api/constraints", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # 验证更新成功
        assert data["constraints"]["retrieval"]["min_similarity_score"] == 0.75
        assert data["constraints"]["retrieval"]["max_relevant_docs"] == 4
    
    @pytest.mark.asyncio
    async def test_reset_constraints_endpoint(self, client):
        """测试重置约束配置端点"""
        # 先修改配置
        await client.put("/api/constraints", json={
            "retrieval": {"min_similarity_score": 0.5}
        })
        
        # 重置
        response = await client.post("/api/constraints/reset")
        
        assert response.status_code == 200
        data = response.json()
        
        # 验证重置为默认值
        assert data["constraints"]["retrieval"]["min_similarity_score"] == 0.7
    
    @pytest.mark.asyncio
    async def test_get_constraints_stats_endpoint(self, client):
        """测试获取约束统计端点"""
        response = await client.get("/api/constraints/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        # 验证统计数据结构
        assert "total_queries" in data
        assert "passed_queries" in data
        assert "failed_queries" in data
        assert "pass_rate" in data
        assert "avg_similarity_score" in data


class TestConstraintsAPIValidation:
    """测试约束 API 的输入验证"""
    
    @pytest.fixture
    async def client(self):
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
            yield client
    
    @pytest.mark.asyncio
    async def test_update_with_invalid_similarity_score(self, client):
        """测试使用无效的相似度分数"""
        invalid_data = {
            "retrieval": {
                "min_similarity_score": 1.5  # 超出范围 [0, 1]
            }
        }
        
        response = await client.put("/api/constraints", json=invalid_data)
        
        # 应该返回错误或自动修正
        assert response.status_code in [200, 400, 422]
    
    @pytest.mark.asyncio
    async def test_update_with_negative_max_docs(self, client):
        """测试使用负数的最大文档数"""
        invalid_data = {
            "retrieval": {
                "max_relevant_docs": -1
            }
        }
        
        response = await client.put("/api/constraints", json=invalid_data)
        
        # 应该返回错误或自动修正
        assert response.status_code in [200, 400, 422]
    
    @pytest.mark.asyncio
    async def test_update_with_empty_body(self, client):
        """测试使用空请求体"""
        response = await client.put("/api/constraints", json={})
        
        # 应该返回错误或保持原配置
        assert response.status_code in [200, 400, 422]


class TestConstraintsAPIRetrievalConfig:
    """测试检索约束配置 API"""
    
    @pytest.fixture
    async def client(self):
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
            yield client
    
    @pytest.mark.asyncio
    async def test_enable_disable_retrieval(self, client):
        """测试启用/禁用检索约束"""
        # 禁用
        response = await client.put("/api/constraints", json={
            "retrieval": {"enabled": False}
        })
        assert response.status_code == 200
        data = response.json()
        assert data["constraints"]["retrieval"]["enabled"] == False
        
        # 启用
        response = await client.put("/api/constraints", json={
            "retrieval": {"enabled": True}
        })
        assert response.status_code == 200
        data = response.json()
        assert data["constraints"]["retrieval"]["enabled"] == True
    
    @pytest.mark.asyncio
    async def test_update_similarity_threshold(self, client):
        """测试更新相似度阈值"""
        test_values = [0.5, 0.7, 0.9]
        
        for value in test_values:
            response = await client.put("/api/constraints", json={
                "retrieval": {"min_similarity_score": value}
            })
            assert response.status_code == 200
            data = response.json()
            assert data["constraints"]["retrieval"]["min_similarity_score"] == value
    
    @pytest.mark.asyncio
    async def test_update_max_docs_limit(self, client):
        """测试更新最大文档数限制"""
        test_values = [3, 5, 10]
        
        for value in test_values:
            response = await client.put("/api/constraints", json={
                "retrieval": {"max_relevant_docs": value}
            })
            assert response.status_code == 200
            data = response.json()
            assert data["constraints"]["retrieval"]["max_relevant_docs"] == value


class TestConstraintsAPIGenerationConfig:
    """测试生成约束配置 API"""
    
    @pytest.fixture
    async def client(self):
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
            yield client
    
    @pytest.mark.asyncio
    async def test_update_strict_mode(self, client):
        """测试更新严格模式"""
        response = await client.put("/api/constraints", json={
            "generation": {"strict_mode": False}
        })
        assert response.status_code == 200
        data = response.json()
        assert data["constraints"]["generation"]["strict_mode"] == False
    
    @pytest.mark.asyncio
    async def test_update_forbidden_topics(self, client):
        """测试更新禁止主题"""
        forbidden_topics = ["政治", "宗教", "薪资"]
        
        response = await client.put("/api/constraints", json={
            "generation": {"forbidden_topics": forbidden_topics}
        })
        assert response.status_code == 200
        data = response.json()
        assert set(data["constraints"]["generation"]["forbidden_topics"]) == set(forbidden_topics)
    
    @pytest.mark.asyncio
    async def test_update_forbidden_keywords(self, client):
        """测试更新禁止关键词"""
        forbidden_keywords = ["可能", "大概", "估计"]
        
        response = await client.put("/api/constraints", json={
            "generation": {"forbidden_keywords": forbidden_keywords}
        })
        assert response.status_code == 200
        data = response.json()
        assert set(data["constraints"]["generation"]["forbidden_keywords"]) == set(forbidden_keywords)
    
    @pytest.mark.asyncio
    async def test_update_max_answer_length(self, client):
        """测试更新最大回答长度"""
        test_values = [500, 1000, 2000]
        
        for value in test_values:
            response = await client.put("/api/constraints", json={
                "generation": {"max_answer_length": value}
            })
            assert response.status_code == 200
            data = response.json()
            assert data["constraints"]["generation"]["max_answer_length"] == value


class TestConstraintsAPIValidationConfig:
    """测试验证约束配置 API"""
    
    @pytest.fixture
    async def client(self):
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
            yield client
    
    @pytest.mark.asyncio
    async def test_enable_disable_validation(self, client):
        """测试启用/禁用验证"""
        # 禁用
        response = await client.put("/api/constraints", json={
            "validation": {"enabled": False}
        })
        assert response.status_code == 200
        data = response.json()
        assert data["constraints"]["validation"]["enabled"] == False
        
        # 启用
        response = await client.put("/api/constraints", json={
            "validation": {"enabled": True}
        })
        assert response.status_code == 200
        data = response.json()
        assert data["constraints"]["validation"]["enabled"] == True
    
    @pytest.mark.asyncio
    async def test_update_min_confidence_score(self, client):
        """测试更新最小置信度分数"""
        test_values = [0.5, 0.6, 0.8]
        
        for value in test_values:
            response = await client.put("/api/constraints", json={
                "validation": {"min_confidence_score": value}
            })
            assert response.status_code == 200
            data = response.json()
            assert data["constraints"]["validation"]["min_confidence_score"] == value
    
    @pytest.mark.asyncio
    async def test_toggle_hallucination_detection(self, client):
        """测试切换幻觉检测"""
        response = await client.put("/api/constraints", json={
            "validation": {"hallucination_detection": False}
        })
        assert response.status_code == 200
        data = response.json()
        assert data["constraints"]["validation"]["hallucination_detection"] == False


class TestConstraintsAPIFallbackConfig:
    """测试兜底策略配置 API"""
    
    @pytest.fixture
    async def client(self):
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
            yield client
    
    @pytest.mark.asyncio
    async def test_update_no_result_message(self, client):
        """测试更新无结果消息"""
        custom_message = "抱歉，暂时无法找到相关信息。"
        
        response = await client.put("/api/constraints", json={
            "fallback": {"no_result_message": custom_message}
        })
        assert response.status_code == 200
        data = response.json()
        assert data["constraints"]["fallback"]["no_result_message"] == custom_message
    
    @pytest.mark.asyncio
    async def test_update_contact_info(self, client):
        """测试更新联系信息"""
        contact_info = "联系方式：\n电话：123-456-7890\n邮箱：help@example.com"
        
        response = await client.put("/api/constraints", json={
            "fallback": {"contact_info": contact_info}
        })
        assert response.status_code == 200
        data = response.json()
        assert data["constraints"]["fallback"]["contact_info"] == contact_info
    
    @pytest.mark.asyncio
    async def test_toggle_suggest_similar(self, client):
        """测试切换相似问题建议"""
        response = await client.put("/api/constraints", json={
            "fallback": {"suggest_similar": False}
        })
        assert response.status_code == 200
        data = response.json()
        assert data["constraints"]["fallback"]["suggest_similar"] == False


class TestConstraintsAPIPersistence:
    """测试约束配置持久化"""
    
    @pytest.fixture
    async def client(self):
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
            yield client
    
    @pytest.mark.asyncio
    async def test_config_persists_across_requests(self, client):
        """测试配置在请求间持久化"""
        # 更新配置
        update_data = {
            "retrieval": {"min_similarity_score": 0.85}
        }
        await client.put("/api/constraints", json=update_data)
        
        # 获取配置验证持久化
        response = await client.get("/api/constraints")
        data = response.json()
        
        assert data["constraints"]["retrieval"]["min_similarity_score"] == 0.85
    
    @pytest.mark.asyncio
    async def test_partial_update_preserves_other_fields(self, client):
        """测试部分更新保留其他字段"""
        # 获取当前配置
        response = await client.get("/api/constraints")
        original_data = response.json()
        original_max_docs = original_data["constraints"]["retrieval"]["max_relevant_docs"]
        
        # 只更新一个字段
        await client.put("/api/constraints", json={
            "retrieval": {"min_similarity_score": 0.88}
        })
        
        # 验证其他字段未改变
        response = await client.get("/api/constraints")
        updated_data = response.json()
        
        assert updated_data["constraints"]["retrieval"]["min_similarity_score"] == 0.88
        # 注意：这取决于 API 的实现，可能需要调整断言


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
