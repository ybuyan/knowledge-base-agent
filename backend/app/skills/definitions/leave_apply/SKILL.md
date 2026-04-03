---
name: leave_apply
display_name: 请假申请
description: 引导员工完成请假申请，收集假期类型、日期、原因并提交
version: "1.0"
enabled: true
skill_type: process
pipeline:
  - step: execute_process
    processor: ProcessExecutor
    params: {}
output:
  return:
    - answer
    - ui_components
    - process_state
nodes:
  - id: step_fetch_user
    title: 获取用户信息
    type: fetch_user_info
    tool: fetch_user_info
    content: 正在获取您的账户信息…
    params:
      fields:
        - username
        - display_name
        - department

  - id: step_select_type
    title: 选择假期类型
    type: info_collect
    tool: info_collect
    content: 请选择您要申请的假期类型。
    params:
      fields:
        - key: leave_type
          label: 假期类型
          type: select
          required: true
          options:
            - 年假
            - 病假
            - 事假
            - 婚假
            - 产假
            - 陪产假

  - id: step_fill_dates
    title: 填写请假日期
    type: info_collect
    tool: info_collect
    content: 请填写请假的开始日期和结束日期。
    params:
      fields:
        - key: start_date
          label: 开始日期
          type: date
          required: true
        - key: end_date
          label: 结束日期
          type: date
          required: true

  - id: step_balance_check
    title: 校验假期余额
    type: balance_check
    tool: leave_balance_check
    content: 正在校验您的假期余额，请稍候…
    params: {}

  - id: step_fill_reason
    title: 填写请假原因
    type: info_collect
    tool: info_collect
    content: 请简要说明请假原因（选填）。
    params:
      fields:
        - key: reason
          label: 请假原因
          type: text
          required: false

  - id: step_submit
    title: 提交申请
    type: process_submit
    tool: process_submit
    content: 确认信息无误后提交请假申请。
    params: {}
---

# 请假申请流程

本流程引导员工完成请假申请，共 6 个步骤：

1. 自动获取账户信息（无需手动填写）
2. 选择假期类型（年假/病假/事假等）
3. 填写请假日期（开始日期 ~ 结束日期）
4. 自动校验假期余额
5. 填写请假原因（选填）
6. 确认并提交申请

## 行为规则

- 假期类型和日期为必填，原因为选填
- 提交后返回申请单号，预计 1-3 个工作日审批
- 用户可随时取消或重新开始流程
- 24 小时内可恢复未完成的流程
