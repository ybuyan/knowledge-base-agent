# 流程自动化管理系统设计方案

## 一、产品概述

### 1.1 核心价值
- **自动化流程识别**：从上传的文档中自动识别和提取流程相关信息
- **智能流程管理**：提供流程模板的增删改查功能
- **快捷访问**：通过快捷按钮快速访问常用流程
- **可视化引导**：为用户提供清晰的流程指引和操作步骤

### 1.2 用户场景
1. **HR管理员**：上传员工手册、流程文档，系统自动识别并生成流程模板
2. **普通员工**：通过快捷按钮快速查看请假、报销等流程指引
3. **系统管理员**：管理和维护流程模板，处理重复流程

## 二、系统架构设计

### 2.1 数据模型设计

#### 流程模板（ProcessTemplate）
```python
{
    "id": "uuid",
    "name": "请假申请",  # 流程名称
    "category": "人事管理",  # 流程分类
    "description": "员工请假申请流程",  # 流程描述
    "source_document_id": "doc_uuid",  # 来源文档ID
    "source_document_name": "员工手册.pdf",  # 来源文档名称
    "steps": [  # 流程步骤
        {
            "step_number": 1,
            "title": "填写请假申请",
            "description": "在OA系统中填写请假申请表",
            "action_url": "https://oa.company.com/leave",  # 操作入口
            "action_text": "前往OA系统",
            "required_materials": ["请假申请表", "相关证明材料"],
            "notes": ["请提前3天申请", "需附上相关证明"],
            "duration": "5-10分钟",
            "responsible_role": "申请人"
        },
        {
            "step_number": 2,
            "title": "直属上级审批",
            "description": "等待直属上级审批",
            "action_url": null,
            "action_text": null,
            "required_materials": [],
            "notes": ["审批时间：1-3个工作日"],
            "duration": "1-3个工作日",
            "responsible_role": "直属上级"
        }
    ],
    "triggers": ["请假", "年假", "病假", "事假"],  # 触发关键词
    "tags": ["人事", "请假", "审批"],
    "version": "1.0",
    "status": "active",  # active, draft, archived
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
    "created_by": "admin",
    "usage_count": 0,  # 使用次数
    "last_used_at": null
}
```

#### 流程分类（ProcessCategory）
```python
{
    "id": "uuid",
    "name": "人事管理",
    "description": "人力资源管理相关流程",
    "icon": "👥",
    "sort_order": 1,
    "created_at": "2024-01-01T00:00:00Z"
}
```

### 2.2 功能模块设计

#### 模块1：文档上传与流程识别
**功能描述**：
- 用户上传文档后，系统自动分析文档内容
- 使用LLM识别文档中的流程相关信息
- 自动生成流程模板并保存到数据库

**处理流程**：
1. 文档上传 → 文档解析 → 文本提取
2. 流程识别 → LLM分析 → 提取流程信息
3. 模板生成 → 数据验证 → 保存到数据库
4. 重复检测 → 提醒用户确认

**LLM Prompt设计**：
```
你是一个流程分析专家。请分析以下文档内容，识别其中的流程信息。

要求：
1. 识别文档中的所有流程
2. 为每个流程提取以下信息：
   - 流程名称
   - 流程分类
   - 流程步骤（包括步骤名称、描述、操作入口、所需材料、注意事项）
   - 触发关键词
   - 相关标签

输出格式：
{
  "processes": [
    {
      "name": "流程名称",
      "category": "流程分类",
      "steps": [...],
      "triggers": [...],
      "tags": [...]
    }
  ]
}
```

#### 模块2：流程管理界面
**功能描述**：
- 提供流程模板的增删改查功能
- 支持流程分类管理
- 提供流程预览和测试功能

**界面设计**：
1. **流程列表页**：
   - 按分类展示所有流程
   - 支持搜索和筛选
   - 显示流程状态、使用次数等信息

2. **流程编辑页**：
   - 流程基本信息编辑
   - 步骤编辑器（支持拖拽排序）
   - 触发关键词管理
   - 预览功能

