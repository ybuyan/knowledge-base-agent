import requests
import urllib3

# 禁用SSL验证警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

print("Testing backend API...")
try:
    # 测试HTTP连接
    response = requests.get('http://localhost:8000/api/health', verify=False)
    print(f"HTTP response: {response.status_code}")
    print(f"HTTP content: {response.json()}")
except Exception as e:
    print(f"HTTP error: {e}")

print("\nTesting frontend proxy...")
try:
    # 测试前端代理
    response = requests.get('http://localhost:3002/api/health', verify=False)
    print(f"Frontend proxy response: {response.status_code}")
    print(f"Frontend proxy content: {response.json()}")
except Exception as e:
    print(f"Frontend proxy error: {e}")
