/**
 * Global file type color system
 * Provides consistent colors for different file types across the application
 */

export interface FileTypeColor {
  bg: string        // Background color
  text: string      // Text color
  border: string    // Border color
  lightBg: string   // Light background for badges/tags
}

// File type color palette based on Material Design
const fileTypeColors: Record<string, FileTypeColor> = {
  // PDF - Red
  'PDF': {
    bg: '#FFEBEE',
    text: '#D32F2F',
    border: '#EF5350',
    lightBg: '#FFCDD2'
  },
  // Word - Blue
  'DOC': {
    bg: '#E3F2FD',
    text: '#1565C0',
    border: '#42A5F5',
    lightBg: '#BBDEFB'
  },
  'DOCX': {
    bg: '#E3F2FD',
    text: '#1565C0',
    border: '#42A5F5',
    lightBg: '#BBDEFB'
  },
  // Excel - Green
  'XLS': {
    bg: '#E8F5E9',
    text: '#2E7D32',
    border: '#66BB6A',
    lightBg: '#C8E6C9'
  },
  'XLSX': {
    bg: '#E8F5E9',
    text: '#2E7D32',
    border: '#66BB6A',
    lightBg: '#C8E6C9'
  },
  // PowerPoint - Orange
  'PPT': {
    bg: '#FFF3E0',
    text: '#E65100',
    border: '#FF9800',
    lightBg: '#FFE0B2'
  },
  'PPTX': {
    bg: '#FFF3E0',
    text: '#E65100',
    border: '#FF9800',
    lightBg: '#FFE0B2'
  },
  // Text - Gray
  'TXT': {
    bg: '#F5F5F5',
    text: '#616161',
    border: '#9E9E9E',
    lightBg: '#E0E0E0'
  },
  // Markdown - Teal/Green
  'MD': {
    bg: '#E0F2F1',
    text: '#00695C',
    border: '#4DB6AC',
    lightBg: '#B2DFDB'
  },
  // Images - Purple
  'PNG': {
    bg: '#F3E5F5',
    text: '#7B1FA2',
    border: '#AB47BC',
    lightBg: '#E1BEE7'
  },
  'JPG': {
    bg: '#F3E5F5',
    text: '#7B1FA2',
    border: '#AB47BC',
    lightBg: '#E1BEE7'
  },
  'JPEG': {
    bg: '#F3E5F5',
    text: '#7B1FA2',
    border: '#AB47BC',
    lightBg: '#E1BEE7'
  },
  'GIF': {
    bg: '#F3E5F5',
    text: '#7B1FA2',
    border: '#AB47BC',
    lightBg: '#E1BEE7'
  },
  // Archives - Brown
  'ZIP': {
    bg: '#EFEBE9',
    text: '#5D4037',
    border: '#8D6E63',
    lightBg: '#D7CCC8'
  },
  'RAR': {
    bg: '#EFEBE9',
    text: '#5D4037',
    border: '#8D6E63',
    lightBg: '#D7CCC8'
  },
  // Code files - Indigo
  'JS': {
    bg: '#E8EAF6',
    text: '#303F9F',
    border: '#5C6BC0',
    lightBg: '#C5CAE9'
  },
  'TS': {
    bg: '#E8EAF6',
    text: '#303F9F',
    border: '#5C6BC0',
    lightBg: '#C5CAE9'
  },
  'HTML': {
    bg: '#E8EAF6',
    text: '#303F9F',
    border: '#5C6BC0',
    lightBg: '#C5CAE9'
  },
  'CSS': {
    bg: '#E8EAF6',
    text: '#303F9F',
    border: '#5C6BC0',
    lightBg: '#C5CAE9'
  },
  'JSON': {
    bg: '#E8EAF6',
    text: '#303F9F',
    border: '#5C6BC0',
    lightBg: '#C5CAE9'
  },
  'PY': {
    bg: '#E8EAF6',
    text: '#303F9F',
    border: '#5C6BC0',
    lightBg: '#C5CAE9'
  }
}

// Default color for unknown file types
const defaultColor: FileTypeColor = {
  bg: '#F5F5F5',
  text: '#757575',
  border: '#BDBDBD',
  lightBg: '#E0E0E0'
}

/**
 * Get file extension from filename
 */
export function getFileExtension(filename: string): string {
  return filename.split('.').pop()?.toUpperCase() || ''
}

/**
 * Get color scheme for a file type
 */
export function getFileTypeColor(filenameOrExt: string): FileTypeColor {
  const ext = filenameOrExt.includes('.') 
    ? getFileExtension(filenameOrExt) 
    : filenameOrExt.toUpperCase()
  
  return fileTypeColors[ext] || defaultColor
}

/**
 * Get style object for file icon
 */
export function getFileIconStyle(filenameOrExt: string) {
  const color = getFileTypeColor(filenameOrExt)
  return {
    backgroundColor: color.bg,
    color: color.text,
    border: `1px solid ${color.border}`
  }
}

/**
 * Get style object for file badge/tag
 */
export function getFileBadgeStyle(filenameOrExt: string) {
  const color = getFileTypeColor(filenameOrExt)
  return {
    backgroundColor: color.lightBg,
    color: color.text,
    border: `1px solid ${color.border}`
  }
}

/**
 * Get CSS class for file type
 */
export function getFileTypeClass(filename: string): string {
  const ext = getFileExtension(filename).toLowerCase()
  return `file-type-${ext}`
}

// Export all file type colors for reference
export { fileTypeColors, defaultColor }
