import asyncio
import httpx
import json
import os

os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''
os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''

async def test_chat_api():
    print("=" * 60)
    print("测试 Chat API (禁用代理)")
    print("=" * 60)
    
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            print("\n1. 测试根路径:")
            response = await client.get(f"{base_url}/")
            print(f"   状态码: {response.status_code}")
            print(f"   响应: {response.json()}")
            
            print("\n2. 测试创建会话:")
            response = await client.post(f"{base_url}/api/chat/sessions")
            print(f"   状态码: {response.status_code}")
            session = response.json()
            print(f"   会话ID: {session['id']}")
            
            print("\n3. 测试问答接口 (非流式):")
            payload = {
                "question": "公司有哪些福利？",
                "sessionId": session['id']
            }
            print(f"   发送问题: {payload['question']}")
            
            response = await client.post(
                f"{base_url}/api/chat/ask",
                json=payload
            )
            print(f"   状态码: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"   回答: {result['answer'][:200]}...")
                print(f"   来源数: {len(result['sources'])}")
            else:
                print(f"   错误: {response.text}")
            
            print("\n4. 测试问答接口 (流式):")
            payload = {
                "question": "年假有几天？",
                "sessionId": session['id']
            }
            print(f"   发送问题: {payload['question']}")
            
            async with client.stream(
                "POST",
                f"{base_url}/api/chat/v2/ask/stream",
                json=payload,
                timeout=60.0
            ) as response:
                print(f"   状态码: {response.status_code}")
                print(f"   流式响应:")
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            print("\n   [完成]")
                            break
                        try:
                            parsed = json.loads(data)
                            if parsed.get("type") == "text":
                                print(parsed["content"], end="", flush=True)
                            elif parsed.get("type") == "sources":
                                print(f"\n   来源数: {len(parsed['sources'])}")
                        except:
                            pass
            
        except Exception as e:
            print(f"\n错误: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_chat_api())
