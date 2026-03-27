/**
 * 内容安全保护配置
 */

export interface ContentProtectionConfig {
  // 禁用复制功能
  disableCopy: boolean
  // 禁用右键菜单
  disableContextMenu: boolean
  // 禁用键盘快捷键（Ctrl+C）
  disableKeyboardShortcuts: boolean
  // 禁用下载功能
  disableDownload: boolean
  // 禁用文本选择
  disableTextSelection: boolean
  // 禁用代码块复制按钮
  disableCodeCopy: boolean
}

/**
 * 默认内容保护配置
 * 所有保护功能默认启用
 */
export const contentProtection: ContentProtectionConfig = {
  disableCopy: true,
  disableContextMenu: true,
  disableKeyboardShortcuts: true,
  disableDownload: true,
  disableTextSelection: true,
  disableCodeCopy: true
}

/**
 * 开发环境配置（可以放宽限制）
 */
export const devContentProtection: ContentProtectionConfig = {
  disableCopy: false,
  disableContextMenu: false,
  disableKeyboardShortcuts: false,
  disableDownload: false,
  disableTextSelection: false,
  disableCodeCopy: false
}

/**
 * 获取当前环境的内容保护配置
 */
export function getContentProtectionConfig(): ContentProtectionConfig {
  // 可以根据环境变量切换配置
  const isDev = import.meta.env.DEV
  
  // 开发环境可以选择使用宽松配置
  // return isDev ? devContentProtection : contentProtection
  
  // 或者始终使用严格配置
  return contentProtection
}