3. **分类管理页**：
   - 分类的增删改查
   - 分类排序
   - 图标选择

#### 模块3：快捷按钮交互
**功能描述**：
- 点击快捷按钮显示流程分类
- 悬停分类显示该分类下的所有流程
- 点击流程显示详情弹窗

**交互流程**：
1. 用户点击快捷按钮 ⚡
2. 展开显示流程分类列表（如：人事管理、财务管理、行政管理）
3. 用户悬停某个分类
4. 左侧展开显示该分类下的所有流程
5. 用户点击某个流程
6. 弹出流程详情弹窗

**弹窗设计**：
```
┌─────────────────────────────────────────┐
│  请假申请流程                            │
│  ─────────────────────────────────────  │
│  📋 流程概述                             │
│  员工请假申请流程，包括填写申请、审批等环节 │
│                                          │
│  📝 流程步骤                             │
│  ┌────────────────────────────────────┐ │
│  │ 步骤1：填写请假申请                 │ │
│  │ 描述：在OA系统中填写请假申请表      │ │
│  │ 🔗 前往OA系统                       │ │
│  │ ⏱️ 预计耗时：5-10分钟              │ │
│  │ 📌 注意事项：                       │ │
│  │   • 请提前3天申请                   │ │
│  │   • 需附上相关证明                   │ │
│  └────────────────────────────────────┘ │
│  ┌────────────────────────────────────┐ │
│  │ 步骤2：直属上级审批                 │ │
│  │ ...                                 │ │
│  └────────────────────────────────────┘ │
│                                          │
│  [开始流程] [收藏流程] [分享流程]        │
└─────────────────────────────────────────┘
```

#### 模块4：重复流程检测与提醒
**功能描述**：
- 上传文档时检测是否存在相似流程
- 提供合并、覆盖、保留选项
- 记录流程版本历史

**检测逻辑**：
1. 使用流程名称、触发关键词、标签进行相似度匹配
2. 相似度 > 80% 时提醒用户
3. 提供三种处理方式：
   - 合并：将新流程步骤合并到现有流程
   - 覆盖：使用新流程替换现有流程
   - 保留：保留现有流程，不导入新流程

## 三、技术实现方案

### 3.1 后端实现

#### API接口设计
```
POST /api/process-templates
  - 创建流程模板（手动创建或从文档导入）

GET /api/process-templates
  - 获取流程模板列表（支持分页、筛选）

GET /api/process-templates/{id}
  - 获取单个流程模板详情

PUT /api/process-templates/{id}
  - 更新流程模板

DELETE /api/process-templates/{id}
  - 删除流程模板

POST /api/process-templates/extract-from-document
  - 从文档中提取流程

GET /api/process-categories
  - 获取流程分类列表

POST /api/process-categories
  - 创建流程分类

GET /api/process-templates/quick-prompts
  - 获取快捷提示词（用于快捷按钮）
```

#### 数据库集合
- `process_templates` - 流程模板
- `process_categories` - 流程分类
- `process_usage_logs` - 流程使用日志

#### 处理器设计
```python
class ProcessExtractorProcessor(BaseProcessor):
    """流程提取处理器"""
    
    async def process(self, input_data: dict) -> dict:
        # 1. 获取文档内容
        document_content = input_data.get("content")
        
        # 2. 使用LLM提取流程
        processes = await self._extract_processes(document_content)
        
        # 3. 检测重复流程
        duplicates = await self._check_duplicates(processes)
        
        # 4. 保存流程模板
        saved_processes = await self._save_processes(processes, duplicates)
        
        return {
            "processes": saved_processes,
            "duplicates": duplicates
        }
```

### 3.2 前端实现

