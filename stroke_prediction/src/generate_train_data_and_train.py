# 卒中预测模型 - 训练数据生成与模型训练脚本

import os
import sys
import pandas as pd
import numpy as np
import logging
import time
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# 添加项目根目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入自定义模块
from new_stroke_data_generator import generate_stroke_dataset, save_dataset
from model_training import ModelTrainer

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 创建日志目录
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
os.makedirs(log_dir, exist_ok=True)

# 创建文件处理器
log_file = os.path.join(log_dir, f'train_data_generation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

def generate_train_data(n_samples=3000, random_state=42, output_path=None):
    """
    生成训练数据集
    
    参数:
        n_samples (int): 样本数量
        random_state (int): 随机种子
        output_path (str): 输出文件路径
        
    返回:
        pd.DataFrame: 生成的数据集
    """
    logger.info(f"开始生成{n_samples}条训练数据...")
    
    # 设置随机种子
    np.random.seed(random_state)
    
    # 生成数据
    train_data = generate_stroke_dataset(n_samples=n_samples, random_state=random_state)
    
    # 格式化日期列
    if 'exam_date' in train_data.columns:
        train_data['exam_date'] = pd.to_datetime(train_data['exam_date']).dt.strftime('%Y/%m/%d')
    
    # 保存数据
    if output_path:
        save_dataset(train_data, output_path)
        logger.info(f"训练数据已保存至: {output_path}")
    
    # 打印数据信息
    logger.info(f"生成的训练数据形状: {train_data.shape}")
    logger.info(f"卒中样本比例: {train_data['stroke'].mean():.2f}")
    
    return train_data

def preprocess_data(data):
    """
    数据预处理
    
    参数:
        data (pd.DataFrame): 原始数据
        
    返回:
        tuple: (X, y, feature_names) 处理后的特征、标签和特征名称
    """
    logger.info("开始数据预处理...")
    
    # 复制数据，避免修改原始数据
    df = data.copy()
    
    # 移除不需要的列
    cols_to_drop = ['patient_id', 'exam_date']
    df = df.drop(columns=[col for col in cols_to_drop if col in df.columns])
    
    # 处理缺失值
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].fillna('unknown')
        else:
            df[col] = df[col].fillna(df[col].median())
    
    # 处理特殊值（例如'-'）
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].replace(' -   ', np.nan)
            df[col] = df[col].fillna(df[col].mode()[0] if not df[col].mode().empty else 0)
    
    # 分离特征和标签
    y = df['stroke']
    X = df.drop('stroke', axis=1)
    
    # 处理分类特征
    cat_features = X.select_dtypes(include=['object']).columns.tolist()
    X = pd.get_dummies(X, columns=cat_features, drop_first=True)
    
    # 获取特征名称
    feature_names = X.columns.tolist()
    
    logger.info(f"预处理后的特征数量: {len(feature_names)}")
    
    return X, y, feature_names

