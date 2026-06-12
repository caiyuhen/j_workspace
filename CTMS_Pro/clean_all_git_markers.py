import os
import re

pattern_head = re.compile(r'^<<<<<<< HEAD\n?', re.MULTILINE)
pattern_sep = re.compile(r'^=======\n?', re.MULTILINE)
pattern_tail = re.compile(r'^>>>>>>> [a-f0-9]+\n?', re.MULTILINE)

count = 0
for root, dirs, files in os.walk('/home/user/CTMS_Pro'):
    if '.git' in root or '__pycache__' in root or 'node_modules' in root or 'pgdata' in root or '.venv' in root:
        continue
    for file in files:
        if file.endswith(('.py', '.sql', '.conf', '.yml', '.yaml', '.sh', '.txt', 'Dockerfile', '.md', '.html', '.bat', '.ps1')):
            path = os.path.join(root, file)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check if it has git markers before doing expensive regex
                if '<<<<<<< HEAD' in content:
                    # Actually, a simpler and safer approach for resolving this specific type of git conflict 
                    # where the file was just duplicated by git:
                    # We just split by <<<<<<< HEAD and take the first part, 
                    # or split by ======= and take the first part.
                    
                    # Since the previous files we saw just had the entire content duplicated
                    # Let's use a simpler logic: just remove everything from ======= to the end of the conflict
                    
                    lines = content.splitlines(True)
                    new_lines = []
                    in_conflict = False
                    keep = True
                    
                    for line in lines:
                        if line.startswith('<<<<<<< HEAD'):
                            in_conflict = True
                            keep = True
                            continue
                        elif line.startswith('======='):
                            if in_conflict:
                                keep = False
                            continue
                        elif line.startswith('>>>>>>> '):
                            if in_conflict:
                                in_conflict = False
                                keep = True
                            continue
                            
                        if keep:
                            new_lines.append(line)
                            
                    new_content = ''.join(new_lines)
                    
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f'Fixed {path}')
                    count += 1
            except Exception as e:
                print(f"Error processing {path}: {e}")

print(f'Total files fixed: {count}')
