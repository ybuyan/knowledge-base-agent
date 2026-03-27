import os
import requests
import time

os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''
os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''

session = requests.Session()
session.trust_env = False

base_url = "http://127.0.0.1:8001"

print("=" * 60)
print("模拟前端完整流程测试")
print("=" * 60)

try:
    print("\n1. 测试文档列表")
    response = session.get(f"{base_url}/api/documents?page=1&pageSize=10", timeout=10)
    print(f"   状态码: {response.status_code}")
    docs = response.json()
    print(f"   文档数量: {docs['total']}")
    
    if docs['documents']:
        print(f"   文档列表:")
        for doc in docs['documents'][:3]:
            print(f"     - {doc['filename']} (状态: {doc['status']})")
    
    print("\n2. 创建会话")
    response = session.post(f"{base_url}/api/chat/sessions", timeout=10)
    print(f"   状态码: {response.status_code}")
    session_data = response.json()
    print(f"   会话ID: {session_data['id']}")
    
    print("\n3. 测试流式查询")
    payload = {
        "question": "公司有哪些福利？",
        "sessionId": session_data['id']
    }
    
    response = session.post(
        f"{base_url}/api/chat/v2/ask/stream",
        json=payload,
        stream=True,
        timeout=30
    )
    
    print(f"   状态码: {response.status_code}")
    print(f"   响应头: {response.headers.get('content-type')}")
    
    print("\n   流式响应内容:")
    full_answer = ""
    sources = []
    
    for line in response.iter_lines():
        if line:
            line_str = line.decode('utf-8')
            if line_str.startswith('data: '):
                data = line_str[6:]
                if data == '[DONE]':
                    print("\n   [完成]")
                    break
                try:
                    import json
                    parsed = json.loads(data)
                    if parsed.get('type') == 'text':
                        print(parsed['content'], end='', flush=True)
                        full_answer += parsed['content']
                    elif parsed.get('type') == 'sources':
                        sources = parsed.get('sources', [])
                        print(f"\n\n   来源数量: {len(sources)}")
                    elif parsed.get('type') == 'error':
                        print(f"\n   ✗ 错误: {parsed.get('message')}")
                except Exception as e:
                    pass
    
    print(f"\n\n4. 验证结果")
    print(f"   回答长度: {len(full_answer)}")
    print(f"   来源数量: {len(sources)}")
    
    if sources:
        print(f"\n   来源详情:")
        for i, source in enumerate(sources[:3]):
            print(f"     {i+1}. {source.get('filename', '未知')}")
            print(f"        内容: {source.get('content', '')[:80]}...")
    else:
        print(f"\n   ⚠️ 没有返回来源信息")
    
    print(f"\n5. 再次查询（非流式）")
    payload = {
        "question": "年假有几天？",
        "sessionId": session_data['id']
    }
    
    response = session.post(
        f"{base_url}/api/chat/ask",
        json=payload,
        timeout=30
    )
    
    print(f"   状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"   回答: {result['answer'][:150]}...")
        print(f"   来源数量: {len(result['sources'])}")
        
        if result['sources']:
            print(f"\n   来源详情:")
            for i, source in enumerate(result['sources'][:3]):
                print(f"     {i+1}. {source.get('filename', '未知')}")
        else:
            print(f"\n   ⚠️ 没有返回来源信息")
    else:
        print(f"   ✗ 查询失败: {response.text}")

except Exception as e:
    print(f"\n✗ 错误: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
