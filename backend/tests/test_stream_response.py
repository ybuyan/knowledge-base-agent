import os
import requests

os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''

session = requests.Session()
session.trust_env = False

base_url = "http://127.0.0.1:8001"

print("=" * 60)
print("测试流式接口的完整响应")
print("=" * 60)

# 创建会话
response = session.post(f"{base_url}/api/chat/sessions", timeout=10)
session_data = response.json()
print(f"\n会话ID: {session_data['id']}")

# 测试流式查询
payload = {
    "question": "公司有哪些福利？",
    "sessionId": session_data['id']
}

print(f"\n查询: {payload['question']}")
print("\n" + "-" * 60)

response = session.post(
    f"{base_url}/api/chat/v2/ask/stream",
    json=payload,
    stream=True,
    timeout=30
)

print(f"状态码: {response.status_code}")
print(f"Content-Type: {response.headers.get('content-type')}")

print("\n原始响应内容:")
print("-" * 60)

full_response = ""
for line in response.iter_lines():
    if line:
        line_str = line.decode('utf-8')
        print(line_str)
        full_response += line_str + "\n"

print("-" * 60)

# 解析响应
print("\n解析响应:")
print("-" * 60)

import json

answer = ""
sources = []

for line in full_response.split('\n'):
    if line.startswith('data: '):
        data = line[6:]
        if data == '[DONE]':
            print("\n✓ 收到完成信号")
            break
        try:
            parsed = json.loads(data)
            msg_type = parsed.get('type')
            
            if msg_type == 'text':
                answer += parsed.get('content', '')
            elif msg_type == 'sources':
                sources = parsed.get('sources', [])
                print(f"✓ 收到 sources 数据: {len(sources)} 个来源")
            elif msg_type == 'error':
                print(f"✗ 收到错误: {parsed.get('message')}")
        except Exception as e:
            print(f"解析失败: {line} - {e}")

print(f"\n结果:")
print(f"  回答长度: {len(answer)}")
print(f"  回答内容: {answer[:200]}...")
print(f"  来源数量: {len(sources)}")

if sources:
    print(f"\n  来源详情:")
    for i, source in enumerate(sources):
        print(f"    {i+1}. {source}")
else:
    print(f"\n  ⚠️ 没有解析到 sources")

print("\n" + "=" * 60)
