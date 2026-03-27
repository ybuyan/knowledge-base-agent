import sys
import os
import asyncio

sys.path.insert(0, 'backend')

from app.agents import agent_engine

async def test_qa_agent():
    print("=" * 60)
    print("测试 QA Agent")
    print("=" * 60)
    
    context = {
        "question": "公司有哪些福利？",
        "session_id": "test_session"
    }
    
    print(f"\n输入:")
    print(f"  查询: {context['question']}")
    
    print(f"\n执行 qa_agent...")
    
    try:
        result = await agent_engine.execute("qa_agent", context)
        
        print(f"\n✓ 执行成功")
        print(f"\n结果:")
        print(f"  回答长度: {len(result.get('answer', ''))}")
        print(f"  来源数量: {len(result.get('sources', []))}")
        
        sources = result.get('sources', [])
        if sources:
            print(f"\n  来源详情:")
            for i, source in enumerate(sources[:3]):
                print(f"    {i+1}. {source.get('filename')}: {source.get('content', '')[:80]}...")
        else:
            print(f"\n  ⚠️ 没有返回来源信息")
            print(f"\n  完整结果:")
            import json
            print(json.dumps(result, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"\n✗ 执行失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_qa_agent())
