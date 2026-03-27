"""
约束配置测试

测试 ConstraintConfig 类的配置加载、更新、重置等功能
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from app.core.constraint_config import (
    ConstraintConfig,
    get_constraint_config,
    DEFAULT_CONSTRAINTS
)


class TestConstraintConfigLoading:
    """测试配置加载功能"""
    
    def test_singleton_pattern(self):
        """测试单例模式"""
        config1 = ConstraintConfig()
        config2 = ConstraintConfig()
        assert config1 is config2
    
    def test_get_constraint_config_returns_singleton(self):
        """测试 get_constraint_config 返回单例"""
        config1 = get_constraint_config()
        config2 = get_constraint_config()
        assert config1 is config2
    
    def test_load_default_config_when_file_not_exists(self):
        """测试文件不存在时加载默认配置"""
        with patch.object(ConstraintConfig, '_get_config_path') as mock_path:
            mock_path.return_value = '/nonexistent/path/constraints.json'
            
            # 重置单例
            ConstraintConfig._instance = None
            ConstraintConfig._config = {}
            
            config = ConstraintConfig()
            
            # 验证加载了默认配置
            assert config.retrieval['enabled'] == DEFAULT_CONSTRAINTS['constraints']['retrieval']['enabled']
            assert config.generation['strict_mode'] == DEFAULT_CONSTRAINTS['constraints']['generation']['strict_mode']
    
    def test_load_config_from_file(self):
        """测试从文件加载配置"""
        # 创建临时配置文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            test_config = {
                "constraints": {
                    "retrieval": {
                        "enabled": False,
                        "min_similarity_score": 0.5
                    },
                    "generation": {
                        "strict_mode": False
                    },
                    "validation": {},
                    "fallback": {}
                }
            }
            json.dump(test_config, f)
            temp_path = f.name
        
        try:
            with patch.object(ConstraintConfig, '_get_config_path') as mock_path:
                mock_path.return_value = temp_path
                
                # 重置单例
                ConstraintConfig._instance = None
                ConstraintConfig._config = {}
                
                config = ConstraintConfig()
                
                # 验证加载了文件中的配置
                assert config.retrieval['enabled'] == False
                assert config.retrieval['min_similarity_score'] == 0.5
                assert config.generation['strict_mode'] == False
        finally:
            os.unlink(temp_path)
    
    def test_load_config_handles_json_error(self):
        """测试处理 JSON 解析错误"""
        # 创建包含无效 JSON 的临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{ invalid json }")
            temp_path = f.name
        
        try:
            with patch.object(ConstraintConfig, '_get_config_path') as mock_path:
                mock_path.return_value = temp_path
                
                # 重置单例
                ConstraintConfig._instance = None
                ConstraintConfig._config = {}
                
                config = ConstraintConfig()
                
                # 验证加载了默认配置
                assert config.retrieval == DEFAULT_CONSTRAINTS['constraints']['retrieval']
        finally:
            os.unlink(temp_path)


class TestConstraintConfigProperties:
    """测试配置属性访问"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """每个测试前重置单例"""
        ConstraintConfig._instance = None
        ConstraintConfig._config = {}
    
    def test_retrieval_property(self):
        """测试 retrieval 属性"""
        config = ConstraintConfig()
        retrieval = config.retrieval
        
        assert 'enabled' in retrieval
        assert 'min_similarity_score' in retrieval
        assert 'min_relevant_docs' in retrieval
        assert 'max_relevant_docs' in retrieval
    
    def test_generation_property(self):
        """测试 generation 属性"""
        config = ConstraintConfig()
        generation = config.generation
        
        assert 'strict_mode' in generation
        assert 'allow_general_knowledge' in generation
        assert 'require_citations' in generation
        assert 'max_answer_length' in generation
        assert 'forbidden_topics' in generation
        assert 'forbidden_keywords' in generation
    
    def test_validation_property(self):
        """测试 validation 属性"""
        config = ConstraintConfig()
        validation = config.validation
        
        assert 'enabled' in validation
        assert 'check_source_attribution' in validation
        assert 'min_confidence_score' in validation
        assert 'hallucination_detection' in validation
    
    def test_fallback_property(self):
        """测试 fallback 属性"""
        config = ConstraintConfig()
        fallback = config.fallback
        
        assert 'no_result_message' in fallback
        assert 'suggest_similar' in fallback
        assert 'suggest_contact' in fallback
        assert 'contact_info' in fallback
    
    def test_suggest_questions_property(self):
        """测试 suggest_questions 属性"""
        config = ConstraintConfig()
        suggest_questions = config.suggest_questions
        
        assert 'enabled' in suggest_questions
        assert 'count' in suggest_questions
        assert 'types' in suggest_questions
    
    def test_get_all_returns_all_constraints(self):
        """测试 get_all 返回所有约束"""
        config = ConstraintConfig()
        all_constraints = config.get_all()
        
        assert 'retrieval' in all_constraints
        assert 'generation' in all_constraints
        assert 'validation' in all_constraints
        assert 'fallback' in all_constraints


class TestConstraintConfigUpdate:
    """测试配置更新功能"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """每个测试前重置单例"""
        ConstraintConfig._instance = None
        ConstraintConfig._config = {}
    
    def test_update_constraints_success(self):
        """测试成功更新约束"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(DEFAULT_CONSTRAINTS, f)
            temp_path = f.name
        
        try:
            with patch.object(ConstraintConfig, '_get_config_path') as mock_path:
                mock_path.return_value = temp_path
                
                config = ConstraintConfig()
                
                new_constraints = {
                    "retrieval": {
                        "enabled": False,
                        "min_similarity_score": 0.8
                    },
                    "generation": {
                        "strict_mode": False,
                        "forbidden_topics": ["test_topic"]
                    },
                    "validation": {},
                    "fallback": {}
                }
                
                result = config.update(new_constraints)
                
                assert result == True
                assert config.retrieval['enabled'] == False
                assert config.retrieval['min_similarity_score'] == 0.8
                assert config.generation['strict_mode'] == False
                assert "test_topic" in config.generation['forbidden_topics']
        finally:
            os.unlink(temp_path)
    
    def test_update_constraints_persists_to_file(self):
        """测试更新约束持久化到文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(DEFAULT_CONSTRAINTS, f)
            temp_path = f.name
        
        try:
            with patch.object(ConstraintConfig, '_get_config_path') as mock_path:
                mock_path.return_value = temp_path
                
                config = ConstraintConfig()
                
                new_constraints = {
                    "retrieval": {"enabled": False},
                    "generation": {"strict_mode": False},
                    "validation": {},
                    "fallback": {}
                }
                
                config.update(new_constraints)
                
                # 读取文件验证持久化
                with open(temp_path, 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)
                
                assert saved_config['constraints']['retrieval']['enabled'] == False
                assert saved_config['constraints']['generation']['strict_mode'] == False
        finally:
            os.unlink(temp_path)
    
    def test_update_constraints_handles_error(self):
        """测试更新约束时处理错误"""
        config = ConstraintConfig()
        
        # 模拟保存失败
        with patch.object(config, '_save_config', side_effect=Exception("Save failed")):
            result = config.update({"retrieval": {"enabled": False}})
            assert result == False


class TestConstraintConfigReset:
    """测试配置重置功能"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """每个测试前重置单例"""
        ConstraintConfig._instance = None
        ConstraintConfig._config = {}
    
    def test_reset_to_defaults(self):
        """测试重置到默认配置"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(DEFAULT_CONSTRAINTS, f)
            temp_path = f.name
        
        try:
            with patch.object(ConstraintConfig, '_get_config_path') as mock_path:
                mock_path.return_value = temp_path
                
                config = ConstraintConfig()
                
                # 先修改配置
                config.update({
                    "retrieval": {"enabled": False},
                    "generation": {"strict_mode": False},
                    "validation": {},
                    "fallback": {}
                })
                
                # 重置
                result = config.reset()
                
                assert result == True
                assert config.retrieval == DEFAULT_CONSTRAINTS['constraints']['retrieval']
                assert config.generation == DEFAULT_CONSTRAINTS['constraints']['generation']
        finally:
            os.unlink(temp_path)
    
    def test_reset_persists_to_file(self):
        """测试重置持久化到文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(DEFAULT_CONSTRAINTS, f)
            temp_path = f.name
        
        try:
            with patch.object(ConstraintConfig, '_get_config_path') as mock_path:
                mock_path.return_value = temp_path
                
                config = ConstraintConfig()
                
                # 修改并重置
                config.update({"retrieval": {"enabled": False}})
                config.reset()
                
                # 读取文件验证
                with open(temp_path, 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)
                
                assert saved_config['constraints'] == DEFAULT_CONSTRAINTS['constraints']
        finally:
            os.unlink(temp_path)
    
    def test_reset_handles_error(self):
        """测试重置时处理错误"""
        config = ConstraintConfig()
        
        # 模拟保存失败
        with patch.object(config, '_save_config', side_effect=Exception("Save failed")):
            result = config.reset()
            assert result == False


class TestConstraintConfigDefaults:
    """测试默认配置值"""
    
    def test_default_retrieval_values(self):
        """测试默认检索配置值"""
        defaults = DEFAULT_CONSTRAINTS['constraints']['retrieval']
        
        assert defaults['enabled'] == True
        assert defaults['min_similarity_score'] == 0.7
        assert defaults['min_relevant_docs'] == 1
        assert defaults['max_relevant_docs'] == 5
        assert defaults['content_coverage_threshold'] == 0.3
    
    def test_default_generation_values(self):
        """测试默认生成配置值"""
        defaults = DEFAULT_CONSTRAINTS['constraints']['generation']
        
        assert defaults['strict_mode'] == True
        assert defaults['allow_general_knowledge'] == False
        assert defaults['require_citations'] == True
        assert defaults['max_answer_length'] == 1000
        assert defaults['forbidden_topics'] == []
        assert defaults['forbidden_keywords'] == []
    
    def test_default_validation_values(self):
        """测试默认验证配置值"""
        defaults = DEFAULT_CONSTRAINTS['constraints']['validation']
        
        assert defaults['enabled'] == True
        assert defaults['check_source_attribution'] == True
        assert defaults['min_confidence_score'] == 0.6
        assert defaults['hallucination_detection'] == True
    
    def test_default_fallback_values(self):
        """测试默认兜底配置值"""
        defaults = DEFAULT_CONSTRAINTS['constraints']['fallback']
        
        assert 'no_result_message' in defaults
        assert defaults['suggest_similar'] == True
        assert defaults['suggest_contact'] == True
        assert 'contact_info' in defaults


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
