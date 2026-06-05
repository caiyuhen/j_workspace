#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pytz

BEIJING_TZ = pytz.timezone('Asia/Shanghai')
UTC_TZ = pytz.utc

def utc_to_beijing_str(utc_time):
    """
    将UTC时间对象转换为北京时间并格式化为字符串
    :param utc_time: UTC时间对象
    :return: 北京时间字符串
    """
    if not utc_time:
        return ""
    # 假设utc_time是来自MongoDB的朴素UTC时间，先附加UTC时区
    utc_time_aware = utc_time.replace(tzinfo=pytz.utc)
    beijing_time = utc_time_aware.astimezone(BEIJING_TZ)
    return beijing_time.strftime('%Y-%m-%d %H:%M:%S')

"""
MongoDB数据提取和解压缩脚本
从MongoDB中提取指定设备和时间范围的压缩数据，解压后保存为JSON文件

功能：
1. 连接MongoDB数据库
2. 根据deviceId和时间范围查询数据
3. 解压缩collectData字段
4. 生成指定格式的JSON输出文件


日期: 2025-10-29
"""

import json
import os
import sys
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
import logging

# 添加当前目录到Python路径，以便导入解压缩模块
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

try:
    import pymongo
    from pymongo import MongoClient
except ImportError:
    print("错误: 未安装pymongo库。请运行: pip install pymongo")
    sys.exit(1)

# 导入解压缩模块
try:
    from decompressed_comp_ppg_data import decompressed_and_upsampled_ppg_data
