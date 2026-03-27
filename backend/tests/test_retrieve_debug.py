#!/usr/bin/env python
"""
测试检索功能，查看返回的 metadata
"""
import sys
sys.path.insert(0, 'c:\\D\\code\\learning\\Agent\\AI-assistent\\backend')

import asyncio
from app.services.qa_agent import QAAgent, QAConfig

async def test_retrieve():
    config = QAConfig()
    agent = QAAgent(config)
    
    # 测试查询
    test_queries = [
        "产假天数",
        "法定产假时长",
        "各地产假规定",
        "生育津贴领取期限"
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"查询: {query}")
        print('='*60)
        
        rag_context = await agent._retrieve(query, [])
        
        print(f"检索到 {rag_context.document_count} 个文档")
        print(f"Sources: {rag_context.sources}")
        
        if rag_context.sources:
            for source in rag_context.sources:
                print(f"  - ID: {source.get('id')}")
                print(f"    Filename: {source.get('filename')}")
                print(f"    Content: {source.get('content', '')[:100]}...")
        else:
            print("  ⚠️ 没有返回有效的 sources")

if __name__ == "__main__":
    asyncio.run(test_retrieve())
