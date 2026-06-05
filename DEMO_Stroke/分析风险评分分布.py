#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
风险评分分布分析脚本
分析为什么风险评分都集中在0.6左右
"""

import json
import os
import glob
import numpy as np
from typing import Dict, List, Any
from 心梗脑卒中风险预测计算器_000 import CardiovascularRiskCalculator

def analyze_individual_risk_factors():
    """分析各个风险因子的评分分布"""
    print("=" * 60)
    print("风险因子评分分布分析")
    print("=" * 60)
    
    # 初始化计算器
    calculator = CardiovascularRiskCalculator()
    
    # 获取所有原始血管分析文件
    risk_files = glob.glob("risk_all_json/analysis/*_vascular_analysis_*.json")
    
    if not risk_files:
        print("未找到血管分析文件")
        return
    
    # 存储各个风险因子的评分
    risk_factors_scores = {
        'pwv_scores': [],
        'vascular_age_scores': [],
        'hrv_scores': [],
        'inflammation_scores': [],
        'bp_variability_scores': [],
        'bp_rhythm_scores': [],
        'sleep_apnea_scores': [],
        'spo2_scores': [],
        'arrhythmia_scores': []
    }
    
    # 存储最终风险评分
    mi_scores = []
    stroke_scores = []
    
    print(f"分析 {len(risk_files)} 个血管分析文件...")
    
    for file_path in risk_files[:10]:  # 分析前10个文件
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 获取原始数据 - 使用正确的数据结构
            vascular_stats = data.get('vascular_function_statistics', {})
            sleep_analysis = data.get('sleep_analysis', {})
            inflammation = data.get('inflammation_risk_assessment', {})
            arrhythmia = data.get('arrhythmia_risk_assessment', {})
            
            # 计算各个风险因子评分
            pwv_score = calculator.calculate_pwv_risk_score(vascular_stats.get('pwv_stats', {}))
            vascular_age_score = calculator.calculate_vascular_age_risk_score(vascular_stats.get('vascular_age_stats', {}))
            hrv_score = calculator.calculate_hrv_risk_score(vascular_stats.get('lf_hf_ratio_stats', {}))
            inflammation_score = calculator.calculate_inflammation_risk_score(inflammation)
            bp_var_score = calculator.calculate_bp_variability_risk_score(sleep_analysis.get('blood_pressure_rhythm_analysis', {}))
            bp_rhythm_score = calculator.calculate_bp_rhythm_risk_score(sleep_analysis.get('blood_pressure_rhythm_analysis', {}))
            sleep_apnea_score = calculator.calculate_sleep_apnea_risk_score(sleep_analysis)
            spo2_score = calculator.calculate_spo2_risk_score(sleep_analysis)
            arrhythmia_score = calculator.calculate_arrhythmia_risk_score(arrhythmia)
            
            # 存储评分
            risk_factors_scores['pwv_scores'].append(pwv_score)
            risk_factors_scores['vascular_age_scores'].append(vascular_age_score)
            risk_factors_scores['hrv_scores'].append(hrv_score)
            risk_factors_scores['inflammation_scores'].append(inflammation_score)
            risk_factors_scores['bp_variability_scores'].append(bp_var_score)
            risk_factors_scores['bp_rhythm_scores'].append(bp_rhythm_score)
            risk_factors_scores['sleep_apnea_scores'].append(sleep_apnea_score)
            risk_factors_scores['spo2_scores'].append(spo2_score)
            risk_factors_scores['arrhythmia_scores'].append(arrhythmia_score)
            
            # 计算最终风险评分
            mi_score = calculator.calculate_mi_risk_score(data)
            stroke_score = calculator.calculate_stroke_risk_score(data)
            
            mi_scores.append(mi_score)
            stroke_scores.append(stroke_score)
            
        except Exception as e:
            print(f"处理文件 {file_path} 时出错: {e}")
            continue
    
    # 分析各个风险因子的分布
    print("\n各风险因子评分统计:")
    print("-" * 50)
    
    factor_names = {
        'pwv_scores': 'PWV脉搏波速度',
        'vascular_age_scores': '血管年龄',
        'hrv_scores': '心率变异性',
        'inflammation_scores': '炎症指标',
        'bp_variability_scores': '血压变异性',
        'bp_rhythm_scores': '血压昼夜节律',
        'sleep_apnea_scores': '睡眠呼吸暂停',
        'spo2_scores': '血氧饱和度',
        'arrhythmia_scores': '心律失常'
    }
    
    for factor, scores in risk_factors_scores.items():
        if scores:
            mean_score = np.mean(scores)
            std_score = np.std(scores)
            min_score = np.min(scores)
            max_score = np.max(scores)
            
            print(f"{factor_names[factor]:12}: 均值={mean_score:.3f}, 标准差={std_score:.3f}, 范围=[{min_score:.3f}, {max_score:.3f}]")
    
    # 分析最终风险评分
    print(f"\n最终风险评分统计:")
    print("-" * 50)
    print(f"心梗风险评分: 均值={np.mean(mi_scores):.3f}, 标准差={np.std(mi_scores):.3f}, 范围=[{np.min(mi_scores):.3f}, {np.max(mi_scores):.3f}]")
    print(f"脑卒中风险评分: 均值={np.mean(stroke_scores):.3f}, 标准差={np.std(stroke_scores):.3f}, 范围=[{np.min(stroke_scores):.3f}, {np.max(stroke_scores):.3f}]")

def analyze_weight_contribution():
    """分析权重对最终评分的贡献"""
    print("\n" + "=" * 60)
    print("权重贡献分析")
    print("=" * 60)
    
    calculator = CardiovascularRiskCalculator()
    
    # 获取权重
    mi_weights = calculator.risk_weights['mi_weights']
    stroke_weights = calculator.risk_weights['stroke_weights']
    
    print("心梗风险因子权重:")
    print("-" * 30)
    for factor, weight in mi_weights.items():
        print(f"{factor:15}: {weight:.3f}")
    
    print(f"\n心梗权重总和: {sum(mi_weights.values()):.3f}")
    
    print("\n脑卒中风险因子权重:")
    print("-" * 30)
    for factor, weight in stroke_weights.items():
        print(f"{factor:15}: {weight:.3f}")
    
    print(f"\n脑卒中权重总和: {sum(stroke_weights.values()):.3f}")

def simulate_risk_score_scenarios():
    """模拟不同风险因子组合的评分情况"""
    print("\n" + "=" * 60)
    print("风险评分场景模拟")
    print("=" * 60)
    
    calculator = CardiovascularRiskCalculator()
    
    # 模拟不同的风险因子评分组合
    scenarios = [
        {
            'name': '全部低风险',
            'pwv': 0.0, 'vascular_age': 0.0, 'hrv': 0.0, 'inflammation': 0.0,
            'bp_variability': 0.0, 'bp_rhythm': 0.0, 'sleep_apnea': 0.0, 
            'spo2': 0.0, 'arrhythmia': 0.0
        },
        {
            'name': '全部中等风险',
            'pwv': 0.5, 'vascular_age': 0.5, 'hrv': 0.5, 'inflammation': 0.5,
            'bp_variability': 0.5, 'bp_rhythm': 0.5, 'sleep_apnea': 0.5, 
            'spo2': 0.5, 'arrhythmia': 0.5
        },
        {
            'name': '全部高风险',
            'pwv': 1.0, 'vascular_age': 1.0, 'hrv': 1.0, 'inflammation': 1.0,
            'bp_variability': 1.0, 'bp_rhythm': 1.0, 'sleep_apnea': 1.0, 
            'spo2': 1.0, 'arrhythmia': 1.0
        },
        {
            'name': '典型高风险组合',
            'pwv': 0.8, 'vascular_age': 0.6, 'hrv': 0.7, 'inflammation': 0.5,
            'bp_variability': 0.6, 'bp_rhythm': 0.7, 'sleep_apnea': 0.4, 
            'spo2': 0.3, 'arrhythmia': 0.5
        }
    ]
    
    mi_weights = calculator.risk_weights['mi_weights']
    stroke_weights = calculator.risk_weights['stroke_weights']
    
    print("场景模拟结果:")
    print("-" * 50)
    
    for scenario in scenarios:
        # 计算心梗风险评分
        mi_score = (
            scenario['pwv'] * mi_weights['pwv'] +
            scenario['vascular_age'] * mi_weights['vascular_age'] +
            scenario['hrv'] * mi_weights['hrv'] +
            scenario['inflammation'] * mi_weights['inflammation'] +
            scenario['bp_variability'] * mi_weights['bp_variability'] +
            scenario['sleep_apnea'] * mi_weights['sleep_apnea'] +
            scenario['spo2'] * mi_weights['spo2']
        )
        
        # 计算脑卒中风险评分
        stroke_score = (
            scenario['bp_rhythm'] * stroke_weights['bp_rhythm'] +
            scenario['pwv'] * stroke_weights['pwv'] +
            scenario['bp_variability'] * stroke_weights['bp_variability'] +
            scenario['vascular_age'] * stroke_weights['vascular_age'] +
            scenario['inflammation'] * stroke_weights['inflammation'] +
            scenario['arrhythmia'] * stroke_weights['arrhythmia'] +
            scenario['spo2'] * stroke_weights['spo2']
        )
        
        print(f"{scenario['name']:12}: 心梗={mi_score:.3f}, 脑卒中={stroke_score:.3f}")

def analyze_actual_data_patterns():
    """分析实际数据中的模式"""
    print("\n" + "=" * 60)
    print("实际数据模式分析")
    print("=" * 60)
    
    calculator = CardiovascularRiskCalculator()
    
    # 获取一个实际文件进行详细分析
    risk_files = glob.glob("risk_all_json/analysis/*_vascular_analysis_*.json")
    
    if not risk_files:
        print("未找到血管分析文件")
        return
    
    # 分析第一个文件
    file_path = risk_files[0]
    print(f"分析文件: {os.path.basename(file_path)}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 获取原始数据
        vascular_stats = data.get('vascular_function_statistics', {})
        sleep_analysis = data.get('sleep_analysis', {})
        inflammation = data.get('inflammation_risk_assessment', {})
        arrhythmia = data.get('arrhythmia_risk_assessment', {})
        
        print("\n原始数据值:")
        print("-" * 30)
        
        # PWV数据
        pwv_stats = vascular_stats.get('pwv_stats', {})
        if pwv_stats:
            print(f"PWV均值: {pwv_stats.get('mean', 'N/A')}")
        
        # 血管年龄数据
        vascular_age_stats = vascular_stats.get('vascular_age_stats', {})
        if vascular_age_stats:
            print(f"血管年龄均值: {vascular_age_stats.get('mean', 'N/A')}")
        
        # HRV数据
        lf_hf_stats = vascular_stats.get('lf_hf_ratio_stats', {})
        if lf_hf_stats:
            print(f"LF/HF比值均值: {lf_hf_stats.get('mean', 'N/A')}")
        
        # 炎症数据
        if inflammation:
            print(f"炎症风险等级: {inflammation.get('overall_risk_level', 'N/A')}")
            print(f"炎症风险评分: {inflammation.get('risk_score', 'N/A')}")
        
        # 计算各个风险因子评分
        print("\n各风险因子评分:")
        print("-" * 30)
        
        pwv_score = calculator.calculate_pwv_risk_score(pwv_stats)
        vascular_age_score = calculator.calculate_vascular_age_risk_score(vascular_age_stats)
        hrv_score = calculator.calculate_hrv_risk_score(lf_hf_stats)
        inflammation_score = calculator.calculate_inflammation_risk_score(inflammation)
        bp_var_score = calculator.calculate_bp_variability_risk_score(sleep_analysis.get('blood_pressure_rhythm_analysis', {}))
        bp_rhythm_score = calculator.calculate_bp_rhythm_risk_score(sleep_analysis.get('blood_pressure_rhythm_analysis', {}))
        sleep_apnea_score = calculator.calculate_sleep_apnea_risk_score(sleep_analysis)
        spo2_score = calculator.calculate_spo2_risk_score(sleep_analysis)
        arrhythmia_score = calculator.calculate_arrhythmia_risk_score(arrhythmia)
        
        print(f"PWV评分: {pwv_score:.3f}")
        print(f"血管年龄评分: {vascular_age_score:.3f}")
        print(f"HRV评分: {hrv_score:.3f}")
        print(f"炎症评分: {inflammation_score:.3f}")
        print(f"血压变异性评分: {bp_var_score:.3f}")
        print(f"血压昼夜节律评分: {bp_rhythm_score:.3f}")
        print(f"睡眠呼吸暂停评分: {sleep_apnea_score:.3f}")
        print(f"血氧饱和度评分: {spo2_score:.3f}")
        print(f"心律失常评分: {arrhythmia_score:.3f}")
        
        # 计算加权贡献
        print("\n心梗风险加权贡献:")
        print("-" * 30)
        mi_weights = calculator.risk_weights['mi_weights']
        
        mi_contributions = {
            'pwv': pwv_score * mi_weights['pwv'],
            'vascular_age': vascular_age_score * mi_weights['vascular_age'],
            'hrv': hrv_score * mi_weights['hrv'],
            'inflammation': inflammation_score * mi_weights['inflammation'],
            'bp_variability': bp_var_score * mi_weights['bp_variability'],
            'sleep_apnea': sleep_apnea_score * mi_weights['sleep_apnea'],
            'spo2': spo2_score * mi_weights['spo2']
        }
        
        for factor, contribution in mi_contributions.items():
            print(f"{factor:15}: {contribution:.4f}")
        
        total_mi = sum(mi_contributions.values())
        print(f"{'总计':15}: {total_mi:.4f}")
        
        print("\n脑卒中风险加权贡献:")
        print("-" * 30)
        stroke_weights = calculator.risk_weights['stroke_weights']
        
        stroke_contributions = {
            'bp_rhythm': bp_rhythm_score * stroke_weights['bp_rhythm'],
            'pwv': pwv_score * stroke_weights['pwv'],
            'bp_variability': bp_var_score * stroke_weights['bp_variability'],
            'vascular_age': vascular_age_score * stroke_weights['vascular_age'],
            'inflammation': inflammation_score * stroke_weights['inflammation'],
            'arrhythmia': arrhythmia_score * stroke_weights['arrhythmia'],
            'spo2': spo2_score * stroke_weights['spo2']
        }
        
        for factor, contribution in stroke_contributions.items():
            print(f"{factor:15}: {contribution:.4f}")
        
        total_stroke = sum(stroke_contributions.values())
        print(f"{'总计':15}: {total_stroke:.4f}")
        
    except Exception as e:
        print(f"分析文件时出错: {e}")

def main():
    """主函数"""
    print("风险评分0.6左右的原因分析")
    print("=" * 60)
    
    # 分析各个风险因子的评分分布
    analyze_individual_risk_factors()
    
    # 分析权重贡献
    analyze_weight_contribution()
    
    # 模拟不同场景
    simulate_risk_score_scenarios()
    
    # 分析实际数据模式
    analyze_actual_data_patterns()
    
    print("\n" + "=" * 60)
    print("分析总结:")
    print("=" * 60)
    print("1. 检查各个风险因子的评分分布")
    print("2. 分析权重配置是否合理")
    print("3. 模拟不同场景下的评分结果")
    print("4. 分析实际数据中的具体数值")
    print("5. 找出导致评分集中在0.6左右的根本原因")

if __name__ == "__main__":
    main()