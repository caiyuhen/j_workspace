import os
import re

files = [f for f in os.listdir('app/api/v1/endpoints') if f.endswith('.py')]

for file in files:
    with open(f"app/api/v1/endpoints/{file}", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Split by @router.get
    endpoints = content.split("@router.get")[1:]
    for e in endpoints:
        func_name_match = re.search(r'def (\w+)\(', e)
        if not func_name_match:
            continue
        func_name = func_name_match.group(1)
        
        # Check if current_user.is_superuser is checked
        if "current_user.is_superuser" not in e:
            print(f"File: {file} - Func: {func_name} has NO isolation!")
