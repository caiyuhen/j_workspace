# 卒中预测模型 - 特征工程模块

import pandas as pd
import numpy as np
import logging
from sklearn.feature_selection import SelectKBest, f_classif, RFE, RFECV
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import PolynomialFeatures
from sklearn.decomposition import PCA
from sklearn.pipeline import Pipeline
import matplotlib.pyplot as plt
import seaborn as sns
import os

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FeatureEngineer:
    """特征工程类，负责特征选择、创建和转换"""
    
    def __init__(self, X_train=None, y_train=None, X_test=None, feature_names=None):
        """初始化特征工程器
        
        参数:
            X_train: 训练集特征
            y_train: 训练集标签
            X_test: 测试集特征
            feature_names: 特征名称列表
        """
        self.X_train = X_train
        self.y_train = y_train
        self.X_test = X_test
        self.feature_names = feature_names
        self.selected_features = None
        self.feature_importances = None
        self.feature_selector = None
    
    def load_data(self, X_train, y_train, X_test=None, feature_names=None):
        """加载数据
        
        参数:
            X_train: 训练集特征
            y_train: 训练集标签
            X_test: 测试集特征
            feature_names: 特征名称列表
        """
        self.X_train = X_train
        self.y_train = y_train
        self.X_test = X_test
        self.feature_names = feature_names
        logger.info(f"数据加载完成，训练集形状: {X_train.shape}")
    
    def create_interaction_features(self, degree=2, include_bias=False):
        """创建特征交互项
        
        参数:
            degree (int): 多项式特征的最高次数
            include_bias (bool): 是否包含偏置项
            
        返回:
            tuple: (X_train_poly, X_test_poly, poly_feature_names)
        """
        if self.X_train is None or self.y_train is None:
            logger.warning("数据尚未加载，无法创建交互特征")
            return None, None, None
        
        # 创建多项式特征转换器
        poly = PolynomialFeatures(degree=degree, include_bias=include_bias, interaction_only=True)
        
        # 转换训练集
        X_train_poly = poly.fit_transform(self.X_train)
        
        # 转换测试集（如果存在）
        X_test_poly = None
        if self.X_test is not None:
            X_test_poly = poly.transform(self.X_test)
        
        # 生成多项式特征名称
        if self.feature_names is not None:
            poly_feature_names = poly.get_feature_names_out(self.feature_names)
        else:
            poly_feature_names = None
        
        logger.info(f"创建交互特征完成，特征数量从 {self.X_train.shape[1]} 增加到 {X_train_poly.shape[1]}")
        
        return X_train_poly, X_test_poly, poly_feature_names
    
    def select_features_univariate(self, k='all'):
        """使用单变量统计测试选择特征
        
        参数:
            k (int or 'all'): 要选择的特征数量
            
        返回:
            tuple: (X_train_selected, X_test_selected, selected_feature_names)
        """
        if self.X_train is None or self.y_train is None:
            logger.warning("数据尚未加载，无法进行特征选择")
            return None, None, None
        
        # 创建特征选择器
        selector = SelectKBest(score_func=f_classif, k=k)
        
        # 对训练集进行拟合和转换
        X_train_selected = selector.fit_transform(self.X_train, self.y_train)
        
        # 保存特征选择器
        self.feature_selector = selector
        
        # 获取特征得分和p值
        scores = selector.scores_
        p_values = selector.pvalues_
        
        # 获取选择的特征索引
        selected_indices = selector.get_support(indices=True)
        
        # 转换测试集（如果存在）
        X_test_selected = None
        if self.X_test is not None:
            X_test_selected = selector.transform(self.X_test)
        
        # 获取选择的特征名称
        selected_feature_names = None
        if self.feature_names is not None:
            selected_feature_names = [self.feature_names[i] for i in selected_indices]
            
            # 创建特征重要性字典
            self.feature_importances = {}
            for i, idx in enumerate(selected_indices):
                self.feature_importances[self.feature_names[idx]] = scores[idx]
        
        logger.info(f"单变量特征选择完成，选择了 {len(selected_indices)} 个特征")
        
        # 保存选择的特征
        self.selected_features = selected_feature_names
        
        return X_train_selected, X_test_selected, selected_feature_names
    
    def select_features_rfe(self, n_features_to_select=None, step=1, estimator=None):
        """使用递归特征消除(RFE)选择特征
        
        参数:
            n_features_to_select (int): 要选择的特征数量
            step (int): 每次迭代要移除的特征数量
            estimator: 用于特征选择的估计器，默认为RandomForestClassifier
            
        返回:
            tuple: (X_train_selected, X_test_selected, selected_feature_names)
        """
        if self.X_train is None or self.y_train is None:
            logger.warning("数据尚未加载，无法进行特征选择")
            return None, None, None
        
        # 如果没有提供估计器，使用随机森林
        if estimator is None:
            estimator = RandomForestClassifier(n_estimators=100, random_state=42)
        
        # 创建RFE选择器
        selector = RFE(estimator=estimator, n_features_to_select=n_features_to_select, step=step)
        
        # 对训练集进行拟合和转换
        X_train_selected = selector.fit_transform(self.X_train, self.y_train)
        
        # 保存特征选择器
        self.feature_selector = selector
        
        # 获取特征排名
        rankings = selector.ranking_
        
        # 获取选择的特征索引
        selected_indices = selector.get_support(indices=True)
        
        # 转换测试集（如果存在）
        X_test_selected = None
        if self.X_test is not None:
            X_test_selected = selector.transform(self.X_test)
        
        # 获取选择的特征名称
        selected_feature_names = None
        if self.feature_names is not None:
            selected_feature_names = [self.feature_names[i] for i in selected_indices]
            
            # 创建特征重要性字典（使用排名的倒数作为重要性度量）
            self.feature_importances = {}
            for i, name in enumerate(self.feature_names):
                # 排名越低越重要，所以使用倒数
                self.feature_importances[name] = 1.0 / rankings[i] if rankings[i] > 0 else 0
        
        logger.info(f"递归特征消除完成，选择了 {len(selected_indices)} 个特征")
        
        # 保存选择的特征
        self.selected_features = selected_feature_names
        
        return X_train_selected, X_test_selected, selected_feature_names
    
    def select_features_rfecv(self, min_features_to_select=1, step=1, cv=5, scoring='roc_auc', estimator=None):
        """使用带交叉验证的递归特征消除(RFECV)选择特征
        
        参数:
            min_features_to_select (int): 最小特征数量
            step (int): 每次迭代要移除的特征数量
            cv (int): 交叉验证折数
            scoring (str): 评分方法
            estimator: 用于特征选择的估计器，默认为RandomForestClassifier
            
        返回:
            tuple: (X_train_selected, X_test_selected, selected_feature_names)
        """
        if self.X_train is None or self.y_train is None:
            logger.warning("数据尚未加载，无法进行特征选择")
            return None, None, None
        
        # 如果没有提供估计器，使用随机森林
        if estimator is None:
            estimator = RandomForestClassifier(n_estimators=100, random_state=42)
        
        # 创建RFECV选择器
        selector = RFECV(estimator=estimator, min_features_to_select=min_features_to_select, 
                        step=step, cv=cv, scoring=scoring)
        
        # 对训练集进行拟合和转换
        X_train_selected = selector.fit_transform(self.X_train, self.y_train)
        
        # 保存特征选择器
        self.feature_selector = selector
        
        # 获取特征排名
        rankings = selector.ranking_
        
        # 获取选择的特征索引
        selected_indices = selector.get_support(indices=True)
        
        # 转换测试集（如果存在）
        X_test_selected = None
        if self.X_test is not None:
            X_test_selected = selector.transform(self.X_test)
        
        # 获取选择的特征名称
        selected_feature_names = None
        if self.feature_names is not None:
            selected_feature_names = [self.feature_names[i] for i in selected_indices]
            
            # 创建特征重要性字典（使用排名的倒数作为重要性度量）
            self.feature_importances = {}
            for i, name in enumerate(self.feature_names):
                # 排名越低越重要，所以使用倒数
                self.feature_importances[name] = 1.0 / rankings[i] if rankings[i] > 0 else 0
        
        logger.info(f"带交叉验证的递归特征消除完成，选择了 {len(selected_indices)} 个特征")
        logger.info(f"最佳特征数量: {selector.n_features_}")
        
        # 保存选择的特征
        self.selected_features = selected_feature_names
        
        return X_train_selected, X_test_selected, selected_feature_names
    
    def select_features_tree_based(self, threshold=0.01, estimator=None):
        """使用基于树的特征重要性选择特征
        
        参数:
            threshold (float): 特征重要性阈值
            estimator: 用于特征选择的估计器，默认为RandomForestClassifier
            
        返回:
            tuple: (X_train_selected, X_test_selected, selected_feature_names)
        """
        if self.X_train is None or self.y_train is None:
            logger.warning("数据尚未加载，无法进行特征选择")
            return None, None, None
        
        # 如果没有提供估计器，使用随机森林
        if estimator is None:
            estimator = RandomForestClassifier(n_estimators=100, random_state=42)
        
        # 拟合估计器
        estimator.fit(self.X_train, self.y_train)
        
        # 获取特征重要性
        importances = estimator.feature_importances_
        
        # 选择重要性大于阈值的特征
        selected_indices = np.where(importances > threshold)[0]
        
        # 转换数据
        X_train_selected = self.X_train[:, selected_indices]
        
        # 转换测试集（如果存在）
        X_test_selected = None
        if self.X_test is not None:
            X_test_selected = self.X_test[:, selected_indices]
        
        # 获取选择的特征名称
        selected_feature_names = None
        if self.feature_names is not None:
            selected_feature_names = [self.feature_names[i] for i in selected_indices]
            
            # 创建特征重要性字典
            self.feature_importances = {}
            for i, idx in enumerate(selected_indices):
                self.feature_importances[self.feature_names[idx]] = importances[idx]
        
        logger.info(f"基于树的特征选择完成，选择了 {len(selected_indices)} 个特征")
        
        # 保存选择的特征
        self.selected_features = selected_feature_names
        
        return X_train_selected, X_test_selected, selected_feature_names
    
    def reduce_dimensions_pca(self, n_components=None, variance_threshold=0.95):
        """使用PCA降维
        
        参数:
            n_components (int): 主成分数量，如果为None则使用方差阈值
            variance_threshold (float): 要保留的方差比例
            
        返回:
            tuple: (X_train_pca, X_test_pca, explained_variance_ratio)
        """
        if self.X_train is None:
            logger.warning("数据尚未加载，无法进行降维")
            return None, None, None
        
        # 如果n_components为None，使用方差阈值
        if n_components is None:
            # 先使用足够多的成分
            temp_pca = PCA(n_components=min(self.X_train.shape[0], self.X_train.shape[1]))
            temp_pca.fit(self.X_train)
            
            # 计算累积方差比
            cumulative_variance = np.cumsum(temp_pca.explained_variance_ratio_)
            
            # 找到满足方差阈值的最小成分数
            n_components = np.argmax(cumulative_variance >= variance_threshold) + 1
        
        # 创建PCA转换器
        pca = PCA(n_components=n_components)
        
        # 转换训练集
        X_train_pca = pca.fit_transform(self.X_train)
        
        # 转换测试集（如果存在）
        X_test_pca = None
        if self.X_test is not None:
            X_test_pca = pca.transform(self.X_test)
        
        logger.info(f"PCA降维完成，特征数量从 {self.X_train.shape[1]} 减少到 {X_train_pca.shape[1]}")
        logger.info(f"保留的方差比例: {np.sum(pca.explained_variance_ratio_):.4f}")
        
        return X_train_pca, X_test_pca, pca.explained_variance_ratio_
    
    def plot_feature_importances(self, top_n=20, output_dir=None):
        """绘制特征重要性图
        
        参数:
            top_n (int): 显示的顶部特征数量
            output_dir (str): 输出目录路径
            
        返回:
            matplotlib.figure.Figure: 图形对象
        """
        if self.feature_importances is None:
            logger.warning("特征重要性尚未计算，无法绘图")
            return None
        
        # 将特征重要性转换为DataFrame
        importance_df = pd.DataFrame({
            'Feature': list(self.feature_importances.keys()),
            'Importance': list(self.feature_importances.values())
        })
        
        # 按重要性排序
        importance_df = importance_df.sort_values('Importance', ascending=False)
        
        # 选择前N个特征
        if top_n is not None and len(importance_df) > top_n:
            importance_df = importance_df.head(top_n)
        
        # 创建图形
        plt.figure(figsize=(12, 8))
        ax = sns.barplot(x='Importance', y='Feature', data=importance_df)
        plt.title(f'Top {len(importance_df)} Feature Importances')
        plt.tight_layout()
        
        # 保存图形（如果指定了输出目录）
        if output_dir is not None:
            os.makedirs(output_dir, exist_ok=True)
            plt.savefig(os.path.join(output_dir, 'feature_importances.png'), dpi=300, bbox_inches='tight')
            logger.info(f"特征重要性图已保存至 {os.path.join(output_dir, 'feature_importances.png')}")
        
        return plt.gcf()
    
    def save_selected_features(self, output_dir):
        """保存选择的特征
        
        参数:
            output_dir (str): 输出目录路径
            
        返回:
            bool: 是否成功保存
        """
        if self.selected_features is None:
            logger.warning("尚未选择特征，无法保存")
            return False
        
        try:
            # 确保输出目录存在
            os.makedirs(output_dir, exist_ok=True)
            
            # 保存选择的特征名称
            with open(os.path.join(output_dir, 'selected_features.txt'), 'w') as f:
                for feature in self.selected_features:
                    f.write(f"{feature}\n")
            
            # 保存特征重要性（如果存在）
            if self.feature_importances is not None:
                importance_df = pd.DataFrame({
                    'Feature': list(self.feature_importances.keys()),
                    'Importance': list(self.feature_importances.values())
                })
                importance_df = importance_df.sort_values('Importance', ascending=False)
                importance_df.to_csv(os.path.join(output_dir, 'feature_importances.csv'), index=False)
            
            # 保存特征选择器（如果存在）
            if self.feature_selector is not None:
                from joblib import dump
                dump(self.feature_selector, os.path.join(output_dir, 'feature_selector.joblib'))
            
            logger.info(f"选择的特征已保存至 {output_dir}")
            return True
            
        except Exception as e:
            logger.error(f"保存选择的特征时出错: {str(e)}")
            return False

