import os
import requests

os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''
os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''

session = requests.Session()
session.trust_env = False

print("=" * 60)
print("测试前端查询功能")
print("=" * 60)

base_url = "http://127.0.0.1:8001"

try:
    print("\n1. 创建会话:")
    response = session.post(f"{base_url}/api/chat/sessions", timeout=10)
    print(f"   状态码: {response.status_code}")
    session_data = response.json()
    print(f"   会话ID: {session_data['id']}")
    
    print("\n2. 测试查询:")
    payload = {
        "question": "公司有哪些福利？",
        "sessionId": session_data['id']
    }
    
    print(f"   问题: {payload['question']}")
    
    response = session.post(
        f"{base_url}/api/chat/ask",
        json=payload,
        timeout=30
    )
    
    print(f"   状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n   ✓ 查询成功!")
        print(f"   回答: {result['answer'][:200]}...")
        print(f"   来源数: {len(result['sources'])}")
        
        if result['sources']:
            print(f"\n   来源:")
            for i, source in enumerate(result['sources'][:3]):
                print(f"   {i+1}. {source.get('filename', '未知')}")
                print(f"      内容: {source.get('content', '')[:100]}...")
    else:
        print(f"\n   ✗ 查询失败")
        print(f"   错误: {response.text}")
        
except Exception as e:
    print(f"\n✗ 错误: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
