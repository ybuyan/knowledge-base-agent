import os
import requests

os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''
os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''

session = requests.Session()
session.trust_env = False

print("=" * 60)
print("验证服务运行状态")
print("=" * 60)

try:
    print("\n1. 后端服务 (http://127.0.0.1:8001):")
    response = session.get("http://127.0.0.1:8001/", timeout=5)
    print(f"   ✓ 状态码: {response.status_code}")
    print(f"   ✓ 响应: {response.json()}")
    
    print("\n2. 前端服务 (http://127.0.0.1:3000):")
    response = session.get("http://127.0.0.1:3000/", timeout=5)
    print(f"   ✓ 状态码: {response.status_code}")
    print(f"   ✓ 响应: HTML 页面 (长度: {len(response.text)} 字符)")
    
    print("\n3. API 代理测试:")
    response = session.get("http://127.0.0.1:3000/api/", timeout=5)
    print(f"   ✓ 状态码: {response.status_code}")
    print(f"   ✓ 响应: {response.json()}")
    
    print("\n" + "=" * 60)
    print("✓ 所有服务运行正常！")
    print("=" * 60)
    print("\n访问地址:")
    print("  前端: http://localhost:3000")
    print("  后端: http://localhost:8001")
    print("  API文档: http://localhost:8001/docs")
    
except Exception as e:
    print(f"\n✗ 错误: {e}")
    import traceback
    traceback.print_exc()
