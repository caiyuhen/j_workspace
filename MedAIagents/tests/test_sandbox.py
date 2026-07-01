"""
代码执行沙箱单元测试
Code Sandbox Unit Tests
"""

import pytest
import time

from medai.sandbox import SecurityChecker, CodeSandbox


# ============================================================
# SecurityChecker Tests
# ============================================================

class TestSecurityChecker:
    
    def test_safe_code(self):
        checker = SecurityChecker()
        code = "x = 1 + 2\nprint(x)"
        safe, msg = checker.check_code(code)
        assert safe is True
        assert msg == ""
    
    def test_banned_import_os(self):
        checker = SecurityChecker()
        code = "import os\nos.system('ls')"
        safe, msg = checker.check_code(code)
        assert safe is False
        assert "banned module" in msg.lower()
    
    def test_banned_import_sys(self):
        checker = SecurityChecker()
        code = "import sys\nprint(sys.path)"
        safe, msg = checker.check_code(code)
        assert safe is False
        assert "banned module" in msg.lower()
    
    def test_banned_import_from(self):
        checker = SecurityChecker()
        code = "from os.path import join"
        safe, msg = checker.check_code(code)
        assert safe is False
        assert "banned module" in msg.lower()
    
    def test_banned_builtin_eval(self):
        checker = SecurityChecker()
        code = "eval('1 + 1')"
        safe, msg = checker.check_code(code)
        assert safe is False
        assert "banned builtin" in msg.lower()
    
    def test_banned_builtin_exec(self):
        checker = SecurityChecker()
        code = "exec('print(1)')"
        safe, msg = checker.check_code(code)
        assert safe is False
        assert "banned builtin" in msg.lower()
    
    def test_dangerous_attribute_subclasses(self):
        checker = SecurityChecker()
        code = "().__class__.__bases__[0].__subclasses__()"
        safe, msg = checker.check_code(code)
        assert safe is False
        assert "dangerous attribute" in msg.lower()
    
    def test_syntax_error(self):
        checker = SecurityChecker()
        code = "if True print('bad syntax')"
        safe, msg = checker.check_code(code)
        assert safe is False
        assert "Syntax error" in msg
    
    def test_sanitize_code(self):
        checker = SecurityChecker()
        code = "import os\nimport math\neval('1+1')\nprint('hello')"
        sanitized = checker.sanitize_code(code)
        assert "# [BLOCKED] import os" in sanitized
        assert "import math" in sanitized
        assert "# [BLOCKED] eval('1+1')" in sanitized
        assert "print('hello')" in sanitized


# ============================================================
# CodeSandbox Tests
# ============================================================

class TestCodeSandbox:
    
    def test_basic_execution(self):
        sandbox = CodeSandbox(timeout=5)
        result = sandbox.execute_python("x = 2 + 3\nprint(x)")
        assert result["success"] is True
        assert "5" in result["stdout"]
    
    def test_execution_result(self):
        sandbox = CodeSandbox(timeout=5)
        result = sandbox.execute_python("result = 10 * 10")
        assert result["success"] is True
        assert result["result"] == 100
    
    def test_execution_error(self):
        sandbox = CodeSandbox(timeout=5)
        result = sandbox.execute_python("1 / 0")
        assert result["success"] is False
        assert "ZeroDivisionError" in result["stderr"]
    
    def test_math_module_available(self):
        sandbox = CodeSandbox(timeout=5)
        result = sandbox.execute_python("import math\nresult = math.sqrt(16)")
        assert result["success"] is True
        assert result["result"] == 4.0
    
    def test_random_module_available(self):
        sandbox = CodeSandbox(timeout=5)
        result = sandbox.execute_python("import random\nresult = random.randint(1, 10)")
        assert result["success"] is True
        assert isinstance(result["result"], int)
        assert 1 <= result["result"] <= 10
    
    def test_banned_module_blocked(self):
        sandbox = CodeSandbox(timeout=5)
        result = sandbox.execute_python("import os\nprint(os.getcwd())")
        assert result["success"] is False
        assert "Security check failed" in result["stderr"]
    
    def test_eval_blocked(self):
        sandbox = CodeSandbox(timeout=5)
        result = sandbox.execute_python("eval('1 + 1')")
        assert result["success"] is False
        assert "Security check failed" in result["stderr"]
    
    def test_open_blocked(self):
        sandbox = CodeSandbox(timeout=5)
        result = sandbox.execute_python("open('test.txt', 'w')")
        assert result["success"] is False
        assert "Security check failed" in result["stderr"]
    
    def test_builtins_restricted(self):
        sandbox = CodeSandbox(timeout=5)
        # __import__ 应该不在受限环境中
        result = sandbox.execute_python("__import__('os')")
        assert result["success"] is False
        # 错误应该是 NameError 或 Security check
        assert result["stderr"] != ""
    
    def test_timeout(self):
        sandbox = CodeSandbox(timeout=2)
        # 无限循环
        result = sandbox.execute_python("while True: pass")
        assert result["success"] is False
        assert "timed out" in result["stderr"].lower()
    
    def test_timeout_with_sleep(self):
        sandbox = CodeSandbox(timeout=2)
        result = sandbox.execute_python("import time\ntime.sleep(10)")
        assert result["success"] is False
        assert "timed out" in result["stderr"].lower()
    
    def test_restricted_globals_no_eval(self):
        sandbox = CodeSandbox(timeout=5)
        restricted = sandbox._create_restricted_globals()
        builtins = restricted.get("__builtins__", {})
        assert "eval" not in builtins
        assert "exec" not in builtins
        assert "__import__" not in builtins
        assert "open" not in builtins
    
    def test_restricted_globals_has_safe_builtins(self):
        sandbox = CodeSandbox(timeout=5)
        restricted = sandbox._create_restricted_globals()
        builtins = restricted.get("__builtins__", {})
        assert "len" in builtins
        assert "print" in builtins
        assert "range" in builtins
        assert "sum" in builtins
        assert "abs" in builtins
    
    def test_restricted_globals_has_safe_modules(self):
        sandbox = CodeSandbox(timeout=5)
        restricted = sandbox._create_restricted_globals()
        assert "math" in restricted
        assert "random" in restricted
        assert "json" in restricted
        assert "datetime" in restricted
        assert "os" not in restricted
        assert "sys" not in restricted
    
    def test_print_capture(self):
        sandbox = CodeSandbox(timeout=5)
        result = sandbox.execute_python("print('Hello')\nprint('World')")
        assert result["success"] is True
        assert result["stdout"] == "Hello\nWorld\n"
    
    def test_complex_calculation(self):
        import math
        sandbox = CodeSandbox(timeout=5)
        code = """
import math
import json

data = {"a": 1, "b": 2}
result = math.sqrt(data["a"] + data["b"])
print(json.dumps(data))
"""
        result = sandbox.execute_python(code)
        assert result["success"] is True
        assert result["result"] == math.sqrt(3)
        assert '{"a": 1, "b": 2}' in result["stdout"]
