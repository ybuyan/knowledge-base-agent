"""
配置加载器测试用例

测试config.json和config_loader的功能
"""
import json
import sys
import pytest
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config_loader import ConfigLoader


class TestConfigLoader:
    """配置加载器测试"""
    
    @pytest.fixture
    def config_loader(self):
        """创建配置加载器实例"""
        return ConfigLoader()
    
    def test_singleton_pattern(self):
        """测试单例模式"""
        loader1 = ConfigLoader()
        loader2 = ConfigLoader()
        assert loader1 is loader2
    
    def test_load_settings_config(self, config_loader):
        """测试加载settings配置"""
        config = config_loader.load("settings")
        
        assert config is not None
        assert isinstance(config, dict)
        assert "version" in config
        assert "llm" in config
        assert "vector_store" in config
    
    def test_load_skills_config(self, config_loader):
        """测试加载skills配置"""
        config = config_loader.load("skills")
        
        assert config is not None
        assert isinstance(config, dict)
    
    def test_load_agents_config(self, config_loader):
        """测试加载agents配置"""
        config = config_loader.load("agents")
        
        assert config is not None
        assert isinstance(config, dict)
    
    def test_load_tools_config(self, config_loader):
        """测试加载tools配置"""
        config = config_loader.load("tools")
        
        assert config is not None
        assert isinstance(config, dict)
    
    def test_load_prompts_config(self, config_loader):
        """测试加载prompts配置"""
        config = config_loader.load("prompts")
        
        assert config is not None
        assert isinstance(config, dict)
    
    def test_get_setting(self, config_loader):
        """测试获取设置值"""
        # 测试获取嵌套值
        temperature = config_loader.get_setting("llm.temperature")
        if temperature is not None:
            assert isinstance(temperature, (int, float))
        
        provider = config_loader.get_setting("llm.provider")
        if provider is not None:
            assert isinstance(provider, str)
    
    def test_get_setting_with_default(self, config_loader):
        """测试获取设置值（带默认值）"""
        value = config_loader.get_setting("non.existent.key", default="default_value")
        assert value == "default_value"
    
    def test_reload_config(self, config_loader):
        """测试重新加载配置"""
        # 加载配置
        config1 = config_loader.load("settings")
        
        # 重新加载
        config_loader.reload("settings")
        config2 = config_loader.load("settings")
        
        # 应该重新加载
        assert config1 == config2
    
    def test_reload_all_configs(self, config_loader):
        """测试重新加载所有配置"""
        # 加载多个配置
        config_loader.load("settings")
        config_loader.load("skills")
        
        # 重新加载所有
        config_loader.reload()
        
        # 重新加载后应该可以再次加载
        config = config_loader.load("settings")
        assert config is not None
    
    def test_config_caching(self, config_loader):
        """测试配置缓存"""
        # 第一次加载
        config1 = config_loader.load("settings")
        
        # 第二次加载应该使用缓存
        config2 = config_loader.load("settings")
        
        # 应该是同一个对象
        assert config1 is config2


