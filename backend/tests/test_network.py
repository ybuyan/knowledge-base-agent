import asyncio
import httpx
import os
import sys

async def test_direct_api_call():
    print("=" * 60)
    print("测试直接 API 调用...")
    print("=" * 60)
    
    api_key = "sk-a530317402894edb852ab83b68e05dab"
    base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    
    print(f"\nAPI Key: {api_key[:20]}...")
    print(f"Base URL: {base_url}")
    
    test_cases = [
        {
            "name": "测试1: 不验证 SSL",
            "client": httpx.AsyncClient(verify=False, timeout=30.0)
        },
        {
            "name": "测试2: 验证 SSL",
            "client": httpx.AsyncClient(timeout=30.0)
        },
        {
            "name": "测试3: 禁用代理",
            "client": httpx.AsyncClient(
                verify=False, 
                timeout=30.0,
                proxies=None
            )
        }
    ]
    
    for test in test_cases:
        print(f"\n{test['name']}:")
        try:
            url = f"{base_url}/embeddings"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "text-embedding-v3",
                "input": "测试文本"
            }
            
            print(f"  发送请求到: {url}")
            response = await test['client'].post(url, json=payload, headers=headers)
            print(f"  ✓ 成功! 状态码: {response.status_code}")
            data = response.json()
            if "data" in data:
                print(f"  ✓ Embedding 维度: {len(data['data'][0]['embedding'])}")
            await test['client'].aclose()
            return True
            
        except Exception as e:
            print(f"  ✗ 失败: {type(e).__name__}: {str(e)[:200]}")
            await test['client'].aclose()
    
    return False

async def test_llm_api():
    print("\n" + "=" * 60)
    print("测试 LLM API...")
    print("=" * 60)
    
    api_key = "sk-a530317402894edb852ab83b68e05dab"
    base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    
    try:
        async with httpx.AsyncClient(verify=False, timeout=60.0) as client:
            url = f"{base_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "qwen-plus",
                "messages": [
                    {"role": "user", "content": "你好"}
                ]
            }
            
            print(f"发送请求到: {url}")
            response = await client.post(url, json=payload, headers=headers)
            print(f"✓ 成功! 状态码: {response.status_code}")
            data = response.json()
            if "choices" in data:
                print(f"✓ 回复: {data['choices'][0]['message']['content'][:100]}")
            return True
            
    except Exception as e:
        print(f"✗ 失败: {type(e).__name__}: {str(e)[:200]}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    print("\n网络诊断测试")
    print("=" * 60)
    
    print(f"Python 版本: {sys.version}")
    print(f"httpx 版本: {httpx.__version__}")
    print(f"当前工作目录: {os.getcwd()}")
    
    print("\n环境变量:")
    print(f"  HTTP_PROXY: {os.environ.get('HTTP_PROXY', '未设置')}")
    print(f"  HTTPS_PROXY: {os.environ.get('HTTPS_PROXY', '未设置')}")
    print(f"  NO_PROXY: {os.environ.get('NO_PROXY', '未设置')}")
    
    embedding_ok = await test_direct_api_call()
    llm_ok = await test_llm_api()
    
    print("\n" + "=" * 60)
    print("测试结果:")
    print(f"  Embedding API: {'✓' if embedding_ok else '✗'}")
    print(f"  LLM API: {'✓' if llm_ok else '✗'}")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
