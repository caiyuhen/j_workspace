"""
代码沙箱执行器模块
Code Sandbox Executor Module
"""

import json
import os
import subprocess
import sys
import tempfile
import traceback
from typing import Dict, Any

from .security import SecurityChecker


def _build_restricted_globals_code() -> str:
    """生成在子进程中构建受限环境的 Python 代码字符串"""
    safe_builtins = [
        'abs', 'all', 'any', 'ascii', 'bin', 'bool', 'bytearray', 'bytes',
        'chr', 'complex', 'dict', 'dir', 'divmod', 'enumerate', 'filter',
        'float', 'format', 'frozenset', 'hasattr', 'hash', 'hex', 'id',
        'int', 'isinstance', 'issubclass', 'iter', 'len', 'list', 'map',
        'max', 'memoryview', 'min', 'next', 'oct', 'ord', 'pow', 'print',
        'property', 'range', 'repr', 'reversed', 'round', 'set', 'slice',
        'sorted', 'staticmethod', 'str', 'sum', 'tuple', 'type', 'vars',
        'zip', 'Exception', 'ValueError', 'TypeError', 'KeyError',
        'IndexError', 'AttributeError', 'ZeroDivisionError',
        'ArithmeticError', 'RuntimeError', 'StopIteration',
        'NotImplementedError', 'OverflowError', 'RecursionError',
    ]

    safe_modules = [
        'math', 'random', 'datetime', 'json', 'statistics',
        'itertools', 'functools', 'decimal', 'fractions',
        'typing', 'collections', 'heapq', 'bisect',
        'copy', 'numbers', 'string', 're', 'time',
    ]

    lines = ["# Build restricted globals"]
    lines.append("safe_builtins = {}")
    for name in safe_builtins:
        lines.append(f"safe_builtins['{name}'] = {name}")

    lines.append("safe_modules = {}")
    for name in safe_modules:
        lines.append(f"try:\n    safe_modules['{name}'] = __import__('{name}')\nexcept ImportError:\n    pass")

    # 添加安全的 __import__
    lines.append(f"_SAFE_MODULE_NAMES = {safe_modules!r}")
    lines.append("""
def _safe_import(name, *args, **kwargs):
    base = name.split('.')[0]
    if base not in _SAFE_MODULE_NAMES:
        raise ImportError(f"Import of '{name}' is not allowed in sandbox")
    return __import__(name, *args, **kwargs)

safe_builtins['__import__'] = _safe_import
""")

    lines.append("globals().update(safe_modules)")
    lines.append("globals()['__builtins__'] = safe_builtins")
    lines.append("globals()['__name__'] = '__sandbox__'")

    return "\n".join(lines)


def _build_runner_script(user_code: str) -> str:
    """构建在子进程中执行的完整脚本"""
    restricted_env = _build_restricted_globals_code()
    return f'''
{restricted_env}

import io, sys, json, traceback

user_code = {repr(user_code)}

local_vars = {{}}
stdout_capture = io.StringIO()
stderr_capture = io.StringIO()
old_stdout = sys.stdout
old_stderr = sys.stderr

result = None
success = False

try:
    sys.stdout = stdout_capture
    sys.stderr = stderr_capture
    exec(user_code, globals(), local_vars)
    
    result = local_vars.get('result', local_vars.get('_result', None))
    if result is None and local_vars:
        for key in sorted(local_vars.keys()):
            if not key.startswith('__'):
                result = local_vars[key]
                break
    
    success = True
except Exception:
    stderr_capture.write("\\n" + traceback.format_exc())
finally:
    sys.stdout = old_stdout
    sys.stderr = old_stderr

# 输出 JSON 结果到 stdout 的最后一行
output = json.dumps({{
    "success": success,
    "stdout": stdout_capture.getvalue(),
    "stderr": stderr_capture.getvalue(),
    "result": result,
}}, ensure_ascii=False)

print("__SANDBOX_RESULT__" + output + "__SANDBOX_END__")
'''


