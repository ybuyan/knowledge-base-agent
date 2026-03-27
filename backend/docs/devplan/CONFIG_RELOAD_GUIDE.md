# 约束配置动态更新指南

## 概述

约束配置系统支持两种更新方式：
1. **通过 API 更新** - 立即生效，无需重启
2. **直接修改配置文件** - 需要调用 reload API 或重启服务

---

## 配置更新方式

### 方式 1: 通过 API 更新（推荐）✅

**优点**:
- 立即生效，无需额外操作
- 自动保存到配置文件
- 有完整的错误处理
- 支持部分更新

**使用方法**:

#### 更新所有配置
```bash
curl -X PUT http://localhost:8000/api/constraints \
  -H "Content-Type: application/json" \
  -d '{
    "retrieval": {
      "min_relevant_docs": 2
    },
    "generation": {
      "forbidden_topics": ["薪资", "工资", "奖金"]
    }
  }'
```

#### 更新检索配置
```bash
curl -X PUT http://localhost:8000/api/constraints/retrieval \
  -H "Content-Type: application/json" \
  -d '{
    "min_relevant_docs": 3,
    "min_similarity_score": 0.5
  }'
```

#### 更新生成配置
```bash
curl -X PUT http://localhost:8000/api/constraints/generation \
  -H "Content-Type: application/json" \
  -d '{
    "forbidden_topics": ["薪资", "工资"],
    "max_answer_length": 1500
  }'
```

---

### 方式 2: 直接修改配置文件

**适用场景**:
- 批量修改多个配置
- 通过配置管理工具部署
- 前端直接编辑配置文件

**步骤**:

#### 1. 修改配置文件
编辑 `backend/config/constraints.json`:

```json
{
  "constraints": {
    "retrieval": {
      "enabled": true,
      "min_similarity_score": 0.3,
      "min_relevant_docs": 2,
      "max_relevant_docs": 5
    },
    "generation": {
      "forbidden_topics": ["薪资", "工资", "奖金"]
    }
  }
}
```

#### 2. 重新加载配置

**选项 A: 调用 reload API（推荐）**
```bash
curl -X POST http://localhost:8000/api/constraints/reload
```

**响应示例**:
```json
{
  "constraints": {
    "retrieval": { ... },
    "generation": { ... }
  },
  "message": "Constraints reloaded successfully from file"
}
```

**选项 B: 重启服务**
```bash
systemctl restart backend-service
```

---

## API 端点详解

### 1. 获取当前配置
```
GET /api/constraints
```

**响应**:
```json
{
  "constraints": {
    "retrieval": { ... },
    "generation": { ... },
    "validation": { ... },
    "fallback": { ... },
    "suggest_questions": { ... }
  },
  "message": "Success"
}
```

---

### 2. 更新配置
```
PUT /api/constraints
```

**请求体**:
```json
{
  "retrieval": { ... },
  "generation": { ... },
  "validation": { ... },
  "fallback": { ... }
}
```

**特点**:
- 支持部分更新（只传需要修改的部分）
- 自动保存到文件
- 立即生效

---

### 3. 重置为默认配置
```
POST /api/constraints/reset
```

**效果**:
- 恢复所有配置为默认值
- 自动保存到文件
- 立即生效

---

### 4. 重新加载配置文件 🆕
```
POST /api/constraints/reload
```

**用途**:
- 配置文件被外部修改后重新加载
- 使文件修改立即生效
- 无需重启服务

**响应**:
```json
{
  "constraints": { ... },
  "message": "Constraints reloaded successfully from file"
}
```

**错误处理**:
- 如果文件不存在，使用默认配置
- 如果 JSON 格式错误，保持当前配置并返回错误
- 返回 500 状态码表示重新加载失败

---

## 前端集成建议

### 场景 1: 前端配置管理界面

**推荐方式**: 使用 API 更新

```javascript
// 更新配置
async function updateConstraints(config) {
  const response = await fetch('/api/constraints', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config)
  });
  
  if (response.ok) {
    console.log('配置更新成功');
    // 配置已立即生效
  }
}

// 使用示例
updateConstraints({
  retrieval: {
    min_relevant_docs: 2
  },
  generation: {
    forbidden_topics: ['薪资', '工资']
  }
});
```

---

### 场景 2: 前端直接编辑配置文件

**推荐方式**: 编辑后调用 reload API

```javascript
// 1. 用户在前端编辑配置文件
// 2. 保存文件到 backend/config/constraints.json
// 3. 调用 reload API

async function reloadConfig() {
  const response = await fetch('/api/constraints/reload', {
    method: 'POST'
  });
  
  if (response.ok) {
    const data = await response.json();
    console.log('配置重新加载成功:', data.message);
    // 配置已立即生效
  } else {
    console.error('配置重新加载失败');
  }
}
```

---

### 场景 3: 配置编辑器

**完整示例**:

