import sys
import os
import asyncio

sys.path.insert(0, 'backend')

from app.core.chroma import get_documents_collection
from app.core.embeddings import get_embeddings
from app.core.llm import stream_llm
from app.prompts.manager import prompt_manager

async def test_stream_flow():
    print("=" * 60)
    print("测试流式接口完整流程")
    print("=" * 60)
    
    question = "公司有哪些福利？"
    
    print(f"\n1. 查询问题: {question}")
    
    print("\n2. 生成查询向量...")
    embeddings = get_embeddings()
    query_embedding = await embeddings.aembed_query(question)
    print(f"   ✓ 向量维度: {len(query_embedding)}")
    
    print("\n3. 查询知识库...")
    collection = get_documents_collection()
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=5
    )
    
    print(f"   查询结果文档数: {len(results['documents'][0]) if results['documents'] and results['documents'][0] else 0}")
    
    print("\n4. 构建上下文和来源...")
    context_parts = []
    sources = []
    
    if results["documents"] and results["documents"][0]:
        for i, doc in enumerate(results["documents"][0]):
            context_parts.append(f"[{i+1}] {doc}")
            metadata = results["metadatas"][0][i] if results["metadatas"] else {}
            sources.append({
                "id": str(i+1),
                "filename": metadata.get("document_name", "未知"),
                "content": doc[:200] + "..."
            })
    
    context = "\n\n".join(context_parts) if context_parts else "暂无相关知识库内容"
    
    print(f"   上下文长度: {len(context)}")
    print(f"   来源数量: {len(sources)}")
    
    print("\n5. 渲染 Prompt...")
    prompts = prompt_manager.render("qa_rag", {
        "context": context,
        "question": question
    })
    
    print(f"   System Prompt 长度: {len(prompts['system'])}")
    print(f"   User Prompt 长度: {len(prompts['user'])}")
    
    print(f"\n   User Prompt 内容:")
    print(f"   {prompts['user'][:500]}...")
    
    print("\n6. 调用 LLM 流式生成...")
    answer = ""
    
    async for chunk in stream_llm(prompts["user"], prompts["system"]):
        print(chunk, end='', flush=True)
        answer += chunk
    
    print(f"\n\n7. 结果:")
    print(f"   回答长度: {len(answer)}")
    print(f"   来源数量: {len(sources)}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    asyncio.run(test_stream_flow())
