#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MongoDB数据提取和解压缩脚本
从MongoDB中提取指定时间范围内的设备数据，进行解压缩处理，并生成JSON文件
"""

import json
import os
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import pymongo
from pymongo import MongoClient
from decompressed_comp_ppg_data import decompressed_and_upsampled_ppg_data
import pytz

# 定义时区
BEIJING_TZ = pytz.timezone('Asia/Shanghai')
UTC_TZ = pytz.utc

def beijing_to_utc(dt):
    """将北京时间转换为UTC时间"""
    return BEIJING_TZ.localize(dt).astimezone(UTC_TZ)

def utc_to_beijing_str(dt):
    """将UTC时间转换为北京时间字符串"""
    if not dt:
        return ""
    # 假设dt是来自MongoDB的朴素UTC时间
    dt_utc = dt.replace(tzinfo=pytz.utc)
    return dt_utc.astimezone(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')

# MongoDB配置
MONGO_CONFIG = {
    'host': 'mongoreplica29ed1d62f12a1.mongodb.cn-beijing.volces.com',
    'port': 3717,
    'username': 'apps-wr',
    'password': 'eEcc7U!nNM3ivzC^f',
    'database': 'andun_1',
    'collection': 'device_collect_compress_data'
}

class MongoDataExtractor:
    """MongoDB数据提取器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化MongoDB连接
        
        Args:
            config: MongoDB配置字典
        """
        self.config = config
        self.client = None
        self.db = None
        self.collection = None
        
    def connect(self) -> bool:
        """
        连接到MongoDB
        
        Returns:
            bool: 连接是否成功
        """
        try:
            # 构建连接URI，指定authSource=admin
            uri = f"mongodb://{self.config['username']}:{self.config['password']}@{self.config['host']}:{self.config['port']}/{self.config['database']}?authSource=admin"
            
            # 创建客户端连接
            self.client = MongoClient(uri, serverSelectionTimeoutMS=5000)
            
            # 测试连接
            self.client.server_info()
            
            # 获取数据库和集合
            self.db = self.client[self.config['database']]
            self.collection = self.db[self.config['collection']]
            
            print(f"成功连接到MongoDB: {self.config['host']}:{self.config['port']}")
            return True
            
        except Exception as e:
            print(f"连接MongoDB失败: {e}")
            return False
    
    def disconnect(self):
        """断开MongoDB连接"""
        if self.client:
            self.client.close()
            print("已断开MongoDB连接")
    
    def get_device_ids(self, limit: Optional[int] = None) -> List[str]:
        """
        获取所有设备ID（随机提取）
        
        Args:
            limit: 限制返回的设备ID数量，None表示不限制
            
        Returns:
            List[str]: 随机选择的设备ID列表
        """
        try:
            # 获取所有唯一的deviceId
            device_ids = self.collection.distinct("deviceId")
            
            if limit and limit > 0:
                # 随机选择指定数量的设备ID
                if len(device_ids) > limit:
                    device_ids = random.sample(device_ids, limit)
                
            print(f"找到 {len(device_ids)} 个设备ID")
            return device_ids
            
        except Exception as e:
            print(f"获取设备ID失败: {e}")
            return []
    
    def extract_device_data(self, device_id: str, days_ago: int = 1) -> List[Dict[str, Any]]:
        """
        提取指定设备的数据（按天数）
        
        Args:
            device_id: 设备ID
            days_ago: 提取多少天前的数据，默认1天
            
        Returns:
            List[Dict]: 设备数据列表
        """
        try:
            # 计算北京时间范围
            end_time_beijing = datetime.now()
            start_time_beijing = end_time_beijing - timedelta(days=days_ago)

            # 转换为UTC时间进行查询
            start_time_utc = beijing_to_utc(start_time_beijing)
            end_time_utc = beijing_to_utc(end_time_beijing)

            # 构建查询条件
            query = {
                "deviceId": device_id,
                "createTime": {
                    "$gte": start_time_utc,
                    "$lte": end_time_utc
                }
            }
            
            # 查询数据
            cursor = self.collection.find(query)
            data_list = list(cursor)
            
            print(f"设备 {device_id} 找到 {len(data_list)} 条数据")
            return data_list
            
        except Exception as e:
            print(f"提取设备 {device_id} 数据失败: {e}")
            return []
    
    def extract_device_data_by_date(self, device_id: str, start_date: str, end_date: str = None) -> List[Dict[str, Any]]:
        """
        提取指定设备在指定日期范围内的数据
        
        Args:
            device_id: 设备ID
            start_date: 开始日期，格式：YYYY-MM-DD
            end_date: 结束日期，格式：YYYY-MM-DD，如果为None则使用当前日期
            
        Returns:
            List[Dict]: 设备数据列表
        """
        try:
            # 解析北京时间
            start_time_beijing = datetime.strptime(start_date, "%Y-%m-%d")
            if end_date:
                end_time_beijing = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
            else:
                end_time_beijing = datetime.now()

            # 转换为UTC时间进行查询
            start_time_utc = beijing_to_utc(start_time_beijing)
            end_time_utc = beijing_to_utc(end_time_beijing)

            # 构建查询条件
            query = {
                "deviceId": device_id,
                "createTime": {
                    "$gte": start_time_utc,
                    "$lte": end_time_utc
                }
            }
            
            # 查询数据
            cursor = self.collection.find(query)
            data_list = list(cursor)
            
            date_range = f"{start_date} 到 {end_date if end_date else '今天'}"
            print(f"设备 {device_id} 在 {date_range} 找到 {len(data_list)} 条数据")
            return data_list
            
        except ValueError as e:
            print(f"日期格式错误: {e}")
            return []
        except Exception as e:
            print(f"提取设备 {device_id} 数据失败: {e}")
            return []

class DataProcessor:
    """数据处理器"""
    
    @staticmethod
    def process_device_data(device_id: str, raw_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        处理单个设备的数据
        
        Args:
            device_id: 设备ID
            raw_data: 原始数据列表
            
        Returns:
            Dict: 处理后的数据
        """
        try:
            if not raw_data:
                return {
                    "deviceId": device_id,
                    "dataCount": 0,
                    "processedData": [],
                    "error": "没有找到数据"
                }
            
            # 提取collectData进行解压缩，排除为空的记录
            collect_data_list = []
            for item in raw_data:
                if "collectData" in item and item["collectData"]:
                    collect_data_list.append({
                        "collectTime": item.get("collectTime"),
                        "collectData": item["collectData"],
                        "createTime": item.get("createTime"),
                        "deviceId": item.get("deviceId")
                    })
            
            if not collect_data_list:
                return {
                    "deviceId": device_id,
                    "dataCount": len(raw_data),
                    "processedData": [],
                    "error": "没有找到collectData字段"
                }
            
            # 使用现有的解压缩函数
            print(f"开始解压缩设备 {device_id} 的 {len(collect_data_list)} 条数据...")
            decompressed_data = decompressed_and_upsampled_ppg_data(collect_data_list)
            
            # 构建结果数据
            processed_data = []
            for i, (original_item, decompressed_item) in enumerate(zip(collect_data_list, decompressed_data)):
                item = {
                    "index": i,
                    "collectTime": original_item.get("collectTime"),
                    "createTime": original_item.get("createTime"),
                    "collectTime_beijing": utc_to_beijing_str(original_item.get("collectTime")),
                    "createTime_beijing": utc_to_beijing_str(original_item.get("createTime")),
                    "originalDataSize": len(original_item["collectData"]) if original_item["collectData"] else 0,
                    "decompressedData": decompressed_item,
                    "decompressedDataSize": len(decompressed_item) if decompressed_item else 0,
                    "success": decompressed_item is not None
                }
                processed_data.append(item)
            
            return {
                "deviceId": device_id,
                "dataCount": len(raw_data),
                "collectDataCount": len(collect_data_list),
                "processedData": processed_data,
                "processTime": datetime.now().isoformat(),
                "success": True
            }
            
        except Exception as e:
            print(f"处理设备 {device_id} 数据时出错: {e}")
            return {
                "deviceId": device_id,
                "dataCount": len(raw_data) if raw_data else 0,
                "processedData": [],
                "error": str(e),
                "success": False
            }

