"""
系统工具集合
System Tools Collection

提供包安装、URL 访问等系统级操作，带安全检查。
"""

import subprocess
import json
import re
import os
from typing import Dict, Any, List, Optional
from loguru import logger

from .registry import ToolRegistry


# 安全包名白名单正则（仅允许字母、数字、连字符、下划线、点）
SAFE_PACKAGE_RE = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9._-]*[a-zA-Z0-9]$')

# 已知的恶意/危险包模式
DANGEROUS_PACKAGES = {
    'os-system', 'subprocess', 'eval-exec', 'cmd-exec',
    'backdoor', 'trojan', 'keylogger', 'spyware',
}

# 已知安全维护者前缀（常用医学/AI 相关包）
KNOWN_SAFE_PREFIXES = [
    'numpy', 'scipy', 'pandas', 'matplotlib', 'seaborn',
    'scikit-learn', 'statsmodels', 'lifelines', 'survival',
    'openai', 'anthropic', 'langchain', 'transformers',
    'torch', 'tensorflow', 'keras', 'opencv', 'pillow',
    'pydicom', 'nibabel', 'nilearn', 'antspyx',
    'biopython', 'pysam', 'cryptography', 'requests',
    'beautifulsoup', 'selenium', 'playwright',
    'fastapi', 'uvicorn', 'pydantic', 'sqlalchemy',
    'httpx', 'aiohttp', 'websockets',
    'plotly', 'bokeh', 'altair', 'streamlit',
    'python-docx', 'python-pptx', 'openpyxl',
    'loguru', 'rich', 'typer', 'click',
    'redis', 'celery', 'pytest', 'black', 'flake8',
    'fhir', 'hl7', 'dicom',
    'medai', 'medical', 'clinical',
    'qwen', 'deepseek', 'dashscope',
    'pywebview', 'mcp', 'stdio',
    'pymilvus', 'chromadb', 'faiss',
    'docx', 'pptx', 'xlsx',
    'bioinf', 'genomic', 'transcript',
]

# 已安装的包缓存
_installed_packages_cache: Dict[str, str] = {}


