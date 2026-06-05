# 简化版增强脚本
try:
    with open(r'D:\doc\数据培训 PPT.html', 'r', encoding='utf-8') as f:
        content = f.read()
    print(f"成功读取文件，长度：{len(content)} 字节")
except Exception as e:
    print(f"读取失败：{e}")
    # 列出当前目录文件
    import os
    files = [f for f in os.listdir(r'D:\doc') if '培训' in f]
    print(f"找到培训文件：{files}")
    exit(1)

# 检查关键标记
if 'SLIDE 18' in content:
    print("找到 SLIDE 18 标记")
else:
    print("未找到 SLIDE 18 标记")

print("准备增强 PPT...")