except ImportError as e:
    print(f"错误: 无法导入解压缩模块: {e}")
    sys.exit(1)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('extract_decompress.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# --- 时间处理辅助函数 ---

beijing_tz = timezone(timedelta(hours=8))

def beijing_to_utc(dt: datetime) -> datetime:
    """将北京时间转换为UTC时间"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=beijing_tz)
    return dt.astimezone(timezone.utc)

def format_beijing_time(dt: Optional[datetime]) -> str:
    """格式化时间为字符串. 根据新要求, 此函数不再执行时区转换."""
    if not dt:
        return ""
    # 根据指令，不再进行时区转换，直接格式化
    # 这意味着如果输入是UTC时间，输出的也是UTC时间的字符串表示
    return dt.strftime("%Y-%m-%d %H:%M:%S")


class MongoDBExtractor:
    """MongoDB数据提取器"""
    
    def __init__(self, host: str = "192.168.77.192", port: int = 27017, 
                 username: str = "root", password: str = "bYDdBQARG4", 
                 database: str = "andun_1", collection: str = "device_collect_compress_data"):
        """
        初始化MongoDB连接参数
        
        Args:
            host: MongoDB主机地址
            port: MongoDB端口
            username: 用户名
            password: 密码
            database: 数据库名
            collection: 集合名
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.database_name = database
        self.collection_name = collection
        self.client = None
        self.db = None
        self.collection = None
        
    def connect(self) -> bool:
        """
        连接到MongoDB数据库
        
        Returns:
            bool: 连接是否成功
        """
        try:
            # 尝试多种连接方式
            connection_attempts = [
                # 方式1: 指定认证数据库为admin
                f"mongodb://{self.username}:{self.password}@{self.host}:{self.port}/{self.database_name}?authSource=admin",
                # 方式2: 指定认证数据库为目标数据库
                f"mongodb://{self.username}:{self.password}@{self.host}:{self.port}/{self.database_name}?authSource={self.database_name}",
                # 方式3: 原始方式
                f"mongodb://{self.username}:{self.password}@{self.host}:{self.port}/{self.database_name}",
                # 方式4: 不指定数据库的连接
                f"mongodb://{self.username}:{self.password}@{self.host}:{self.port}?authSource=admin"
            ]
            
            for i, uri in enumerate(connection_attempts, 1):
                try:
                    logger.info(f"尝试连接方式 {i}...")
                    
                    # 创建MongoDB客户端
                    self.client = MongoClient(uri, serverSelectionTimeoutMS=5000)
                    
                    # 测试连接
                    self.client.server_info()
                    
                    # 获取数据库和集合
                    self.db = self.client[self.database_name]
                    self.collection = self.db[self.collection_name]
                    
                    # 测试集合访问
                    self.collection.count_documents({}, limit=1)
                    
                    logger.info(f"成功连接到MongoDB (方式 {i}): {self.host}:{self.port}/{self.database_name}")
                    return True
                    
                except Exception as e:
                    logger.warning(f"连接方式 {i} 失败: {e}")
                    if self.client:
                        self.client.close()
                        self.client = None
                    continue
            
            logger.error("所有连接方式都失败了")
            return False
            
        except Exception as e:
            logger.error(f"连接MongoDB失败: {e}")
            return False
    
    def disconnect(self):
        """断开MongoDB连接"""
        if self.client:
            self.client.close()
            logger.info("已断开MongoDB连接")
    
    def query_data(self, device_id: str, start_time: str, end_time: str) -> List[Dict[str, Any]]:
        """
        根据设备ID和时间范围查询数据
        
        Args:
            device_id: 设备ID
            start_time: 开始时间 (格式: "YYYY-MM-DD")
            end_time: 结束时间 (格式: "YYYY-MM-DD")
            
        Returns:
            List[Dict]: 查询结果列表
        """
        try:
            # 将字符串时间转换为datetime对象
            start_datetime_beijing = datetime.strptime(start_time, "%Y-%m-%d")
            end_datetime_beijing = datetime.strptime(end_time + " 23:59:59", "%Y-%m-%d %H:%M:%S")

            # 根据新指令，直接使用北京时间进行查询
            
            # 构建查询条件
            query = {
                "deviceId": device_id,
                "collectTime": {
                    "$gte": start_datetime_beijing,
                    "$lte": end_datetime_beijing
                }
            }
            
            # 指定需要的字段
            projection = {
                "deviceId": 1,
                "collectTime": 1,
                "createTime": 1,
                "collectData": 1,
                "_id": 0  # 排除_id字段
            }
            
            # 执行查询并按collectTime排序
            cursor = self.collection.find(query, projection).sort("collectTime", 1)
            
            # 转换为列表
            results = list(cursor)
            
            logger.info(f"查询到 {len(results)} 条数据 (设备: {device_id}, 时间范围: {start_time} ~ {end_time})")
            
            return results
            
        except ValueError as e:
            logger.error(f"时间格式错误: {e}")
            return []
        except Exception as e:
            logger.error(f"查询数据失败: {e}")
            return []
    
    def extract_and_decompress(self, device_id: str, start_time: str, end_time: str, 
                             output_dir: str = "output") -> Optional[str]:
        """
        提取并解压数据，生成JSON文件
        
        Args:
            device_id: 设备ID
            start_time: 开始时间 (格式: "YYYY-MM-DD")
            end_time: 结束时间 (格式: "YYYY-MM-DD")
            output_dir: 输出目录
            
        Returns:
            Optional[str]: 生成的文件路径，失败时返回None
        """
        try:
            # 确保输出目录存在
            os.makedirs(output_dir, exist_ok=True)
            
            # 查询原始数据
            raw_data = self.query_data(device_id, start_time, end_time)
            
            if not raw_data:
                logger.warning(f"未找到符合条件的数据: 设备 {device_id}, 时间范围 {start_time} ~ {end_time}")
                return None
            
            # 准备解压缩数据
            logger.info("开始解压缩数据...")
            
            # 提取collectData用于解压缩
            collect_data_list = []
            for item in raw_data:
                if "collectData" in item and item["collectData"]:
                    collect_data_list.append({
                        "collectTime": item["collectTime"],
                        "collectData": item["collectData"]
                    })
            
            if not collect_data_list:
                logger.warning("没有找到有效的collectData数据")
                return None
            
            # 调用解压缩函数
            try:
                decompressed_data_list = decompressed_and_upsampled_ppg_data(collect_data_list)
            except Exception as e:
                logger.error(f"解压缩数据失败: {e}")
                return None
            
            # 构建输出数据结构
            processed_data = []
            
            for i, (raw_item, decompressed_data) in enumerate(zip(raw_data, decompressed_data_list)):
                if decompressed_data is not None:
                    # 转换时间为北京时间字符串
                    collect_time_str = format_beijing_time(raw_item.get("collectTime"))
                    create_time_str = format_beijing_time(raw_item.get("createTime"))
                    
                    processed_item = {
                        "index": i,
                        "collectTime": collect_time_str,
                        "createTime": create_time_str,
                        "collectTime_beijing": utc_to_beijing_str(raw_item.get("collectTime")),
                        "createTime_beijing": utc_to_beijing_str(raw_item.get("createTime")),
                        "originalDataSize": len(decompressed_data),
                        "decompressedData": decompressed_data
                    }
                    processed_data.append(processed_item)
                else:
                    logger.warning(f"第 {i} 条数据解压失败，跳过")
            
            # 构建最终输出结构
            output_data = {
                "deviceId": device_id,
                "dataCount": len(processed_data),
                "collectDataCount": len(raw_data),
                "processedData": processed_data
            }
            
            # 生成输出文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"{device_id}_{timestamp}.json"
            output_path = os.path.join(output_dir, output_filename)
            
            # 保存JSON文件
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"数据提取和解压完成，已保存到: {output_path}")
            logger.info(f"总数据条数: {len(raw_data)}, 成功处理: {len(processed_data)}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"提取和解压数据失败: {e}")
            return None

def main():
    """主函数 - 提供命令行接口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="MongoDB数据提取和解压缩工具")
    parser.add_argument("--device-id", required=True, help="设备ID")
    parser.add_argument("--start-time", required=True, help="开始时间 (格式: YYYY-MM-DD)")
    parser.add_argument("--end-time", required=True, help="结束时间 (格式: YYYY-MM-DD)")
    parser.add_argument("--output-dir", default="output", help="输出目录 (默认: output)")
    parser.add_argument("--host", default="192.168.77.192", help="MongoDB主机地址")
    parser.add_argument("--port", type=int, default=27017, help="MongoDB端口")
    parser.add_argument("--username", default="root", help="MongoDB用户名")
    parser.add_argument("--password", default="bYDdBQARG4", help="MongoDB密码")
    parser.add_argument("--database", default="andun_1", help="数据库名")
    parser.add_argument("--collection", default="device_collect_compress_data", help="集合名")
    
    args = parser.parse_args()
    
    # 验证时间格式
    try:
        datetime.strptime(args.start_time, "%Y-%m-%d")
        datetime.strptime(args.end_time, "%Y-%m-%d")
    except ValueError as e:
        logger.error(f"时间格式错误: {e}")
        logger.error("请使用格式: YYYY-MM-DD")
        return
    
    # 创建提取器
    extractor = MongoDBExtractor(
        host=args.host,
        port=args.port,
        username=args.username,
        password=args.password,
        database=args.database,
        collection=args.collection
    )
    
    try:
        # 连接数据库
        if not extractor.connect():
            logger.error("无法连接到数据库，程序退出")
            return
        
        # 提取和解压数据
        output_file = extractor.extract_and_decompress(
            device_id=args.device_id,
            start_time=args.start_time,
            end_time=args.end_time,
            output_dir=args.output_dir
        )
        
        if output_file:
            print(f"✅ 数据提取成功！输出文件: {output_file}")
        else:
            print("❌ 数据提取失败！")
            
    finally:
        # 断开连接
        extractor.disconnect()

def extract_data_interactive():
    """交互式数据提取函数"""
    print("=" * 60)
    print("MongoDB数据提取和解压缩工具")
    print("=" * 60)
    
    # 获取用户输入
    device_id = input("请输入设备ID: ").strip()
    if not device_id:
        print("错误: 设备ID不能为空")
        return
    
    start_time = input("请输入开始时间 (格式: YYYY-MM-DD): ").strip()
    end_time = input("请输入结束时间 (格式: YYYY-MM-DD): ").strip()
    
    # 验证时间格式
    try:
        datetime.strptime(start_time, "%Y-%m-%d")
        datetime.strptime(end_time, "%Y-%m-%d")
    except ValueError as e:
        print(f"错误: 时间格式不正确 - {e}")
        print("请使用格式: YYYY-MM-DD")
        return
    
    output_dir = input("请输入输出目录 (默认: output): ").strip()
    if not output_dir:
        output_dir = "output"
    
    # 创建提取器
    extractor = MongoDBExtractor()
    
    try:
        print("\n正在连接数据库...")
        if not extractor.connect():
            print("❌ 无法连接到数据库")
            return
        
        print("✅ 数据库连接成功")
        print(f"\n开始提取数据...")
        print(f"设备ID: {device_id}")
        print(f"时间范围: {start_time} ~ {end_time}")
        
        # 提取和解压数据
        output_file = extractor.extract_and_decompress(
            device_id=device_id,
            start_time=start_time,
            end_time=end_time,
            output_dir=output_dir
        )
        
        if output_file:
            print(f"\n✅ 数据提取成功！")
            print(f"输出文件: {output_file}")
        else:
            print("\n❌ 数据提取失败！")
            
    finally:
        extractor.disconnect()

if __name__ == "__main__":
    # 如果有命令行参数，使用命令行模式
    if len(sys.argv) > 1:
        main()
    else:
        # 否则使用交互式模式
        extract_data_interactive()