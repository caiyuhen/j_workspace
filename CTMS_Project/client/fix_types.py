import os
import re

api_dir = r"d:\workspace\CTMS_Project\client\src\api"

for filename in os.listdir(api_dir):
    if not filename.endswith(".ts"):
        continue
    filepath = os.path.join(api_dir, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # We need to replace api.get<PaginatedResponse<T>> with api.get<ApiResponse<PaginatedResponse<T>>>
    # And api.get<T> with api.get<ApiResponse<T>> (but careful with things that are already ApiResponse)
    
    # Actually, if we just fix the types, it will compile correctly.
    # Let's use regex.
    # Find all api.(get|post|put|delete)<Type>
    
    # It might be easier to just fix the components to not use ts-ignore or fix the return types.
    # Let's just fix the return types by wrapping them in ApiResponse<...> where missing.
    
    new_content = content
    # For PaginatedResponse
    new_content = re.sub(r'api\.(get|post|put)<PaginatedResponse<(.+?)>>', r'api.\1<ApiResponse<PaginatedResponse<\2>>>', new_content)
    
    # For regular types not wrapped in ApiResponse
    # We want to match api.get<Type> where Type is not ApiResponse and not PaginatedResponse
    # and replace with api.get<ApiResponse<Type>>
    def wrap_type(match):
        method = match.group(1)
        type_name = match.group(2)
        if type_name.startswith('ApiResponse') or type_name.startswith('PaginatedResponse'):
            return match.group(0)
        return f"api.{method}<ApiResponse<{type_name}>>"
        
    new_content = re.sub(r'api\.(get|post|put)<([A-Za-z0-9_\[\]\{\}\s:,]+)>', wrap_type, new_content)
    
    if new_content != content:
        # ensure ApiResponse is imported
        if 'ApiResponse' not in new_content:
            # Add import
            new_content = "import type { ApiResponse } from '@/types';\n" + new_content
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
