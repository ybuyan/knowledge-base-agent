<script setup lang="ts">
import { ref } from 'vue'
import { getContentProtectionConfig } from '@/config/security'

const config = getContentProtectionConfig()

const testResults = ref({
  textSelection: false,
  contextMenu: false,
  keyboardCopy: false,
  codeBlockCopy: false,
  linkDownload: false
})

const testContent = `
# 测试内容保护功能

这是一段测试文本，用于验证内容保护功能是否正常工作。

## 代码块测试

\`\`\`javascript
function test() {
  console.log('这段代码应该无法复制')
}
\`\`\`

## 链接测试

[测试下载链接](https://example.com/file.pdf)

## 表格测试

| 列1 | 列2 | 列3 |
|-----|-----|-----|
| 数据1 | 数据2 | 数据3 |
`

const handleContextMenu = (e: MouseEvent) => {
  if (config.disableContextMenu) {
    e.preventDefault()
    testResults.value.contextMenu = true
    setTimeout(() => {
      testResults.value.contextMenu = false
    }, 2000)
  }
}
</script>

<template>
  <div class="test-page">
    <div class="test-header">
      <h1>内容保护功能测试</h1>
      <p>测试各项内容保护功能是否正常工作</p>
    </div>

    <div class="config-section">
      <h2>当前配置</h2>
      <div class="config-list">
        <div class="config-item">
          <span>禁用复制:</span>
          <el-tag :type="config.disableCopy ? 'success' : 'info'">
            {{ config.disableCopy ? '已启用' : '未启用' }}
          </el-tag>
        </div>
        <div class="config-item">
          <span>禁用右键菜单:</span>
          <el-tag :type="config.disableContextMenu ? 'success' : 'info'">
            {{ config.disableContextMenu ? '已启用' : '未启用' }}
          </el-tag>
        </div>
        <div class="config-item">
          <span>禁用键盘快捷键:</span>
          <el-tag :type="config.disableKeyboardShortcuts ? 'success' : 'info'">
            {{ config.disableKeyboardShortcuts ? '已启用' : '未启用' }}
          </el-tag>
        </div>
        <div class="config-item">
          <span>禁用文本选择:</span>
          <el-tag :type="config.disableTextSelection ? 'success' : 'info'">
            {{ config.disableTextSelection ? '已启用' : '未启用' }}
          </el-tag>
        </div>
        <div class="config-item">
          <span>禁用代码块复制:</span>
          <el-tag :type="config.disableCodeCopy ? 'success' : 'info'">
            {{ config.disableCodeCopy ? '已启用' : '未启用' }}
          </el-tag>
        </div>
      </div>
    </div>

    <div class="test-section">
      <h2>测试区域</h2>
      <div 
        class="protected-content"
        :class="{ 'no-select': config.disableTextSelection }"
        @contextmenu="handleContextMenu"
      >
        <div class="markdown-body" v-html="testContent"></div>
      </div>
    </div>

    <div class="test-results">
      <h2>测试结果</h2>
      <div class="result-list">
        <div class="result-item">
          <span>右键菜单拦截:</span>
          <el-tag :type="testResults.contextMenu ? 'success' : 'info'">
            {{ testResults.contextMenu ? '已拦截' : '等待测试' }}
          </el-tag>
        </div>
      </div>
    </div>

    <div class="test-instructions">
      <h2>测试说明</h2>
      <ol>
        <li>尝试选择上方测试区域的文本（应该无法选择）</li>
        <li>尝试右键点击测试区域（应该无法弹出菜单）</li>
        <li>尝试使用 Ctrl+C 复制内容（应该无法复制）</li>
        <li>检查代码块是否有复制按钮（应该没有）</li>
        <li>尝试点击链接下载（应该无法下载）</li>
      </ol>
    </div>
  </div>
</template>

<style scoped>
.test-page {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.test-header {
  margin-bottom: 32px;
}

.test-header h1 {
  font-size: 28px;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.test-header p {
  color: var(--text-secondary);
}

.config-section,
.test-section,
.test-results,
.test-instructions {
  background: var(--bg-white);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 24px;
  margin-bottom: 24px;
}

.config-section h2,
.test-section h2,
.test-results h2,
.test-instructions h2 {
  font-size: 18px;
  color: var(--text-primary);
  margin-bottom: 16px;
}

.config-list,
.result-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.config-item,
.result-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: var(--bg-gray);
  border-radius: var(--radius-md);
}

.protected-content {
  padding: 24px;
  background: var(--bg-gray);
  border-radius: var(--radius-md);
  min-height: 300px;
}

.protected-content.no-select {
  user-select: none;
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
}

.test-instructions ol {
  padding-left: 24px;
}

.test-instructions li {
  margin-bottom: 8px;
  color: var(--text-secondary);
  line-height: 1.6;
}
</style>
