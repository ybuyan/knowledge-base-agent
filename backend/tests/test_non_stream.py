import os
import requests
import json

os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''

session = requests.Session()
session.trust_env = False

base_url = "http://127.0.0.1:8001"

print("=" * 60)
print("测试非流式接口")
print("=" * 60)

# 创建会话
response = session.post(f"{base_url}/api/chat/sessions", timeout=10)
session_data = response.json()
print(f"\n会话ID: {session_data['id']}")

# 测试非流式查询
payload = {
    "question": "公司有哪些福利？",
    "sessionId": session_data['id']
}

print(f"\n查询: {payload['question']}")

response = session.post(
    f"{base_url}/api/chat/ask",
    json=payload,
    timeout=30
)

print(f"状态码: {response.status_code}")

if response.status_code == 200:
    result = response.json()
    print(f"\n回答: {result['answer'][:300]}...")
    print(f"\n来源数量: {len(result['sources'])}")
    
    if result['sources']:
        print(f"\n来源详情:")
        for i, source in enumerate(result['sources'][:3]):
            print(f"  {i+1}. {source.get('filename', '未知')}")
            print(f"     内容: {source.get('content', '')[:80]}...")
    else:
        print(f"\n⚠️ 没有返回来源信息")
else:
    print(f"\n✗ 查询失败: {response.text}")

print("\n" + "=" * 60)
