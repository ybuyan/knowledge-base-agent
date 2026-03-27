#!/usr/bin/env python
"""
调试 SSE 响应，查看实际的 sources 数据
"""
import sys
sys.path.insert(0, 'c:\\D\\code\\learning\\Agent\\AI-assistent\\backend')

import asyncio
import json
from app.services.qa_agent import QAAgent, QAConfig
from app.services.response_builder import ResponseBuilder
from app.services.content_analyzer import ContentAnalyzer

async def debug_sse_response():
    """模拟 SSE 响应，查看 sources 数据"""
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
        print(f"\n{'='*70}")
        print(f"查询: {query}")
        print('='*70)
        
        # 模拟 RAG 流程
        rag_context = await agent._retrieve(query, [])
        
        print(f"\n检索到的 documents: {len(rag_context.documents)}")
        print(f"检索到的 sources: {rag_context.sources}")
        
        # 模拟 LLM 回答
        mock_answer = f"根据员工手册，{query}的相关规定如下..."
        
        # 生成 done_chunk
        done_chunk = ResponseBuilder.done_chunk(rag_context.sources, mock_answer)
        print(f"\nSSE done_chunk:")
        print(done_chunk)
        
        # 解析 chunk
        data_str = done_chunk[6:].strip()
        try:
            data = json.loads(data_str)
            print(f"\n解析后的数据:")
            print(json.dumps(data, ensure_ascii=False, indent=2))
        except:
            print(f"\n解析失败: {data_str}")

if __name__ == "__main__":
    asyncio.run(debug_sse_response())
