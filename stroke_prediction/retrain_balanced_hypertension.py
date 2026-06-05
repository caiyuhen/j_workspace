#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import json
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from sklearn.utils.class_weight import compute_class_weight

def retrain_balanced_hypertension_model():
    """使用更平衡的数据重新训练高血压模型"""
    
    print("=== 重新训练平衡的高血压模型 ===")
    
    # 加载数据
    data = pd.read_csv('data/enhanced_8diseases_data.csv')
    print(f"原始数据形状: {data.shape}")
    
    # 加载特征映射
    with open('models/hypertension_feature_mapping.json', 'r') as f:
        feature_mapping = json.load(f)
    
    # 定义更严格的高血压标准
    def define_hypertension_balanced(row):
        systolic = row['systolic_bp']
        diastolic = row['diastolic_bp']
        
        # 使用更严格的标准
        # 正常: <130/80
        # 高血压前期: 130-139/80-89 (归为正常)
        # 高血压1期: 140-159/90-99
        # 高血压2期: >=160/100
        
        if systolic >= 150 or diastolic >= 95:  # 更严格的高血压标准
            return 1
        elif systolic < 125 and diastolic < 78:  # 更严格的正常标准
            return 0
        else:
            return None  # 中间区域，排除
    
    # 应用新的标签定义
    data['hypertension_balanced'] = data.apply(define_hypertension_balanced, axis=1)
    
    # 移除中间区域的样本
    data_filtered = data.dropna(subset=['hypertension_balanced']).copy()
    print(f"过滤后数据形状: {data_filtered.shape}")
    
    print(f"平衡标准下的高血压分布:")
    print(data_filtered['hypertension_balanced'].value_counts())
    print(f"高血压比例: {data_filtered['hypertension_balanced'].mean():.2%}")
    
    # 准备特征数据
    model_features = list(feature_mapping.keys())
    data_features = [feature_mapping[feat] for feat in model_features]
    
    # 创建特征矩阵
    X_raw = data_filtered[data_features].copy()
    y = data_filtered['hypertension_balanced'].copy()
    
    # 重命名列为模型期望的特征名
    X_raw.columns = model_features
    
    # 处理缺失值和数据转换
    feature_defaults = {
        'age': 45, 'systolic_bp': 120, 'diastolic_bp': 80, 'bmi': 25,
        'cholesterol_level': 200, 'avg_glucose_level': 100, 'hba1c_level': 5.5,
        'sleep_hours': 7, 'alcohol_consumption': 0, 'diabetes_duration': 0,
        'stress_level': 0, 'medication_adherence': 1, 'liver_function': 0,
        'kidney_function': 0, 'ever_married': 1
    }
    
    for feature in model_features:
        if feature in feature_defaults:
            X_raw[feature] = X_raw[feature].fillna(feature_defaults[feature])
        else:
            X_raw[feature] = X_raw[feature].fillna(X_raw[feature].median())
    
    # 特殊处理：反转肾病和肝功能指标（0=正常，1=异常）
    X_raw['liver_function'] = 1 - X_raw['liver_function']
    X_raw['kidney_function'] = 1 - X_raw['kidney_function']
    
    # 转换数据类型
    for col in X_raw.columns:
        X_raw[col] = pd.to_numeric(X_raw[col], errors='coerce')
    
    X_raw = X_raw.fillna(0)
    
    print(f"特征矩阵形状: {X_raw.shape}")
    print(f"目标变量分布: {y.value_counts()}")
    
    # 分割数据
    X_train, X_test, y_train, y_test = train_test_split(
        X_raw, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # 标准化特征
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # 计算类别权重
    class_weights = compute_class_weight(
        'balanced', 
        classes=np.unique(y_train), 
        y=y_train
    )
    class_weight_dict = {0: class_weights[0], 1: class_weights[1]}
    
    print(f"类别权重: {class_weight_dict}")
    
    # 训练随机森林模型
    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=10,
        min_samples_split=10,
        min_samples_leaf=5,
        class_weight=class_weight_dict,
        random_state=42,
        n_jobs=-1
    )
    
    print("训练模型...")
    model.fit(X_train_scaled, y_train)
    
    # 评估模型
    print("\n=== 模型评估 ===")
    
    # 训练集评估
    y_train_pred = model.predict(X_train_scaled)
    y_train_proba = model.predict_proba(X_train_scaled)[:, 1]
    
    print("训练集性能:")
    print(classification_report(y_train, y_train_pred))
    print(f"ROC AUC: {roc_auc_score(y_train, y_train_proba):.4f}")
    
    # 测试集评估
    y_test_pred = model.predict(X_test_scaled)
    y_test_proba = model.predict_proba(X_test_scaled)[:, 1]
    
    print("\\n测试集性能:")
    print(classification_report(y_test, y_test_pred))
    print(f"ROC AUC: {roc_auc_score(y_test, y_test_proba):.4f}")
    
    # 混淆矩阵
    cm = confusion_matrix(y_test, y_test_pred)
    tn, fp, fn, tp = cm.ravel()
    
    print(f"\\n混淆矩阵:")
    print(f"真阴性: {tn}, 假阳性: {fp}")
    print(f"假阴性: {fn}, 真阳性: {tp}")
    print(f"正常血压误判率: {fp/(tn+fp):.4f}")
    print(f"高血压漏诊率: {fn/(fn+tp):.4f}")
    
    # 特征重要性
    feature_importance = dict(zip(model_features, model.feature_importances_))
    sorted_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
    
    print(f"\\n特征重要性:")
    for feat, importance in sorted_features[:10]:
        print(f"  {feat}: {importance:.4f}")
    
    # 测试正常血压样本
    print("\\n=== 测试正常血压样本 ===")
    normal_samples = [
        [45, 120, 80, 23.5, 200, 100, 5.2, 7, 0, 0, 0, 1, 1, 1, 1],  # 理想血压
        [35, 115, 75, 22.0, 180, 95, 5.0, 8, 0, 0, 0, 1, 1, 1, 0],   # 低正常
        [50, 122, 78, 24.0, 190, 105, 5.4, 7, 0, 0, 0, 1, 1, 1, 1],  # 高正常
    ]
    
    for i, sample in enumerate(normal_samples):
        sample_scaled = scaler.transform([sample])
        prob = model.predict_proba(sample_scaled)[0][1]
        pred = model.predict(sample_scaled)[0]
        
        print(f"样本 {i+1}: 收缩压{sample[1]}/舒张压{sample[2]}")
        print(f"  预测概率: {prob:.4f}")
        print(f"  预测结果: {'高血压' if pred == 1 else '正常'}")
    
    # 保存模型
    joblib.dump(model, 'models/balanced_hypertension_model.joblib')
    joblib.dump(scaler, 'models/balanced_hypertension_scaler.joblib')
    
    # 保存特征配置
    feature_config = {
        'selected_features': model_features,
        'feature_importance': feature_importance,
        'model_type': 'balanced_random_forest',
        'class_weights': class_weight_dict,
        'test_auc': float(roc_auc_score(y_test, y_test_proba))
    }
    
    with open('models/balanced_hypertension_features.json', 'w') as f:
        json.dump(feature_config, f, indent=2)
    
    print(f"\\n平衡模型已保存:")
    print(f"  - models/balanced_hypertension_model.joblib")
    print(f"  - models/balanced_hypertension_scaler.joblib")
    print(f"  - models/balanced_hypertension_features.json")
    
    return model, scaler

if __name__ == "__main__":
    retrain_balanced_hypertension_model()