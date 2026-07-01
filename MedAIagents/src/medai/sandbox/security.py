"""
代码沙箱安全检查模块
Sandbox Security Module
"""

import re
import ast
from typing import Tuple, List


class SecurityChecker:
    """代码安全检查器
    
    检查 Python 代码中是否包含危险操作，
    并提供代码清理功能。
    """
    
    BANNED_MODULES = [
        'os', 'sys', 'subprocess', 'socket', 'urllib', 'requests',
        'ftplib', 'http', 'telnetlib', 'smtplib', 'poplib', 'imaplib',
        'nntplib', 'shlex', 'pathlib', 'platform', 'pwd', 'grp',
        'spwd', 'crypt', 'termios', 'tty', 'pty', 'fcntl', 'pipes',
        'ctypes', 'mmap', 'resource', 'nis', 'msvcrt', 'winreg',
        '_winapi', 'posix', 'java', 'netrc', 'webbrowser',
        'sqlite3', 'dbm', 'pickle', 'shelve', 'multiprocessing',
    ]
    
    BANNED_BUILTINS = [
        'eval', 'exec', 'compile', '__import__', 'open',
        'input', 'raw_input', 'reload',
        'breakpoint', 'open_code', 'help',
    ]
    
    # 危险模式（正则表达式）
    DANGEROUS_PATTERNS = [
        r'__subclasses__\s*\(',
        r'__bases__\s*\[',
        r'__mro__\s*\[',
        r'__globals__\s*\[',
        r'__code__',
        r'func_globals',
        r'\.\s*__class__\s*\.\s*__bases__',
        r'import\s+\w+\s+as\s+\w+',
    ]
    
    def check_code(self, code: str) -> Tuple[bool, str]:
        """检查代码安全性
        
        Args:
            code: Python 代码字符串
        
        Returns:
            (是否安全, 错误信息)
        """
        # 1. 语法检查
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return False, f"Syntax error: {e}"
        
        # 2. AST 遍历检查
        issues = self._check_ast(tree)
        if issues:
            return False, "; ".join(issues)
        
        # 3. 正则表达式模式检查（针对字符串混淆）
        pattern_issues = self._check_patterns(code)
        if pattern_issues:
            return False, "; ".join(pattern_issues)
        
        return True, ""
    
    def _check_ast(self, tree: ast.AST) -> List[str]:
        """通过 AST 检查代码"""
        issues = []
        
        for node in ast.walk(tree):
            # 检查 import 语句
            if isinstance(node, ast.Import):
                for alias in node.names:
                    base_module = alias.name.split('.')[0]
                    if base_module in self.BANNED_MODULES:
                        issues.append(f"Import of banned module: '{alias.name}'")
            
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                base_module = module.split('.')[0]
                if base_module in self.BANNED_MODULES:
                    issues.append(f"Import from banned module: '{module}'")
            
            # 检查危险内置函数调用
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in self.BANNED_BUILTINS:
                        issues.append(f"Call to banned builtin: '{node.func.id}'")
                elif isinstance(node.func, ast.Attribute):
                    # 检查 getattr(obj, 'eval') 等模式
                    if isinstance(node.func.value, ast.Constant):
                        if node.func.attr in self.BANNED_BUILTINS:
                            issues.append(f"Call to banned function via getattr: '{node.func.attr}'")
            
            # 检查属性访问（__subclasses__ 等）
            elif isinstance(node, ast.Attribute):
                if node.attr in ('__subclasses__', '__bases__', '__mro__', '__globals__', '__code__', 'func_globals'):
                    issues.append(f"Access to dangerous attribute: '{node.attr}'")
            
            # 检查文件操作
            elif isinstance(node, ast.With):
                for item in node.items:
                    if isinstance(item.context_expr, ast.Call):
                        if isinstance(item.context_expr.func, ast.Name):
                            if item.context_expr.func.id == 'open':
                                issues.append("File operation 'open' is not allowed")
        
        return issues
    
    def _check_patterns(self, code: str) -> List[str]:
        """通过正则表达式检查危险模式"""
        issues = []
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, code):
                issues.append(f"Dangerous pattern detected: {pattern}")
        return issues
    
    def sanitize_code(self, code: str) -> str:
        """清理代码中的潜在危险内容
        
        注意：此方法仅提供基础的字符串清理，
        不能替代严格的 AST 检查。不可信代码应直接拒绝执行。
        
        Args:
            code: Python 代码字符串
        
        Returns:
            清理后的代码
        """
        lines = code.split('\n')
        cleaned = []
        
        for line in lines:
            stripped = line.strip()
            
            # 跳过明显的危险 import
            if stripped.startswith('import ') or stripped.startswith('from '):
                base = stripped.split()[1].split('.')[0]
                if base in self.BANNED_MODULES:
                    cleaned.append(f"# [BLOCKED] {line}")
                    continue
            
            # 注释掉对危险内置函数的调用（简单匹配）
            for banned in self.BANNED_BUILTINS:
                if re.search(rf'\b{banned}\s*\(', line):
                    cleaned.append(f"# [BLOCKED] {line}")
                    break
            else:
                cleaned.append(line)
        
        return '\n'.join(cleaned)