#### 组件设计
```
components/
├── Process/
│   ├── ProcessList.vue          # 流程列表
│   ├── ProcessEditor.vue        # 流程编辑器
│   ├── ProcessDetail.vue        # 流程详情弹窗
│   ├── ProcessStepEditor.vue    # 步骤编辑器
│   └── ProcessCategoryManager.vue  # 分类管理
├── QuickPromptButton/
│   └── index.vue                # 快捷按钮（已存在，需扩展）
```

#### 状态管理
```typescript
// stores/process.ts
export const useProcessStore = defineStore('process', {
  state: () => ({
    categories: [],
    processes: [],
    currentProcess: null,
    loading: false
  }),
  
  actions: {
    async fetchCategories() {},
    async fetchProcesses(category?: string) {},
    async createProcess(process: ProcessTemplate) {},
    async updateProcess(id: string, process: ProcessTemplate) {},
    async deleteProcess(id: string) {},
    async extractFromDocument(documentId: string) {}
  }
})
```

## 四、实施计划

### 阶段一：基础架构（1-2天）
- [ ] 设计并创建数据库模型
- [ ] 实现基础的API接口（CRUD）
- [ ] 创建流程分类管理功能

### 阶段二：流程提取（2-3天）
- [ ] 实现文档内容提取功能
- [ ] 设计并实现LLM流程识别逻辑
- [ ] 实现流程模板生成功能
- [ ] 实现重复流程检测

### 阶段三：前端界面（2-3天）
- [ ] 实现流程列表页面
- [ ] 实现流程编辑器
- [ ] 扩展快捷按钮功能
- [ ] 实现流程详情弹窗

### 阶段四：集成与优化（1-2天）
- [ ] 集成文档上传与流程提取
- [ ] 实现重复流程提醒
- [ ] 优化用户体验
- [ ] 测试与修复bug

## 五、关键决策点

### 5.1 流程识别准确性
**问题**：LLM识别的流程可能不准确或不完整
**解决方案**：
- 提供人工审核和编辑功能
- 使用多轮对话优化识别结果
- 建立流程模板库，提高识别准确率

### 5.2 重复流程处理
**问题**：如何判断两个流程是否重复
**解决方案**：
- 使用多维度相似度计算（名称、关键词、步骤）
- 提供人工确认机制
- 记录版本历史，支持回滚

### 5.3 流程入口管理
**问题**：流程的操作入口URL可能变化
**解决方案**：
- 提供URL模板功能，支持变量替换
- 支持相对路径和绝对路径
- 提供URL有效性检测

### 5.4 权限控制
**问题**：不同用户对流程的访问权限不同
**解决方案**：
- 基于角色的权限控制（RBAC）
- 流程模板支持可见性设置（公开/部门/个人）
- 敏感流程需要特定权限才能查看

## 六、扩展功能（后续迭代）

### 6.1 流程执行跟踪
- 记录用户的流程执行进度
- 提供流程完成提醒
- 统计流程执行效率

### 6.2 流程优化建议
- 基于使用数据提供流程优化建议
- 识别流程瓶颈
- 提供流程改进方案

### 6.3 流程模板市场
- 支持流程模板导入导出
- 建立流程模板共享平台
- 提供行业标准流程模板

### 6.4 智能推荐
- 根据用户角色推荐相关流程
- 根据使用频率推荐常用流程
- 根据上下文推荐相关流程

## 七、风险与挑战

### 7.1 技术风险
- LLM识别准确率不稳定
- 文档格式多样性导致解析困难
- 大量流程数据的性能问题

### 7.2 产品风险
- 用户可能不愿意手动编辑流程
- 流程分类可能不够清晰
- 快捷按钮的使用频率可能不高

### 7.3 解决方案
- 提供多种流程创建方式（自动、半自动、手动）
- 建立清晰的分类标准和标签体系
- 通过数据分析优化快捷按钮的展示逻辑

## 八、成功指标

### 8.1 使用指标
- 流程模板创建数量
- 快捷按钮点击率
- 流程详情查看次数
- 流程完成率

### 8.2 质量指标
- 流程识别准确率
- 用户满意度评分
- 流程模板完善度
- 重复流程处理效率
