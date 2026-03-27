import os
import sys

print("=" * 60)
print("检查环境变量配置")
print("=" * 60)

print(f"\n当前工作目录: {os.getcwd()}")
print(f"Python 路径: {sys.path[:3]}")

print("\n环境变量:")
print(f"  DASHSCOPE_API_KEY: {os.environ.get('DASHSCOPE_API_KEY', '未设置')[:20]}...")
print(f"  LLM_API_KEY: {os.environ.get('LLM_API_KEY', '未设置')}")
print(f"  LLM_BASE_URL: {os.environ.get('LLM_BASE_URL', '未设置')}")
print(f"  LLM_MODEL: {os.environ.get('LLM_MODEL', '未设置')}")

print("\n尝试加载配置...")
sys.path.insert(0, 'backend')

from app.config import settings

print(f"\nSettings 配置:")
print(f"  dashscope_api_key: {settings.dashscope_api_key[:20] if settings.dashscope_api_key else 'None'}...")
print(f"  llm_api_key: {settings.llm_api_key[:20] if settings.llm_api_key else 'None'}...")
print(f"  llm_base_url: {settings.llm_base_url}")
print(f"  llm_model: {settings.llm_model}")

print("\n.env 文件路径检查:")
env_path = os.path.join('backend', '.env')
print(f"  路径: {os.path.abspath(env_path)}")
print(f"  存在: {os.path.exists(env_path)}")

if os.path.exists(env_path):
    print("\n.env 文件内容:")
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            if 'API_KEY' in line:
                parts = line.strip().split('=')
                if len(parts) == 2:
                    print(f"  {parts[0]}: {parts[1][:20]}...")
            else:
                print(f"  {line.strip()}")
