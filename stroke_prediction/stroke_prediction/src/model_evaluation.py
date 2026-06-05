# 卒中预测模型 - 模型评估模块

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import logging
import os
import joblib
from sklearn.metrics import (confusion_matrix, classification_report, roc_curve, 
                             precision_recall_curve, auc, roc_auc_score, 
                             accuracy_score, precision_score, recall_score, f1_score,
                             brier_score_loss)
from sklearn.calibration import calibration_curve
from sklearn.inspection import permutation_importance

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ModelEvaluator:
    """模型评估类，负责评估模型性能并生成可视化结果"""
    
    def __init__(self, model=None, X_test=None, y_test=None, feature_names=None):
        """初始化模型评估器
        
        参数:
            model: 训练好的模型
            X_test: 测试集特征
            y_test: 测试集标签
            feature_names: 特征名称列表
        """
        self.model = model
        self.X_test = X_test
        self.y_test = y_test
        self.feature_names = feature_names
        self.y_pred = None
        self.y_prob = None
        self.metrics = {}
        self.figures_dir = None
    
    def load_data(self, X_test, y_test, feature_names=None):
        """加载测试数据
        
        参数:
            X_test: 测试集特征
            y_test: 测试集标签
            feature_names: 特征名称列表
        """
        self.X_test = X_test
        self.y_test = y_test
        self.feature_names = feature_names
        logger.info(f"测试数据加载完成，测试集形状: {X_test.shape}")
    
    def load_model(self, model_path):
        """加载模型
        
        参数:
            model_path: 模型文件路径
        """
        try:
            self.model = joblib.load(model_path)
            logger.info(f"模型已从 {model_path} 加载")
        except Exception as e:
            logger.error(f"加载模型时出错: {str(e)}")
    
    def set_figures_dir(self, figures_dir):
        """设置图表保存目录
        
        参数:
            figures_dir: 图表保存目录
        """
        self.figures_dir = figures_dir
        os.makedirs(figures_dir, exist_ok=True)
        logger.info(f"图表保存目录设置为: {figures_dir}")
    
    def predict(self, model=None, X=None, threshold=0.005, save_results=True):
        """使用模型进行预测
        
        参数:
            model: 模型对象，如果为None则使用已加载的模型
            X: 特征数据，如果为None则使用已加载的测试数据
            threshold: 分类阈值，默认设为0.005以提高召回率
            save_results: 是否将预测结果保存到实例中，默认为True
            
        返回:
            numpy.ndarray: 预测标签
        """
        if model is None:
            model = self.model
        
        if X is None:
            X = self.X_test
        
        if model is None or X is None:
            logger.warning("模型或数据尚未加载，无法进行预测")
            return None
        
        try:
            # 预测概率
            if hasattr(model, 'predict_proba'):
                y_prob = model.predict_proba(X)[:, 1]
                # 根据阈值进行分类（使用较低的阈值以提高召回率）
                y_pred = (y_prob >= threshold).astype(int)
            else:
                # 如果没有概率预测，使用模型的默认预测
                logger.warning("模型不支持概率预测，将使用默认预测")
                y_pred = model.predict(X)
                y_prob = None
            
            # 如果需要，保存预测结果到实例中
            if save_results and X is self.X_test:
                self.y_pred = y_pred
                self.y_prob = y_prob
                logger.info(f"测试集预测完成，使用阈值: {threshold}")
            
            return y_pred
            
        except Exception as e:
            logger.error(f"预测时出错: {str(e)}")
            return None
    
    def calculate_metrics(self, y_true=None, y_pred=None, y_pred_proba=None, threshold=0.005):
        """计算评估指标
        
        参数:
            y_true: 真实标签，如果为None则使用已加载的测试标签
            y_pred: 预测标签，如果为None则使用已加载的预测结果或根据阈值生成
            y_pred_proba: 预测概率，如果为None则使用已加载的预测概率
            threshold: 分类阈值，用于从概率生成预测标签
            
        返回:
            dict: 评估指标字典
        """
        # 确定使用的数据
        if y_true is None:
            y_true = self.y_test
            
        if y_true is None:
            logger.warning("测试标签尚未加载，无法计算评估指标")
            return {}
        
        # 确定预测概率
        if y_pred_proba is None:
            y_pred_proba = self.y_prob
        
        # 确定预测标签
        if y_pred is None:
            if y_pred_proba is not None:
                # 根据阈值生成预测标签
                y_pred = (y_pred_proba >= threshold).astype(int)
            else:
                y_pred = self.y_pred
        
        if y_pred is None:
            logger.warning("预测结果尚未加载，无法计算评估指标")
            return {}
        
        try:
            # 创建新的指标字典
            metrics = {}
            
            # 计算基本分类指标
            metrics['accuracy'] = accuracy_score(y_true, y_pred)
            metrics['precision'] = precision_score(y_true, y_pred)
            metrics['recall'] = recall_score(y_true, y_pred)
            metrics['f1'] = f1_score(y_true, y_pred)
            
            # 计算F2分数（更注重召回率）
            from sklearn.metrics import fbeta_score
            metrics['f2'] = fbeta_score(y_true, y_pred, beta=2)
            
            # 计算混淆矩阵相关指标
            tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
            metrics['specificity'] = tn / (tn + fp) if (tn + fp) > 0 else 0  # 特异度
            metrics['npv'] = tn / (tn + fn) if (tn + fn) > 0 else 0  # 阴性预测值
            metrics['false_positive_rate'] = fp / (fp + tn) if (fp + tn) > 0 else 0  # 假阳性率
            metrics['false_negative_rate'] = fn / (fn + tp) if (fn + tp) > 0 else 0  # 假阴性率
            metrics['threshold'] = threshold  # 记录使用的阈值
            
            # 如果有概率预测，计算AUC和Brier分数
            if y_pred_proba is not None:
                metrics['roc_auc'] = roc_auc_score(y_true, y_pred_proba)
                metrics['brier_score'] = brier_score_loss(y_true, y_pred_proba)
                
                # 计算PR曲线下面积
                precision, recall, _ = precision_recall_curve(y_true, y_pred_proba)
                metrics['pr_auc'] = auc(recall, precision)
            
            # 记录评估结果
            logger.info(f"模型评估指标计算完成 (阈值: {threshold})")
            for metric, value in metrics.items():
                if metric != 'threshold':
                    logger.info(f"{metric}: {value:.4f}")
            
            # 如果是对测试集的评估，则更新实例的指标
            if y_true is self.y_test and ((y_pred is self.y_pred) or (y_pred_proba is self.y_prob)):
                self.metrics = metrics
                logger.info("已更新模型实例的评估指标")
            
            return metrics
            
        except Exception as e:
            logger.error(f"计算评估指标时出错: {str(e)}")
            return {}
            
    def calculate_fbeta_score(self, y_true=None, y_pred=None, beta=1):
        """计算F-beta分数
        
        参数:
            y_true: 真实标签，如果为None则使用已加载的测试标签
            y_pred: 预测标签，如果为None则使用已加载的预测结果
            beta: beta参数，控制精确率和召回率的权重
                 beta=1时等同于F1分数（精确率和召回率权重相同）
                 beta>1时更注重召回率
                 beta<1时更注重精确率
                 beta=2是临床上常用的值，更注重减少假阴性
        
        返回:
            float: F-beta分数
        """
        # 确定使用的数据
        if y_true is None:
            y_true = self.y_test
            
        if y_pred is None:
            y_pred = self.y_pred
            
        if y_true is None or y_pred is None:
            logger.warning("测试标签或预测结果尚未加载，无法计算F-beta分数")
            return 0.0
            
        try:
            from sklearn.metrics import fbeta_score
            return fbeta_score(y_true, y_pred, beta=beta)
        except Exception as e:
            logger.error(f"计算F-beta分数时出错: {str(e)}")
            return 0.0
    
    def print_classification_report(self):
        """打印分类报告"""
        if self.y_test is None or self.y_pred is None:
            logger.warning("测试标签或预测结果尚未加载，无法生成分类报告")
            return
        
        try:
            # 生成分类报告
            report = classification_report(self.y_test, self.y_pred)
            print("\n分类报告:")
            print(report)
            logger.info("分类报告已生成")
            
        except Exception as e:
            logger.error(f"生成分类报告时出错: {str(e)}")
    
    def plot_confusion_matrix(self, normalize=False, save_fig=True):
        """绘制混淆矩阵
        
        参数:
            normalize: 是否归一化
            save_fig: 是否保存图表
        """
        if self.y_test is None or self.y_pred is None:
            logger.warning("测试标签或预测结果尚未加载，无法绘制混淆矩阵")
            return
        
        try:
            # 计算混淆矩阵
            cm = confusion_matrix(self.y_test, self.y_pred)
            
            # 归一化（如果需要）
            if normalize:
                cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
                fmt = '.2f'
                title = '归一化混淆矩阵'
            else:
                fmt = 'd'
                title = '混淆矩阵'
            
            # 绘制混淆矩阵
            plt.figure(figsize=(8, 6))
            sns.heatmap(cm, annot=True, fmt=fmt, cmap='Blues', 
                        xticklabels=['无脑卒中', '脑卒中'], 
                        yticklabels=['无脑卒中', '脑卒中'])
            plt.xlabel('预测标签')
            plt.ylabel('真实标签')
            plt.title(title)
            
            # 保存图表（如果需要）
            if save_fig and self.figures_dir is not None:
                filename = 'confusion_matrix'
                if normalize:
                    filename += '_normalized'
                filename += '.png'
                plt.savefig(os.path.join(self.figures_dir, filename), dpi=300, bbox_inches='tight')
                logger.info(f"混淆矩阵已保存至 {os.path.join(self.figures_dir, filename)}")
            
            plt.show()
            logger.info("混淆矩阵已绘制")
            
        except Exception as e:
            logger.error(f"绘制混淆矩阵时出错: {str(e)}")
    
    def plot_roc_curve(self, save_fig=True):
        """绘制ROC曲线
        
        参数:
            save_fig: 是否保存图表
        """
        if self.y_test is None or self.y_prob is None:
            logger.warning("测试标签或预测概率尚未加载，无法绘制ROC曲线")
            return
        
        try:
            # 计算ROC曲线
            fpr, tpr, thresholds = roc_curve(self.y_test, self.y_prob)
            roc_auc = auc(fpr, tpr)
            
            # 绘制ROC曲线
            plt.figure(figsize=(8, 6))
            plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC曲线 (AUC = {roc_auc:.3f})')
            plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
            plt.xlim([0.0, 1.0])
            plt.ylim([0.0, 1.05])
            plt.xlabel('假阳性率')
            plt.ylabel('真阳性率')
            plt.title('接收者操作特征曲线 (ROC)')
            plt.legend(loc='lower right')
            
            # 保存图表（如果需要）
            if save_fig and self.figures_dir is not None:
                filename = 'roc_curve.png'
                plt.savefig(os.path.join(self.figures_dir, filename), dpi=300, bbox_inches='tight')
                logger.info(f"ROC曲线已保存至 {os.path.join(self.figures_dir, filename)}")
            
            plt.show()
            logger.info("ROC曲线已绘制")
            
        except Exception as e:
            logger.error(f"绘制ROC曲线时出错: {str(e)}")
    
    def plot_precision_recall_curve(self, save_fig=True):
        """绘制精确率-召回率曲线
        
        参数:
            save_fig: 是否保存图表
        """
        if self.y_test is None or self.y_prob is None:
            logger.warning("测试标签或预测概率尚未加载，无法绘制精确率-召回率曲线")
            return
        
        try:
            # 计算精确率-召回率曲线
            precision, recall, thresholds = precision_recall_curve(self.y_test, self.y_prob)
            pr_auc = auc(recall, precision)
            
            # 绘制精确率-召回率曲线
            plt.figure(figsize=(8, 6))
            plt.plot(recall, precision, color='blue', lw=2, label=f'PR曲线 (AUC = {pr_auc:.3f})')
            plt.axhline(y=sum(self.y_test)/len(self.y_test), color='red', linestyle='--', label=f'基线 (阳性率 = {sum(self.y_test)/len(self.y_test):.3f})')
            plt.xlim([0.0, 1.0])
            plt.ylim([0.0, 1.05])
            plt.xlabel('召回率')
            plt.ylabel('精确率')
            plt.title('精确率-召回率曲线')
            plt.legend(loc='lower left')
            
            # 保存图表（如果需要）
            if save_fig and self.figures_dir is not None:
                filename = 'precision_recall_curve.png'
                plt.savefig(os.path.join(self.figures_dir, filename), dpi=300, bbox_inches='tight')
                logger.info(f"精确率-召回率曲线已保存至 {os.path.join(self.figures_dir, filename)}")
            
            plt.show()
            logger.info("精确率-召回率曲线已绘制")
            
        except Exception as e:
            logger.error(f"绘制精确率-召回率曲线时出错: {str(e)}")
    
    def plot_calibration_curve(self, n_bins=10, save_fig=True):
        """绘制校准曲线
        
        参数:
            n_bins: 分箱数量
            save_fig: 是否保存图表
        """
        if self.y_test is None or self.y_prob is None:
            logger.warning("测试标签或预测概率尚未加载，无法绘制校准曲线")
            return
        
        try:
            # 计算校准曲线
            prob_true, prob_pred = calibration_curve(self.y_test, self.y_prob, n_bins=n_bins)
            
            # 绘制校准曲线
            plt.figure(figsize=(8, 6))
            plt.plot(prob_pred, prob_true, marker='o', linewidth=1, label='模型')
            plt.plot([0, 1], [0, 1], linestyle='--', label='完美校准')
            plt.xlabel('预测概率')
            plt.ylabel('实际概率')
            plt.title('校准曲线')
            plt.legend(loc='lower right')
            plt.grid(True)
            
            # 保存图表（如果需要）
            if save_fig and self.figures_dir is not None:
                filename = 'calibration_curve.png'
                plt.savefig(os.path.join(self.figures_dir, filename), dpi=300, bbox_inches='tight')
                logger.info(f"校准曲线已保存至 {os.path.join(self.figures_dir, filename)}")
            
            plt.show()
            logger.info("校准曲线已绘制")
            
        except Exception as e:
            logger.error(f"绘制校准曲线时出错: {str(e)}")
    
    def plot_feature_importance(self, importance_type='model', n_top=20, save_fig=True):
        """绘制特征重要性
        
        参数:
            importance_type: 重要性类型，'model'使用模型内置的特征重要性，'permutation'使用排列重要性
            n_top: 显示前n个重要特征
            save_fig: 是否保存图表
        """
        if self.model is None:
            logger.warning("模型尚未加载，无法绘制特征重要性")
            return
        
        try:
            # 获取特征重要性
            if importance_type == 'model':
                # 使用模型内置的特征重要性
                if hasattr(self.model, 'feature_importances_'):
                    importances = self.model.feature_importances_
                elif hasattr(self.model, 'coef_'):
                    importances = np.abs(self.model.coef_[0])
                else:
                    logger.warning("模型不支持内置特征重要性，将使用排列重要性")
                    importance_type = 'permutation'
            
            if importance_type == 'permutation':
                # 使用排列重要性
                if self.X_test is None or self.y_test is None:
                    logger.warning("测试数据尚未加载，无法计算排列重要性")
                    return
                
                result = permutation_importance(self.model, self.X_test, self.y_test, 
                                               n_repeats=10, random_state=42, n_jobs=-1)
                importances = result.importances_mean
            
            # 准备特征名称
            if self.feature_names is None:
                feature_names = [f'特征 {i}' for i in range(len(importances))]
            else:
                feature_names = self.feature_names
            
            # 创建特征重要性DataFrame
            importance_df = pd.DataFrame({
                '特征': feature_names,
                '重要性': importances
            })
            
            # 排序并选择前n个特征
            importance_df = importance_df.sort_values('重要性', ascending=False).head(n_top)
            
            # 绘制特征重要性
            plt.figure(figsize=(10, 8))
            sns.barplot(x='重要性', y='特征', data=importance_df)
            plt.title(f'特征重要性 ({"模型内置" if importance_type == "model" else "排列重要性"})')
            plt.tight_layout()
            
            # 保存图表（如果需要）
            if save_fig and self.figures_dir is not None:
                filename = f'feature_importance_{importance_type}.png'
                plt.savefig(os.path.join(self.figures_dir, filename), dpi=300, bbox_inches='tight')
                logger.info(f"特征重要性图已保存至 {os.path.join(self.figures_dir, filename)}")
            
            plt.show()
            logger.info("特征重要性图已绘制")
            
            return importance_df
            
        except Exception as e:
            logger.error(f"绘制特征重要性时出错: {str(e)}")
            return None
    
    def plot_probability_distribution(self, save_fig=True):
        """绘制预测概率分布
        
        参数:
            save_fig: 是否保存图表
        """
        if self.y_test is None or self.y_prob is None:
            logger.warning("测试标签或预测概率尚未加载，无法绘制概率分布")
            return
        
        try:
            # 创建DataFrame
            df = pd.DataFrame({
                '预测概率': self.y_prob,
                '实际标签': self.y_test
            })
            
            # 绘制概率分布
            plt.figure(figsize=(10, 6))
            sns.histplot(data=df, x='预测概率', hue='实际标签', bins=20, 
                         element='step', common_norm=False, stat='probability')
            plt.title('预测概率分布')
            plt.xlabel('预测概率')
            plt.ylabel('密度')
            
            # 保存图表（如果需要）
            if save_fig and self.figures_dir is not None:
                filename = 'probability_distribution.png'
                plt.savefig(os.path.join(self.figures_dir, filename), dpi=300, bbox_inches='tight')
                logger.info(f"概率分布图已保存至 {os.path.join(self.figures_dir, filename)}")
            
            plt.show()
            logger.info("概率分布图已绘制")
            
        except Exception as e:
            logger.error(f"绘制概率分布时出错: {str(e)}")
    
    def plot_threshold_metrics(self, thresholds=None, save_fig=True):
        """绘制不同阈值下的评估指标
        
        参数:
            thresholds: 阈值列表，如果为None则自动生成
            save_fig: 是否保存图表
        """
        if self.y_test is None or self.y_prob is None:
            logger.warning("测试标签或预测概率尚未加载，无法绘制阈值指标")
            return
        
        try:
            # 如果未提供阈值，则自动生成
            if thresholds is None:
                thresholds = np.linspace(0.1, 0.9, 9)
            
            # 计算不同阈值下的指标
            results = []
            for threshold in thresholds:
                y_pred_threshold = (self.y_prob >= threshold).astype(int)
                
                # 计算指标
                accuracy = accuracy_score(self.y_test, y_pred_threshold)
                precision = precision_score(self.y_test, y_pred_threshold)
                recall = recall_score(self.y_test, y_pred_threshold)
                f1 = f1_score(self.y_test, y_pred_threshold)
                
                results.append({
                    '阈值': threshold,
                    '准确率': accuracy,
                    '精确率': precision,
                    '召回率': recall,
                    'F1分数': f1
                })
            
            # 创建DataFrame
            results_df = pd.DataFrame(results)
            
            # 绘制阈值指标
            plt.figure(figsize=(10, 6))
            for metric in ['准确率', '精确率', '召回率', 'F1分数']:
                plt.plot(results_df['阈值'], results_df[metric], marker='o', label=metric)
            
            plt.xlabel('阈值')
            plt.ylabel('指标值')
            plt.title('不同阈值下的评估指标')
            plt.legend()
            plt.grid(True)
            
            # 保存图表（如果需要）
            if save_fig and self.figures_dir is not None:
                filename = 'threshold_metrics.png'
                plt.savefig(os.path.join(self.figures_dir, filename), dpi=300, bbox_inches='tight')
                logger.info(f"阈值指标图已保存至 {os.path.join(self.figures_dir, filename)}")
            
            plt.show()
            logger.info("阈值指标图已绘制")
            
            return results_df
            
        except Exception as e:
            logger.error(f"绘制阈值指标时出错: {str(e)}")
            return None
    
    def find_optimal_threshold(self, y_true=None, y_pred_proba=None, criterion='f2', min_threshold=0.001, max_threshold=0.5, n_thresholds=100, plot=False, save_fig=True):
        """寻找最优阈值
        
        参数:
            y_true: 真实标签，如果为None则使用已加载的测试标签
            y_pred_proba: 预测概率，如果为None则使用已加载的预测概率
            criterion: 优化标准，可选值：'f1', 'f2', 'accuracy', 'precision', 'recall', 'balanced', 'specificity', 'npv'
                      其中'f2'更注重召回率，适用于需要高召回率的场景
            min_threshold: 最小阈值，默认为0.001
            max_threshold: 最大阈值，默认为0.5
            n_thresholds: 阈值数量，默认为100
            plot: 是否绘制阈值-指标曲线
            save_fig: 是否保存图表
            
        返回:
            float: 最优阈值
        """
        # 确定使用的数据
        if y_true is None:
            y_true = self.y_test
            
        if y_pred_proba is None:
            y_pred_proba = self.y_prob
            
        if y_true is None or y_pred_proba is None:
            logger.warning("测试标签或预测概率尚未加载，无法寻找最优阈值")
            return 0.5
        
        try:
            # 生成细粒度阈值
            thresholds = np.linspace(min_threshold, max_threshold, n_thresholds)
            
            # 计算不同阈值下的指标
            results = []
            for threshold in thresholds:
                y_pred_threshold = (y_pred_proba >= threshold).astype(int)
                
                # 计算基本指标
                accuracy = accuracy_score(y_true, y_pred_threshold)
                precision = precision_score(y_true, y_pred_threshold)
                recall = recall_score(y_true, y_pred_threshold)
                f1 = f1_score(y_true, y_pred_threshold)
                
                # 计算F2分数（更注重召回率）
                from sklearn.metrics import fbeta_score
                f2 = fbeta_score(y_true, y_pred_threshold, beta=2)
                
                # 计算混淆矩阵相关指标
                tn, fp, fn, tp = confusion_matrix(y_true, y_pred_threshold).ravel()
                specificity = tn / (tn + fp) if (tn + fp) > 0 else 0  # 特异度
                npv = tn / (tn + fn) if (tn + fn) > 0 else 0  # 阴性预测值
                false_positive_rate = fp / (fp + tn) if (fp + tn) > 0 else 0  # 假阳性率
                false_negative_rate = fn / (fn + tp) if (fn + tp) > 0 else 0  # 假阴性率
                
                # 计算平衡指标（精确率和召回率的调和平均）
                if precision + recall > 0:
                    balanced = 2 * (precision * recall) / (precision + recall)
                else:
                    balanced = 0
                
                # 计算临床相关指标
                # 约登指数 (Youden's J statistic) = 敏感度 + 特异度 - 1
                youdens_j = recall + specificity - 1
                
                results.append({
                    'threshold': threshold,
                    'accuracy': accuracy,
                    'precision': precision,
                    'recall': recall,
                    'f1': f1,
                    'f2': f2,
                    'specificity': specificity,
                    'npv': npv,
                    'false_positive_rate': false_positive_rate,
                    'false_negative_rate': false_negative_rate,
                    'balanced': balanced,
                    'youdens_j': youdens_j
                })
            
            # 创建DataFrame
            results_df = pd.DataFrame(results)
            
            # 根据标准选择最优阈值
            if criterion in results_df.columns:
                # 对于大多数指标，我们希望最大化它们
                if criterion in ['false_positive_rate', 'false_negative_rate']:
                    best_idx = results_df[criterion].idxmin()  # 最小化假阳性率或假阴性率
                else:
                    best_idx = results_df[criterion].idxmax()  # 最大化其他指标
                    
                best_threshold = results_df.loc[best_idx, 'threshold']
                best_score = results_df.loc[best_idx, criterion]
                
                logger.info(f"根据{criterion}标准找到的最优阈值为 {best_threshold:.4f}，对应的{criterion}分数为 {best_score:.4f}")
                
                # 绘制阈值-指标曲线
                if plot:
                    plt.figure(figsize=(12, 8))
                    
                    # 绘制主要指标
                    for metric in ['accuracy', 'precision', 'recall', 'f1', 'f2', 'specificity']:
                        plt.plot(results_df['threshold'], results_df[metric], label=metric)
                    
                    # 标记最优阈值
                    plt.axvline(x=best_threshold, color='r', linestyle='--', label=f'最优阈值 ({best_threshold:.4f})')
                    
                    plt.xlabel('阈值')
                    plt.ylabel('指标值')
                    plt.title(f'不同阈值下的评估指标 (优化{criterion})')
                    plt.legend()
                    plt.grid(True)
                    
                    # 保存图表（如果需要）
                    if save_fig and self.figures_dir is not None:
                        filename = f'optimal_threshold_{criterion}.png'
                        plt.savefig(os.path.join(self.figures_dir, filename), dpi=300, bbox_inches='tight')
                        logger.info(f"阈值-指标曲线已保存至 {os.path.join(self.figures_dir, filename)}")
                    
                    plt.show()
                
                return best_threshold
            else:
                logger.warning(f"未知的优化标准: {criterion}，将使用默认阈值0.5")
                return 0.5
            
        except Exception as e:
            logger.error(f"寻找最优阈值时出错: {str(e)}")
            return 0.5
    
    def generate_evaluation_report(self, output_path=None):
        """生成评估报告
        
        参数:
            output_path: 报告输出路径，如果为None则打印到控制台
            
        返回:
            str: 评估报告文本
        """
        if self.y_test is None or self.y_pred is None:
            logger.warning("测试标签或预测结果尚未加载，无法生成评估报告")
            return ""
        
        try:
            # 如果尚未计算指标，则计算
            if not self.metrics:
                self.calculate_metrics()
            
            # 生成报告文本
            report = "卒中预测模型评估报告\n"
            report += "===================\n\n"
            
            # 基本指标
            report += "1. 基本评估指标\n"
            report += "------------------\n"
            # 确保F2分数被突出显示
            for metric, value in self.metrics.items():
                if metric == 'f2':
                    report += f"{metric}: {value:.4f} (更注重召回率)\n"
                else:
                    report += f"{metric}: {value:.4f}\n"
            report += "\n"
            
            # 分类报告
            report += "2. 详细分类报告\n"
            report += "------------------\n"
            report += classification_report(self.y_test, self.y_pred)
            report += "\n"
            
            # 混淆矩阵
            report += "3. 混淆矩阵\n"
            report += "------------------\n"
            cm = confusion_matrix(self.y_test, self.y_pred)
            report += f"真阴性 (TN): {cm[0, 0]}\n"
            report += f"假阳性 (FP): {cm[0, 1]}\n"
            report += f"假阴性 (FN): {cm[1, 0]}\n"
            report += f"真阳性 (TP): {cm[1, 1]}\n\n"
            
            # 最优阈值（如果有概率预测）
            if self.y_prob is not None:
                report += "4. 阈值优化\n"
                report += "------------------\n"
                for criterion in ['f1', 'accuracy', 'precision', 'recall', 'balanced']:
                    best_threshold = self.find_optimal_threshold(criterion)
                    report += f"基于{criterion}的最优阈值: {best_threshold:.3f}\n"
                report += "\n"
            
            # 输出报告
            if output_path is not None:
                with open(output_path, 'w') as f:
                    f.write(report)
                logger.info(f"评估报告已保存至 {output_path}")
            else:
                print(report)
            
            return report
            
        except Exception as e:
            logger.error(f"生成评估报告时出错: {str(e)}")
            return ""
    
    def evaluate_and_visualize(self, figures_dir=None, threshold=0.01):
        """执行完整的评估和可视化流程
        
        参数:
            figures_dir: 图表保存目录
            threshold: 分类阈值，默认设为0.01以提高召回率
        """
        if figures_dir is not None:
            self.set_figures_dir(figures_dir)
        
        # 预测（使用较低的阈值以提高召回率）
        self.predict(threshold=threshold)
        
        # 计算指标
        self.calculate_metrics()
        
        # 打印分类报告
        self.print_classification_report()
        
        # 绘制混淆矩阵
        self.plot_confusion_matrix()
        self.plot_confusion_matrix(normalize=True)
        
        # 如果有概率预测，绘制相关曲线
        if self.y_prob is not None:
            self.plot_roc_curve()
            self.plot_precision_recall_curve()
            self.plot_calibration_curve()
            self.plot_probability_distribution()
            self.plot_threshold_metrics()
        
        # 绘制特征重要性
        if self.feature_names is not None:
            self.plot_feature_importance(importance_type='model')
            self.plot_feature_importance(importance_type='permutation')
        
        # 生成评估报告
        if self.figures_dir is not None:
            report_path = os.path.join(self.figures_dir, 'evaluation_report.txt')
            self.generate_evaluation_report(report_path)
        else:
            self.generate_evaluation_report()

# 使用示例
def main():
    # 加载测试数据
    X_test = np.load('../data/processed/X_test.npy')
    y_test = np.load('../data/processed/y_test.npy')
    
    # 加载特征名称（如果有）
    try:
        feature_names = np.load('../data/processed/feature_names.npy')
    except:
        feature_names = None
    
    # 加载模型
    model_path = '../models/gradient_boosting_model.joblib'
    
    # 创建评估器
    evaluator = ModelEvaluator()
    evaluator.load_model(model_path)
    evaluator.load_data(X_test, y_test, feature_names)
    
    # 设置图表保存目录
    figures_dir = '../models/evaluation_results'
    
    # 执行评估和可视化
    evaluator.evaluate_and_visualize(figures_dir)

if __name__ == "__main__":
    main()