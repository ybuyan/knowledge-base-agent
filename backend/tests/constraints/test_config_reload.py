"""
测试配置重新加载功能

验证配置文件修改后可以通过 reload 方法重新加载
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from app.core.constraint_config import ConstraintConfig, get_constraint_config


class TestConfigReload:
    """测试配置重新加载"""

    def test_reload_after_file_modification(self, tmp_path):
        """测试文件修改后重新加载"""
        # 创建临时配置文件
        config_file = tmp_path / "constraints.json"
        
        # 初始配置
        initial_config = {
            "constraints": {
                "retrieval": {
                    "min_relevant_docs": 1
                },
                "generation": {
                    "forbidden_topics": ["薪资"]
                }
            }
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(initial_config, f)
        
        # Mock 配置文件路径
        with patch.object(ConstraintConfig, '_get_config_path', return_value=str(config_file)):
            # 重置单例
            ConstraintConfig._instance = None
            ConstraintConfig._config = {}
            
            # 加载初始配置
            config = ConstraintConfig()
            assert config.retrieval.get('min_relevant_docs') == 1
            assert config.generation.get('forbidden_topics') == ["薪资"]
            
            # 修改配置文件
            modified_config = {
                "constraints": {
                    "retrieval": {
                        "min_relevant_docs": 3  # 修改值
                    },
                    "generation": {
                        "forbidden_topics": ["薪资", "工资"]  # 添加新值
                    }
                }
            }
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(modified_config, f)
            
            # 重新加载配置
            success = config.reload()
            
            # 验证
            assert success is True
            assert config.retrieval.get('min_relevant_docs') == 3
            assert config.generation.get('forbidden_topics') == ["薪资", "工资"]

    def test_reload_preserves_singleton(self):
        """测试重新加载保持单例模式"""
        config1 = get_constraint_config()
        config1.reload()
        config2 = get_constraint_config()
        
        # 验证是同一个实例
        assert config1 is config2

    def test_reload_handles_invalid_json(self, tmp_path):
        """测试重新加载处理无效 JSON"""
        # 创建临时配置文件
        config_file = tmp_path / "constraints.json"
        
        # 写入有效配置
        valid_config = {
            "constraints": {
                "retrieval": {
                    "min_relevant_docs": 1
                }
            }
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(valid_config, f)
        
        # Mock 配置文件路径
        with patch.object(ConstraintConfig, '_get_config_path', return_value=str(config_file)):
            # 重置单例
            ConstraintConfig._instance = None
            ConstraintConfig._config = {}
            
            # 加载初始配置
            config = ConstraintConfig()
            assert config.retrieval.get('min_relevant_docs') == 1
            
            # 写入无效 JSON
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write("{ invalid json }")
            
            # 尝试重新加载
            success = config.reload()
            
            # 验证：重新加载失败，但保持原有配置
            assert success is False
            assert config.retrieval.get('min_relevant_docs') == 1

    def test_reload_handles_missing_file(self, tmp_path):
        """测试重新加载处理文件不存在"""
        # 创建临时配置文件
        config_file = tmp_path / "constraints.json"
        
        # 写入有效配置
        valid_config = {
            "constraints": {
                "retrieval": {
                    "min_relevant_docs": 1
                }
            }
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(valid_config, f)
        
        # Mock 配置文件路径
        with patch.object(ConstraintConfig, '_get_config_path', return_value=str(config_file)):
            # 重置单例
            ConstraintConfig._instance = None
            ConstraintConfig._config = {}
            
            # 加载初始配置
            config = ConstraintConfig()
            assert config.retrieval.get('min_relevant_docs') == 1
            
            # 删除配置文件
            os.remove(config_file)
            
            # 尝试重新加载
            success = config.reload()
            
            # 验证：使用默认配置
            assert success is True
            # 默认配置的 min_relevant_docs 是 1
            assert 'min_relevant_docs' in config.retrieval


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
