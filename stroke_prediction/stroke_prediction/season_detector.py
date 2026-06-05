#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
季节识别模块
基于系统时间自动识别当前季节，并提供季节相关的健康风险信息
"""

import datetime
from typing import Dict, List, Tuple
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SeasonDetector:
    """季节识别器类"""
    
    def __init__(self):
        """初始化季节识别器"""
        # 定义季节划分（北半球标准）
        self.season_ranges = {
            'spring': [(3, 1), (5, 31)],    # 春季：3月1日-5月31日
            'summer': [(6, 1), (8, 31)],    # 夏季：6月1日-8月31日
            'autumn': [(9, 1), (11, 30)],   # 秋季：9月1日-11月30日
            'winter': [(12, 1), (2, 28)]    # 冬季：12月1日-2月28日（29日）
        }
        
        # 季节中文名称映射
        self.season_names = {
            'spring': '春季',
            'summer': '夏季', 
            'autumn': '秋季',
            'winter': '冬季'
        }
        
        # 季节特征描述
        self.season_characteristics = {
            'spring': {
                'temperature': '温和',
                'temperature_range': '15-25°C',
                'humidity': '适中',
                'weather_pattern': '多变',
                'description': '万物复苏，气温回升，但天气多变'
            },
            'summer': {
                'temperature': '炎热',
                'temperature_range': '25-35°C',
                'humidity': '较高',
                'weather_pattern': '稳定',
                'description': '高温高湿，阳光充足，雷雨频繁'
            },
            'autumn': {
                'temperature': '凉爽',
                'temperature_range': '10-20°C',
                'humidity': '干燥',
                'weather_pattern': '稳定',
                'description': '秋高气爽，温度适宜，空气干燥'
            },
            'winter': {
                'temperature': '寒冷',
                'temperature_range': '0-10°C',
                'humidity': '干燥',
                'weather_pattern': '稳定',
                'description': '寒冷干燥，日照时间短，易有雾霾'
            }
        }
        
        # 季节健康风险
        self.season_health_risks = {
            'spring': [
                '过敏性疾病高发（花粉过敏、哮喘）',
                '呼吸道感染风险增加',
                '情绪波动（春季抑郁）',
                '心血管疾病复发风险'
            ],
            'summer': [
                '中暑和热射病风险',
                '肠胃疾病高发',
                '皮肤病增多',
                '心脑血管疾病急性发作',
                '脱水风险增加'
            ],
            'autumn': [
                '呼吸道疾病高发',
                '关节炎症状加重',
                '季节性抑郁症',
                '心血管疾病风险上升'
            ],
            'winter': [
                '流感和感冒高发',
                '心脑血管疾病急性期',
                '关节疼痛加重',
                '季节性情感障碍',
                '维生素D缺乏'
            ]
        }
        
        # 季节健康建议
        self.season_health_advice = {
            'spring': [
                '注意防过敏，外出戴口罩',
                '适量运动，增强免疫力',
                '保持室内通风，预防感冒',
                '调节情绪，保持心情愉快'
            ],
            'summer': [
                '防暑降温，多喝水',
                '注意饮食卫生，预防肠胃病',
                '避免长时间暴晒',
                '保持充足睡眠',
                '适当补充电解质'
            ],
            'autumn': [
                '注意保暖，预防感冒',
                '适当运动，增强体质',
                '保持室内湿度',
                '调节作息，预防抑郁',
                '补充维生素'
            ],
            'winter': [
                '注意保暖，预防感冒',
                '适量运动，但避免过度',
                '保持室内温湿度适宜',
                '补充维生素D',
                '关注心理健康'
            ]
        }
    
    def get_current_season(self, date: datetime.date = None) -> str:
        """
        获取当前季节
        
        Args:
            date: 指定日期，默认为当前日期
            
        Returns:
            str: 季节英文名称
        """
        if date is None:
            date = datetime.date.today()
        
        month = date.month
        day = date.day
        
        # 判断季节
        if (month == 3 and day >= 1) or month in [4, 5]:
            return 'spring'
        elif month in [6, 7, 8]:
            return 'summer'
        elif month in [9, 10, 11]:
            return 'autumn'
        else:  # 12, 1, 2月
            return 'winter'
    
    def get_season_info(self, season: str = None) -> Dict:
        """
        获取指定季节的详细信息
        
        Args:
            season: 季节名称，默认为当前季节
            
        Returns:
            Dict: 包含季节详细信息的字典
        """
        if season is None:
            season = self.get_current_season()
        
        return {
            'season': season,
            'name': self.season_names[season],
            'chinese_name': self.season_names[season],
            'description': self.season_characteristics[season]['description'],
            'temperature_range': self.season_characteristics[season]['temperature_range'],
            'health_risks': self.season_health_risks[season],
            'health_advice': self.season_health_advice[season]
        }
    
    def get_disease_risk_factor(self, disease: str, season: str = None) -> float:
        """
        获取特定疾病在指定季节的风险因子
        
        Args:
            disease: 疾病名称
            season: 季节名称，默认为当前季节
            
        Returns:
            float: 风险因子（1.0为基准，>1.0表示风险增加，<1.0表示风险降低）
        """
        if season is None:
            season = self.get_current_season()
        
        # 定义各疾病的季节风险因子
        seasonal_risk_factors = {
            'stroke': {
                'spring': 1.1,  # 春季血压波动大
                'summer': 1.2,  # 夏季脱水风险
                'autumn': 1.1,  # 秋季血压上升
                'winter': 1.3   # 冬季最高风险
            },
            'hypertension': {
                'spring': 1.1,
                'summer': 1.0,
                'autumn': 1.2,
                'winter': 1.3
            },
            'diabetes': {
                'spring': 1.0,
                'summer': 1.1,  # 夏季饮食不规律
                'autumn': 1.0,
                'winter': 1.2   # 冬季活动减少
            },
            'depression': {
                'spring': 1.1,  # 春季抑郁高发
                'summer': 0.9,  # 夏季阳光充足
                'autumn': 1.2,  # 秋季情绪低落
                'winter': 1.4   # 冬季抑郁最严重
            },
            'anxiety': {
                'spring': 1.2,  # 春季焦虑高发
                'summer': 1.0,
                'autumn': 1.1,
                'winter': 1.2
            },
            'heart_disease': {
                'spring': 1.1,
                'summer': 1.1,
                'autumn': 1.1,
                'winter': 1.3
            },
            'coronary_heart_disease': {
                'spring': 1.1,
                'summer': 1.1,
                'autumn': 1.1,
                'winter': 1.3
            },
            'arrhythmia': {
                'spring': 1.0,
                'summer': 1.1,
                'autumn': 1.0,
                'winter': 1.2
            },
            'kidney_disease': {
                'spring': 1.0,
                'summer': 1.2,  # 夏季脱水风险
                'autumn': 1.0,
                'winter': 1.1
            },
            'alzheimer': {
                'spring': 1.0,
                'summer': 1.0,
                'autumn': 1.1,
                'winter': 1.2   # 冬季认知功能下降
            },
            'gout': {
                'spring': 1.1,
                'summer': 1.2,  # 夏季啤酒海鲜消费增加
                'autumn': 1.1,
                'winter': 1.0
            },
            'parkinson': {
                'spring': 1.0,
                'summer': 1.0,
                'autumn': 1.1,
                'winter': 1.2
            },
            'heart_failure': {
                'spring': 1.1,
                'summer': 1.1,
                'autumn': 1.1,
                'winter': 1.3
            },
            'bronchial_asthma': {
                'spring': 1.4,  # 春季过敏高发，风险提高
                'summer': 1.0,  # 夏季风险相对较低
                'autumn': 1.3,  # 秋季过敏，风险提高
                'winter': 1.3   # 冬季呼吸道感染，风险提高
            },
            'bronchiectasis': {
                'spring': 1.3,  # 春季呼吸道疾病高发，风险提高
                'summer': 1.0,  # 夏季风险相对较低
                'autumn': 1.2,  # 秋季呼吸道疾病增多，风险提高
                'winter': 1.4   # 冬季呼吸道感染高发，风险显著提高
            }
        }
        
        return seasonal_risk_factors.get(disease, {}).get(season, 1.0)

    def get_seasonal_risk_factor(self, disease: str, date: datetime.date = None) -> float:
        """
        获取特定疾病的季节风险因子
        
        Args:
            disease: 疾病名称
            date: 指定日期，默认为当前日期
            
        Returns:
            float: 风险因子（1.0为基准，>1.0表示风险增加，<1.0表示风险降低）
        """
        if date is None:
            date = datetime.date.today()
        
        season = self.get_current_season(date)
        
        # 定义各疾病的季节风险因子
        seasonal_risk_factors = {
            'stroke': {
                'spring': 1.1,  # 春季血压波动大
                'summer': 1.2,  # 夏季脱水风险
                'autumn': 1.1,  # 秋季血压上升
                'winter': 1.3   # 冬季最高风险
            },
            'heart_failure': {
                'spring': 1.0,
                'summer': 1.2,  # 高温负荷
                'autumn': 1.1,
                'winter': 1.3   # 寒冷刺激
            },
            'hypertension': {
                'spring': 1.1,
                'summer': 0.9,  # 血管扩张
                'autumn': 1.2,
                'winter': 1.4   # 血管收缩
            },
            'diabetes': {
                'spring': 1.0,
                'summer': 1.1,  # 饮食变化
                'autumn': 1.0,
                'winter': 1.2   # 活动减少
            },
            'arrhythmia': {
                'spring': 1.1,
                'summer': 1.2,
                'autumn': 1.0,
                'winter': 1.2
            },
            'depression': {
                'spring': 1.2,  # 春季抑郁
                'summer': 0.8,
                'autumn': 1.3,  # 秋季抑郁
                'winter': 1.5   # 冬季抑郁最严重
            },
            'anxiety': {
                'spring': 1.2,
                'summer': 0.9,
                'autumn': 1.1,
                'winter': 1.3
            },
            'gout': {
                'spring': 1.0,
                'summer': 1.3,  # 啤酒海鲜季节
                'autumn': 1.1,
                'winter': 0.9
            },
            'alzheimer': {
                'spring': 1.0,
                'summer': 1.1,
                'autumn': 1.0,
                'winter': 1.2   # 日照不足
            },
            'parkinson': {
                'spring': 1.0,
                'summer': 1.1,
                'autumn': 1.0,
                'winter': 1.2
            },
            'bronchial_asthma': {
                'spring': 1.4,  # 春季过敏高发，风险提高
                'summer': 1.0,  # 夏季风险相对较低
                'autumn': 1.3,  # 秋季过敏，风险提高
                'winter': 1.3   # 冬季呼吸道感染，风险提高
            },
            'bronchiectasis': {
                'spring': 1.3,  # 春季呼吸道疾病高发，风险提高
                'summer': 1.0,  # 夏季风险相对较低
                'autumn': 1.2,  # 秋季呼吸道疾病增多，风险提高
                'winter': 1.4   # 冬季呼吸道感染高发，风险显著提高
            }
        }
        
        # 默认风险因子
        default_factors = {
            'spring': 1.0,
            'summer': 1.0,
            'autumn': 1.0,
            'winter': 1.1
        }
        
        disease_factors = seasonal_risk_factors.get(disease.lower(), default_factors)
        return disease_factors.get(season, 1.0)
    
    def get_seasonal_recommendations(self, diseases: List[str], date: datetime.date = None) -> Dict:
        """
        根据疾病列表和季节获取个性化建议
        
        Args:
            diseases: 疾病列表
            date: 指定日期，默认为当前日期
            
        Returns:
            Dict: 个性化建议
        """
        if date is None:
            date = datetime.date.today()
        
        season_info = self.get_season_info(date)
        season = season_info['season_en']
        
        # 基础季节建议
        recommendations = {
            'season_info': season_info,
            'general_advice': self.season_health_advice[season],
            'specific_advice': [],
            'high_risk_diseases': []
        }
        
        # 针对特定疾病的建议
        disease_specific_advice = {
            'stroke': {
                'spring': '注意血压监测，避免情绪激动',
                'summer': '充分补水，避免脱水，注意防暑',
                'autumn': '定期测量血压，注意保暖',
                'winter': '严格控制血压，避免寒冷刺激'
            },
            'heart_failure': {
                'spring': '适量运动，避免过度劳累',
                'summer': '避免高温环境，控制水盐摄入',
                'autumn': '注意保暖，预防感冒',
                'winter': '避免寒冷刺激，室内保温'
            },
            'hypertension': {
                'spring': '监测血压变化，调整用药',
                'summer': '适当减少降压药物（遵医嘱）',
                'autumn': '加强血压监测',
                'winter': '严格控制血压，注意保暖'
            },
            'depression': {
                'spring': '多参加户外活动，保持社交',
                'summer': '保持规律作息，适度运动',
                'autumn': '增加光照时间，调节情绪',
                'winter': '补充维生素D，寻求专业帮助'
            }
        }
        
        for disease in diseases:
            risk_factor = self.get_seasonal_risk_factor(disease, date)
            
            # 高风险疾病
            if risk_factor > 1.2:
                recommendations['high_risk_diseases'].append({
                    'disease': disease,
                    'risk_factor': risk_factor,
                    'risk_level': '高风险'
                })
            
            # 特定建议
            if disease.lower() in disease_specific_advice:
                advice = disease_specific_advice[disease.lower()].get(season)
                if advice:
                    recommendations['specific_advice'].append({
                        'disease': disease,
                        'advice': advice
                    })
        
        return recommendations
    
    def is_leap_year(self, year: int) -> bool:
        """
        判断是否为闰年
        
        Args:
            year: 年份
            
        Returns:
            bool: 是否为闰年
        """
        return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
    
    def get_season_progress(self, date: datetime.date = None) -> Dict:
        """
        获取当前季节的进度信息
        
        Args:
            date: 指定日期，默认为当前日期
            
        Returns:
            Dict: 季节进度信息
        """
        if date is None:
            date = datetime.date.today()
        
        season = self.get_current_season(date)
        year = date.year
        
        # 计算季节开始和结束日期
        if season == 'spring':
            start_date = datetime.date(year, 3, 1)
            end_date = datetime.date(year, 5, 31)
        elif season == 'summer':
            start_date = datetime.date(year, 6, 1)
            end_date = datetime.date(year, 8, 31)
        elif season == 'autumn':
            start_date = datetime.date(year, 9, 1)
            end_date = datetime.date(year, 11, 30)
        else:  # winter
            if date.month >= 12:
                start_date = datetime.date(year, 12, 1)
                end_date = datetime.date(year + 1, 2, 28 + (1 if self.is_leap_year(year + 1) else 0))
            else:
                start_date = datetime.date(year - 1, 12, 1)
                end_date = datetime.date(year, 2, 28 + (1 if self.is_leap_year(year) else 0))
        
        # 计算进度
        total_days = (end_date - start_date).days + 1
        elapsed_days = (date - start_date).days + 1
        progress = min(elapsed_days / total_days * 100, 100)
        
        return {
            'season': season,
            'season_cn': self.season_names[season],
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'current_date': date.strftime('%Y-%m-%d'),
            'total_days': total_days,
            'elapsed_days': elapsed_days,
            'remaining_days': total_days - elapsed_days,
            'progress_percent': round(progress, 1)
        }

# 创建全局实例
season_detector = SeasonDetector()

def get_current_season_info():
    """获取当前季节信息的便捷函数"""
    return season_detector.get_season_info()

def get_seasonal_risk_adjustment(disease: str):
    """获取疾病季节风险调整因子的便捷函数"""
    return season_detector.get_seasonal_risk_factor(disease)

if __name__ == "__main__":
    # 测试代码
    detector = SeasonDetector()
    
    # 测试当前季节
    current_info = detector.get_season_info()
    print("=== 当前季节信息 ===")
    print(f"日期: {current_info['date']}")
    print(f"季节: {current_info['season_cn']} ({current_info['season_en']})")
    print(f"特征: {current_info['characteristics']['description']}")
    
    print("\n=== 健康风险 ===")
    for risk in current_info['health_risks']:
        print(f"• {risk}")
    
    print("\n=== 健康建议 ===")
    for advice in current_info['health_advice']:
        print(f"• {advice}")
    
    # 测试季节进度
    progress = detector.get_season_progress()
    print(f"\n=== 季节进度 ===")
    print(f"{progress['season_cn']}进度: {progress['progress_percent']}%")
    print(f"剩余天数: {progress['remaining_days']}天")
    
    # 测试疾病风险因子
    print(f"\n=== 疾病季节风险因子 ===")
    diseases = ['stroke', 'hypertension', 'depression', 'diabetes']
    for disease in diseases:
        factor = detector.get_seasonal_risk_factor(disease)
        print(f"{disease}: {factor}")