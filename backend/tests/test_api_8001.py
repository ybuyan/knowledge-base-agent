import os
import sys

os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''
os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''
os.environ['NO_PROXY'] = '*'
os.environ['no_proxy'] = '*'

import requests
import json

def test_api():
    print("=" * 60)
    print("测试 API (端口 8001)")
    print("=" * 60)
    
    base_url = "http://127.0.0.1:8001"
    
    session = requests.Session()
    session.trust_env = False
    
    try:
        print("\n1. 测试根路径:")
        response = session.get(f"{base_url}/", timeout=5)
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.json()}")
        
        print("\n2. 测试创建会话:")
        response = session.post(f"{base_url}/api/chat/sessions", timeout=5)
        print(f"   状态码: {response.status_code}")
        session_data = response.json()
        print(f"   会话ID: {session_data['id']}")
        
        print("\n3. 测试问答接口 (非流式):")
        payload = {
            "question": "公司有哪些福利？",
            "sessionId": session_data['id']
        }
        print(f"   发送问题: {payload['question']}")
        
        response = session.post(
            f"{base_url}/api/chat/ask",
            json=payload,
            timeout=60
        )
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   回答: {result['answer'][:200]}...")
            print(f"   来源数: {len(result['sources'])}")
        else:
            print(f"   错误: {response.text}")
            
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_api()
