# 卒中预测模型 - 模型训练模块

import numpy as np
import pandas as pd
import logging
import os
import time
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV
from sklearn.pipeline import Pipeline
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import roc_auc_score, accuracy_score, precision_score, recall_score, f1_score
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline
from joblib import dump, load
import xgboost as xgb
import lightgbm as lgb

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ModelTrainer:
    """模型训练类，负责模型训练、调优和保存"""
    
    def __init__(self, X_train=None, y_train=None, X_test=None, y_test=None):
        """初始化模型训练器
        
        参数:
            X_train: 训练集特征
            y_train: 训练集标签
            X_test: 测试集特征
            y_test: 测试集标签
        """
        self.X_train = X_train
        self.y_train = y_train
        self.X_test = X_test
        self.y_test = y_test
        self.model = None
        self.best_params = None
        self.feature_importances = None
        self.training_time = None
        self.is_calibrated = False
    
    def load_data(self, X_train, y_train, X_test=None, y_test=None):
        """加载数据
        
        参数:
            X_train: 训练集特征
            y_train: 训练集标签
            X_test: 测试集特征
            y_test: 测试集标签
        """
        self.X_train = X_train
        self.y_train = y_train
        self.X_test = X_test
        self.y_test = y_test
        logger.info(f"数据加载完成，训练集形状: {X_train.shape}")
    
    def train_logistic_regression(self, class_weight='balanced', C=1.0, solver='liblinear', max_iter=1000):
        """训练逻辑回归模型
        
        参数:
            class_weight (str or dict): 类别权重
            C (float): 正则化强度的倒数
            solver (str): 优化算法
            max_iter (int): 最大迭代次数
            
        返回:
            self: 训练器实例
        """
        if self.X_train is None or self.y_train is None:
            logger.warning("数据尚未加载，无法训练模型")
            return self
        
        logger.info("开始训练逻辑回归模型...")
        start_time = time.time()
        
        # 创建逻辑回归模型
        model = LogisticRegression(
            class_weight=class_weight,
            C=C,
            solver=solver,
            max_iter=max_iter,
            random_state=42
        )
        
        # 训练模型
        model.fit(self.X_train, self.y_train)
        
        # 记录训练时间
        self.training_time = time.time() - start_time
        logger.info(f"逻辑回归模型训练完成，耗时: {self.training_time:.2f}秒")
        
        # 保存模型和参数
        self.model = model
        self.best_params = {
            'class_weight': class_weight,
            'C': C,
            'solver': solver,
            'max_iter': max_iter
        }
        
        # 获取特征重要性（系数的绝对值）
        if hasattr(model, 'coef_'):
            self.feature_importances = np.abs(model.coef_[0])
        
        return self
    
    def train_random_forest(self, n_estimators=100, max_depth=None, min_samples_split=2, 
                           min_samples_leaf=1, class_weight='balanced'):
        """训练随机森林模型
        
        参数:
            n_estimators (int): 树的数量
            max_depth (int): 树的最大深度
            min_samples_split (int): 分裂内部节点所需的最小样本数
            min_samples_leaf (int): 叶节点所需的最小样本数
            class_weight (str or dict): 类别权重
            
        返回:
            self: 训练器实例
        """
        if self.X_train is None or self.y_train is None:
            logger.warning("数据尚未加载，无法训练模型")
            return self
        
        logger.info("开始训练随机森林模型...")
        start_time = time.time()
        
        # 创建随机森林模型
        model = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            min_samples_split=min_samples_split,
            min_samples_leaf=min_samples_leaf,
            class_weight=class_weight,
            random_state=42,
            n_jobs=-1
        )
        
        # 训练模型
        model.fit(self.X_train, self.y_train)
        
        # 记录训练时间
        self.training_time = time.time() - start_time
        logger.info(f"随机森林模型训练完成，耗时: {self.training_time:.2f}秒")
        
        # 保存模型和参数
        self.model = model
        self.best_params = {
            'n_estimators': n_estimators,
            'max_depth': max_depth,
            'min_samples_split': min_samples_split,
            'min_samples_leaf': min_samples_leaf,
            'class_weight': class_weight
        }
        
        # 获取特征重要性
        if hasattr(model, 'feature_importances_'):
            self.feature_importances = model.feature_importances_
        
        return self
    
    def train_gradient_boosting(self, n_estimators=100, learning_rate=0.1, max_depth=3, 
                               min_samples_split=2, min_samples_leaf=1, subsample=1.0):
        """训练梯度提升模型
        
        参数:
            n_estimators (int): 树的数量
            learning_rate (float): 学习率
            max_depth (int): 树的最大深度
            min_samples_split (int): 分裂内部节点所需的最小样本数
            min_samples_leaf (int): 叶节点所需的最小样本数
            subsample (float): 用于拟合个体基础学习器的样本比例
            
        返回:
            self: 训练器实例
        """
        if self.X_train is None or self.y_train is None:
            logger.warning("数据尚未加载，无法训练模型")
            return self
        
        logger.info("开始训练梯度提升模型...")
        start_time = time.time()
        
        # 创建梯度提升模型
        model = GradientBoostingClassifier(
            n_estimators=n_estimators,
            learning_rate=learning_rate,
            max_depth=max_depth,
            min_samples_split=min_samples_split,
            min_samples_leaf=min_samples_leaf,
            subsample=subsample,
            random_state=42
        )
        
        # 训练模型
        model.fit(self.X_train, self.y_train)
        
        # 记录训练时间
        self.training_time = time.time() - start_time
        logger.info(f"梯度提升模型训练完成，耗时: {self.training_time:.2f}秒")
        
        # 保存模型和参数
        self.model = model
        self.best_params = {
            'n_estimators': n_estimators,
            'learning_rate': learning_rate,
            'max_depth': max_depth,
            'min_samples_split': min_samples_split,
            'min_samples_leaf': min_samples_leaf,
            'subsample': subsample
        }
        
        # 获取特征重要性
        if hasattr(model, 'feature_importances_'):
            self.feature_importances = model.feature_importances_
        
        return self
    
    def train_svm(self, C=1.0, kernel='rbf', gamma='scale', class_weight='balanced', probability=True):
        """训练支持向量机模型
        
        参数:
            C (float): 正则化参数
            kernel (str): 核函数类型
            gamma (str or float): 核系数
            class_weight (str or dict): 类别权重
            probability (bool): 是否启用概率估计
            
        返回:
            self: 训练器实例
        """
        if self.X_train is None or self.y_train is None:
            logger.warning("数据尚未加载，无法训练模型")
            return self
        
        logger.info("开始训练支持向量机模型...")
        start_time = time.time()
        
        # 创建SVM模型
        model = SVC(
            C=C,
            kernel=kernel,
            gamma=gamma,
            class_weight=class_weight,
            probability=probability,
            random_state=42
        )
        
        # 训练模型
        model.fit(self.X_train, self.y_train)
        
        # 记录训练时间
        self.training_time = time.time() - start_time
        logger.info(f"支持向量机模型训练完成，耗时: {self.training_time:.2f}秒")
        
        # 保存模型和参数
        self.model = model
        self.best_params = {
            'C': C,
            'kernel': kernel,
            'gamma': gamma,
            'class_weight': class_weight,
            'probability': probability
        }
        
        # SVM没有直接的特征重要性
        self.feature_importances = None
        
        return self
    
    def train_neural_network(self, hidden_layer_sizes=(100,), activation='relu', solver='adam', 
                            alpha=0.0001, learning_rate='constant', max_iter=200):
        """训练神经网络模型
        
        参数:
            hidden_layer_sizes (tuple): 隐藏层大小
            activation (str): 激活函数
            solver (str): 权重优化器
            alpha (float): L2惩罚参数
            learning_rate (str): 学习率调度
            max_iter (int): 最大迭代次数
            
        返回:
            self: 训练器实例
        """
        if self.X_train is None or self.y_train is None:
            logger.warning("数据尚未加载，无法训练模型")
            return self
        
        logger.info("开始训练神经网络模型...")
        start_time = time.time()
        
        # 创建神经网络模型
        model = MLPClassifier(
            hidden_layer_sizes=hidden_layer_sizes,
            activation=activation,
            solver=solver,
            alpha=alpha,
            learning_rate=learning_rate,
            max_iter=max_iter,
            random_state=42
        )
        
        # 训练模型
        model.fit(self.X_train, self.y_train)
        
        # 记录训练时间
        self.training_time = time.time() - start_time
        logger.info(f"神经网络模型训练完成，耗时: {self.training_time:.2f}秒")
        
        # 保存模型和参数
        self.model = model
        self.best_params = {
            'hidden_layer_sizes': hidden_layer_sizes,
            'activation': activation,
            'solver': solver,
            'alpha': alpha,
            'learning_rate': learning_rate,
            'max_iter': max_iter
        }
        
        # 神经网络没有直接的特征重要性
        self.feature_importances = None
        
        return self
        
    def train_xgboost(self, n_estimators=100, learning_rate=0.1, max_depth=3, 
                     min_child_weight=1, subsample=1.0, colsample_bytree=1.0, 
                     gamma=0, reg_alpha=0, reg_lambda=1, scale_pos_weight=10):
        """训练XGBoost模型
        
        参数:
            n_estimators (int): 树的数量
            learning_rate (float): 学习率
            max_depth (int): 树的最大深度
            min_child_weight (int): 子节点所需的最小样本权重和
            subsample (float): 训练实例的子采样比例
            colsample_bytree (float): 构建树时特征的子采样比例
            gamma (float): 在节点分裂时所需的最小损失函数减少量
            reg_alpha (float): L1正则化项
            reg_lambda (float): L2正则化项
            scale_pos_weight (float): 正样本的权重，默认设为10以显著提高召回率
            
        返回:
            self: 训练器实例
        """
        
    def train_high_recall_xgboost(self, X_train=None, y_train=None):
        """训练专注于高召回率的XGBoost模型
        
        该方法使用特定的参数组合来最大化召回率，适用于需要尽可能减少假阴性的场景，
        如脑卒中风险预测，其中漏诊的代价远高于误诊。
        
        参数组合包括：
        - 高scale_pos_weight (20)：显著增加正样本权重
        - 较低的分类阈值 (0.005)：降低预测为阳性的门槛
        - 较大的max_depth (5)：增加模型复杂度以捕获更多模式
        - 较小的min_child_weight (0.5)：允许更细粒度的分裂
        - 使用F2分数作为评估指标：更注重召回率而非精确率
        
        参数:
            X_train: 训练集特征，如果提供则使用此数据，否则使用self.X_train
            y_train: 训练集标签，如果提供则使用此数据，否则使用self.y_train
            
        返回:
            self: 训练器实例
        """
        logger.info("训练高召回率XGBoost模型")
        
        # 如果提供了X_train和y_train，则使用这些数据
        if X_train is not None and y_train is not None:
            self.load_data(X_train, y_train)
        
        # 检查数据是否已加载
        if self.X_train is None or self.y_train is None:
            logger.warning("数据尚未加载，无法训练模型")
            return self
        
        # 使用专注于召回率的参数
        params = {
            'n_estimators': 200,
            'learning_rate': 0.05,
            'max_depth': 5,
            'min_child_weight': 0.5,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'gamma': 0,
            'reg_alpha': 0,
            'reg_lambda': 0.5,
            'scale_pos_weight': 20,
            'objective': 'binary:logistic',
            'eval_metric': 'auc',
            'use_label_encoder': False
        }
        
        # 创建XGBoost分类器
        model = xgb.XGBClassifier(**params)
        
        # 训练模型
        start_time = time.time()
        model.fit(self.X_train, self.y_train)
        training_time = time.time() - start_time
        
        # 保存模型和元数据
        self.model = model
        self.model_type = 'xgboost_high_recall'
        self.best_params = params
        self.training_time = training_time
        self.is_calibrated = False
        
        # 获取特征重要性（如果模型支持）
        if hasattr(model, 'feature_importances_'):
            self.feature_importances = model.feature_importances_
        else:
            self.feature_importances = None
        
        logger.info(f"高召回率XGBoost模型训练完成，耗时 {training_time:.2f} 秒")
        return self
    
    def train_lightgbm(self, n_estimators=100, learning_rate=0.1, max_depth=-1, 
                      num_leaves=31, min_child_samples=20, subsample=1.0, 
                      colsample_bytree=1.0, reg_alpha=0, reg_lambda=0, 
                      class_weight=None):
        """训练LightGBM模型
        
        参数:
            n_estimators (int): 树的数量
            learning_rate (float): 学习率
            max_depth (int): 树的最大深度，-1表示无限制
            num_leaves (int): 一棵树上的最大叶子数
            min_child_samples (int): 一个叶子节点所需的最小样本数
            subsample (float): 训练实例的子采样比例
            colsample_bytree (float): 构建树时特征的子采样比例
            reg_alpha (float): L1正则化项
            reg_lambda (float): L2正则化项
            class_weight (dict or str): 类别权重
            
        返回:
            self: 训练器实例
        """
        if self.X_train is None or self.y_train is None:
            logger.warning("数据尚未加载，无法训练模型")
            return self
        
        logger.info("开始训练LightGBM模型...")
        start_time = time.time()
        
        # 创建LightGBM模型
        model = lgb.LGBMClassifier(
            n_estimators=n_estimators,
            learning_rate=learning_rate,
            max_depth=max_depth,
            num_leaves=num_leaves,
            min_child_samples=min_child_samples,
            subsample=subsample,
            colsample_bytree=colsample_bytree,
            reg_alpha=reg_alpha,
            reg_lambda=reg_lambda,
            class_weight=class_weight,
            random_state=42
        )
        
        # 训练模型
        model.fit(self.X_train, self.y_train)
        
        # 记录训练时间
        self.training_time = time.time() - start_time
        logger.info(f"LightGBM模型训练完成，耗时: {self.training_time:.2f}秒")
        
        # 保存模型和参数
        self.model = model
        self.best_params = {
            'n_estimators': n_estimators,
            'learning_rate': learning_rate,
            'max_depth': max_depth,
            'num_leaves': num_leaves,
            'min_child_samples': min_child_samples,
            'subsample': subsample,
            'colsample_bytree': colsample_bytree,
            'reg_alpha': reg_alpha,
            'reg_lambda': reg_lambda,
            'class_weight': class_weight
        }
        
        # 获取特征重要性
        if hasattr(model, 'feature_importances_'):
            self.feature_importances = model.feature_importances_
        
        return self
    
    def train_with_smote(self, model_type='gradient_boosting', sampling_strategy=1.0, k_neighbors=5, **model_params):
        """使用SMOTE过采样训练模型
        
        参数:
            model_type (str): 模型类型，可选值：'logistic', 'random_forest', 'gradient_boosting', 'svm', 'neural_network', 'xgboost', 'lightgbm'
            sampling_strategy (float or str): 采样策略，默认设为1.0以完全平衡类别分布，提高召回率
            k_neighbors (int): SMOTE中用于构造合成样本的最近邻数量
            **model_params: 模型参数
            
        返回:
            self: 训练器实例
        """
        if self.X_train is None or self.y_train is None:
            logger.warning("数据尚未加载，无法训练模型")
            return self
        
        logger.info(f"开始使用SMOTE过采样训练{model_type}模型...")
        start_time = time.time()
        
        # 创建SMOTE对象
        smote = SMOTE(sampling_strategy=sampling_strategy, k_neighbors=k_neighbors, random_state=42)
        
        # 根据模型类型创建基础模型
        if model_type == 'logistic':
            base_model = LogisticRegression(random_state=42, **model_params)
        elif model_type == 'random_forest':
            base_model = RandomForestClassifier(random_state=42, n_jobs=-1, **model_params)
        elif model_type == 'gradient_boosting':
            base_model = GradientBoostingClassifier(random_state=42, **model_params)
        elif model_type == 'svm':
            base_model = SVC(random_state=42, probability=True, **model_params)
        elif model_type == 'neural_network':
            base_model = MLPClassifier(random_state=42, **model_params)
        elif model_type == 'xgboost':
            base_model = xgb.XGBClassifier(use_label_encoder=False, eval_metric='logloss', random_state=42, **model_params)
        elif model_type == 'lightgbm':
            base_model = lgb.LGBMClassifier(random_state=42, **model_params)
        else:
            logger.error(f"不支持的模型类型: {model_type}")
            return self
        
        # 创建SMOTE + 模型的管道
        pipeline = ImbPipeline([
            ('smote', smote),
            ('model', base_model)
        ])
        
        # 训练模型
        pipeline.fit(self.X_train, self.y_train)
        
        # 记录训练时间
        self.training_time = time.time() - start_time
        logger.info(f"使用SMOTE过采样训练{model_type}模型完成，耗时: {self.training_time:.2f}秒")
        
        # 保存模型和参数
        self.model = pipeline
        self.best_params = {
            'model_type': model_type,
            'sampling_strategy': sampling_strategy,
            'k_neighbors': k_neighbors,
            **model_params
        }
        
        # 获取特征重要性（如果模型支持）
        base_model = pipeline.named_steps['model']
        if hasattr(base_model, 'feature_importances_'):
            self.feature_importances = base_model.feature_importances_
        elif hasattr(base_model, 'coef_'):
            self.feature_importances = np.abs(base_model.coef_[0])
        else:
            self.feature_importances = None
        
        return self
    
    def tune_hyperparameters(self, model_type='gradient_boosting', param_grid=None, cv=5, 
                            scoring='f1', n_jobs=-1, method='grid', n_iter=10):
        """超参数调优
        
        参数:
            model_type (str): 模型类型，可选值：'logistic', 'random_forest', 'gradient_boosting', 'svm', 'neural_network', 'xgboost', 'lightgbm'
            param_grid (dict): 参数网格
            cv (int): 交叉验证折数
            scoring (str): 评分方法，默认使用f1分数以平衡精确率和召回率，有助于提高模型的召回率
            n_jobs (int): 并行作业数
            method (str): 调优方法，'grid'或'random'
            n_iter (int): 随机搜索的迭代次数
            
        返回:
            self: 训练器实例
        """
        if self.X_train is None or self.y_train is None:
            logger.warning("数据尚未加载，无法进行超参数调优")
            return self
        
        logger.info(f"开始{model_type}模型的超参数调优...")
        start_time = time.time()
        
        # 根据模型类型创建基础模型
        if model_type == 'logistic':
            base_model = LogisticRegression(random_state=42)
            # 默认参数网格
            if param_grid is None:
                param_grid = {
                    'C': [0.01, 0.1, 1, 10, 100],
                    'solver': ['liblinear', 'saga'],
                    'class_weight': [None, 'balanced']
                }
        elif model_type == 'random_forest':
            base_model = RandomForestClassifier(random_state=42, n_jobs=-1)
            # 默认参数网格
            if param_grid is None:
                param_grid = {
                    'n_estimators': [50, 100, 200],
                    'max_depth': [None, 5, 10, 15],
                    'min_samples_split': [2, 5, 10],
                    'min_samples_leaf': [1, 2, 4],
                    'class_weight': [None, 'balanced']
                }
        elif model_type == 'gradient_boosting':
            base_model = GradientBoostingClassifier(random_state=42)
            # 默认参数网格
            if param_grid is None:
                param_grid = {
                    'n_estimators': [50, 100, 200],
                    'learning_rate': [0.01, 0.1, 0.2],
                    'max_depth': [3, 5, 7],
                    'min_samples_split': [2, 5],
                    'min_samples_leaf': [1, 2],
                    'subsample': [0.8, 1.0]
                }
        elif model_type == 'svm':
            base_model = SVC(random_state=42, probability=True)
            # 默认参数网格
            if param_grid is None:
                param_grid = {
                    'C': [0.1, 1, 10],
                    'kernel': ['linear', 'rbf'],
                    'gamma': ['scale', 'auto', 0.1, 1],
                    'class_weight': [None, 'balanced']
                }
        elif model_type == 'neural_network':
            base_model = MLPClassifier(random_state=42)
            # 默认参数网格
            if param_grid is None:
                param_grid = {
                    'hidden_layer_sizes': [(50,), (100,), (50, 50), (100, 50)],
                    'activation': ['relu', 'tanh'],
                    'solver': ['adam', 'sgd'],
                    'alpha': [0.0001, 0.001, 0.01],
                    'learning_rate': ['constant', 'adaptive']
                }
        elif model_type == 'xgboost':
            base_model = xgb.XGBClassifier(use_label_encoder=False, eval_metric='logloss', random_state=42)
            # 默认参数网格
            if param_grid is None:
                param_grid = {
                    'n_estimators': [50, 100, 200],
                    'learning_rate': [0.01, 0.1, 0.2],
                    'max_depth': [3, 5, 7],
                    'min_child_weight': [1, 3, 5],
                    'subsample': [0.6, 0.8, 1.0],
                    'colsample_bytree': [0.6, 0.8, 1.0],
                    'gamma': [0, 0.1, 0.2],
                    'reg_alpha': [0, 0.1, 1],
                    'reg_lambda': [0.1, 1, 10],
                    'scale_pos_weight': [1, 3, 5, 7, 10, 15, 20]
                }
        elif model_type == 'lightgbm':
            base_model = lgb.LGBMClassifier(random_state=42)
            # 默认参数网格
            if param_grid is None:
                param_grid = {
                    'n_estimators': [50, 100, 200],
                    'learning_rate': [0.01, 0.1, 0.2],
                    'max_depth': [-1, 5, 10],
                    'num_leaves': [31, 50, 100],
                    'min_child_samples': [10, 20, 30],
                    'subsample': [0.6, 0.8, 1.0],
                    'colsample_bytree': [0.6, 0.8, 1.0],
                    'reg_alpha': [0, 0.1, 1],
                    'reg_lambda': [0, 0.1, 1]
                }
        else:
            logger.error(f"不支持的模型类型: {model_type}")
            return self
        
        # 创建搜索对象
        if method == 'grid':
            search = GridSearchCV(
                estimator=base_model,
                param_grid=param_grid,
                cv=cv,
                scoring=scoring,
                n_jobs=n_jobs,
                verbose=1
            )
        elif method == 'random':
            search = RandomizedSearchCV(
                estimator=base_model,
                param_distributions=param_grid,
                n_iter=n_iter,
                cv=cv,
                scoring=scoring,
                n_jobs=n_jobs,
                random_state=42,
                verbose=1
            )
        else:
            logger.error(f"不支持的调优方法: {method}")
            return self
        
        # 执行搜索
        search.fit(self.X_train, self.y_train)
        
        # 记录训练时间
        self.training_time = time.time() - start_time
        logger.info(f"{model_type}模型的超参数调优完成，耗时: {self.training_time:.2f}秒")
        logger.info(f"最佳参数: {search.best_params_}")
        logger.info(f"最佳得分: {search.best_score_:.4f}")
        
        # 保存最佳模型和参数
        self.model = search.best_estimator_
        self.best_params = search.best_params_
        
        # 获取特征重要性（如果模型支持）
        if hasattr(self.model, 'feature_importances_'):
            self.feature_importances = self.model.feature_importances_
        elif hasattr(self.model, 'coef_'):
            self.feature_importances = np.abs(self.model.coef_[0])
        else:
            self.feature_importances = None
        
        return self
    
    def calibrate_probabilities(self, method='isotonic', cv=5):
        """校准模型概率
        
        参数:
            method (str): 校准方法，'sigmoid'或'isotonic'
            cv (int): 交叉验证折数
            
        返回:
            self: 训练器实例
        """
        if self.model is None:
            logger.warning("模型尚未训练，无法校准概率")
            return self
        
        logger.info(f"开始使用{method}方法校准模型概率...")
        
        # 创建校准器
        calibrated_model = CalibratedClassifierCV(
            estimator=self.model,
            method=method,
            cv=cv
        )
        
        # 训练校准器
        calibrated_model.fit(self.X_train, self.y_train)
        
        # 更新模型
        self.model = calibrated_model
        self.is_calibrated = True
        
        logger.info("模型概率校准完成")
        
        return self
    
    def evaluate_model(self, X=None, y=None):
        """评估模型性能
        
        参数:
            X: 特征数据，如果为None则使用测试集
            y: 标签数据，如果为None则使用测试集标签
            
        返回:
            dict: 评估指标
        """
        if self.model is None:
            logger.warning("模型尚未训练，无法评估性能")
            return None
        
        # 如果未提供数据，使用测试集
        if X is None or y is None:
            if self.X_test is None or self.y_test is None:
                logger.warning("测试集尚未加载，无法评估性能")
                return None
            X = self.X_test
            y = self.y_test
        
        # 预测概率和类别
        try:
            y_prob = self.model.predict_proba(X)[:, 1]
            y_pred = self.model.predict(X)
            
            # 计算评估指标
            metrics = {
                'accuracy': accuracy_score(y, y_pred),
                'precision': precision_score(y, y_pred),
                'recall': recall_score(y, y_pred),
                'f1': f1_score(y, y_pred),
                'roc_auc': roc_auc_score(y, y_prob)
            }
            
            logger.info("模型评估完成")
            logger.info(f"准确率: {metrics['accuracy']:.4f}")
            logger.info(f"精确率: {metrics['precision']:.4f}")
            logger.info(f"召回率: {metrics['recall']:.4f}")
            logger.info(f"F1分数: {metrics['f1']:.4f}")
            logger.info(f"ROC AUC: {metrics['roc_auc']:.4f}")
            
            return metrics
            
        except Exception as e:
            logger.error(f"评估模型时出错: {str(e)}")
            return None
    
    def save_model(self, model_path, save_metrics=True):
        """保存模型
        
        参数:
            model_path (str): 模型保存路径
            save_metrics (bool): 是否保存评估指标
            
        返回:
            bool: 是否成功保存
        """
        if self.model is None:
            logger.warning("模型尚未训练，无法保存")
            return False
        
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(model_path), exist_ok=True)
            
            # 保存模型
            dump(self.model, model_path)
            logger.info(f"模型已保存至 {model_path}")
            
            # 保存模型元数据
            metadata = {
                'model_type': type(self.model).__name__,
                'best_params': self.best_params,
                'training_time': self.training_time,
                'is_calibrated': self.is_calibrated,
                'feature_importances': self.feature_importances.tolist() if self.feature_importances is not None else None
            }
            
            # 如果需要，计算并保存评估指标
            if save_metrics and self.X_test is not None and self.y_test is not None:
                metrics = self.evaluate_model()
                if metrics is not None:
                    metadata['metrics'] = metrics
            
            # 保存元数据
            metadata_path = os.path.splitext(model_path)[0] + '_metadata.json'
            import json
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=4)
            
            logger.info(f"模型元数据已保存至 {metadata_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"保存模型时出错: {str(e)}")
            return False
    
    def load_model(self, model_path):
        """加载模型
        
        参数:
            model_path (str): 模型加载路径
            
        返回:
            self: 训练器实例
        """
        try:
            # 加载模型
            self.model = load(model_path)
            logger.info(f"模型已从 {model_path} 加载")
            
            # 尝试加载元数据
            metadata_path = os.path.splitext(model_path)[0] + '_metadata.json'
            if os.path.exists(metadata_path):
                import json
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                
                # 恢复元数据
                self.best_params = metadata.get('best_params')
                self.training_time = metadata.get('training_time')
                self.is_calibrated = metadata.get('is_calibrated', False)
                
                # 恢复特征重要性
                feature_importances = metadata.get('feature_importances')
                if feature_importances is not None:
                    self.feature_importances = np.array(feature_importances)
                
                logger.info(f"模型元数据已从 {metadata_path} 加载")
            
            return self
            
        except Exception as e:
            logger.error(f"加载模型时出错: {str(e)}")
            return self

# 使用示例
def main():
    # 加载处理后的数据
    X_train = np.load('../data/processed/X_train.npy')
    y_train = np.load('../data/processed/y_train.npy')
    X_test = np.load('../data/processed/X_test.npy')
    y_test = np.load('../data/processed/y_test.npy')
    
    # 创建模型训练器
    trainer = ModelTrainer(X_train, y_train, X_test, y_test)
    
    # 使用SMOTE过采样训练梯度提升模型
    trainer.train_with_smote(
        model_type='gradient_boosting',
        sampling_strategy=0.5,
        n_estimators=100,
        learning_rate=0.1,
        max_depth=5
    )
    
    # 校准模型概率
    trainer.calibrate_probabilities()
    
    # 评估模型
    metrics = trainer.evaluate_model()
    
    # 保存模型
    trainer.save_model('../models/gradient_boosting_model.joblib')
    
    # 输出结果
    print("\n模型训练与评估完成")
    print(f"最佳参数: {trainer.best_params}")
    print(f"训练时间: {trainer.training_time:.2f}秒")
    print("\n评估指标:")
    for metric, value in metrics.items():
        print(f"{metric}: {value:.4f}")

if __name__ == "__main__":
    main()