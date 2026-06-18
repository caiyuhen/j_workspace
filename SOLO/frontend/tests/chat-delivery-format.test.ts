import { describe, expect, it } from 'vitest'
import fs from 'node:fs'
import path from 'node:path'

const chatSource = fs.readFileSync(path.resolve(__dirname, '../src/pages/Chat.tsx'), 'utf-8')

describe('Chat 交付格式', () => {
  it('不再渲染交付文件格式选择框', () => {
    expect(chatSource).not.toContain('setDeliverableFormat')
    expect(chatSource).not.toContain("label: 'Word'")
    expect(chatSource).not.toContain("label: 'Excel'")
    expect(chatSource).not.toContain("label: 'PPT'")
    expect(chatSource).not.toContain("label: 'Markdown'")
  })

  it('任务执行固定使用 Word/docx 交付格式', () => {
    expect(chatSource).toContain("deliverable_format: 'docx'")
  })
})
