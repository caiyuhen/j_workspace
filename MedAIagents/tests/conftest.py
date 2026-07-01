"""
pytest 全局配置
"""
import sys
import os

# 将 src 加入路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# 测试数据目录
TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
os.makedirs(TEST_DATA_DIR, exist_ok=True)
