# 多疾病预测模型 - 训练模块

import numpy as np
import pandas as pd
import logging
import os
import time
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.multioutput import MultiOutputClassifier
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import roc_auc_score, accuracy_score, precision_score, recall_score, f1_score, classification_report
from sklearn.calibration import CalibratedClassifierCV
from imblearn.over_sampling import SMOTE
from joblib import dump, load
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple, Optional
from .multi_disease_data_processor import MultiDiseaseDataProcessor
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("XGBoost not available. Install with: pip install xgboost")

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MultiDiseaseTrainer:
    """多疾病预测训练器类，支持同时预测多种疾病风险"""
    
    def __init__(self, diseases: List[str] = None):
        """初始化多疾病预测训练器
        
        参数:
            diseases: 要预测的疾病列表，默认为8种疾病
        """
        if diseases is None:
            self.diseases = ['stroke', 'diabetes', 'arrhythmia', 'hypertension', 'kidney_disease', 'depression', 'anxiety', 'alzheimer']
        else:
            self.diseases = diseases
            
        self.models = {}  # 存储每个疾病的模型
        self.multi_task_model = None  # 多任务学习模型
        self.feature_importances = {}
        self.training_times = {}
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        self.data_processor = MultiDiseaseDataProcessor(diseases=self.diseases)
        self.feature_names = []
        
        logger.info(f"初始化多疾病预测训练器，目标疾病: {self.diseases}")
    
    def prepare_labels_from_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """从现有特征中推导疾病标签
        
        参数:
            df: 包含特征的数据框
            
        返回:
            包含疾病标签的数据框
        """
        logger.info("从特征数据中推导疾病标签...")
        
        # 复制数据框
        result_df = df.copy()
        
        # 糖尿病标签：基于糖尿病年限、血糖、糖化血红蛋白
        if 'diabetes' in self.diseases:
            diabetes_conditions = (
                (df.get('diabetes_years', 0) > 0) |
                (df.get('fasting_glucose', 0) >= 126) |
                (df.get('hba1c', 0) >= 6.5)
            )
            result_df['diabetes'] = diabetes_conditions.astype(int)
        
        # 心律失常标签：基于房颤和心率异常
        if 'arrhythmia' in self.diseases:
            arrhythmia_conditions = (
                (df.get('atrial_fibrillation', 0) == 1) |
                (df.get('heart_rate', 70) < 50) |
                (df.get('heart_rate', 70) > 100) |
                (df.get('heart_rate_variability', 30) < 15)
            )
            result_df['arrhythmia'] = arrhythmia_conditions.astype(int)
        
        # 高血压标签：基于血压值和高血压年限
        if 'hypertension' in self.diseases:
            hypertension_conditions = (
                (df.get('hypertension_years', 0) > 0) |
                (df.get('systolic_bp', 120) >= 140) |
                (df.get('diastolic_bp', 80) >= 90) |
                (df.get('avg_systolic_bp_24h', 120) >= 135)
            )
            result_df['hypertension'] = hypertension_conditions.astype(int)
        
        # 慢性肾病标签：基于现有肾病标志和相关指标
        if 'kidney_disease' in self.diseases:
            kidney_conditions = (
                (df.get('chronic_kidney_disease', 0) == 1) |
                ((df.get('diabetes_years', 0) > 10) & (df.get('systolic_bp', 120) > 140)) |
                ((df.get('age', 50) > 65) & (df.get('hypertension_years', 0) > 15))
            )
            result_df['kidney_disease'] = kidney_conditions.astype(int)
        
        # 记录各疾病的患病率
        for disease in self.diseases:
            if disease in result_df.columns:
                prevalence = result_df[disease].mean()
                logger.info(f"{disease} 患病率: {prevalence:.3f}")
        
        return result_df
    
    def load_data_from_file(self, data_path: str, test_size: float = 0.2):
        """从文件加载和预处理数据
        
        参数:
            data_path: 数据文件路径
            test_size: 测试集比例
        """
        logger.info(f"从文件加载数据: {data_path}")
        
        # 使用数据处理器准备数据
        X_train, y_train, X_test, y_test, feature_names = self.data_processor.prepare_multi_disease_data(
            data_path, test_size=test_size
        )
        
        self.X_train = X_train
        self.y_train = y_train
        self.X_test = X_test
        self.y_test = y_test
        self.feature_names = feature_names
        
        logger.info(f"数据加载完成，训练集: {X_train.shape}, 测试集: {X_test.shape}")
        
        # 检查标签列是否存在
        missing_diseases = [disease for disease in self.diseases if disease not in y_train.columns]
        if missing_diseases:
            logger.warning(f"缺少疾病标签: {missing_diseases}")
    
    def load_data(self, X_train: np.ndarray, y_train: pd.DataFrame, X_test: np.ndarray = None, y_test: pd.DataFrame = None, feature_names: List[str] = None):
        """直接加载预处理后的数据
        
        参数:
            X_train: 训练集特征
            y_train: 训练集多疾病标签
            X_test: 测试集特征
            y_test: 测试集多疾病标签
            feature_names: 特征名称列表
        """
        self.X_train = X_train
        self.y_train = y_train
        self.X_test = X_test
        self.y_test = y_test
        self.feature_names = feature_names if feature_names else [f'feature_{i}' for i in range(X_train.shape[1])]
        
        logger.info(f"数据加载完成，训练集形状: {X_train.shape}")
        logger.info(f"目标疾病数量: {len(self.diseases)}")
        
        # 检查标签列是否存在
        missing_diseases = [disease for disease in self.diseases if disease not in y_train.columns]
        if missing_diseases:
            logger.warning(f"缺少疾病标签: {missing_diseases}")
    
    def train_individual_models(self, model_type: str = 'gradient_boosting', use_smote: bool = True, **kwargs):
        """为每种疾病训练独立的模型
        
        参数:
            model_type: 模型类型
            use_smote: 是否使用SMOTE处理类别不平衡
            **kwargs: 模型参数
        """
        logger.info(f"开始训练独立模型，模型类型: {model_type}")
        
        for disease in self.diseases:
            if disease not in self.y_train.columns:
                logger.warning(f"标签中缺少疾病: {disease}，跳过训练")
                continue
                
            logger.info(f"训练 {disease} 预测模型...")
            start_time = time.time()
            
            # 获取当前疾病的标签
            y_disease = self.y_train[disease]
            
            # 处理类别不平衡
            X_train_disease = self.X_train
            y_train_disease = y_disease
            
            if use_smote and len(np.unique(y_disease)) > 1:
                try:
                    smote = SMOTE(random_state=42)
                    X_train_disease, y_train_disease = smote.fit_resample(self.X_train, y_disease)
                    logger.info(f"{disease}: SMOTE后样本数量 {X_train_disease.shape[0]}")
                except Exception as e:
                    logger.warning(f"{disease}: SMOTE失败，使用原始数据: {e}")
            
            # 创建模型
            model = self._create_model(model_type, **kwargs)
            
            # 训练模型
            model.fit(X_train_disease, y_train_disease)
            
            # 保存模型和训练时间
            self.models[disease] = model
            self.training_times[disease] = time.time() - start_time
            
            # 获取特征重要性
            if hasattr(model, 'feature_importances_'):
                self.feature_importances[disease] = model.feature_importances_
            elif hasattr(model, 'coef_'):
                self.feature_importances[disease] = np.abs(model.coef_[0])
            
            logger.info(f"{disease} 模型训练完成，耗时: {self.training_times[disease]:.2f}秒")
    
    def train_multi_task_model(self, model_type: str = 'gradient_boosting', use_smote: bool = True, **kwargs):
        """训练多任务学习模型
        
        参数:
            model_type: 基础模型类型
            use_smote: 是否使用SMOTE处理类别不平衡
            **kwargs: 模型参数
        """
        logger.info(f"开始训练多任务学习模型，基础模型: {model_type}")
        start_time = time.time()
        
        # 准备多标签数据
        y_multi = self.y_train[self.diseases].values
        
        # 处理类别不平衡
        X_train_multi = self.X_train
        y_train_multi = y_multi
        
        if use_smote:
            try:
                # 对多标签问题，我们需要特殊处理
                # 这里简化处理，只对主要疾病（如stroke）进行SMOTE
                primary_disease = 'stroke' if 'stroke' in self.diseases else self.diseases[0]
                if primary_disease in self.y_train.columns:
                    smote = SMOTE(random_state=42)
                    X_train_multi, y_primary = smote.fit_resample(self.X_train, self.y_train[primary_disease])
                    # 重新获取对应的多标签
                    indices = smote.sample_indices_
                    y_train_multi = y_multi[indices]
                    logger.info(f"多任务SMOTE后样本数量: {X_train_multi.shape[0]}")
            except Exception as e:
                logger.warning(f"多任务SMOTE失败，使用原始数据: {e}")
        
        # 创建多输出分类器
        base_model = self._create_model(model_type, **kwargs)
        self.multi_task_model = MultiOutputClassifier(base_model, n_jobs=-1)
        
        # 训练模型
        self.multi_task_model.fit(X_train_multi, y_train_multi)
        
        training_time = time.time() - start_time
        logger.info(f"多任务模型训练完成，耗时: {training_time:.2f}秒")
    
    def _create_model(self, model_type: str, **kwargs):
        """创建指定类型的模型
        
        参数:
            model_type: 模型类型
            **kwargs: 模型参数
            
        返回:
            模型实例
        """
        if model_type == 'logistic':
            return LogisticRegression(
                class_weight='balanced',
                random_state=42,
                max_iter=1000,
                **kwargs
            )
        elif model_type == 'random_forest':
            return RandomForestClassifier(
                n_estimators=kwargs.get('n_estimators', 100),
                class_weight='balanced',
                random_state=42,
                n_jobs=-1,
                **{k: v for k, v in kwargs.items() if k != 'n_estimators'}
            )
        elif model_type == 'gradient_boosting':
            return GradientBoostingClassifier(
                n_estimators=kwargs.get('n_estimators', 100),
                learning_rate=kwargs.get('learning_rate', 0.1),
                max_depth=kwargs.get('max_depth', 6),
                random_state=kwargs.get('random_state', 42)
            )
        elif model_type == 'xgboost':
            return xgb.XGBClassifier(
                n_estimators=kwargs.get('n_estimators', 100),
                learning_rate=kwargs.get('learning_rate', 0.1),
                random_state=42,
                eval_metric='logloss',
                **{k: v for k, v in kwargs.items() if k not in ['n_estimators', 'learning_rate']}
            )
        else:
            raise ValueError(f"不支持的模型类型: {model_type}")
    
    def predict(self, X: np.ndarray, use_multi_task: bool = False) -> Dict[str, np.ndarray]:
        """预测多种疾病的风险
        
        参数:
            X: 特征数据
            use_multi_task: 是否使用多任务模型
            
        返回:
            各疾病的预测结果字典
        """
        predictions = {}
        
        if use_multi_task and self.multi_task_model is not None:
            # 使用多任务模型预测
            multi_pred = self.multi_task_model.predict_proba(X)
            for i, disease in enumerate(self.diseases):
                # 多输出分类器返回的是每个输出的概率数组列表
                if len(multi_pred[i].shape) > 1 and multi_pred[i].shape[1] > 1:
                    predictions[disease] = multi_pred[i][:, 1]  # 正类概率
                else:
                    predictions[disease] = multi_pred[i].ravel()
        else:
            # 使用独立模型预测
            for disease in self.diseases:
                if disease in self.models:
                    model = self.models[disease]
                    if hasattr(model, 'predict_proba'):
                        pred_proba = model.predict_proba(X)
                        if pred_proba.shape[1] > 1:
                            predictions[disease] = pred_proba[:, 1]  # 正类概率
                        else:
                            predictions[disease] = pred_proba.ravel()
                    else:
                        predictions[disease] = model.predict(X)
        
        return predictions
    
    def evaluate(self, X_test: np.ndarray = None, y_test: pd.DataFrame = None, use_multi_task: bool = False) -> Dict[str, Dict[str, float]]:
        """评估模型性能
        
        参数:
            X_test: 测试集特征
            y_test: 测试集标签
            use_multi_task: 是否使用多任务模型
            
        返回:
            各疾病的评估指标字典
        """
        if X_test is None:
            X_test = self.X_test
        if y_test is None:
            y_test = self.y_test
            
        if X_test is None or y_test is None:
            logger.error("缺少测试数据")
            return {}
        
        # 获取预测结果
        predictions = self.predict(X_test, use_multi_task=use_multi_task)
        
        results = {}
        for disease in self.diseases:
            if disease not in y_test.columns or disease not in predictions:
                continue
                
            y_true = y_test[disease]
            y_pred_proba = predictions[disease]
            y_pred = (y_pred_proba > 0.5).astype(int)
            
            # 计算评估指标
            try:
                results[disease] = {
                    'accuracy': accuracy_score(y_true, y_pred),
                    'precision': precision_score(y_true, y_pred, zero_division=0),
                    'recall': recall_score(y_true, y_pred, zero_division=0),
                    'f1': f1_score(y_true, y_pred, zero_division=0),
                    'auc': roc_auc_score(y_true, y_pred_proba) if len(np.unique(y_true)) > 1 else 0.0
                }
            except Exception as e:
                logger.warning(f"{disease} 评估失败: {e}")
                results[disease] = {'error': str(e)}
        
        return results
    
    def save_models(self, save_dir: str):
        """保存训练好的模型
        
        参数:
            save_dir: 保存目录
        """
        os.makedirs(save_dir, exist_ok=True)
        
        # 保存独立模型
        for disease, model in self.models.items():
            model_path = os.path.join(save_dir, f'{disease}_model.joblib')
            dump(model, model_path)
            logger.info(f"{disease} 模型已保存至: {model_path}")
        
        # 保存多任务模型
        if self.multi_task_model is not None:
            multi_task_path = os.path.join(save_dir, 'multi_task_model.joblib')
            dump(self.multi_task_model, multi_task_path)
            logger.info(f"多任务模型已保存至: {multi_task_path}")
        
        # 保存特征重要性
        if self.feature_importances:
            import json
            importance_path = os.path.join(save_dir, 'feature_importances.json')
            # 转换numpy数组为列表以便JSON序列化
            importance_dict = {}
            for disease, importance in self.feature_importances.items():
                if isinstance(importance, np.ndarray):
                    importance_dict[disease] = importance.tolist()
                else:
                    importance_dict[disease] = importance
            
            with open(importance_path, 'w', encoding='utf-8') as f:
                json.dump(importance_dict, f, indent=2, ensure_ascii=False)
            logger.info(f"特征重要性已保存至: {importance_path}")
    
    def load_models(self, save_dir: str):
        """加载训练好的模型
        
        参数:
            save_dir: 模型保存目录
        """
        # 加载独立模型
        for disease in self.diseases:
            model_path = os.path.join(save_dir, f'{disease}_model.joblib')
            if os.path.exists(model_path):
                self.models[disease] = load(model_path)
                logger.info(f"{disease} 模型已加载")
        
        # 加载多任务模型
        multi_task_path = os.path.join(save_dir, 'multi_task_model.joblib')
        if os.path.exists(multi_task_path):
            self.multi_task_model = load(multi_task_path)
            logger.info("多任务模型已加载")
        
        # 加载特征重要性
        importance_path = os.path.join(save_dir, 'feature_importances.json')
        if os.path.exists(importance_path):
            import json
            with open(importance_path, 'r', encoding='utf-8') as f:
                self.feature_importances = json.load(f)
            logger.info("特征重要性已加载")
    
    def plot_feature_importance(self, disease: str, top_n: int = 20, save_path: str = None):
        """绘制特征重要性图
        
        参数:
            disease: 疾病名称
            top_n: 显示前N个重要特征
            save_path: 保存路径
        """
        if disease not in self.feature_importances:
            logger.warning(f"没有找到 {disease} 的特征重要性数据")
            return
        
        importance = self.feature_importances[disease]
        
        # 使用实际的特征名称
        feature_names = self.feature_names if self.feature_names else [f'feature_{i}' for i in range(len(importance))]
        
        # 排序并选择前N个
        indices = np.argsort(importance)[::-1][:top_n]
        
        plt.figure(figsize=(12, 8))
        plt.title(f'{disease.title()} - Top {top_n} Feature Importance')
        plt.bar(range(top_n), importance[indices])
        plt.xticks(range(top_n), [feature_names[i] for i in indices], rotation=45, ha='right')
        plt.xlabel('特征')
        plt.ylabel('重要性')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"特征重要性图已保存至: {save_path}")
        
        plt.show()
    
    def plot_all_feature_importances(self, top_n: int = 15, save_dir: str = None):
        """绘制所有疾病的特征重要性图
        
        参数:
            top_n: 显示前N个重要特征
            save_dir: 保存目录
        """
        n_diseases = len(self.feature_importances)
        if n_diseases == 0:
            logger.warning("没有特征重要性数据")
            return
        
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        axes = axes.flatten()
        
        for i, (disease, importance) in enumerate(self.feature_importances.items()):
            if i >= len(axes):
                break
                
            feature_names = self.feature_names if self.feature_names else [f'feature_{j}' for j in range(len(importance))]
            indices = np.argsort(importance)[::-1][:top_n]
            
            axes[i].bar(range(top_n), importance[indices])
            axes[i].set_title(f'{disease.title()}')
            axes[i].set_xticks(range(top_n))
            axes[i].set_xticklabels([feature_names[j] for j in indices], rotation=45, ha='right')
            axes[i].set_ylabel('重要性')
        
        # 隐藏多余的子图
        for i in range(len(self.feature_importances), len(axes)):
            axes[i].set_visible(False)
        
        plt.tight_layout()
        
        if save_dir:
            os.makedirs(save_dir, exist_ok=True)
            save_path = os.path.join(save_dir, 'all_feature_importances.png')
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"所有特征重要性图已保存至: {save_path}")
        
        plt.show()