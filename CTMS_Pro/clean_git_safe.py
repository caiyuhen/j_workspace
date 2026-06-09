import os

def clean_git_markers(directory):
    count = 0
    for root, dirs, files in os.walk(directory):
        if '.git' in root or '__pycache__' in root or 'node_modules' in root:
            continue
        for file in files:
            if file.endswith(('.py', '.js', '.html', '.css', '.bat', '.ps1', '.sh', '.yml', '.md', '.txt')):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    new_lines = []
                    for line in lines:
                        if line.startswith('<<<<<<< HEAD'):
                            continue
                        if line.startswith('======='):
                            continue
                        if line.startswith('>>>>>>> '):
                            continue
                        new_lines.append(line)
                        
                    if len(new_lines) != len(lines):
                        with open(path, 'w', encoding='utf-8') as f:
                            f.writelines(new_lines)
                        print(f"Fixed {path}")
                        count += 1
                except Exception as e:
                    pass
    print(f"Total files fixed: {count}")

if __name__ == "__main__":
    clean_git_markers(r'D:\workspace\CTMS_Pro')