def _get_installed_packages() -> Dict[str, str]:
    """获取已安装的包列表（带缓存）"""
    if _installed_packages_cache:
        return _installed_packages_cache
    try:
        result = subprocess.run(
            ['pip', 'list', '--format=json'],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            for pkg in json.loads(result.stdout):
                _installed_packages_cache[pkg.get('name', '').lower()] = pkg.get('version', '')
    except Exception as e:
        logger.warning(f"Failed to get installed packages: {e}")
    return _installed_packages_cache


def _validate_package_name(name: str) -> Dict[str, Any]:
    """验证包名安全性

    Returns:
        {"valid": bool, "reason": str}
    """
    name_lower = name.lower().strip()

    # 检查包名格式
    if not SAFE_PACKAGE_RE.match(name_lower):
        return {"valid": False, "reason": f"包名 '{name}' 包含非法字符"}

    # 检查危险包
    if name_lower in DANGEROUS_PACKAGES:
        return {"valid": False, "reason": f"包名 '{name}' 在已知危险包列表中"}

    # 检查可疑模式（如包含命令关键词）
    suspicious = ['sys', 'exec', 'eval', 'shell', 'cmd', 'hack', 'exploit']
    for s in suspicious:
        if s in name_lower and name_lower != s:
            return {"valid": False, "reason": f"包名 '{name}' 包含可疑关键词 '{s}'"}

    return {"valid": True, "reason": "包名通过安全检查"}


def _check_package_info(name: str) -> Dict[str, Any]:
    """通过 pip show 检查包的详细信息

    Returns:
        {"name": str, "version": str, "summary": str, "author": str, "home_page": str, "license": str}
    """
    try:
        result = subprocess.run(
            ['pip', 'show', name],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode != 0:
            return {"error": f"包 '{name}' 未找到或未安装"}

        info = {}
        for line in result.stdout.strip().split('\n'):
            if ':' in line:
                key, val = line.split(':', 1)
                info[key.strip().lower()] = val.strip()

        return {
            "name": info.get('name', name),
            "version": info.get('version', 'unknown'),
            "summary": info.get('summary', ''),
            "author": info.get('author', ''),
            "home_page": info.get('home-page', ''),
            "license": info.get('license', ''),
        }
    except Exception as e:
        return {"error": str(e)}


def install_package(
    package_name: str,
    version: str = "",
    upgrade: bool = False,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """安全安装 Python 包

    Args:
        package_name: 包名
        version: 指定版本（可选）
        upgrade: 是否升级已安装的包
        dry_run: 仅模拟安装，不实际执行

    Returns:
        {"success": bool, "package": str, "version": str, "message": str, "details": dict}
    """
    # 1. 安全校验
    validation = _validate_package_name(package_name)
    if not validation["valid"]:
        return {
            "success": False,
            "package": package_name,
            "error": validation["reason"],
        }

    # 2. 检查是否已安装
    installed = _get_installed_packages()
    pkg_lower = package_name.lower().replace('-', '_')
    if pkg_lower in installed and not upgrade:
        return {
            "success": True,
            "package": package_name,
            "version": installed[pkg_lower],
            "message": f"包 '{package_name}' 已安装（版本 {installed[pkg_lower]}）",
            "action": "already_installed",
        }

    # 3. 预检查：pip install --dry-run
    if not dry_run:
        pre_check = subprocess.run(
            ['pip', 'install', '--dry-run', package_name],
            capture_output=True, text=True, timeout=30
        )
        if pre_check.returncode != 0:
            return {
                "success": False,
                "package": package_name,
                "error": f"pip 预检查失败: {pre_check.stderr[:500]}",
            }

    # 4. dry_run 模式
    if dry_run:
        return {
            "success": True,
            "package": package_name,
            "version": version or "latest",
            "message": f"模拟安装成功（dry_run 模式）",
            "action": "dry_run",
            "validation": validation,
        }

    # 5. 实际安装
    install_target = package_name
    if version:
        install_target = f"{package_name}=={version}"

    try:
        result = subprocess.run(
            ['pip', 'install', install_target],
            capture_output=True, text=True, timeout=120
        )

        if result.returncode != 0:
            return {
                "success": False,
                "package": package_name,
                "error": f"安装失败: {result.stderr[:500]}",
            }

        # 安装成功后获取版本
        installed = _get_installed_packages()
        installed_version = installed.get(pkg_lower, version or "unknown")

        # 检查安装后的包信息
        pkg_info = _check_package_info(package_name)

        return {
            "success": True,
            "package": package_name,
            "version": installed_version,
            "message": f"包 '{package_name}' 安装成功",
            "action": "installed",
            "package_info": pkg_info,
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "package": package_name,
            "error": "安装超时（120秒）",
        }
    except Exception as e:
        return {
            "success": False,
            "package": package_name,
            "error": str(e),
        }


def uninstall_package(package_name: str) -> Dict[str, Any]:
    """安全卸载 Python 包"""
    validation = _validate_package_name(package_name)
    if not validation["valid"]:
        return {"success": False, "package": package_name, "error": validation["reason"]}

    # 保护核心包不被卸载
    protected = ['pip', 'setuptools', 'wheel', 'python', 'fastapi', 'uvicorn',
                 'pydantic', 'loguru', 'openai', 'anthropic']
    if package_name.lower() in protected:
        return {
            "success": False,
            "package": package_name,
            "error": f"包 '{package_name}' 是核心依赖，不允许卸载",
        }

    try:
        result = subprocess.run(
            ['pip', 'uninstall', '-y', package_name],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            return {"success": False, "package": package_name, "error": result.stderr[:500]}

        # 清除缓存
        _installed_packages_cache.pop(package_name.lower().replace('-', '_'), None)

        return {"success": True, "package": package_name, "message": f"包 '{package_name}' 已卸载"}
    except Exception as e:
        return {"success": False, "package": package_name, "error": str(e)}


def list_packages(filter_text: str = "") -> Dict[str, Any]:
    """列出已安装的包"""
    installed = _get_installed_packages()
    packages = []
    for name, version in sorted(installed.items()):
        if filter_text and filter_text.lower() not in name:
            continue
        packages.append({"name": name, "version": version})

    return {
        "total": len(packages),
        "packages": packages,
    }


def check_package(package_name: str) -> Dict[str, Any]:
    """检查包的安全性和信息"""
    validation = _validate_package_name(package_name)

    installed = _get_installed_packages()
    pkg_lower = package_name.lower().replace('-', '_')
    is_installed = pkg_lower in installed

    # 尝试获取 PyPI 上的信息
    pypi_info = None
    try:
        result = subprocess.run(
            ['pip', 'index', 'versions', package_name],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0:
            pypi_info = result.stdout[:500]
    except Exception:
        pass

    return {
        "package": package_name,
        "validation": validation,
        "is_installed": is_installed,
        "installed_version": installed.get(pkg_lower, None),
        "pypi_info": pypi_info,
    }


# ============================================================
# Schema 定义
# ============================================================

INSTALL_PACKAGE_SCHEMA = {
    "type": "object",
    "properties": {
        "package_name": {
            "type": "string",
            "description": "要安装的 Python 包名"
        },
        "version": {
            "type": "string",
            "description": "指定版本号（可选）"
        },
        "dry_run": {
            "type": "boolean",
            "description": "仅模拟安装，不实际执行"
        },
    },
    "required": ["package_name"]
}

UNINSTALL_PACKAGE_SCHEMA = {
    "type": "object",
    "properties": {
        "package_name": {
            "type": "string",
            "description": "要卸载的 Python 包名"
        },
    },
    "required": ["package_name"]
}

LIST_PACKAGES_SCHEMA = {
    "type": "object",
    "properties": {
        "filter_text": {
            "type": "string",
            "description": "过滤关键词（可选）"
        },
    }
}

CHECK_PACKAGE_SCHEMA = {
    "type": "object",
    "properties": {
        "package_name": {
            "type": "string",
            "description": "要检查的 Python 包名"
        },
    },
    "required": ["package_name"]
}


def register_system_tools(registry: ToolRegistry) -> ToolRegistry:
    """注册系统工具"""
    registry.register(
        name="install_package",
        description="安全安装 Python 包。先进行安全验证（包名检查、dry-run预检），再执行安装。支持指定版本。",
        parameters=INSTALL_PACKAGE_SCHEMA,
        func=install_package
    )

    registry.register(
        name="uninstall_package",
        description="安全卸载 Python 包。核心依赖包受保护无法卸载。",
        parameters=UNINSTALL_PACKAGE_SCHEMA,
        func=uninstall_package
    )

    registry.register(
        name="list_packages",
        description="列出已安装的 Python 包，支持关键词过滤",
        parameters=LIST_PACKAGES_SCHEMA,
        func=list_packages
    )

    registry.register(
        name="check_package",
        description="检查 Python 包的安全性和安装状态，返回验证结果和版本信息",
        parameters=CHECK_PACKAGE_SCHEMA,
        func=check_package
    )

    logger.info("Registered 4 system tools (install/uninstall/list/check package)")
    return registry
