#!/usr/bin/env python3
"""
检查配置是否正确加载

使用方法：
    python scripts/check_config.py
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def main():
    print("=" * 70)
    print("配置检查")
    print("=" * 70)
    print()
    
    try:
        from app.config import settings
        
        print("✅ 配置加载成功")
        print()
        
        # 显示关键配置
        print("📋 当前配置:")
        print("-" * 70)
        
        # LLM 配置
        print("\n🤖 LLM 配置:")
        print(f"  模型: {settings.llm_model}")
        print(f"  Base URL: {settings.llm_base_url}")
        
        # API Key
        api_key = settings.dashscope_api_key or settings.llm_api_key
        if api_key:
            print(f"  API Key: {api_key[:10]}...{api_key[-4:]} (已隐藏)")
        else:
            print("  ⚠️  API Key: 未配置")
        
        # Embedding 配置
        print("\n📊 Embedding 配置:")
        print(f"  模型: {settings.embedding_model}")
        
        # 数据库配置
        print("\n💾 数据库配置:")
        print(f"  MongoDB: {settings.mongo_url}")
        print(f"  数据库名: {settings.mongo_db_name}")
        print(f"  ChromaDB: {settings.chroma_persist_dir}")
        
        # 记忆配置
        print("\n🧠 记忆配置:")
        print(f"  最大 Tokens: {settings.memory_max_tokens}")
        print(f"  最大会话数: {settings.memory_max_sessions}")
        
        # 应用配置
        print("\n⚙️  应用配置:")
        print(f"  环境: {settings.app_env}")
        print(f"  调试模式: {settings.app_debug}")
        print(f"  CORS Origins: {', '.join(settings.allowed_origins)}")
        
        print()
        print("-" * 70)
        
        # 检查常见问题
        print("\n🔍 配置检查:")
        issues = []
        
        # 检查 API Key
        if not api_key:
            issues.append("❌ API Key 未配置")
        else:
            print("✅ API Key 已配置")
        
        # 检查模型配置
        supported_models = [
            'qwen-turbo', 'qwen-plus', 'qwen-max', 'qwen-math-turbo',
            'gpt-4', 'gpt-3.5-turbo', 'gpt-4-turbo'
        ]
        if settings.llm_model in supported_models:
            print(f"✅ LLM 模型配置正确: {settings.llm_model}")
        else:
            issues.append(f"⚠️  LLM 模型可能不受支持: {settings.llm_model}")
        
        # 检查 .env 文件
        env_file = project_root / ".env"
        if env_file.exists():
            print(f"✅ .env 文件存在: {env_file}")
        else:
            issues.append(f"❌ .env 文件不存在: {env_file}")
        
        # 检查生产环境配置
        if settings.app_env == "production":
            if "dev-secret-key" in settings.secret_key.lower():
                issues.append("❌ 生产环境使用了开发环境的 SECRET_KEY")
            else:
                print("✅ 生产环境 SECRET_KEY 已配置")
        
        # 显示问题
        if issues:
            print()
            print("⚠️  发现以下问题:")
            for issue in issues:
                print(f"  {issue}")
        else:
            print()
            print("🎉 所有配置检查通过！")
        
        print()
        print("=" * 70)
        
        # 提示
        print("\n💡 提示:")
        print("  - 修改 .env 文件后需要重启应用")
        print("  - 使用 LLM_MODEL 而不是 DASHSCOPE_MODEL")
        print("  - 详细说明请查看: backend/docs/ENV_CONFIGURATION.md")
        print()
        
        return 0 if not issues else 1
        
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        print()
        print("请检查:")
        print("  1. .env 文件是否存在")
        print("  2. .env 文件格式是否正确")
        print("  3. 必需的配置项是否都已设置")
        return 1


if __name__ == "__main__":
    exit(main())
