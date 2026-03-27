import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'

const md: MarkdownIt = new MarkdownIt({
  html: false,
  xhtmlOut: false,
  breaks: true,
  linkify: true,
  typographer: true,
  highlight: function (str: string, lang: string): string {
    if (lang && hljs.getLanguage(lang)) {
      try {
        // 移除复制按钮
        return `<pre class="code-block"><code class="hljs language-${lang}">${hljs.highlight(str, { language: lang, ignoreIllegals: true }).value}</code></pre>`
      } catch {
        return ''
      }
    }
    // 移除复制按钮
    return `<pre class="code-block"><code class="hljs">${md.utils.escapeHtml(str)}</code></pre>`
  }
})

// 自定义表格渲染 - 添加 table-wrapper 容器以支持横向滚动
md.renderer.rules.table_open = function() {
  return '<div class="table-wrapper"><table>'
}

md.renderer.rules.table_close = function() {
  return '</table></div>'
}

md.renderer.rules.thead_open = function() {
  return '<thead>'
}

md.renderer.rules.thead_close = function() {
  return '</thead>'
}

md.renderer.rules.tbody_open = function() {
  return '<tbody>'
}

md.renderer.rules.tbody_close = function() {
  return '</tbody>'
}

md.renderer.rules.tr_open = function() {
  return '<tr>'
}

md.renderer.rules.tr_close = function() {
  return '</tr>'
}

md.renderer.rules.th_open = function() {
  return '<th>'
}

md.renderer.rules.th_close = function() {
  return '</th>'
}

md.renderer.rules.td_open = function() {
  return '<td>'
}

md.renderer.rules.td_close = function() {
  return '</td>'
}

// 自定义链接渲染 - 移除 download 属性，禁用下载
md.renderer.rules.link_open = function(tokens, idx) {
  const token = tokens[idx]
  const hrefIndex = token.attrIndex('href')
  
  if (hrefIndex >= 0) {
    const href = token.attrs![hrefIndex][1]
    // 移除 download 属性，添加 target="_blank" 和 rel="noopener noreferrer"
    return `<a href="${href}" target="_blank" rel="noopener noreferrer" onclick="return false;">`
  }
  
  return '<a>'
}

md.renderer.rules.link_close = function() {
  return '</a>'
}

export function renderMarkdown(content: string): string {
  return md.render(content)
}

export function escapeHtml(text: string): string {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}
