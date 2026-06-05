#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级医学风险分析器
结合医学逻辑与算法逻辑，分析心梗和脑卒中风险
基于血管功能、心律、炎症、血流等多维度指标进行综合评估
"""

import json
import os
import math
import numpy as np
import argparse
import glob
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AdvancedMedicalRiskAnalyzer:
    """高级医学风险分析器"""
    
    def __init__(self):
        """初始化风险分析器"""
        # 心梗风险权重配置（基于医学文献和临床经验）
        self.mi_weights = {
            'vascular_function': 0.25,    # 血管功能权重
            'arrhythmia': 0.20,          # 心律失常权重
            'inflammation': 0.20,         # 炎症指标权重
            'blood_flow': 0.15,          # 血流动力学权重
            'sleep_apnea': 0.10,         # 睡眠呼吸暂停权重
            'bp_variability': 0.10       # 血压变异性权重
        }
        
        # 脑卒中风险权重配置
        self.stroke_weights = {
            'vascular_function': 0.30,    # 血管功能权重（脑卒中更依赖血管状态）
            'arrhythmia': 0.25,          # 心律失常权重（房颤是重要因素）
            'inflammation': 0.15,         # 炎症指标权重
            'blood_flow': 0.15,          # 血流动力学权重
            'bp_variability': 0.15       # 血压变异性权重（脑卒中重要因素）
        }
        
        # 风险阈值配置
        self.risk_thresholds = {
            'low': 30,
            'moderate': 60,
            'high': 80,
            'very_high': 90
        }
        
    def calculate_vascular_function_risk(self, vascular_stats: Dict) -> Dict:
        """计算血管功能风险评分"""
        risk_score = 0
        risk_factors = []
        
        # PWV (脉搏波速度) 风险评估
        pwv_mean = vascular_stats.get('pwv_stats', {}).get('mean', 0)
        if pwv_mean > 12:
            risk_score += 25
            risk_factors.append(f"PWV显著升高 ({pwv_mean:.1f} m/s)")
        elif pwv_mean > 10:
            risk_score += 15
            risk_factors.append(f"PWV轻度升高 ({pwv_mean:.1f} m/s)")
        
        # 血管年龄风险评估
        vascular_age_mean = vascular_stats.get('vascular_age_stats', {}).get('mean', 0)
        if vascular_age_mean > 80:
            risk_score += 20
            risk_factors.append(f"血管年龄显著老化 ({vascular_age_mean:.1f}岁)")
        elif vascular_age_mean > 70:
            risk_score += 12
            risk_factors.append(f"血管年龄轻度老化 ({vascular_age_mean:.1f}岁)")
        
        # AIx (增强指数) 风险评估
        aix_mean = vascular_stats.get('aix_stats', {}).get('mean', 0)
        if aix_mean > 30:
            risk_score += 15
            risk_factors.append(f"动脉硬化指数升高 ({aix_mean:.1f}%)")
        elif aix_mean > 20:
            risk_score += 8
            risk_factors.append(f"动脉硬化指数轻度升高 ({aix_mean:.1f}%)")
        
        # 心率变异性评估
        lf_hf_ratio = vascular_stats.get('lf_hf_ratio_stats', {}).get('mean', 0)
        if lf_hf_ratio > 4:
            risk_score += 10
            risk_factors.append("自主神经功能失衡")
        elif lf_hf_ratio > 2.5:
            risk_score += 5
            risk_factors.append("自主神经功能轻度异常")
        
        return {
            'score': min(risk_score, 100),
            'risk_factors': risk_factors,
            'details': {
                'pwv_mean': pwv_mean,
                'vascular_age_mean': vascular_age_mean,
                'aix_mean': aix_mean,
                'lf_hf_ratio': lf_hf_ratio
            }
        }
    
    def calculate_arrhythmia_risk(self, arrhythmia_stats: Dict) -> Dict:
        """计算心律失常风险评分"""
        risk_score = 0
        risk_factors = []
        
        detection_stats = arrhythmia_stats.get('arrhythmia_detection_statistics', {})
        
        # 房颤检出率风险评估
        afib_rate = detection_stats.get('afib_detection_rate', 0)
        if afib_rate > 0.1:  # 10%以上
            risk_score += 40
            risk_factors.append(f"房颤检出率高 ({afib_rate*100:.1f}%)")
        elif afib_rate > 0.05:  # 5-10%
            risk_score += 25
            risk_factors.append(f"房颤检出率中等 ({afib_rate*100:.1f}%)")
        elif afib_rate > 0:
            risk_score += 10
            risk_factors.append(f"偶发房颤 ({afib_rate*100:.1f}%)")
        
        # 室性早搏检出率
        pvc_rate = detection_stats.get('pvc_detection_rate', 0)
        if pvc_rate > 0.1:
            risk_score += 20
            risk_factors.append(f"室性早搏频发 ({pvc_rate*100:.1f}%)")
        elif pvc_rate > 0.05:
            risk_score += 10
            risk_factors.append(f"室性早搏中等 ({pvc_rate*100:.1f}%)")
        
        # 房性早搏检出率
        pac_rate = detection_stats.get('pac_detection_rate', 0)
        if pac_rate > 0.1:
            risk_score += 15
            risk_factors.append(f"房性早搏频发 ({pac_rate*100:.1f}%)")
        elif pac_rate > 0.05:
            risk_score += 8
            risk_factors.append(f"房性早搏中等 ({pac_rate*100:.1f}%)")
        
        # 正常心律比例
        normal_rate = detection_stats.get('normal_rhythm_rate', 1.0)
        if normal_rate < 0.8:
            risk_score += 15
            risk_factors.append(f"正常心律比例低 ({normal_rate*100:.1f}%)")
        
        return {
            'score': min(risk_score, 100),
            'risk_factors': risk_factors,
            'details': {
                'afib_rate': afib_rate,
                'pvc_rate': pvc_rate,
                'pac_rate': pac_rate,
                'normal_rate': normal_rate
            }
        }
    
    def calculate_inflammation_risk(self, inflammation_stats: Dict) -> Dict:
        """计算炎症风险评分"""
        risk_score = 0
        risk_factors = []
        
        # 平均炎症评分
        avg_inflammation = inflammation_stats.get('average_inflammation_score', 0)
        if avg_inflammation > 4:
            risk_score += 25
            risk_factors.append(f"炎症评分高 ({avg_inflammation:.2f})")
        elif avg_inflammation > 3:
            risk_score += 15
            risk_factors.append(f"炎症评分中等 ({avg_inflammation:.2f})")
        
        # 炎症等级分布
        grade_dist = inflammation_stats.get('inflammation_grade_distribution', {})
        moderate_pct = grade_dist.get('moderate', {}).get('percentage', 0)
        if moderate_pct > 50:
            risk_score += 15
            risk_factors.append(f"中度炎症比例高 ({moderate_pct:.1f}%)")
        
        # HRV统计
        hrv_stats = inflammation_stats.get('hrv_statistics', {})
        avg_rmssd = hrv_stats.get('average_rmssd', 0)
        if avg_rmssd < 20:
            risk_score += 20
            risk_factors.append("心率变异性显著降低")
        elif avg_rmssd < 30:
            risk_score += 10
            risk_factors.append("心率变异性轻度降低")
        
        # 灌注统计
        perfusion_stats = inflammation_stats.get('perfusion_statistics', {})
        avg_perfusion = perfusion_stats.get('average_perfusion_index', 0)
        if avg_perfusion < 2:
            risk_score += 15
            risk_factors.append("微循环灌注不足")
        
        return {
            'score': min(risk_score, 100),
            'risk_factors': risk_factors,
            'details': {
                'avg_inflammation': avg_inflammation,
                'moderate_pct': moderate_pct,
                'avg_rmssd': avg_rmssd,
                'avg_perfusion': avg_perfusion
            }
        }
    
    def calculate_blood_flow_risk(self, blood_flow_stats: Dict) -> Dict:
        """计算血流动力学风险评分"""
        risk_score = 0
        risk_factors = []
        
        # 血管阻力评估
        resistance_mean = blood_flow_stats.get('vascular_resistance_stats', {}).get('mean', 0)
        if resistance_mean > 10:
            risk_score += 20
            risk_factors.append(f"血管阻力显著增高 ({resistance_mean:.2f})")
        elif resistance_mean > 5:
            risk_score += 10
            risk_factors.append(f"血管阻力轻度增高 ({resistance_mean:.2f})")
        
        # 血流速度评估
        flow_velocity_mean = blood_flow_stats.get('flow_velocity_stats', {}).get('mean', 0)
        if flow_velocity_mean < 5:
            risk_score += 15
            risk_factors.append("血流速度降低")
        
        # 灌注指数评估
        perfusion_mean = blood_flow_stats.get('perfusion_index_stats', {}).get('mean', 0)
        if perfusion_mean < 2:
            risk_score += 15
            risk_factors.append("灌注指数降低")
        elif perfusion_mean > 10:
            risk_score += 10
            risk_factors.append("灌注指数异常升高")
        
        # 血流状态分布
        flow_dist = blood_flow_stats.get('flow_status_distribution', {})
        low_perfusion = flow_dist.get('低灌注', 0)
        total_segments = blood_flow_stats.get('total_analyzed_segments', 1)
        low_perfusion_pct = (low_perfusion / total_segments) * 100 if total_segments > 0 else 0
        
        if low_perfusion_pct > 30:
            risk_score += 25
            risk_factors.append(f"低灌注比例高 ({low_perfusion_pct:.1f}%)")
        elif low_perfusion_pct > 10:
            risk_score += 15
            risk_factors.append(f"低灌注比例中等 ({low_perfusion_pct:.1f}%)")
        
        return {
            'score': min(risk_score, 100),
            'risk_factors': risk_factors,
            'details': {
                'resistance_mean': resistance_mean,
                'flow_velocity_mean': flow_velocity_mean,
                'perfusion_mean': perfusion_mean,
                'low_perfusion_pct': low_perfusion_pct
            }
        }
    
    def calculate_sleep_apnea_risk(self, sleep_analysis: Dict) -> Dict:
        """计算睡眠呼吸暂停风险评分"""
        risk_score = 0
        risk_factors = []
        
        apnea_analysis = sleep_analysis.get('sleep_apnea_analysis', {})
        
        # AHI指数评估
        ahi_index = apnea_analysis.get('ahi_index', 0)
        if ahi_index >= 30:
            risk_score += 30
            risk_factors.append(f"重度睡眠呼吸暂停 (AHI: {ahi_index})")
        elif ahi_index >= 15:
            risk_score += 20
            risk_factors.append(f"中度睡眠呼吸暂停 (AHI: {ahi_index})")
        elif ahi_index >= 5:
            risk_score += 10
            risk_factors.append(f"轻度睡眠呼吸暂停 (AHI: {ahi_index})")
        
        # SpO2评估
        spo2_analysis = sleep_analysis.get('nocturnal_spo2_analysis', {})
        min_spo2 = spo2_analysis.get('min_spo2', 100)
        spo2_below_90 = spo2_analysis.get('spo2_below_90_percent', 0)
        
        if min_spo2 < 85:
            risk_score += 20
            risk_factors.append(f"严重低氧血症 (最低SpO2: {min_spo2:.1f}%)")
        elif min_spo2 < 90:
            risk_score += 15
            risk_factors.append(f"中度低氧血症 (最低SpO2: {min_spo2:.1f}%)")
        
        if spo2_below_90 > 5:
            risk_score += 15
            risk_factors.append(f"低氧时间比例高 ({spo2_below_90:.1f}%)")
        
        return {
            'score': min(risk_score, 100),
            'risk_factors': risk_factors,
            'details': {
                'ahi_index': ahi_index,
                'min_spo2': min_spo2,
                'spo2_below_90': spo2_below_90
            }
        }
    
    def calculate_bp_variability_risk(self, sleep_analysis: Dict) -> Dict:
        """计算血压变异性风险评分"""
        risk_score = 0
        risk_factors = []
        
        bp_analysis = sleep_analysis.get('blood_pressure_rhythm_analysis', {})
        
        # 血压变异性评估
        bp_var = bp_analysis.get('bp_variability', {})
        cv = bp_var.get('coefficient_of_variation', 0)
        
        if cv > 20:
            risk_score += 25
            risk_factors.append(f"血压变异性显著增高 (CV: {cv:.1f}%)")
        elif cv > 15:
            risk_score += 15
            risk_factors.append(f"血压变异性轻度增高 (CV: {cv:.1f}%)")
        
        # 昼夜节律评估
        dipping = bp_analysis.get('nocturnal_dipping', {})
        dipping_pattern = dipping.get('dipping_pattern', '')
        dipping_pct = dipping.get('dipping_percentage', 0)
        
        if dipping_pattern == 'reverse_dipper':
            risk_score += 20
            risk_factors.append("反杓型血压模式")
        elif dipping_pattern == 'non_dipper':
            risk_score += 15
            risk_factors.append("非杓型血压模式")
        elif abs(dipping_pct) < 5:
            risk_score += 10
            risk_factors.append("血压昼夜节律异常")
        
        return {
            'score': min(risk_score, 100),
            'risk_factors': risk_factors,
            'details': {
                'cv': cv,
                'dipping_pattern': dipping_pattern,
                'dipping_pct': dipping_pct
            }
        }
    
    def calculate_mi_risk(self, data: Dict, time_period: int = 7) -> Dict:
        """计算心梗风险评分"""
        # 计算各维度风险评分
        vascular_risk = self.calculate_vascular_function_risk(data.get('vascular_function_statistics', {}))
        arrhythmia_risk = self.calculate_arrhythmia_risk(data.get('arrhythmia_statistics', {}))
        inflammation_risk = self.calculate_inflammation_risk(data.get('inflammation_statistics', {}))
        blood_flow_risk = self.calculate_blood_flow_risk(data.get('blood_flow_statistics', {}))
        sleep_risk = self.calculate_sleep_apnea_risk(data.get('sleep_analysis', {}))
        bp_risk = self.calculate_bp_variability_risk(data.get('sleep_analysis', {}))
        
        # 加权计算总风险评分
        total_score = (
            vascular_risk['score'] * self.mi_weights['vascular_function'] +
            arrhythmia_risk['score'] * self.mi_weights['arrhythmia'] +
            inflammation_risk['score'] * self.mi_weights['inflammation'] +
            blood_flow_risk['score'] * self.mi_weights['blood_flow'] +
            sleep_risk['score'] * self.mi_weights['sleep_apnea'] +
            bp_risk['score'] * self.mi_weights['bp_variability']
        )
        
        # 时间因子调整（7日vs30日）
        time_factor = 1.0 if time_period == 7 else 1.3  # 30日风险相对更高
        adjusted_score = min(total_score * time_factor, 100)
        
        # 风险等级判定
        if adjusted_score >= self.risk_thresholds['very_high']:
            risk_level = '极高风险'
        elif adjusted_score >= self.risk_thresholds['high']:
            risk_level = '高风险'
        elif adjusted_score >= self.risk_thresholds['moderate']:
            risk_level = '中等风险'
        else:
            risk_level = '低风险'
        
        # 风险概率计算（基于logistic回归模型）
        risk_probability = 1 / (1 + math.exp(-(adjusted_score - 50) / 15))
        
        # 收集所有风险因素
        all_risk_factors = []
        all_risk_factors.extend(vascular_risk['risk_factors'])
        all_risk_factors.extend(arrhythmia_risk['risk_factors'])
        all_risk_factors.extend(inflammation_risk['risk_factors'])
        all_risk_factors.extend(blood_flow_risk['risk_factors'])
        all_risk_factors.extend(sleep_risk['risk_factors'])
        all_risk_factors.extend(bp_risk['risk_factors'])
        
        return {
            'risk_score': round(adjusted_score, 2),
            'risk_level': risk_level,
            'risk_probability': round(risk_probability * 100, 2),
            'time_period_days': time_period,
            'risk_factors': all_risk_factors,
            'component_scores': {
                'vascular_function': vascular_risk,
                'arrhythmia': arrhythmia_risk,
                'inflammation': inflammation_risk,
                'blood_flow': blood_flow_risk,
                'sleep_apnea': sleep_risk,
                'bp_variability': bp_risk
            },
            'weights_used': self.mi_weights,
            'calculation_method': 'weighted_sum_with_logistic_probability'
        }
    
    def calculate_stroke_risk(self, data: Dict, time_period: int = 7) -> Dict:
        """计算脑卒中风险评分"""
        # 计算各维度风险评分（脑卒中不包括睡眠呼吸暂停）
        vascular_risk = self.calculate_vascular_function_risk(data.get('vascular_function_statistics', {}))
        arrhythmia_risk = self.calculate_arrhythmia_risk(data.get('arrhythmia_statistics', {}))
        inflammation_risk = self.calculate_inflammation_risk(data.get('inflammation_statistics', {}))
        blood_flow_risk = self.calculate_blood_flow_risk(data.get('blood_flow_statistics', {}))
        bp_risk = self.calculate_bp_variability_risk(data.get('sleep_analysis', {}))
        
        # 加权计算总风险评分
        total_score = (
            vascular_risk['score'] * self.stroke_weights['vascular_function'] +
            arrhythmia_risk['score'] * self.stroke_weights['arrhythmia'] +
            inflammation_risk['score'] * self.stroke_weights['inflammation'] +
            blood_flow_risk['score'] * self.stroke_weights['blood_flow'] +
            bp_risk['score'] * self.stroke_weights['bp_variability']
        )
        
        # 时间因子调整
        time_factor = 1.0 if time_period == 7 else 1.25  # 30日风险相对更高
        adjusted_score = min(total_score * time_factor, 100)
        
        # 风险等级判定
        if adjusted_score >= self.risk_thresholds['very_high']:
            risk_level = '极高风险'
        elif adjusted_score >= self.risk_thresholds['high']:
            risk_level = '高风险'
        elif adjusted_score >= self.risk_thresholds['moderate']:
            risk_level = '中等风险'
        else:
            risk_level = '低风险'
        
        # 风险概率计算
        risk_probability = 1 / (1 + math.exp(-(adjusted_score - 45) / 18))  # 脑卒中阈值稍低
        
        # 收集所有风险因素
        all_risk_factors = []
        all_risk_factors.extend(vascular_risk['risk_factors'])
        all_risk_factors.extend(arrhythmia_risk['risk_factors'])
        all_risk_factors.extend(inflammation_risk['risk_factors'])
        all_risk_factors.extend(blood_flow_risk['risk_factors'])
        all_risk_factors.extend(bp_risk['risk_factors'])
        
        return {
            'risk_score': round(adjusted_score, 2),
            'risk_level': risk_level,
            'risk_probability': round(risk_probability * 100, 2),
            'time_period_days': time_period,
            'risk_factors': all_risk_factors,
            'component_scores': {
                'vascular_function': vascular_risk,
                'arrhythmia': arrhythmia_risk,
                'inflammation': inflammation_risk,
                'blood_flow': blood_flow_risk,
                'bp_variability': bp_risk
            },
            'weights_used': self.stroke_weights,
            'calculation_method': 'weighted_sum_with_logistic_probability'
        }
    
    def analyze_single_device(self, file_path: str) -> Dict:
        """分析单个设备的风险数据"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            device_id = data.get('device_id', 'unknown')
            analysis_timestamp = data.get('analysis_timestamp', datetime.now().isoformat())
            
            # 计算心梗风险（7日和30日）
            mi_risk_7d = self.calculate_mi_risk(data, 7)
            mi_risk_30d = self.calculate_mi_risk(data, 30)
            
            # 计算脑卒中风险（7日和30日）
            stroke_risk_7d = self.calculate_stroke_risk(data, 7)
            stroke_risk_30d = self.calculate_stroke_risk(data, 30)
            
            # 生成医学建议
            recommendations = self.generate_medical_recommendations(
                mi_risk_7d, stroke_risk_7d, data
            )
            
            result = {
                'device_id': device_id,
                'analysis_timestamp': datetime.now().isoformat(),
                'source_data_timestamp': analysis_timestamp,
                'myocardial_infarction_risk': {
                    '7_day_risk': mi_risk_7d,
                    '30_day_risk': mi_risk_30d
                },
                'stroke_risk': {
                    '7_day_risk': stroke_risk_7d,
                    '30_day_risk': stroke_risk_30d
                },
                'medical_recommendations': recommendations,
                'analysis_summary': {
                    'highest_risk_category': self.get_highest_risk_category(mi_risk_7d, stroke_risk_7d),
                    'primary_risk_factors': self.get_primary_risk_factors(mi_risk_7d, stroke_risk_7d),
                    'overall_risk_level': self.get_overall_risk_level(mi_risk_7d, stroke_risk_7d)
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"分析设备数据时出错: {e}")
            return None
    
    def generate_medical_recommendations(self, mi_risk: Dict, stroke_risk: Dict, data: Dict) -> List[str]:
        """生成医学建议"""
        recommendations = []
        
        # 基于心梗风险的建议
        if mi_risk['risk_score'] > 60:
            recommendations.extend([
                "建议立即就医进行心血管专科评估",
                "考虑进行冠状动脉造影检查",
                "严格控制血压、血脂、血糖"
            ])
        elif mi_risk['risk_score'] > 40:
            recommendations.extend([
                "建议3个月内进行心血管专科检查",
                "定期监测心电图和心脏标志物",
                "加强生活方式干预"
            ])
        
        # 基于脑卒中风险的建议
        if stroke_risk['risk_score'] > 60:
            recommendations.extend([
                "建议立即进行神经科评估",
                "考虑进行颈动脉超声和脑血管检查",
                "评估抗凝治疗的必要性"
            ])
        elif stroke_risk['risk_score'] > 40:
            recommendations.extend([
                "建议6个月内进行神经科检查",
                "定期监测血压和凝血功能"
            ])
        
        # 基于具体风险因素的建议
        all_factors = set(mi_risk['risk_factors'] + stroke_risk['risk_factors'])
        
        if any('房颤' in factor for factor in all_factors):
            recommendations.append("建议评估抗凝治疗，预防血栓栓塞")
        
        if any('血管年龄' in factor for factor in all_factors):
            recommendations.append("建议进行血管功能专项检查和抗衰老治疗")
        
        if any('炎症' in factor for factor in all_factors):
            recommendations.append("建议检查炎症标志物（CRP、IL-6等）")
        
        if any('血压' in factor for factor in all_factors):
            recommendations.append("建议24小时动态血压监测")
        
        # 通用建议
        recommendations.extend([
            "保持健康饮食，低盐低脂",
            "适量规律运动，避免剧烈运动",
            "戒烟限酒，保持良好作息",
            "定期复查，密切监测病情变化"
        ])
        
        return list(set(recommendations))  # 去重
    
    def get_highest_risk_category(self, mi_risk: Dict, stroke_risk: Dict) -> str:
        """获取最高风险类别"""
        if mi_risk['risk_score'] > stroke_risk['risk_score']:
            return f"心梗风险 ({mi_risk['risk_level']})"
        else:
            return f"脑卒中风险 ({stroke_risk['risk_level']})"
    
    def get_primary_risk_factors(self, mi_risk: Dict, stroke_risk: Dict) -> List[str]:
        """获取主要风险因素"""
        all_factors = mi_risk['risk_factors'] + stroke_risk['risk_factors']
        # 统计频次，返回最常见的风险因素
        factor_counts = {}
        for factor in all_factors:
            factor_counts[factor] = factor_counts.get(factor, 0) + 1
        
        # 按频次排序，返回前5个
        sorted_factors = sorted(factor_counts.items(), key=lambda x: x[1], reverse=True)
        return [factor for factor, count in sorted_factors[:5]]
    
    def get_overall_risk_level(self, mi_risk: Dict, stroke_risk: Dict) -> str:
        """获取总体风险等级"""
        max_score = max(mi_risk['risk_score'], stroke_risk['risk_score'])
        
        if max_score >= self.risk_thresholds['very_high']:
            return '极高风险'
        elif max_score >= self.risk_thresholds['high']:
            return '高风险'
        elif max_score >= self.risk_thresholds['moderate']:
            return '中等风险'
        else:
            return '低风险'
    
    def process_all_devices(self, input_dir: str, output_dir: str) -> Dict:
        """处理所有设备的风险分析"""
        # 将相对路径转换为绝对路径
        input_dir = os.path.abspath(input_dir)
        output_dir = os.path.abspath(output_dir)
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 获取所有JSON文件
        json_files = glob.glob(os.path.join(input_dir, "*.json"))
        
        if not json_files:
            logger.warning(f"在目录 {input_dir} 中没有找到JSON文件")
            return {
                'analysis_timestamp': datetime.now().isoformat(),
                'summary': {
                    'total_devices': 0,
                    'successful_analyses': 0,
                    'failed_analyses': 0,
                    'risk_distribution': {'低风险': 0, '中等风险': 0, '高风险': 0, '极高风险': 0}
                },
                'detailed_results': []
            }
        
        logger.info(f"找到 {len(json_files)} 个JSON文件，开始分析...")
        
        results = []
        summary = {
            'total_devices': len(json_files),
            'successful_analyses': 0,
            'failed_analyses': 0,
            'risk_distribution': {'低风险': 0, '中等风险': 0, '高风险': 0, '极高风险': 0}
        }
        
        for json_file in json_files:
            logger.info(f"正在分析: {os.path.basename(json_file)}")
            
            try:
                result = self.analyze_single_device(json_file)
                if result:
                    results.append(result)
                    summary['successful_analyses'] += 1
                    
                    # 统计风险分布（使用心梗7日风险等级）
                    mi_risk_level = result.get('myocardial_infarction_risk', {}).get('7_day_risk', {}).get('risk_level', '低风险')
                    if mi_risk_level in summary['risk_distribution']:
                        summary['risk_distribution'][mi_risk_level] += 1
                    else:
                        summary['risk_distribution']['低风险'] += 1
                    
                    # 保存单个设备的分析结果
                    device_id = result['device_id']
                    output_filename = f"{device_id}_medical_risk_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    output_path = os.path.join(output_dir, output_filename)
                    
                    with open(output_path, 'w', encoding='utf-8') as f:
                        json.dump(result, f, ensure_ascii=False, indent=2)
                    
                    logger.info(f"已保存分析结果: {output_filename}")
                else:
                    summary['failed_analyses'] += 1
            except Exception as e:
                logger.error(f"分析文件 {json_file} 时出错: {e}")
                summary['failed_analyses'] += 1
        
        # 保存汇总报告
        summary_report = {
            'analysis_timestamp': datetime.now().isoformat(),
            'summary': summary,
            'detailed_results': results
        }
        
        summary_path = os.path.join(output_dir, f"medical_risk_analysis_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary_report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"分析完成，共处理 {summary['total_devices']} 个设备，成功 {summary['successful_analyses']} 个")
        return summary_report

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='高级医学风险分析器 - 支持相对路径输入')
    parser.add_argument('-i', '--input', 
                       default='./analysis_results',
                       help='输入分析目录路径（支持相对路径，默认: ./analysis_results）')
    parser.add_argument('-o', '--output', 
                       default='./risk_json',
                       help='输出结果目录路径（支持相对路径，默认: ./risk_json）')
    parser.add_argument('-v', '--verbose', 
                       action='store_true',
                       help='显示详细日志信息')
    
    return parser.parse_args()

def main():
    """主函数"""
    # 解析命令行参数
    args = parse_arguments()
    
    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    analyzer = AdvancedMedicalRiskAnalyzer()
    
    # 使用命令行参数或默认值
    input_dir = args.input
    output_dir = args.output
    
    # 显示使用的路径信息
    abs_input_dir = os.path.abspath(input_dir)
    abs_output_dir = os.path.abspath(output_dir)
    
    print(f"\n=== 高级医学风险分析器 ===")
    print(f"输入目录: {input_dir} -> {abs_input_dir}")
    print(f"输出目录: {output_dir} -> {abs_output_dir}")
    
    # 检查输入目录是否存在
    if not os.path.exists(abs_input_dir):
        print(f"错误: 输入目录不存在: {abs_input_dir}")
        return
    
    # 执行批量分析
    logger.info("开始医学风险分析...")
    summary = analyzer.process_all_devices(input_dir, output_dir)
    
    print("\n=== 医学风险分析完成 ===")
    print(f"总设备数: {summary['summary']['total_devices']}")
    print(f"成功分析: {summary['summary']['successful_analyses']}")
    print(f"失败分析: {summary['summary']['failed_analyses']}")
    print("\n风险分布:")
    for level, count in summary['summary']['risk_distribution'].items():
        print(f"  {level}: {count} 个设备")
    
    print(f"\n结果已保存到: {abs_output_dir}")

if __name__ == "__main__":
    main()