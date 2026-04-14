/**
 * 全局常量配置
 * 集中管理前端所有重复使用的常量
 */

// 文档处理相关常量
export const DOCUMENT_CONSTANTS = {
  // 支持的文档格式
  SUPPORTED_FORMATS: [
    "pdf",
    "docx",
    "txt",
    "xlsx",
    "pptx",
    "png",
    "jpg",
    "jpeg",
    "gif",
    "bmp",
    "webp",
  ],

  // 支持的文件扩展名（用于上传组件 accept 属性）
  ACCEPT_TYPES: ".pdf,.docx,.txt,.xlsx,.pptx,.png,.jpg,.jpeg,.gif,.bmp,.webp",

  // 文件类型映射
  FILE_TYPE_MAP: {
    pdf: "PDF文档",
    docx: "Word文档",
    txt: "文本文件",
    xlsx: "Excel表格",
    pptx: "PowerPoint",
    png: "PNG图片",
    jpg: "JPEG图片",
    jpeg: "JPEG图片",
    gif: "GIF图片",
    bmp: "BMP图片",
    webp: "WebP图片",
  } as const,

  // 最大文件大小 (MB)
  MAX_FILE_SIZE_MB: 50,

  // 分块配置
  CHUNK_SIZE: 500,
  CHUNK_OVERLAP: 50,
} as const;
