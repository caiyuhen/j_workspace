import os
import re

def clean_git_conflicts(directory):
    count = 0
    # Match <<<<<<< HEAD\n
    head_pattern = re.compile(r'^<<<<<<< HEAD\r?\n?', re.MULTILINE)
    # Match ======= to >>>>>>> <hash>\n
    conflict_pattern = re.compile(r'^=======\r?\n?.*?^>>>>>>> [a-f0-9]+\r?\n?', re.MULTILINE | re.DOTALL)
    
    for root, dirs, files in os.walk(directory):
        if '.git' in root or '__pycache__' in root or 'node_modules' in root:
            continue
        for file in files:
            if file.endswith(('.py', '.js', '.html', '.css', '.bat', '.ps1', '.sh', '.yml', '.md', '.txt')):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    if '<<<<<<< HEAD' in content and '=======' in content:
                        new_content = head_pattern.sub('', content)
                        new_content = conflict_pattern.sub('', new_content)
                        
                        if new_content != content:
                            with open(path, 'w', encoding='utf-8') as f:
                                f.write(new_content)
                            print(f"Fixed {path}")
                            count += 1
                except Exception as e:
                    pass
    print(f"Total files fixed: {count}")

if __name__ == "__main__":
    clean_git_conflicts(r'D:\workspace\CTMS_Pro')