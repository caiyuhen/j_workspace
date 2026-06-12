import re
with open('D:/workspace/Hermes_workspace/doc/数据要素/申报书填充内容_part2a.md', 'r', encoding='utf-8') as f:
    text = f.read()
chinese = re.findall(r'[\u4e00-\u9fff]', text)
print('Chinese chars:', len(chinese))
print('Total chars:', len(text))