```javascript
class ConstraintConfigEditor {
  constructor() {
    this.apiBase = '/api/constraints';
  }
  
  // 获取当前配置
  async getConfig() {
    const response = await fetch(this.apiBase);
    const data = await response.json();
    return data.constraints;
  }
  
  // 更新配置（推荐）
  async updateConfig(config) {
    const response = await fetch(this.apiBase, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config)
    });
    
    if (!response.ok) {
      throw new Error('更新配置失败');
    }
    
    return await response.json();
  }
  
  // 保存文件后重新加载
  async reloadFromFile() {
    const response = await fetch(`${this.apiBase}/reload`, {
      method: 'POST'
    });
    
    if (!response.ok) {
      throw new Error('重新加载配置失败');
    }
    
    return await response.json();
  }
  
  // 重置为默认值
  async resetToDefaults() {
    const response = await fetch(`${this.apiBase}/reset`, {
      method: 'POST'
    });
    
    if (!response.ok) {
      throw new Error('重置配置失败');
    }
    
    return await response.json();
  }
}

// 使用示例
const editor = new ConstraintConfigEditor();

// 获取配置
const config = await editor.getConfig();
console.log('当前配置:', config);

// 修改配置
config.retrieval.min_relevant_docs = 3;
await editor.updateConfig(config);

// 或者：编辑文件后重新加载
await editor.reloadFromFile();
```

---

## 配置生效机制

### 单例模式
约束配置使用单例模式，整个应用共享一个配置实例。

```python
# 所有地方获取的都是同一个实例
config1 = get_constraint_config()
config2 = get_constraint_config()
assert config1 is config2  # True
```

### 内存缓存
配置加载后缓存在内存中，避免频繁读取文件。

### 更新机制
1. **API 更新**: 直接修改内存中的配置，然后保存到文件
2. **文件修改**: 需要调用 `reload()` 重新从文件加载到内存

---

## 最佳实践

### ✅ 推荐做法

1. **使用 API 更新配置**
   - 立即生效
   - 自动保存
   - 有错误处理

2. **前端提供配置界面**
   - 用户友好
   - 实时验证
   - 即时生效

3. **定期备份配置**
   ```bash
   cp config/constraints.json config/constraints.json.backup
   ```

4. **使用版本控制**
   ```bash
   git add config/constraints.json
   git commit -m "Update constraints config"
   ```

---

### ❌ 不推荐做法

1. **直接修改文件后不重新加载**
   - 修改不会生效
   - 容易造成混淆

2. **频繁重启服务**
   - 影响用户体验
   - 不必要的开销

3. **不备份配置**
   - 误操作无法恢复
   - 缺少历史记录

---

## 故障排查

### 问题 1: 修改配置文件后不生效

**原因**: 配置缓存在内存中

**解决方案**:
```bash
# 方案 A: 调用 reload API
curl -X POST http://localhost:8000/api/constraints/reload

# 方案 B: 重启服务
systemctl restart backend-service
```

---

### 问题 2: reload API 返回错误

**可能原因**:
1. JSON 格式错误
2. 文件权限问题
3. 文件不存在

**检查步骤**:
```bash
# 1. 验证 JSON 格式
python -m json.tool config/constraints.json

# 2. 检查文件权限
ls -l config/constraints.json

# 3. 查看日志
tail -f logs/app.log | grep constraint
```

---

### 问题 3: 配置更新后部分功能未生效

**可能原因**:
1. 配置项名称错误
2. 配置值类型错误
3. 代码中未使用该配置

**检查步骤**:
```bash
# 1. 验证配置格式
python tests/constraints/check_all_constraints.py

# 2. 查看当前配置
curl http://localhost:8000/api/constraints

# 3. 运行测试
pytest tests/constraints/ -v
```

---

## 监控建议

### 配置变更日志
```python
# 在 constraint_config.py 中
logger.info(f"Config updated: {changed_keys}")
logger.info(f"Config reloaded from file")
```

### 监控指标
- 配置更新次数
- 配置重新加载次数
- 配置更新失败次数

### 告警规则
- 配置重新加载失败 → 发送告警
- 配置频繁变更 → 记录审计日志

---

## 总结

### 配置更新流程

**推荐流程（通过 API）**:
```
前端修改 → API 更新 → 内存更新 → 保存文件 → 立即生效 ✅
```

**备选流程（修改文件）**:
```
前端修改 → 保存文件 → 调用 reload API → 重新加载 → 立即生效 ✅
```

**不推荐流程**:
```
前端修改 → 保存文件 → 重启服务 → 生效 ❌（影响用户）
前端修改 → 保存文件 → 不做任何操作 ❌（不会生效）
```

### 关键要点

1. ✅ **API 更新是首选方式** - 立即生效，无需额外操作
2. ✅ **文件修改后必须 reload** - 否则不会生效
3. ✅ **reload API 是新增功能** - 专门解决文件修改后的生效问题
4. ✅ **单例模式保证一致性** - 所有地方使用同一份配置
5. ✅ **错误处理保证稳定性** - JSON 错误时保持当前配置

---

**文档版本**: 1.0  
**更新日期**: 2024-03-25  
**相关 API**: `/api/constraints/reload`
