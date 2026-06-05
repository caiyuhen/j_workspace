#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
心梗与脑卒中风险预测计算器
基于PPG数据分析结果计算未来7天和30天内的心梗与脑卒中风险比率
"""

import json
import math
import os
import glob
import numpy as np
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any

class CardiovascularRiskCalculator:
    """心血管风险计算器"""
    
    def __init__(self):
        # 风险权重系数 (基于临床研究和文献)
        self.risk_weights = {
            # 心梗风险因子权重
            'mi_weights': {
                'pwv': 0.25,           # 脉搏波速度
                'vascular_age': 0.20,  # 血管年龄
                'hrv': 0.15,           # 心率变异性
                'inflammation': 0.15,  # 炎症指标
                'bp_variability': 0.10, # 血压变异性
                'sleep_apnea': 0.10,   # 睡眠呼吸暂停
                'spo2': 0.05          # 血氧饱和度
            },
            # 脑卒中风险因子权重
            'stroke_weights': {
                'bp_rhythm': 0.30,     # 血压昼夜节律
                'pwv': 0.20,           # 脉搏波速度
                'bp_variability': 0.15, # 血压变异性
                'vascular_age': 0.15,  # 血管年龄
                'inflammation': 0.10,  # 炎症指标
                'arrhythmia': 0.05,    # 心律失常
                'spo2': 0.05          # 血氧饱和度
            }
        }
        
        # 基础风险率 (每1000人年)
        self.baseline_risks = {
            'mi_7day': 0.0019,     # 7天心梗基础风险
            'mi_30day': 0.0082,    # 30天心梗基础风险
            'stroke_7day': 0.0015, # 7天脑卒中基础风险
            'stroke_30day': 0.0065 # 30天脑卒中基础风险
        }
    
    def load_analysis_data(self, file_path: str) -> Dict[str, Any]:
        """加载PPG分析结果数据"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise Exception(f"无法加载分析数据: {e}")
    
    def calculate_pwv_risk_score(self, pwv_stats: Dict) -> float:
        """计算脉搏波速度风险评分"""
        if not pwv_stats or pwv_stats.get('count', 0) == 0:
            return 0.0
        
        mean_pwv = pwv_stats.get('mean', 0)
        
        # PWV风险评分 (基于临床标准)
        if mean_pwv < 7:
            return 0.0      # 正常
        elif mean_pwv < 10:
            return 0.3      # 轻度升高
        elif mean_pwv < 12:
            return 0.6      # 中度升高
        elif mean_pwv < 15:
            return 0.8      # 重度升高
        else:
            return 1.0      # 极重度升高
    
    def calculate_vascular_age_risk_score(self, vascular_age_stats: Dict) -> float:
        """计算血管年龄风险评分"""
        if not vascular_age_stats or vascular_age_stats.get('count', 0) == 0:
            return 0.0
        
        mean_age = vascular_age_stats.get('mean', 0)
        
        # 血管年龄风险评分
        if mean_age < 40:
            return 0.0
        elif mean_age < 50:
            return 0.2
        elif mean_age < 60:
            return 0.4
        elif mean_age < 70:
            return 0.6
        elif mean_age < 80:
            return 0.8
        else:
            return 1.0
    
    def calculate_hrv_risk_score(self, lf_hf_ratio_stats: Dict) -> float:
        """计算心率变异性风险评分"""
        if not lf_hf_ratio_stats or lf_hf_ratio_stats.get('count', 0) == 0:
            return 0.0
        
        mean_lf_hf = lf_hf_ratio_stats.get('mean', 0)
        
        # LF/HF比值风险评分 (正常范围: 0.5-2.0)
        if 0.5 <= mean_lf_hf <= 2.0:
            return 0.0      # 正常
        elif mean_lf_hf < 0.5:
            return 0.7      # 副交感神经过度激活
        elif mean_lf_hf < 3.0:
            return 0.4      # 轻度交感神经激活
        elif mean_lf_hf < 5.0:
            return 0.7      # 中度交感神经激活
        else:
            return 1.0      # 重度交感神经激活
    
    def calculate_inflammation_risk_score(self, inflammation_assessment: Dict) -> float:
        """计算炎症风险评分"""
        if not inflammation_assessment:
            return 0.0
        
        risk_level = inflammation_assessment.get('overall_risk_level', 'low')
        risk_score = inflammation_assessment.get('risk_score', 0)
        
        # 炎症风险评分
        if risk_level == 'low' or risk_score < 30:
            return 0.0
        elif risk_level == 'moderate' or risk_score < 60:
            return 0.5
        else:
            return 1.0
    
    def calculate_bp_variability_risk_score(self, bp_analysis: Dict) -> float:
        """计算血压变异性风险评分"""
        if not bp_analysis or 'bp_variability' not in bp_analysis:
            return 0.0
        
        bp_var = bp_analysis['bp_variability']
        cv = bp_var.get('coefficient_of_variation', 0)
        
        # 血压变异性风险评分 (CV > 15%为高变异性)
        if cv < 10:
            return 0.0
        elif cv < 15:
            return 0.3
        elif cv < 20:
            return 0.6
        else:
            return 1.0
    
    def calculate_bp_rhythm_risk_score(self, bp_analysis: Dict) -> float:
        """计算血压昼夜节律风险评分"""
        if not bp_analysis or 'nocturnal_dipping' not in bp_analysis:
            return 0.0
        
        dipping = bp_analysis['nocturnal_dipping']
        pattern = dipping.get('dipping_pattern', 'normal')
        dipping_pct = dipping.get('dipping_percentage', 0)
        
        # 血压昼夜节律风险评分
        if pattern == 'normal' and 10 <= abs(dipping_pct) <= 20:
            return 0.0      # 正常杓型
        elif pattern == 'non_dipper':
            return 0.6      # 非杓型
        elif pattern == 'reverse_dipper':
            return 1.0      # 反杓型 (最高风险)
        elif pattern == 'extreme_dipper':
            return 0.8      # 超杓型
        else:
            return 0.3
    
    def calculate_sleep_apnea_risk_score(self, sleep_analysis: Dict) -> float:
        """计算睡眠呼吸暂停风险评分"""
        if not sleep_analysis or 'sleep_apnea_analysis' not in sleep_analysis:
            return 0.0
        
        apnea = sleep_analysis['sleep_apnea_analysis']
        ahi = apnea.get('ahi_index', 0)
        severity = apnea.get('severity', 'normal')
        
        # AHI风险评分
        if ahi < 5 or severity == 'normal':
            return 0.0
        elif ahi < 15 or severity == 'mild':
            return 0.3
        elif ahi < 30 or severity == 'moderate':
            return 0.6
        else:
            return 1.0
    
    def calculate_spo2_risk_score(self, sleep_analysis: Dict) -> float:
        """计算血氧饱和度风险评分"""
        if not sleep_analysis or 'nocturnal_spo2_analysis' not in sleep_analysis:
            return 0.0
        
        spo2 = sleep_analysis['nocturnal_spo2_analysis']
        mean_spo2 = spo2.get('mean_spo2', 100)
        min_spo2 = spo2.get('min_spo2', 100)
        below_90_pct = spo2.get('spo2_below_90_percent', 0)
        
        # SpO2风险评分
        risk_score = 0.0
        
        if mean_spo2 < 95:
            risk_score += 0.4
        elif mean_spo2 < 97:
            risk_score += 0.2
        
        if min_spo2 < 85:
            risk_score += 0.4
        elif min_spo2 < 90:
            risk_score += 0.2
        
        if below_90_pct > 0.1:  # >10%时间低于90%
            risk_score += 0.4
        elif below_90_pct > 0.05:  # >5%时间低于90%
            risk_score += 0.2
        
        return min(risk_score, 1.0)
    
    def calculate_arrhythmia_risk_score(self, arrhythmia_assessment: Dict) -> float:
        """计算心律失常风险评分"""
        if not arrhythmia_assessment:
            return 0.0
        
        risk_level = arrhythmia_assessment.get('risk_level', 'normal')
        detection_summary = arrhythmia_assessment.get('detection_summary', {})
        
        afib_rate = float(detection_summary.get('afib_detection_rate', '0%').replace('%', ''))
        premature_rate = float(detection_summary.get('premature_beats_rate', '0%').replace('%', ''))
        
        # 心律失常风险评分
        risk_score = 0.0
        
        if afib_rate > 0:
            risk_score += min(afib_rate / 10, 0.8)  # 房颤风险
        
        if premature_rate > 5:
            risk_score += min(premature_rate / 20, 0.3)  # 早搏风险
        
        return min(risk_score, 1.0)
    
    def calculate_mi_risk_score(self, data: Dict) -> float:
        """计算心梗风险评分"""
        vascular_stats = data.get('vascular_function_statistics', {})
        sleep_analysis = data.get('sleep_analysis', {})
        inflammation = data.get('inflammation_risk_assessment', {})
        
        # 各风险因子评分
        pwv_score = self.calculate_pwv_risk_score(vascular_stats.get('pwv_stats', {}))
        vascular_age_score = self.calculate_vascular_age_risk_score(vascular_stats.get('vascular_age_stats', {}))
        hrv_score = self.calculate_hrv_risk_score(vascular_stats.get('lf_hf_ratio_stats', {}))
        inflammation_score = self.calculate_inflammation_risk_score(inflammation)
        bp_var_score = self.calculate_bp_variability_risk_score(sleep_analysis.get('blood_pressure_rhythm_analysis', {}))
        sleep_apnea_score = self.calculate_sleep_apnea_risk_score(sleep_analysis)
        spo2_score = self.calculate_spo2_risk_score(sleep_analysis)
        
        # 加权计算总风险评分
        weights = self.risk_weights['mi_weights']
        total_score = (
            pwv_score * weights['pwv'] +
            vascular_age_score * weights['vascular_age'] +
            hrv_score * weights['hrv'] +
            inflammation_score * weights['inflammation'] +
            bp_var_score * weights['bp_variability'] +
            sleep_apnea_score * weights['sleep_apnea'] +
            spo2_score * weights['spo2']
        )
        
        return min(total_score, 1.0)
    
    def calculate_stroke_risk_score(self, data: Dict) -> float:
        """计算脑卒中风险评分"""
        vascular_stats = data.get('vascular_function_statistics', {})
        sleep_analysis = data.get('sleep_analysis', {})
        inflammation = data.get('inflammation_risk_assessment', {})
        arrhythmia = data.get('arrhythmia_risk_assessment', {})
        
        # 各风险因子评分
        bp_rhythm_score = self.calculate_bp_rhythm_risk_score(sleep_analysis.get('blood_pressure_rhythm_analysis', {}))
        pwv_score = self.calculate_pwv_risk_score(vascular_stats.get('pwv_stats', {}))
        bp_var_score = self.calculate_bp_variability_risk_score(sleep_analysis.get('blood_pressure_rhythm_analysis', {}))
        vascular_age_score = self.calculate_vascular_age_risk_score(vascular_stats.get('vascular_age_stats', {}))
        inflammation_score = self.calculate_inflammation_risk_score(inflammation)
        arrhythmia_score = self.calculate_arrhythmia_risk_score(arrhythmia)
        spo2_score = self.calculate_spo2_risk_score(sleep_analysis)
        
        # 加权计算总风险评分
        weights = self.risk_weights['stroke_weights']
        total_score = (
            bp_rhythm_score * weights['bp_rhythm'] +
            pwv_score * weights['pwv'] +
            bp_var_score * weights['bp_variability'] +
            vascular_age_score * weights['vascular_age'] +
            inflammation_score * weights['inflammation'] +
            arrhythmia_score * weights['arrhythmia'] +
            spo2_score * weights['spo2']
        )
        
        return min(total_score, 1.0)
    
    def calculate_risk_ratios(self, data: Dict) -> Dict[str, float]:
        """计算风险比率"""
        mi_risk_score = self.calculate_mi_risk_score(data)
        stroke_risk_score = self.calculate_stroke_risk_score(data)
        
        # 使用指数函数将风险评分转换为风险比率
        # 风险比率 = 基础风险 × exp(风险评分 × 系数)
        risk_multiplier = 3.0  # 调节系数
        
        # 计算风险比率
        mi_7day_ratio = self.baseline_risks['mi_7day'] * math.exp(mi_risk_score * risk_multiplier)
        mi_30day_ratio = self.baseline_risks['mi_30day'] * math.exp(mi_risk_score * risk_multiplier)
        stroke_7day_ratio = self.baseline_risks['stroke_7day'] * math.exp(stroke_risk_score * risk_multiplier)
        stroke_30day_ratio = self.baseline_risks['stroke_30day'] * math.exp(stroke_risk_score * risk_multiplier)
        
        # 计算风险倍数（相对于正常人群）
        mi_7day_multiplier = mi_7day_ratio / self.baseline_risks['mi_7day']
        mi_30day_multiplier = mi_30day_ratio / self.baseline_risks['mi_30day']
        stroke_7day_multiplier = stroke_7day_ratio / self.baseline_risks['stroke_7day']
        stroke_30day_multiplier = stroke_30day_ratio / self.baseline_risks['stroke_30day']
        
        results = {
            'mi_7day_ratio': mi_7day_ratio,
            'mi_30day_ratio': mi_30day_ratio,
            'stroke_7day_ratio': stroke_7day_ratio,
            'stroke_30day_ratio': stroke_30day_ratio,
            'mi_risk_score': mi_risk_score,
            'stroke_risk_score': stroke_risk_score,
            'mi_7day_multiplier': mi_7day_multiplier,
            'mi_30day_multiplier': mi_30day_multiplier,
            'stroke_7day_multiplier': stroke_7day_multiplier,
            'stroke_30day_multiplier': stroke_30day_multiplier
        }
        
        return results
    
    def generate_risk_report(self, file_path: str) -> Dict[str, Any]:
        """生成风险预测报告"""
        # 加载数据
        data = self.load_analysis_data(file_path)
        
        # 计算风险比率
        risk_results = self.calculate_risk_ratios(data)
        
        # 生成详细报告
        report = {
            'device_id': data.get('device_id', ''),
            'analysis_timestamp': datetime.now().isoformat(),
            'risk_prediction': {
                'myocardial_infarction': {
                    '7_day_risk_ratio': risk_results['mi_7day_ratio'],
                    '30_day_risk_ratio': risk_results['mi_30day_ratio'],
                    'risk_score': risk_results['mi_risk_score'],
                    'risk_level': self.get_risk_level(risk_results['mi_risk_score']),
                    '7_day_percentage': risk_results['mi_7day_ratio'] * 100,
                    '30_day_percentage': risk_results['mi_30day_ratio'] * 100,
                    '7_day_risk_level': self.get_risk_level(risk_results['mi_risk_score']),
                    '7_day_multiplier': risk_results['mi_7day_multiplier'],
                    '30_day_multiplier': risk_results['mi_30day_multiplier']
                },
                'stroke': {
                    '7_day_risk_ratio': risk_results['stroke_7day_ratio'],
                    '30_day_risk_ratio': risk_results['stroke_30day_ratio'],
                    'risk_score': risk_results['stroke_risk_score'],
                    'risk_level': self.get_risk_level(risk_results['stroke_risk_score']),
                    '7_day_percentage': risk_results['stroke_7day_ratio'] * 100,
                    '30_day_percentage': risk_results['stroke_30day_ratio'] * 100,
                    '7_day_risk_level': self.get_risk_level(risk_results['stroke_risk_score']),
                    '7_day_multiplier': risk_results['stroke_7day_multiplier'],
                    '30_day_multiplier': risk_results['stroke_30day_multiplier']
                }
            },
            'risk_factors_analysis': self.analyze_risk_factors(data),
            'recommendations': self.generate_recommendations(risk_results),
            'calculation_details': {
                'baseline_risks': self.baseline_risks,
                'risk_weights': self.risk_weights,
                'methodology': '基于PPG信号分析的多因子风险评估模型'
            }
        }
        
        return report
    
    def get_risk_level(self, risk_score: float) -> str:
        """获取风险等级"""
        if risk_score < 0.25:
            return '低风险'
        elif risk_score < 0.5:
            return '中风险'
        else:
            return '高风险'
    
    def analyze_risk_factors(self, data: Dict) -> Dict[str, Any]:
        """分析具体风险因子"""
        vascular_stats = data.get('vascular_function_statistics', {})
        sleep_analysis = data.get('sleep_analysis', {})
        
        analysis = {
            'primary_risk_factors': [],
            'secondary_risk_factors': [],
            'protective_factors': []
        }
        
        # 分析主要风险因子
        pwv_mean = vascular_stats.get('pwv_stats', {}).get('mean', 0)
        if pwv_mean > 12:
            analysis['primary_risk_factors'].append(f'脉搏波速度严重升高 ({pwv_mean:.1f} m/s)')
        
        vascular_age = vascular_stats.get('vascular_age_stats', {}).get('mean', 0)
        if vascular_age > 70:
            analysis['primary_risk_factors'].append(f'血管年龄显著老化 ({vascular_age:.1f}岁)')
        
        bp_analysis = sleep_analysis.get('blood_pressure_rhythm_analysis', {})
        if bp_analysis.get('nocturnal_dipping', {}).get('dipping_pattern') == 'reverse_dipper':
            analysis['primary_risk_factors'].append('血压昼夜节律异常 (反杓型)')
        
        # 分析次要风险因子
        lf_hf = vascular_stats.get('lf_hf_ratio_stats', {}).get('mean', 0)
        if lf_hf < 0.5:
            analysis['secondary_risk_factors'].append(f'心率变异性异常 (LF/HF={lf_hf:.3f})')
        
        inflammation = data.get('inflammation_risk_assessment', {})
        if inflammation.get('overall_risk_level') == 'moderate':
            analysis['secondary_risk_factors'].append('中度慢性炎症风险')
        
        # 分析保护性因子
        arrhythmia = data.get('arrhythmia_risk_assessment', {})
        if arrhythmia.get('risk_level') == 'normal':
            analysis['protective_factors'].append('心律正常')
        
        spo2_analysis = sleep_analysis.get('nocturnal_spo2_analysis', {})
        if spo2_analysis.get('mean_spo2', 0) > 97:
            analysis['protective_factors'].append('血氧饱和度良好')
        
        return analysis
    
    def generate_recommendations(self, risk_results: Dict) -> List[str]:
        """生成个性化建议"""
        recommendations = []
        
        mi_score = risk_results['mi_risk_score']
        stroke_score = risk_results['stroke_risk_score']
        
        if mi_score >= 0.75 or stroke_score >= 0.75:
            recommendations.extend([
                '立即就医进行专业心血管评估',
                '考虑进行冠状动脉造影或颈动脉超声检查',
                '严格控制血压、血脂和血糖'
            ])
        elif mi_score >= 0.5 or stroke_score >= 0.5:
            recommendations.extend([
                '建议3个月内进行心血管专科检查',
                '加强生活方式干预',
                '定期监测血压和心率'
            ])
        else:
            recommendations.extend([
                '保持健康的生活方式',
                '定期进行心血管健康检查'
            ])
        
        # 通用建议
        recommendations.extend([
            '戒烟限酒，保持适当体重',
            '规律有氧运动，每周至少150分钟',
            '保持充足睡眠，管理压力',
            '定期使用PPG设备进行健康监测'
        ])
        
        return recommendations

    def batch_process_files(self, input_dir: str, output_dir: str) -> Dict[str, Any]:
        """批量处理所有JSON文件"""
        # 将相对路径转换为绝对路径
        input_dir = os.path.abspath(input_dir)
        output_dir = os.path.abspath(output_dir)
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 获取所有JSON文件
        json_files = glob.glob(os.path.join(input_dir, "*.json"))
        
        if not json_files:
            print(f"在目录 {input_dir} 中没有找到JSON文件")
            return {"success": False, "message": "没有找到JSON文件"}
        
        print(f"找到 {len(json_files)} 个JSON文件，开始批量处理...")
        
        results = {
            "total_files": len(json_files),
            "processed_files": 0,
            "failed_files": 0,
            "success_files": [],
            "failed_files_list": [],
            "processing_time": datetime.now().isoformat()
        }
        
        for i, file_path in enumerate(json_files, 1):
            try:
                print(f"正在处理 [{i}/{len(json_files)}]: {os.path.basename(file_path)}")
                
                # 生成风险报告
                report = self.generate_risk_report(file_path)
                
                # 构建输出文件名
                base_name = os.path.splitext(os.path.basename(file_path))[0]
                output_filename = f"{base_name}_risk_assessment.json"
                output_path = os.path.join(output_dir, output_filename)
                
                # 保存报告
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(report, f, ensure_ascii=False, indent=2)
                
                results["processed_files"] += 1
                results["success_files"].append({
                    "input_file": file_path,
                    "output_file": output_path,
                    "device_id": report.get("device_id", ""),
                    "mi_risk_level": report["risk_prediction"]["myocardial_infarction"]["risk_level"],
                    "stroke_risk_level": report["risk_prediction"]["stroke"]["risk_level"]
                })
                
                print(f"  ✓ 成功生成风险报告: {output_filename}")
                
            except Exception as e:
                print(f"  ✗ 处理失败: {str(e)}")
                results["failed_files"] += 1
                results["failed_files_list"].append({
                    "file": file_path,
                    "error": str(e)
                })
        
        print(f"\n批量处理完成!")
        print(f"成功处理: {results['processed_files']} 个文件")
        print(f"处理失败: {results['failed_files']} 个文件")
        print(f"结果保存在: {output_dir}")
        
        return results

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='心梗脑卒中风险预测计算器 - 支持相对路径输入')
    parser.add_argument('-i', '--input', 
                       default='./analysis_results',
                       help='输入分析目录路径（支持相对路径，默认: ./analysis_results）')
    parser.add_argument('-o', '--output', 
                       default='./risk_assessment_results',
                       help='输出结果目录路径（支持相对路径，默认: ./risk_assessment_results）')
    parser.add_argument('-v', '--verbose', 
                       action='store_true',
                       help='显示详细处理信息')
    
    return parser.parse_args()