def train_model(X, y, model_type='gradient_boosting', use_smote=True, save_path=None):
    """
    训练模型
    
    参数:
        X (pd.DataFrame): 特征数据
        y (pd.Series): 标签数据
        model_type (str): 模型类型
        use_smote (bool): 是否使用SMOTE过采样
        save_path (str): 模型保存路径
        
    返回:
        ModelTrainer: 训练好的模型训练器实例
    """
    logger.info(f"开始训练{model_type}模型...")
    
    # 划分训练集和测试集
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # 标准化数值特征
    scaler = StandardScaler()
    X_train = pd.DataFrame(scaler.fit_transform(X_train), columns=X_train.columns)
    X_test = pd.DataFrame(scaler.transform(X_test), columns=X_test.columns)
    
    # 创建模型训练器
    trainer = ModelTrainer(X_train, y_train, X_test, y_test)
    
    # 训练模型
    if use_smote:
        # 使用SMOTE过采样训练模型
        if model_type == 'gradient_boosting':
            trainer.train_with_smote(
                model_type=model_type,
                sampling_strategy=1.0,  # 完全平衡类别分布
                k_neighbors=5,
                n_estimators=100,
                learning_rate=0.1,
                max_depth=5,
                min_samples_split=2,
                min_samples_leaf=1,
                subsample=0.8
            )
        elif model_type == 'random_forest':
            trainer.train_with_smote(
                model_type=model_type,
                sampling_strategy=1.0,
                k_neighbors=5,
                n_estimators=100,
                max_depth=10,
                min_samples_split=2,
                min_samples_leaf=1,
                class_weight='balanced'
            )
        elif model_type == 'xgboost':
            trainer.train_with_smote(
                model_type=model_type,
                sampling_strategy=1.0,
                k_neighbors=5,
                n_estimators=100,
                learning_rate=0.1,
                max_depth=5,
                subsample=0.8,
                colsample_bytree=0.8
            )
        else:
            # 默认使用梯度提升
            trainer.train_with_smote(
                model_type='gradient_boosting',
                sampling_strategy=1.0,
                k_neighbors=5
            )
    else:
        # 不使用SMOTE，直接训练模型
        if model_type == 'gradient_boosting':
            trainer.train_gradient_boosting(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=5,
                min_samples_split=2,
                min_samples_leaf=1,
                subsample=0.8
            )
        elif model_type == 'random_forest':
            trainer.train_random_forest(
                n_estimators=100,
                max_depth=10,
                min_samples_split=2,
                min_samples_leaf=1,
                class_weight='balanced'
            )
        elif model_type == 'logistic':
            trainer.train_logistic_regression(
                class_weight='balanced',
                C=1.0,
                solver='liblinear',
                max_iter=1000
            )
        else:
            # 默认使用梯度提升
            trainer.train_gradient_boosting()
    
    # 评估模型
    metrics = trainer.evaluate_model()
    logger.info(f"模型评估结果: {metrics}")
    
    # 打印特征重要性
    if trainer.feature_importances is not None:
        feature_importance = pd.DataFrame({
            'feature': X.columns,
            'importance': trainer.feature_importances
        })
        feature_importance = feature_importance.sort_values('importance', ascending=False)
        
        # 打印前20个重要特征
        logger.info("前20个重要特征:")
        for i, (feature, importance) in enumerate(zip(feature_importance['feature'].head(20), 
                                                  feature_importance['importance'].head(20))):
            logger.info(f"{i+1}. {feature}: {importance:.4f}")
    
    # 保存模型
    if save_path:
        trainer.save_model(save_path, save_metrics=True)
        logger.info(f"模型已保存至: {save_path}")
    
    return trainer

def plot_feature_importance(trainer, X, output_path=None):
    """
    绘制特征重要性图
    
    参数:
        trainer (ModelTrainer): 训练好的模型训练器实例
        X (pd.DataFrame): 特征数据
        output_path (str): 输出文件路径
    """
    if trainer.feature_importances is None:
        logger.warning("模型没有特征重要性信息，无法绘图")
        return
    
    # 创建特征重要性DataFrame
    feature_importance = pd.DataFrame({
        'feature': X.columns,
        'importance': trainer.feature_importances
    })
    feature_importance = feature_importance.sort_values('importance', ascending=False)
    
    # 绘制前20个重要特征
    plt.figure(figsize=(12, 8))
    sns.barplot(x='importance', y='feature', data=feature_importance.head(20))
    plt.title('Top 20 Feature Importance')
    plt.tight_layout()
    
    # 保存图表
    if output_path:
        plt.savefig(output_path)
        logger.info(f"特征重要性图已保存至: {output_path}")
    
    plt.close()

def main():
    # 设置路径
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(project_dir, 'data')
    raw_data_dir = os.path.join(data_dir, 'raw')
    processed_data_dir = os.path.join(data_dir, 'processed')
    models_dir = os.path.join(project_dir, 'models')
    results_dir = os.path.join(project_dir, 'results')
    
    # 创建必要的目录
    os.makedirs(raw_data_dir, exist_ok=True)
    os.makedirs(processed_data_dir, exist_ok=True)
    os.makedirs(models_dir, exist_ok=True)
    os.makedirs(results_dir, exist_ok=True)
    
    # 设置文件路径
    original_data_path = os.path.join(raw_data_dir, 'stroke_data1.csv')
    train_data_path = os.path.join(raw_data_dir, 'stroke_train_data.csv')
    model_path = os.path.join(models_dir, 'stroke_prediction_model.joblib')
    feature_importance_path = os.path.join(results_dir, 'feature_importance.png')
    
    # 检查原始数据是否存在
    if not os.path.exists(original_data_path):
        logger.error(f"原始数据文件不存在: {original_data_path}")
        return
    
    # 生成训练数据
    train_data = generate_train_data(n_samples=3000, random_state=42, output_path=train_data_path)
    
    # 预处理数据
    X, y, feature_names = preprocess_data(train_data)
    
    # 训练模型
    trainer = train_model(X, y, model_type='gradient_boosting', use_smote=True, save_path=model_path)
    
    # 绘制特征重要性
    plot_feature_importance(trainer, X, output_path=feature_importance_path)
    
    logger.info("训练数据生成与模型训练完成")

if __name__ == "__main__":
    main()