class CodeSandbox:
    """代码沙箱
    
    在受限环境中安全执行 Python 代码，
    限制可用模块、内置函数和执行时间。
    """
    
    def __init__(self, timeout: int = 30):
        """
        Args:
            timeout: 代码执行超时时间（秒）
        """
        self.timeout = timeout
        self.security = SecurityChecker()
    
    def execute_python(self, code: str) -> Dict[str, Any]:
        """执行 Python 代码
        
        Args:
            code: Python 代码字符串
        
        Returns:
            执行结果字典，包含：
                - success: 是否成功
                - stdout: 标准输出
                - stderr: 标准错误
                - result: 返回值（如果有）
        """
        # 安全检查
        safe, msg = self.security.check_code(code)
        if not safe:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Security check failed: {msg}",
                "result": None
            }
        
        # 代码清理
        sanitized = self.security.sanitize_code(code)
        
        # 生成 runner 脚本
        runner_script = _build_runner_script(sanitized)
        
        # 写入临时文件
        tmp_file = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
                f.write(runner_script)
                tmp_file = f.name
            
            # 在子进程中执行
            proc = subprocess.run(
                [sys.executable, tmp_file],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                encoding='utf-8',
                errors='replace'
            )
            
            # 从 stdout 中提取结果标记
            result = self._parse_result(proc.stdout, proc.stderr)
            
            if proc.returncode != 0 and result["success"]:
                # 如果进程退出码非零但解析到成功结果，视为失败
                result["success"] = False
                result["stderr"] = result.get("stderr", "") + f"\nProcess exited with code {proc.returncode}"
            
            return result
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Execution timed out after {self.timeout} seconds",
                "result": None
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Sandbox execution error: {e}",
                "result": None
            }
        finally:
            if tmp_file and os.path.exists(tmp_file):
                try:
                    os.unlink(tmp_file)
                except Exception:
                    pass
    
    def _parse_result(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """解析子进程输出中的结果"""
        # 查找标记之间的 JSON
        import re
        pattern = r'__SANDBOX_RESULT__(.+?)__SANDBOX_END__'
        match = re.search(pattern, stdout, re.DOTALL)
        
        if match:
            try:
                result = json.loads(match.group(1))
                # 去掉标记后的剩余 stdout
                clean_stdout = re.sub(pattern, '', stdout, flags=re.DOTALL).strip()
                if clean_stdout:
                    result["stdout"] = clean_stdout + "\n" + result.get("stdout", "")
                if stderr:
                    result["stderr"] = result.get("stderr", "") + "\n" + stderr
                return result
            except json.JSONDecodeError:
                pass
        
        # 如果没有找到标记，返回原始输出
        return {
            "success": False,
            "stdout": stdout,
            "stderr": stderr,
            "result": None
        }
    
    def _create_restricted_globals(self) -> Dict[str, Any]:
        """创建受限的全局命名空间
        
        限制可用的内置函数和模块，移除危险功能。
        
        Returns:
            受限的全局字典
        """
        # 安全的内置函数白名单
        safe_builtins = {
            'abs': abs,
            'all': all,
            'any': any,
            'ascii': ascii,
            'bin': bin,
            'bool': bool,
            'bytearray': bytearray,
            'bytes': bytes,
            'chr': chr,
            'complex': complex,
            'dict': dict,
            'dir': dir,
            'divmod': divmod,
            'enumerate': enumerate,
            'filter': filter,
            'float': float,
            'format': format,
            'frozenset': frozenset,
            'hasattr': hasattr,
            'hash': hash,
            'hex': hex,
            'id': id,
            'int': int,
            'isinstance': isinstance,
            'issubclass': issubclass,
            'iter': iter,
            'len': len,
            'list': list,
            'map': map,
            'max': max,
            'memoryview': memoryview,
            'min': min,
            'next': next,
            'oct': oct,
            'ord': ord,
            'pow': pow,
            'print': print,
            'property': property,
            'range': range,
            'repr': repr,
            'reversed': reversed,
            'round': round,
            'set': set,
            'slice': slice,
            'sorted': sorted,
            'staticmethod': staticmethod,
            'str': str,
            'sum': sum,
            'tuple': tuple,
            'type': type,
            'vars': vars,
            'zip': zip,
            'Exception': Exception,
            'ValueError': ValueError,
            'TypeError': TypeError,
            'KeyError': KeyError,
            'IndexError': IndexError,
            'AttributeError': AttributeError,
            'ZeroDivisionError': ZeroDivisionError,
            'ArithmeticError': ArithmeticError,
            'RuntimeError': RuntimeError,
            'StopIteration': StopIteration,
            'NotImplementedError': NotImplementedError,
            'OverflowError': OverflowError,
            'RecursionError': RecursionError,
        }
        
        # 安全模块白名单
        safe_modules = {}
        safe_module_names = [
            'math', 'random', 'datetime', 'json', 'statistics',
            'itertools', 'functools', 'decimal', 'fractions',
            'typing', 'collections', 'heapq', 'bisect',
            'copy', 'numbers', 'string', 're', 'time',
        ]
        
        for name in safe_module_names:
            try:
                safe_modules[name] = __import__(name)
            except ImportError:
                pass
        
        # 构建受限 globals
        restricted = {
            '__builtins__': safe_builtins,
            '__name__': '__sandbox__',
            '__doc__': None,
            '__package__': None,
            '__spec__': None,
            **safe_modules
        }
        
        return restricted
