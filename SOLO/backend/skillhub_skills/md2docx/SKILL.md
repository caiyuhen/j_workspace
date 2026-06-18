---
name: "md2docx"
description: "Markdown 与 Word 双向转换，支持合并单元格（rowspan/colspan）、Mermaid 图表渲染、代码高亮、中文排版优化"
---

# md2docx — Markdown ↔ Word 双向转换

支持 `.md` 和 `.docx` 之间的双向转换，自动识别文件类型。

## 用法

```bash
# Markdown → Word
python md2docx.py input.md output.docx

# Word → Markdown
python md2docx.py input.docx output.md
```

脚本根据文件扩展名自动判断转换方向。

## 功能

### MD → DOCX
- **中文排版**：全文微软雅黑，正文 10.5pt，表格 9pt
- **动态标题字号**：自动检测标题层级，末级 12.5pt，每升一级 +2pt
- **Mermaid 图表**：自动渲染为 PNG 嵌入文档，动态检测系统 Chrome/Edge
- **代码块**：灰色背景 + 四边框 + Consolas 等宽字体
- **行内格式**：`**粗体**`、`*斜体*`、`` `代码` ``、`[链接](url)`
- **表格**：表头灰底，支持 HTML 转义
- **HTML 表格**：支持合并单元格（rowspan/colspan），虚拟网格算法还原
- **引用块 / 分割线 / 图片 / HTML 块**

### DOCX → MD
- **完整结构提取**：标题、段落、列表、表格全部保留
- **合并单元格**：HTML `<table>` 直接嵌入 MD（绕过 MD 不支持合并的限制）
- **图片提取**：内联图片转为 MD 图片引用
- **Mermaid 图表**：代码块原样保留

### 合并单元格方案

Markdown 表格语法不支持 `rowspan` / `colspan`，本工具采用 **HTML 嵌入方案**：

```
DOCX → MD：mammoth 转 HTML → HTML <table> 嵌入 .md
MD → DOCX：解析 HTML <table> → 虚拟网格算法 → cell.merge() 还原
```

MD 文件中嵌入的 HTML 表格能被主流 Markdown 渲染器正确显示，反向还原时也能精确恢复合并结构。

## 依赖

### Python 3.8+

```bash
pip install python-docx pygments pillow mammoth beautifulsoup4
```

| 包 | 必须 | 用途 |
|---|---|---|
| `python-docx` | 是 | 生成/解析 Word 文档 |
| `mammoth` | 是 | DOCX → HTML 转换（保留合并单元格） |
| `beautifulsoup4` | 是 | HTML 表格解析 |
| `pygments` | 否 | 代码块语法高亮（缺失时回退纯文本） |
| `pillow` | 否 | Mermaid 图片自动缩放（缺失时用默认宽度） |

### Node.js（Mermaid 渲染，可选）

如需 MD→DOCX 时渲染 Mermaid 图表：

```bash
cd <skill目录>
npm install
```

安装后 `node_modules/.bin/mmdc.cmd` 会被自动调用。

**浏览器配置**：脚本会自动检测系统已安装的 Chrome / Edge / Chromium，无需手动下载。若系统无浏览器，Mermaid 以文字占位符代替。

若不需要 Mermaid 支持，可跳过 `npm install`。

## 个性化配置

在 `md2docx.py` 顶部修改常量：

```python
FONT_NAME         = '微软雅黑'  # 全文字体
BODY_FONT_SIZE    = 10.5        # 正文字号
TABLE_FONT_SIZE   = 9           # 表格字号
MIN_HEADING_SIZE  = 12.5        # 最末级标题字号
HEADING_SIZE_STEP = 2           # 每升一级递增字号
```

## 文件结构

```
md2docx/
├── md2docx.py        # 主转换脚本（双向）
├── code_block.py     # 代码块样式渲染
├── SKILL.md          # Skill 描述（本文件）
├── README.md         # 详细文档
└── package.json      # Node.js 依赖（Mermaid CLI）
```
