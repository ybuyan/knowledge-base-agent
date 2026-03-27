/**
 * 全局常量配置
 * 集中管理前端所有重复使用的常量
 */

// 文档处理相关常量
export const DOCUMENT_CONSTANTS = {
  // 支持的文档格式
  SUPPORTED_FORMATS: [
    'pdf', 'docx', 'txt', 
    'xlsx', 'pptx', 
    'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'
  ],
  
  // 支持的文件扩展名（用于上传组件 accept 属性）
  ACCEPT_TYPES: '.pdf,.docx,.txt,.xlsx,.pptx,.png,.jpg,.jpeg,.gif,.bmp,.webp',
  
  // 文件类型映射
  FILE_TYPE_MAP: {
    pdf: 'PDF文档',
    docx: 'Word文档',
    txt: '文本文件',
    xlsx: 'Excel表格',
    pptx: 'PowerPoint',
    png: 'PNG图片',
    jpg: 'JPEG图片',
    jpeg: 'JPEG图片',
    gif: 'GIF图片',
    bmp: 'BMP图片',
    webp: 'WebP图片'
  } as const,
  
  // 最大文件大小 (MB)
  MAX_FILE_SIZE_MB: 50,
  
  // 分块配置
  CHUNK_SIZE: 500,
  CHUNK_OVERLAP: 50
} as const

// API 相关常量
export const API_CONSTANTS = {
  // 默认超时时间 (毫秒)
  DEFAULT_TIMEOUT: 30000,
  
  // 流式响应超时
  STREAM_TIMEOUT: 60000,
  
  // 重试次数
  MAX_RETRIES: 3,
  
  // 重试延迟 (毫秒)
  RETRY_DELAY: 1000
} as const

// 消息相关常量
export const MESSAGE_CONSTANTS = {
  // 最大显示的消息长度
  MAX_DISPLAY_LENGTH: 500,
  
  // 消息角色
  ROLES: {
    USER: 'user',
    ASSISTANT: 'assistant',
    SYSTEM: 'system'
  } as const
} as const

// 会话相关常量
export const SESSION_CONSTANTS = {
  // 默认用户ID
  DEFAULT_USER_ID: 'default_user',
  
  // 会话标题最大长度
  MAX_TITLE_LENGTH: 100,
  
  // 每页消息数量
  MESSAGES_PER_PAGE: 50
} as const
