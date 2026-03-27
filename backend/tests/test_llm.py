"""
测试 LLM 连接
运行方式: cd backend && python -m tests.test_llm
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.llm import get_llm


async def main():
    print("=" * 50)
    print("测试通义千问 LLM 连接")
    print("=" * 50)
    
    try:
        llm = get_llm()
        print(f"\n模型: {llm.model_name}")
        print(f"Base URL: {llm.openai_api_base}")
        
        print("\n发送测试消息: '你好，请简单介绍一下你自己'")
        print("-" * 50)
        
        response = await llm.ainvoke("你好，请简单介绍一下你自己")
        print(f"\n回复:\n{response.content}")
        
        print("\n" + "=" * 50)
        print("✅ LLM 连接测试成功!")
        print("=" * 50)
        
    except ValueError as e:
        print(f"\n❌ 配置错误: {e}")
        print("\n请在 backend/.env 文件中配置:")
        print("  DASHSCOPE_API_KEY=your_api_key")
        print("\n获取 API Key: https://dashscope.console.aliyun.com/")
        
    except Exception as e:
        print(f"\n❌ 连接失败: {e}")


if __name__ == "__main__":
    asyncio.run(main())