class JSONExporter:
    """JSON文件导出器"""
    
    def __init__(self, output_dir: str = "output"):
        """
        初始化导出器
        
        Args:
            output_dir: 输出目录
        """
        self.output_dir = output_dir
        self._ensure_output_dir()
    
    def _ensure_output_dir(self):
        """确保输出目录存在"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            print(f"创建输出目录: {self.output_dir}")
    
    def export_device_data(self, device_data: Dict[str, Any]) -> str:
        """
        导出单个设备的数据到JSON文件
        
        Args:
            device_data: 设备数据字典
            
        Returns:
            str: 生成的文件路径
        """
        try:
            device_id = device_data.get("deviceId", "unknown")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{device_id}_{timestamp}.json"
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(device_data, f, ensure_ascii=False, indent=4, default=str)
            
            print(f"已导出设备 {device_id} 数据到: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"导出设备数据失败: {e}")
            return ""

def main():
    """主函数"""
    print("=" * 60)
    print("MongoDB数据提取和解压缩工具")
    print("=" * 60)
    
    # 选择提取模式
    print("\n请选择数据提取模式:")
    print("1. 批量提取（处理多个设备）")
    print("2. 指定设备提取（单个设备ID）")
    
    mode = input("请输入选择（1或2，回车默认为1）: ").strip()
    mode = mode if mode in ['1', '2'] else '1'
    
    if mode == '2':
        # 指定设备模式
        device_id = input("请输入设备ID: ").strip()
        if not device_id:
            print("设备ID不能为空！")
            return
        
        # 选择时间提取方式
        print("\n请选择时间提取方式:")
        print("1. 按天数提取（从今天往前推几天）")
        print("2. 按日期范围提取（指定开始和结束日期）")
        
        time_mode = input("请输入选择（1或2，回车默认为1）: ").strip()
        time_mode = time_mode if time_mode in ['1', '2'] else '1'
        
        # 初始化组件
        extractor = MongoDataExtractor(MONGO_CONFIG)
        processor = DataProcessor()
        exporter = JSONExporter()
        
        # 连接数据库
        if not extractor.connect():
            return
        
        if time_mode == '1':
            # 按天数提取
            try:
                days_ago = input("请输入提取多少天前的数据（回车默认1天）: ").strip()
                days_ago = int(days_ago) if days_ago else 1
            except ValueError:
                days_ago = 1
                print("输入无效，使用默认值1天")
            
            # 提取单个设备数据
            device_data = extractor.extract_device_data(device_id, days_ago)
            
        else:
            # 按日期范围提取
            start_date = input("请输入开始日期（格式：YYYY-MM-DD）: ").strip()
            if not start_date:
                print("开始日期不能为空！")
                return
            
            end_date = input("请输入结束日期（格式：YYYY-MM-DD，回车默认为今天）: ").strip()
            end_date = end_date if end_date else None
            
            # 提取单个设备数据
            device_data = extractor.extract_device_data_by_date(device_id, start_date, end_date)
        
        if device_data:
            # 处理数据
            processed_data = processor.process_device_data(device_id, device_data)
            
            # 导出数据
            output_file = exporter.export_device_data(processed_data)
            if output_file:
                print(f"\n✓ 设备 {device_id} 数据处理完成")
                print(f"输出文件: {output_file}")
            else:
                print(f"✗ 设备 {device_id} 数据导出失败")
        else:
            print(f"✗ 设备 {device_id} 没有找到数据")
    
    else:
        # 批量提取模式（原有逻辑）
        # 获取用户输入
        try:
            max_devices = input("请输入要处理的设备数量（回车默认处理所有设备）: ").strip()
            max_devices = int(max_devices) if max_devices else None
        except ValueError:
            max_devices = None
            print("输入无效，将处理所有设备")
        
        try:
            days_ago = input("请输入提取多少天前的数据（回车默认1天）: ").strip()
            days_ago = int(days_ago) if days_ago else 1
        except ValueError:
            days_ago = 1
            print("输入无效，使用默认值1天")
        
        # 初始化组件
        extractor = MongoDataExtractor(MONGO_CONFIG)
        processor = DataProcessor()
        exporter = JSONExporter()
        
        # 连接数据库
        if not extractor.connect():
            return
        
        # 获取设备ID列表
        device_ids = extractor.get_device_ids(max_devices)
        
        if not device_ids:
            print("没有找到设备ID")
            return
        
        # 处理每个设备的数据
        success_count = 0
        total_count = len(device_ids)
        
        for i, device_id in enumerate(device_ids, 1):
            print(f"\n处理设备 {i}/{total_count}: {device_id}")
            
            # 提取设备数据
            device_data = extractor.extract_device_data(device_id, days_ago)
            
            if device_data:
                # 处理数据
                processed_data = processor.process_device_data(device_id, device_data)
                
                # 导出数据
                output_file = exporter.export_device_data(processed_data)
                if output_file:
                    success_count += 1
                    print(f"✓ 设备 {device_id} 处理完成")
                else:
                    print(f"✗ 设备 {device_id} 导出失败")
            else:
                print(f"✗ 设备 {device_id} 没有数据")
        
        print(f"\n" + "=" * 60)
        print(f"处理完成！成功: {success_count}/{total_count}")
        print("=" * 60)
    
    try:
        # 连接数据库
        if not extractor.connect():
            return
        
    except KeyboardInterrupt:
        print("\n用户中断操作")
    except Exception as e:
        print(f"程序执行出错: {e}")
    finally:
        # 关闭数据库连接
        if 'extractor' in locals():
            extractor.disconnect()

if __name__ == "__main__":
    main()