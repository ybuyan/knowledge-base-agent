@echo off

REM 启动后端服务
echo 启动后端服务...
start "Backend Server" cmd /c "cd backend; uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload"

REM 等待后端服务启动
ping 127.0.0.1 -n 3 > nul

REM 启动前端服务
echo 启动前端服务...
start "Frontend Server" cmd /c "cd frontend; npm run dev"

echo 服务启动完成！
echo 后端服务地址: http://localhost:8001
echo 前端服务地址: http://localhost:3000
echo 后端API文档: http://localhost:8001/docs

# 基本启动（会扫描现有文件）
python scripts/file_watcher.py

# 指定配置文件
python scripts/file_watcher.py --config scripts/config/watch.json

# 跳过初始扫描（只监控新变化）
python scripts/file_watcher.py --no-initial-scan