class TestAgentsConfig:
    """Agents配置测试"""
    
    @pytest.fixture
    def agents_config_path(self):
        """获取agents配置文件路径"""
        return Path(__file__).parent.parent.parent / "app" / "agents" / "config.json"
    
    def test_agents_config_exists(self, agents_config_path):
        """测试agents配置文件存在"""
        assert agents_config_path.exists()
    
    def test_agents_config_structure(self, agents_config_path):
        """测试agents配置结构"""
        with open(agents_config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        assert "agents" in config
        agents = config.get("agents", [])
        assert isinstance(agents, list)
        
        # 检查每个agent的配置
        for agent in agents:
            assert "id" in agent
            assert "name" in agent
            assert "description" in agent
            assert "enabled" in agent
            assert isinstance(agent.get("enabled"), bool)
    
    def test_orchestrator_agent_config(self, agents_config_path):
        """测试orchestrator agent配置"""
        with open(agents_config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        agents = config.get("agents", [])
        orchestrator = None
        for agent in agents:
            if agent.get("id") == "orchestrator_agent":
                orchestrator = agent
                break
        
        if orchestrator:
            assert "description" in orchestrator
            assert "enabled" in orchestrator


class TestSkillsConfig:
    """Skills配置测试"""
    
    @pytest.fixture
    def skills_config_path(self):
        """获取skills配置文件路径"""
        return Path(__file__).parent.parent.parent / "app" / "skills" / "config.json"
    
    def test_skills_config_exists(self, skills_config_path):
        """测试skills配置文件存在"""
        assert skills_config_path.exists()
    
    def test_skills_config_structure(self, skills_config_path):
        """测试skills配置结构"""
        with open(skills_config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        assert "skills" in config
        skills = config.get("skills", [])
        assert isinstance(skills, list)
        
        # 检查每个skill的配置
        for skill in skills:
            assert "id" in skill
            assert "name" in skill
            assert "description" in skill
            assert "enabled" in skill
            assert "pipeline" in skill
            assert isinstance(skill.get("enabled"), bool)
            assert isinstance(skill.get("pipeline"), list)
    
    def test_skill_processors(self, skills_config_path):
        """测试skill处理器配置"""
        with open(skills_config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        skills = config.get("skills", [])
        for skill in skills:
            pipeline = skill.get("pipeline", [])
            for step in pipeline:
                assert "step" in step
                assert "processor" in step


class TestToolsConfig:
    """Tools配置测试"""
    
    @pytest.fixture
    def tools_config_path(self):
        """获取tools配置文件路径"""
        return Path(__file__).parent.parent.parent / "app" / "tools" / "config.json"
    
    def test_tools_config_exists(self, tools_config_path):
        """测试tools配置文件存在"""
        assert tools_config_path.exists()
    
    def test_tools_config_structure(self, tools_config_path):
        """测试tools配置结构"""
        with open(tools_config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        assert "tools" in config
        tools = config.get("tools", [])
        assert isinstance(tools, list)
        
        # 检查每个tool的配置
        for tool in tools:
            assert "id" in tool
            assert "name" in tool
            assert "description" in tool
            assert "enabled" in tool
            assert isinstance(tool.get("enabled"), bool)


class TestPromptsConfig:
    """Prompts配置测试"""
    
    @pytest.fixture
    def prompts_config_path(self):
        """获取prompts配置文件路径"""
        return Path(__file__).parent.parent.parent / "app" / "prompts" / "config.json"
    
    def test_prompts_config_exists(self, prompts_config_path):
        """测试prompts配置文件存在"""
        assert prompts_config_path.exists()
    
    def test_prompts_config_structure(self, prompts_config_path):
        """测试prompts配置结构"""
        with open(prompts_config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        assert "prompts" in config
        prompts = config.get("prompts", {})
        
        # 检查每个prompt的配置
        for prompt_name, prompt_config in prompts.items():
            assert "template" in prompt_config or "file" in prompt_config


class TestConfigIntegration:
    """配置集成测试"""
    
    def test_all_configs_loadable(self):
        """测试所有配置文件可加载"""
        base_path = Path(__file__).parent.parent.parent / "app"
        config_files = [
            base_path / "core" / "config.json",
            base_path / "agents" / "config.json",
            base_path / "skills" / "config.json",
            base_path / "tools" / "config.json",
            base_path / "prompts" / "config.json"
        ]
        
        for config_file in config_files:
            if config_file.exists():
                with open(config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    assert config is not None
                    assert isinstance(config, dict)
    
    def test_config_consistency(self):
        """测试配置一致性"""
        # 加载核心配置
        core_config_path = Path(__file__).parent.parent.parent / "app" / "core" / "config.json"
        if core_config_path.exists():
            with open(core_config_path, "r", encoding="utf-8") as f:
                core_config = json.load(f)
            
            # 验证配置版本
            assert "version" in core_config
            version = core_config.get("version")
            assert version is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
