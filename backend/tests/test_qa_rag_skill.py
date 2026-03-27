import sys
import os
import asyncio

sys.path.insert(0, 'backend')

from app.skills.engine import SkillEngine

async def test_qa_rag_skill():
    print("=" * 60)
    print("测试 QA RAG Skill 完整流程")
    print("=" * 60)
    
    skill_engine = SkillEngine()
    
    context = {
        "query": "公司有哪些福利？",
        "question": "公司有哪些福利？",
        "session_id": "test_session"
    }
    
    print(f"\n输入:")
    print(f"  查询: {context['query']}")
    
    print(f"\n执行 qa_rag skill...")
    
    try:
        result = await skill_engine.execute("qa_rag", context)
        
        print(f"\n✓ 执行成功")
        print(f"\n结果:")
        print(f"  回答长度: {len(result.get('answer', ''))}")
        print(f"  回答内容: {result.get('answer', '')[:200]}...")
        print(f"  来源数量: {len(result.get('sources', []))}")
        
        sources = result.get('sources', [])
        if sources:
            print(f"\n  来源详情:")
            for i, source in enumerate(sources):
                print(f"    {i+1}. {source}")
        else:
            print(f"\n  ⚠️ 没有返回来源信息")
            
            # 检查中间步骤
            print(f"\n  调试中间步骤:")
            print(f"    query_embedding 存在: {'query_embedding' in result}")
            print(f"    retrieved_documents 存在: {'retrieved_documents' in result}")
            
            if 'retrieved_documents' in result:
                docs = result['retrieved_documents']
                print(f"    retrieved_documents 数量: {len(docs)}")
                if docs:
                    print(f"    第一个文档: {docs[0]}")
            
            print(f"    context 存在: {'context' in result}")
            if 'context' in result:
                print(f"    context 长度: {len(result['context'])}")
                print(f"    context 预览: {result['context'][:200]}...")
        
    except Exception as e:
        print(f"\n✗ 执行失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_qa_rag_skill())
