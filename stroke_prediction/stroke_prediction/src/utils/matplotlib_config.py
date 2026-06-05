# 卒中预测模型 - Matplotlib配置工具

import matplotlib.pyplot as plt
import logging
import os
import sys

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def configure_matplotlib_chinese():
    """配置matplotlib以正确显示中文
    
    此函数设置matplotlib的字体配置，以确保中文字符能够正确显示在图表中。
    """
    try:
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun', 'Arial Unicode MS']
        # 用来正常显示负号
        plt.rcParams['axes.unicode_minus'] = False
        
        logger.info("Matplotlib中文字体配置成功")
        return True
    except Exception as e:
        logger.error(f"配置Matplotlib中文字体时出错: {str(e)}")
        return False

# 在导入时自动配置
configure_matplotlib_chinese()