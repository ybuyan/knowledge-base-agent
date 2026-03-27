import sys
import os
import asyncio

sys.path.insert(0, 'backend')

from app.skills.engine import SkillEngine
from app.core.chroma import get_documents_collection

async def test_qa_flow():
    print("=" * 60)
    print("测试完整的 QA 流程")
    print("=" * 60)
    
    print("\n1. 检查知识库状态")
    collection = get_documents_collection()
    count = collection.count()
    print(f"   文档总数: {count}")
    
    if count == 0:
        print("\n✗ 精神库为空，请先上传文档")
        return
    
    print("\n2. 执行 QA RAG 流程")
    
    skill_engine = SkillEngine()
    
    context = {
        "query": "公司有哪些福利？",
        "question": "公司有哪些福利？",
        "session_id": "test_session"
    }
    
    try:
        result = await skill_engine.execute("qa_rag", context)
        
        print("\n✓ QA 流程执行成功")
        print(f"\n结果:")
        print(f"  回答: {result.get('answer', '')[:200]}...")
        print(f"  来源数量: {len(result.get('sources', []))}")
        
        sources = result.get('sources', [])
        if sources:
            print(f"\n  来源详情:")
            for i, source in enumerate(sources[:3]):
                print(f"    {i+1}. ID: {source.get('id')}")
                print(f"       文件名: {source.get('filename')}")
                print(f"       内容: {source.get('content', '')[:100]}...")
        else:
            print(f"\n  ⚠️ 没有返回来源信息")
            
            # 检查中间步骤
            print(f"\n  调试信息:")
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
        print(f"\n✗ QA 流程执行失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_qa_flow())
