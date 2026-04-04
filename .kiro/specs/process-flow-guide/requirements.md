# 需求文档 - 文档解析流程指引功能

## 简介

基于现有 QuickPromptButton 组件扩展，实现"文档上传 → 自动解析流程知识 → 生成快捷指引按钮 → 弹窗展示步骤"的完整链路。用户上传文档后，系统自动识别文档中的流程类知识并提取步骤，生成可管理的流程指引模板，通过快捷按钮入口展示给用户。现有流程指引功能（GuideAgent）保持不变。

## 术语表

- **Flow_Guide**: 流程指引模板，从文档中解析出的一个完整流程，包含名称、分类、步骤列表
- **Flow_Step**: 流程步骤，流程指引中的单个操作步骤，包含序号、标题、说明
- **Quick_Button**: 快捷指引按钮，即现有 QuickPromptButton 组件，展示流程分类入口
- **Guide_Modal**: 流程指引弹窗，用户点击快捷按钮后展示的步骤详情弹窗
- **Document_Parser**: 文档解析器，负责从上传文档中提取流程类知识
- **Flow_Manager**: 流程管理页面，供管理员对流程指引模板进行增删改查
- **Duplicate_Confirm**: 重复确认，当解析到已存在流程时弹出的二次确认对话框

## 需求

### 需求 1: 文档上传时自动解析流程知识

**用户故事:** 作为管理员，我希望上传文档后系统能自动识别并提取其中的流程类知识，这样我就不需要手动录入流程步骤。

#### 验收标准

1. WHEN Document is uploaded and indexed successfully, THE Document_Parser SHALL analyze the document content for flow-type knowledge
2. WHEN Document_Parser identifies flow content, THE System SHALL extract flow name, category, and ordered steps
3. WHEN Document_Parser extracts a Flow_Guide, THE System SHALL save it to the database with status "active"
4. WHEN Document_Parser finds a Flow_Guide with the same name as an existing one, THE System SHALL trigger Duplicate_Confirm instead of auto-saving
5. WHEN Document_Parser finds no flow content in a document, THE System SHALL skip flow extraction silently without error
6. THE Document_Parser SHALL extract at minimum: flow name, flow category, and at least 2 ordered steps per flow
7. WHEN multiple flows are detected in one document, THE System SHALL extract all of them

### 需求 2: 重复流程二次确认

**用户故事:** 作为管理员，我希望当上传的文档解析到已存在的流程时，系统提示我确认，这样我就能决定是覆盖还是保留原有流程。

#### 验收标准

1. WHEN Document_Parser detects a flow with the same name as an existing Flow_Guide, THE System SHALL display Duplicate_Confirm dialog
2. THE Duplicate_Confirm dialog SHALL show the existing flow's name, category, step count, and last updated time
3. THE Duplicate_Confirm dialog SHALL show the newly parsed flow's name, category, and step count
4. WHEN User selects "覆盖更新", THE System SHALL replace the existing Flow_Guide with the newly parsed one
5. WHEN User selects "保留原有", THE System SHALL discard the newly parsed flow and keep the existing one
6. WHEN User selects "另存为新流程", THE System SHALL save the new flow with a modified name (appending document name or timestamp)
7. WHEN multiple duplicate flows are detected, THE System SHALL show Duplicate_Confirm for each one sequentially

### 需求 3: 快捷指引按钮展示流程分类

**用户故事:** 作为最终用户，我希望通过现有的快捷按钮看到可用的流程指引分类，这样我就能快速找到需要的流程。

#### 验收标准

1. WHEN QuickPromptButton component mounts, THE System SHALL load all active Flow_Guides grouped by category
2. THE Quick_Button SHALL display each category as a menu item in the expanded state
3. WHEN User hovers over a category, THE System SHALL display all Flow_Guides in that category as a list
4. WHEN User clicks a Flow_Guide item, THE System SHALL open Guide_Modal with that flow's steps
5. WHEN no active Flow_Guides exist, THE Quick_Button SHALL hide or show an empty state
6. THE Quick_Button SHALL reflect real-time changes when Flow_Guides are added or disabled

### 需求 4: 流程指引弹窗展示步骤

**用户故事:** 作为最终用户，我希望点击流程指引后看到清晰的步骤说明弹窗，这样我就能按步骤完成操作。

#### 验收标准

1. WHEN User clicks a Flow_Guide item, THE Guide_Modal SHALL open displaying the flow name and all steps
2. THE Guide_Modal SHALL display each Flow_Step with sequence number, title, and description
3. THE Guide_Modal SHALL support scrolling when steps exceed the visible area
4. WHEN User closes Guide_Modal, THE System SHALL return to the normal chat interface without side effects
5. THE Guide_Modal SHALL be closable via close button and clicking outside the modal
6. THE Guide_Modal SHALL display the source document name and last updated time

### 需求 5: 流程指引模板管理

**用户故事:** 作为管理员，我希望能在管理页面对流程指引模板进行增删改查，这样我就能维护准确的流程内容。

#### 验收标准

1. THE Flow_Manager SHALL display all Flow_Guides in a list with name, category, step count, status, and last updated time
2. THE Flow_Manager SHALL support search by flow name and filter by category and status
3. WHEN Admin clicks "新增", THE Flow_Manager SHALL open a form to manually create a Flow_Guide with name, category, and steps
4. WHEN Admin clicks "编辑", THE Flow_Manager SHALL open the Flow_Guide for editing with all existing data pre-filled
5. WHEN Admin saves a Flow_Guide, THE System SHALL validate that name is not empty and at least one step exists
6. WHEN Admin clicks "删除", THE Flow_Manager SHALL show a confirmation dialog before deleting
7. THE Flow_Manager SHALL support enabling/disabling a Flow_Guide without deleting it
8. WHEN a Flow_Guide is disabled, THE Quick_Button SHALL not display it to end users
9. THE Flow_Manager SHALL support reordering steps within a Flow_Guide via drag-and-drop or up/down buttons

### 需求 6: 流程指引数据持久化

**用户故事:** 作为系统，我需要将流程指引模板持久化存储，这样数据在服务重启后不会丢失。

#### 验收标准

1. THE System SHALL store all Flow_Guides in MongoDB with fields: id, name, category, steps, status, source_document, created_at, updated_at
2. THE System SHALL store each Flow_Step with fields: sequence, title, description
3. WHEN a Flow_Guide is updated, THE System SHALL update the updated_at timestamp
4. THE System SHALL support querying Flow_Guides by status, category, and name
5. THE System SHALL maintain referential integrity between Flow_Guide and its source document

## 正确性属性

### 不变性属性

1. **步骤序号连续性**: FOR ALL Flow_Guides, steps SHALL have continuous sequence numbers starting from 1
2. **流程名称唯一性**: FOR ALL active Flow_Guides, name SHALL be unique within the same category
3. **状态一致性**: FOR ALL Flow_Guides, status SHALL be either "active" or "disabled"

### 往返属性

1. **解析一致性**: FOR ALL documents, parse(document) followed by serialize(flow) followed by parse(serialized) SHALL produce equivalent Flow_Guide
2. **编辑往返**: WHEN Admin edits and saves a Flow_Guide without changes, THE resulting Flow_Guide SHALL be identical to the original

### 幂等性属性

1. **重复加载**: WHEN Quick_Button loads Flow_Guides multiple times, THE displayed categories SHALL remain consistent
2. **重复禁用**: WHEN a Flow_Guide is disabled multiple times, THE status SHALL remain "disabled" without error