# 使用示例
def main():
    # 加载处理后的数据
    X_train = np.load('../data/processed/X_train.npy')
    y_train = np.load('../data/processed/y_train.npy')
    X_test = np.load('../data/processed/X_test.npy')
    
    # 尝试加载特征名称
    feature_names = None
    try:
        with open('../data/processed/feature_names.txt', 'r') as f:
            feature_names = [line.strip() for line in f.readlines()]
    except FileNotFoundError:
        logger.warning("特征名称文件不存在，将使用索引作为特征名称")
        feature_names = [f'feature_{i}' for i in range(X_train.shape[1])]
    
    # 创建特征工程器
    engineer = FeatureEngineer(X_train, y_train, X_test, feature_names)
    
    # 使用RFECV选择特征
    X_train_selected, X_test_selected, selected_features = engineer.select_features_rfecv(cv=5)
    
    # 绘制特征重要性
    engineer.plot_feature_importances(top_n=20, output_dir='../notebooks/figures')
    
    # 保存选择的特征
    engineer.save_selected_features('../data/processed')
    
    # 输出结果
    print(f"原始特征数量: {X_train.shape[1]}")
    print(f"选择的特征数量: {X_train_selected.shape[1]}")
    print(f"选择的特征: {selected_features[:10]}...（共{len(selected_features)}个）")

if __name__ == "__main__":
    main()