def main():
    """主函数"""
    # 解析命令行参数
    args = parse_arguments()
    
    calculator = CardiovascularRiskCalculator()
    
    # 使用命令行参数或默认值
    input_dir = args.input
    output_dir = args.output
    
    # 显示使用的路径信息
    abs_input_dir = os.path.abspath(input_dir)
    abs_output_dir = os.path.abspath(output_dir)
    
    print(f"\n=== 心梗脑卒中风险预测计算器 ===")
    print(f"输入目录: {input_dir} -> {abs_input_dir}")
    print(f"输出目录: {output_dir} -> {abs_output_dir}")
    
    # 检查输入目录是否存在
    if not os.path.exists(abs_input_dir):
        print(f"错误: 输入目录不存在: {abs_input_dir}")
        return

    try:
        # 批量处理所有文件
        results = calculator.batch_process_files(input_dir, output_dir)
        
        # 保存处理结果摘要
        summary_path = os.path.join(abs_output_dir, "batch_processing_summary.json")
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n处理结果摘要已保存: {summary_path}")
        
        # 显示成功处理的文件摘要
        if results.get("success_files"):
            print("\n=== 风险评估结果摘要 ===")
            for file_info in results["success_files"]:
                print(f"设备ID: {file_info['device_id']}")
                print(f"  心梗风险等级: {file_info['mi_risk_level']}")
                print(f"  脑卒中风险等级: {file_info['stroke_risk_level']}")
                print(f"  报告文件: {os.path.basename(file_info['output_file'])}")
                print("-" * 50)
        
        print(f"\n结果已保存到: {abs_output_dir}")
        
    except Exception as e:
        print(f"批量处理出错: {e}")

if __name__ == "__main__":
    main()