# 多疾病预测评估模块

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, 
    roc_auc_score, roc_curve, precision_recall_curve, 
    confusion_matrix, classification_report
)
from sklearn.calibration import calibration_curve
import logging
from typing import Dict, List, Tuple, Optional
import os

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MultiDiseaseEvaluator:
    """多疾病预测评估器"""
    
    def __init__(self, diseases: List[str] = None):
        """初始化评估器
        
        参数:
            diseases: 疾病列表
        """
        if diseases is None:
            self.diseases = ['stroke', 'diabetes', 'arrhythmia', 'hypertension', 'kidney_disease']
        else:
            self.diseases = diseases
            
        self.evaluation_results = {}
        
        logger.info(f"初始化多疾病评估器，目标疾病: {self.diseases}")
    
    def evaluate_single_disease(self, y_true: np.ndarray, y_pred: np.ndarray, y_prob: np.ndarray = None, disease_name: str = 'disease') -> Dict:
        """评估单个疾病的预测性能
        
        参数:
            y_true: 真实标签
            y_pred: 预测标签
            y_prob: 预测概率
            disease_name: 疾病名称
            
        返回:
            评估结果字典
        """
        results = {
            'disease': disease_name,
            'accuracy': accuracy_score(y_true, y_pred),
            'precision': precision_score(y_true, y_pred, average='binary', zero_division=0),
            'recall': recall_score(y_true, y_pred, average='binary', zero_division=0),
            'f1_score': f1_score(y_true, y_pred, average='binary', zero_division=0),
            'support': len(y_true),
            'positive_cases': np.sum(y_true),
            'predicted_positive': np.sum(y_pred)
        }
        
        # 如果有预测概率，计算AUC
        if y_prob is not None:
            try:
                results['auc'] = roc_auc_score(y_true, y_prob)
            except ValueError as e:
                logger.warning(f"无法计算 {disease_name} 的AUC: {e}")
                results['auc'] = np.nan
        else:
            results['auc'] = np.nan
        
        # 计算混淆矩阵
        cm = confusion_matrix(y_true, y_pred)
        if cm.shape == (2, 2):
            tn, fp, fn, tp = cm.ravel()
            results['true_negative'] = tn
            results['false_positive'] = fp
            results['false_negative'] = fn
            results['true_positive'] = tp
            
            # 计算特异性和敏感性
            results['specificity'] = tn / (tn + fp) if (tn + fp) > 0 else 0
            results['sensitivity'] = tp / (tp + fn) if (tp + fn) > 0 else 0
        
        return results
    
    def evaluate_multi_disease(self, y_true: pd.DataFrame, y_pred: pd.DataFrame, y_prob: pd.DataFrame = None) -> Dict:
        """评估多疾病预测性能
        
        参数:
            y_true: 真实标签数据框
            y_pred: 预测标签数据框
            y_prob: 预测概率数据框
            
        返回:
            评估结果字典
        """
        logger.info("开始多疾病预测评估...")
        
        results = {
            'individual_results': {},
            'overall_metrics': {},
            'summary': {}
        }
        
        # 评估每个疾病
        for disease in self.diseases:
            if disease in y_true.columns and disease in y_pred.columns:
                y_true_disease = y_true[disease].values
                y_pred_disease = y_pred[disease].values
                y_prob_disease = y_prob[disease].values if y_prob is not None and disease in y_prob.columns else None
                
                disease_results = self.evaluate_single_disease(
                    y_true_disease, y_pred_disease, y_prob_disease, disease
                )
                results['individual_results'][disease] = disease_results
                
                logger.info(f"{disease}: Accuracy={disease_results['accuracy']:.3f}, F1={disease_results['f1_score']:.3f}, AUC={disease_results.get('auc', 'N/A')}")
        
        # 计算整体指标
        if results['individual_results']:
            # 平均指标
            metrics = ['accuracy', 'precision', 'recall', 'f1_score', 'auc']
            for metric in metrics:
                values = [res[metric] for res in results['individual_results'].values() if not np.isnan(res.get(metric, np.nan))]
                if values:
                    results['overall_metrics'][f'mean_{metric}'] = np.mean(values)
                    results['overall_metrics'][f'std_{metric}'] = np.std(values)
        
        # 生成摘要
        results['summary'] = self._generate_summary(results)
        
        self.evaluation_results = results
        logger.info("多疾病预测评估完成")
        
        return results
    
    def _generate_summary(self, results: Dict) -> Dict:
        """生成评估摘要
        
        参数:
            results: 评估结果
            
        返回:
            摘要字典
        """
        summary = {
            'total_diseases': len(results['individual_results']),
            'best_performing_disease': None,
            'worst_performing_disease': None,
            'diseases_with_good_performance': [],  # F1 > 0.7
            'diseases_needing_improvement': []     # F1 < 0.5
        }
        
        if results['individual_results']:
            # 找出表现最好和最差的疾病（基于F1分数）
            f1_scores = {disease: res['f1_score'] for disease, res in results['individual_results'].items()}
            
            if f1_scores:
                best_disease = max(f1_scores, key=f1_scores.get)
                worst_disease = min(f1_scores, key=f1_scores.get)
                
                summary['best_performing_disease'] = {
                    'disease': best_disease,
                    'f1_score': f1_scores[best_disease]
                }
                summary['worst_performing_disease'] = {
                    'disease': worst_disease,
                    'f1_score': f1_scores[worst_disease]
                }
                
                # 分类疾病表现
                for disease, f1_score in f1_scores.items():
                    if f1_score > 0.7:
                        summary['diseases_with_good_performance'].append(disease)
                    elif f1_score < 0.5:
                        summary['diseases_needing_improvement'].append(disease)
        
        return summary
    
    def plot_roc_curves(self, y_true: pd.DataFrame, y_prob: pd.DataFrame, save_path: str = None):
        """绘制ROC曲线
        
        参数:
            y_true: 真实标签
            y_prob: 预测概率
            save_path: 保存路径
        """
        plt.figure(figsize=(12, 8))
        
        for disease in self.diseases:
            if disease in y_true.columns and disease in y_prob.columns:
                y_true_disease = y_true[disease].values
                y_prob_disease = y_prob[disease].values
                
                try:
                    fpr, tpr, _ = roc_curve(y_true_disease, y_prob_disease)
                    auc = roc_auc_score(y_true_disease, y_prob_disease)
                    plt.plot(fpr, tpr, label=f'{disease.title()} (AUC = {auc:.3f})')
                except ValueError as e:
                    logger.warning(f"无法绘制 {disease} 的ROC曲线: {e}")
        
        plt.plot([0, 1], [0, 1], 'k--', label='Random')
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('假阳性率')
        plt.ylabel('真阳性率')
        plt.title('ROC Curves for Multi-Disease Prediction')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"ROC曲线图已保存至: {save_path}")
        
        plt.show()
    
    def plot_precision_recall_curves(self, y_true: pd.DataFrame, y_prob: pd.DataFrame, save_path: str = None):
        """绘制精确率-召回率曲线
        
        参数:
            y_true: 真实标签
            y_prob: 预测概率
            save_path: 保存路径
        """
        plt.figure(figsize=(12, 8))
        
        for disease in self.diseases:
            if disease in y_true.columns and disease in y_prob.columns:
                y_true_disease = y_true[disease].values
                y_prob_disease = y_prob[disease].values
                
                try:
                    precision, recall, _ = precision_recall_curve(y_true_disease, y_prob_disease)
                    plt.plot(recall, precision, label=f'{disease.title()}')
                except ValueError as e:
                    logger.warning(f"无法绘制 {disease} 的PR曲线: {e}")
        
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('召回率')
        plt.ylabel('精确率')
        plt.title('Precision-Recall Curves for Multi-Disease Prediction')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"PR曲线图已保存至: {save_path}")
        
        plt.show()
    
    def plot_confusion_matrices(self, y_true: pd.DataFrame, y_pred: pd.DataFrame, save_dir: str = None):
        """绘制混淆矩阵
        
        参数:
            y_true: 真实标签
            y_pred: 预测标签
            save_dir: 保存目录
        """
        n_diseases = len(self.diseases)
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        axes = axes.flatten()
        
        for i, disease in enumerate(self.diseases):
            if i >= len(axes):
                break
                
            if disease in y_true.columns and disease in y_pred.columns:
                y_true_disease = y_true[disease].values
                y_pred_disease = y_pred[disease].values
                
                cm = confusion_matrix(y_true_disease, y_pred_disease)
                
                sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=axes[i],
                           xticklabels=['阴性', '阳性'],
                           yticklabels=['阴性', '阳性'])
                axes[i].set_title(f'{disease.title()}')
                axes[i].set_xlabel('预测标签')
                axes[i].set_ylabel('真实标签')
        
        # 隐藏多余的子图
        for i in range(len(self.diseases), len(axes)):
            axes[i].set_visible(False)
        
        plt.tight_layout()
        
        if save_dir:
            os.makedirs(save_dir, exist_ok=True)
            save_path = os.path.join(save_dir, 'confusion_matrices.png')
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"混淆矩阵图已保存至: {save_path}")
        
        plt.show()
    
    def plot_calibration_curves(self, y_true: pd.DataFrame, y_prob: pd.DataFrame, save_path: str = None):
        """绘制校准曲线
        
        参数:
            y_true: 真实标签
            y_prob: 预测概率
            save_path: 保存路径
        """
        plt.figure(figsize=(12, 8))
        
        for disease in self.diseases:
            if disease in y_true.columns and disease in y_prob.columns:
                y_true_disease = y_true[disease].values
                y_prob_disease = y_prob[disease].values
                
                try:
                    fraction_of_positives, mean_predicted_value = calibration_curve(
                        y_true_disease, y_prob_disease, n_bins=10
                    )
                    plt.plot(mean_predicted_value, fraction_of_positives, 's-', label=f'{disease.title()}')
                except ValueError as e:
                    logger.warning(f"无法绘制 {disease} 的校准曲线: {e}")
        
        plt.plot([0, 1], [0, 1], 'k--', label='Perfect Calibration')
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.0])
        plt.xlabel('平均预测概率')
        plt.ylabel('阳性样本比例')
        plt.title('Calibration Curves for Multi-Disease Prediction')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"校准曲线图已保存至: {save_path}")
        
        plt.show()
    
    def generate_report(self, save_path: str = None) -> str:
        """生成评估报告
        
        参数:
            save_path: 保存路径
            
        返回:
            报告文本
        """
        if not self.evaluation_results:
            logger.warning("没有评估结果，请先运行评估")
            return ""
        
        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("多疾病预测模型评估报告")
        report_lines.append("=" * 60)
        report_lines.append("")
        
        # 整体摘要
        summary = self.evaluation_results['summary']
        report_lines.append("整体摘要:")
        report_lines.append(f"  评估疾病数量: {summary['total_diseases']}")
        
        if summary['best_performing_disease']:
            best = summary['best_performing_disease']
            report_lines.append(f"  表现最佳疾病: {best['disease']} (F1: {best['f1_score']:.3f})")
        
        if summary['worst_performing_disease']:
            worst = summary['worst_performing_disease']
            report_lines.append(f"  表现最差疾病: {worst['disease']} (F1: {worst['f1_score']:.3f})")
        
        if summary['diseases_with_good_performance']:
            report_lines.append(f"  表现良好疾病 (F1>0.7): {', '.join(summary['diseases_with_good_performance'])}")
        
        if summary['diseases_needing_improvement']:
            report_lines.append(f"  需要改进疾病 (F1<0.5): {', '.join(summary['diseases_needing_improvement'])}")
        
        report_lines.append("")
        
        # 整体指标
        overall = self.evaluation_results['overall_metrics']
        if overall:
            report_lines.append("整体指标 (平均值):")
            for metric, value in overall.items():
                if 'mean_' in metric:
                    metric_name = metric.replace('mean_', '')
                    std_key = f'std_{metric_name}'
                    std_value = overall.get(std_key, 0)
                    report_lines.append(f"  {metric_name.upper()}: {value:.3f} (±{std_value:.3f})")
            report_lines.append("")
        
        # 各疾病详细结果
        report_lines.append("各疾病详细结果:")
        report_lines.append("-" * 60)
        
        for disease, results in self.evaluation_results['individual_results'].items():
            report_lines.append(f"\n{disease.upper()}:")
            report_lines.append(f"  准确率: {results['accuracy']:.3f}")
            report_lines.append(f"  精确率: {results['precision']:.3f}")
            report_lines.append(f"  召回率: {results['recall']:.3f}")
            report_lines.append(f"  F1分数: {results['f1_score']:.3f}")
            if not np.isnan(results.get('auc', np.nan)):
                report_lines.append(f"  AUC: {results['auc']:.3f}")
            report_lines.append(f"  样本数: {results['support']}")
            report_lines.append(f"  阳性样本: {results['positive_cases']}")
            report_lines.append(f"  预测阳性: {results['predicted_positive']}")
            
            if 'specificity' in results:
                report_lines.append(f"  特异性: {results['specificity']:.3f}")
                report_lines.append(f"  敏感性: {results['sensitivity']:.3f}")
        
        report_lines.append("")
        report_lines.append("=" * 60)
        
        report_text = "\n".join(report_lines)
        
        if save_path:
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(report_text)
            logger.info(f"评估报告已保存至: {save_path}")
        
        return report_text
    
    def save_results(self, save_path: str):
        """保存评估结果
        
        参数:
            save_path: 保存路径
        """
        import json
        
        # 转换numpy类型为Python原生类型
        def convert_numpy(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {key: convert_numpy(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy(item) for item in obj]
            else:
                return obj
        
        results_to_save = convert_numpy(self.evaluation_results)
        
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(results_to_save, f, indent=2, ensure_ascii=False)
        
        logger.info(f"评估结果已保存至: {save_path}")
    
    def load_results(self, save_path: str):
        """加载评估结果
        
        参数:
            save_path: 保存路径
        """
        import json
        
        with open(save_path, 'r', encoding='utf-8') as f:
            self.evaluation_results = json.load(f)
        
        logger.info(f"评估结果已从 {save_path} 加载")