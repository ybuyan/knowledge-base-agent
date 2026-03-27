import requests
import json

def test_api():
    print("=" * 60)
    print("测试 API (使用 requests)")
    print("=" * 60)
    
    base_url = "http://127.0.0.1:8000"
    
    try:
        print("\n1. 测试根路径:")
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.json()}")
        
        print("\n2. 测试创建会话:")
        response = requests.post(f"{base_url}/api/chat/sessions", timeout=5)
        print(f"   状态码: {response.status_code}")
        session = response.json()
        print(f"   会话ID: {session['id']}")
        
        print("\n3. 测试问答接口 (非流式):")
        payload = {
            "question": "公司有哪些福利？",
            "sessionId": session['id']
        }
        print(f"   发送问题: {payload['question']}")
        
        response = requests.post(
            f"{base_url}/api/chat/ask",
            json=payload,
            timeout=30
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
