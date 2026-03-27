import urllib.request
import json

print("Testing backend API...")
try:
    # 测试HTTP连接
    response = urllib.request.urlopen('http://localhost:8000/api/health')
    status_code = response.getcode()
    content = response.read().decode('utf-8')
    print(f"HTTP response: {status_code}")
    print(f"HTTP content: {content}")
except Exception as e:
    print(f"HTTP error: {e}")
