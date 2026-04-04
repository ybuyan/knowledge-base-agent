# 后端服务重启指南

## 问题现状

- ✅ `leave_apply` skill 文件已删除
- ✅ `leave_guide` skill 已创建（qa 类型）
- ✅ 代码中没有 process 类型的请假 skill
- ❌ 但前端仍然显示"您是想发起「请假」吗？"

## 原因

后端服务正在运行，使用的是启动时加载的旧缓存。即使文件已删除，内存中的单例 `SkillEngine` 仍然保留着旧的 skill 定义。

## 解决方案

### 方法 1：重启后端服务（推荐）

1. 找到运行后端服务的终端/命令行窗口
2. 按 `Ctrl+C` 停止服务
3. 重新启动：
   ```bash
   cd backend
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### 方法 2：使用 reload API（需要 HR 权限）

如果不想重启，可以调用 API 强制重新加载：

```bash
# 需要先登录获取 token
curl -X POST "http://localhost:8000/api/flow-config/skills/leave_apply/reload" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

但这个方法可能不完全有效，因为 `leave_apply` 已经不存在了。

### 方法 3：杀死进程（如果找不到终端）

Windows:
```powershell
# 查找 Python 进程
Get-Process python | Where-Object {$_.Path -like "*uvicorn*"}

# 杀死进程（替换 PID）
Stop-Process -Id <PID> -Force
```

Linux/Mac:
```bash
# 查找进程
ps aux | grep uvicorn

# 杀死进程
kill -9 <PID>
```

## 验证

重启后，测试"我想请假"，应该会：
1. orchestrator 识别为 `qa` 意图
2. qa_agent 调用 `qa_rag` skill
3. LLM 根据 SKILL.md 中的指引回答
4. 提供请假操作指引，而不是发起流程

## 预期行为

```
用户：我想请假
AI：好的，我来帮您了解请假流程。请问您要申请什么类型的假期呢？
    我们有年假、病假、事假、婚假、产假、陪产假和高温假。

用户：年假，3天
AI：明白了！以下是请假操作指引：

    📊 假期类型：年假
    📝 申请流程：
    1. 发起请假申请
    2. 直属上级审批
    3. HR 备案

    🔗 申请入口：https://oa.company.com/leave

    📄 参考模板：
    【年假申请】
    申请人：xxx
    时间：xxxx 年 xx 月 xx 日 - xxxx 年 xx 月 xx 日，共 3 天
    事由：个人事务

    ⚠️ 注意事项：
    - 请提前 3 天申请
    - 审批时间：1-3 个工作日
```

## 如果重启后仍然有问题

1. 检查是否有多个后端服务实例在运行
2. 检查是否有其他地方缓存了 skill 定义
3. 查看后端日志，确认 skill 加载情况
4. 运行 `python force_reload_skills.py` 验证 skill 状态

## 相关文件

- `backend/force_reload_skills.py` - 验证当前 skill 状态的脚本
- `backend/clear_skill_cache.py` - 清理缓存的脚本
- `FINAL_SOLUTION.md` - 完整的解决方案说明
