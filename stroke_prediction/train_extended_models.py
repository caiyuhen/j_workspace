#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
扩展多疾病预测模型训练脚本
训练包含抑郁症、焦虑症、阿尔茨海默病的8疾病预测模型
"""

import os
import sys
import logging
import pandas as pd
import numpy as np
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.multi_disease_trainer import MultiDiseaseTrainer
from src.multi_disease_data_processor import MultiDiseaseDataProcessor

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/extended_training.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    """主训练函数"""
    logger.info("开始扩展多疾病预测模型训练...")
    
    # 创建结果目录
    results_dir = 'results/extended_models'
    os.makedirs(results_dir, exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    # 定义8种疾病
    diseases = ['stroke', 'diabetes', 'arrhythmia', 'hypertension', 'kidney_disease', 'depression', 'anxiety', 'alzheimer']
    
    # 初始化训练器
    trainer = MultiDiseaseTrainer(diseases=diseases)
    
    # 加载扩展后的数据
    data_path = 'data/raw/multi_disease_data_8diseases_4000.csv'
    logger.info(f"加载数据: {data_path}")
    
    try:
        trainer.load_data_from_file(data_path, test_size=0.2)
        logger.info("数据加载成功")
        
        # 检查数据质量
        logger.info(f"训练集形状: {trainer.X_train.shape}")
        logger.info(f"测试集形状: {trainer.X_test.shape}")
        logger.info(f"疾病标签: {list(trainer.y_train.columns)}")
        
        # 显示各疾病的患病率
        for disease in diseases:
            if disease in trainer.y_train.columns:
                prevalence = trainer.y_train[disease].mean()
                positive_cases = trainer.y_train[disease].sum()
                logger.info(f"{disease}: 患病率 {prevalence:.3f} ({positive_cases}/{len(trainer.y_train)})")
        
        # 训练模型类型列表
        model_types = ['logistic', 'random_forest', 'gradient_boosting']
        
        # 为每种模型类型训练所有疾病
        for model_type in model_types:
            logger.info(f"\n开始训练 {model_type} 模型...")
            
            try:
                # 训练独立模型
                trainer.train_individual_models(
                    model_type=model_type,
                    use_smote=True
                )
                
                # 评估模型
                results = trainer.evaluate()
                
                # 保存模型
                model_save_path = os.path.join(results_dir, f'{model_type}_models')
                trainer.save_models(model_save_path)
                logger.info(f"{model_type} 模型已保存到: {model_save_path}")
                
                # 保存评估结果
                results_df = pd.DataFrame(results).T
                results_file = os.path.join(results_dir, f'{model_type}_results.csv')
                results_df.to_csv(results_file)
                logger.info(f"{model_type} 评估结果已保存到: {results_file}")
                
                # 显示关键指标
                logger.info(f"\n{model_type} 模型性能摘要:")
                for disease in diseases:
                    if disease in results:
                        auc = results[disease].get('auc', 0)
                        accuracy = results[disease].get('accuracy', 0)
                        logger.info(f"  {disease}: AUC={auc:.3f}, Accuracy={accuracy:.3f}")
                
            except Exception as e:
                logger.error(f"训练 {model_type} 模型时出错: {e}")
                continue
        
        # 训练多任务模型
        logger.info("\n开始训练多任务学习模型...")
        try:
            trainer.train_multi_task_model(model_type='gradient_boosting')
            
            # 评估多任务模型
            multi_task_results = trainer.evaluate(use_multi_task=True)
            
            # 保存多任务模型
            multi_task_save_path = os.path.join(results_dir, 'multi_task_model')
            trainer.save_models(multi_task_save_path)
            logger.info(f"多任务模型已保存到: {multi_task_save_path}")
            
            # 保存多任务评估结果
            multi_task_df = pd.DataFrame(multi_task_results).T
            multi_task_file = os.path.join(results_dir, 'multi_task_results.csv')
            multi_task_df.to_csv(multi_task_file)
            logger.info(f"多任务评估结果已保存到: {multi_task_file}")
            
        except Exception as e:
            logger.error(f"训练多任务模型时出错: {e}")
        
        # 生成特征重要性报告
        try:
            trainer.plot_all_feature_importances(save_dir=results_dir)
            logger.info("特征重要性图表已生成")
        except Exception as e:
            logger.error(f"生成特征重要性图表时出错: {e}")
        
        # 生成训练报告
        generate_training_report(trainer, results_dir)
        
        logger.info("\n扩展多疾病预测模型训练完成！")
        logger.info(f"所有结果已保存到: {results_dir}")
        
    except Exception as e:
        logger.error(f"训练过程中出现错误: {e}")
        raise

def generate_training_report(trainer, results_dir):
    """生成训练报告"""
    report_path = os.path.join(results_dir, 'training_report.md')
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# 扩展多疾病预测模型训练报告\n\n")
        f.write(f"**训练时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## 模型概述\n\n")
        f.write("本次训练扩展了原有的5疾病预测系统，新增了以下3种疾病的预测能力：\n")
        f.write("- 抑郁症 (Depression)\n")
        f.write("- 焦虑症 (Anxiety)\n")
        f.write("- 阿尔茨海默病 (Alzheimer's Disease)\n\n")
        
        f.write("## 数据集信息\n\n")
        f.write(f"- 训练样本数: {len(trainer.X_train)}\n")
        f.write(f"- 测试样本数: {len(trainer.X_test)}\n")
        f.write(f"- 特征数量: {len(trainer.feature_names)}\n")
        f.write(f"- 疾病数量: {len(trainer.diseases)}\n\n")
        
        f.write("## 疾病患病率\n\n")
        f.write("| 疾病 | 患病率 | 阳性样本数 |\n")
        f.write("|------|--------|-----------|\n")
        
        for disease in trainer.diseases:
            if disease in trainer.y_train.columns:
                prevalence = trainer.y_train[disease].mean()
                positive_cases = trainer.y_train[disease].sum()
                f.write(f"| {disease} | {prevalence:.3f} | {positive_cases} |\n")
        
        f.write("\n## 模型架构\n\n")
        f.write("训练了以下类型的模型：\n")
        f.write("1. **逻辑回归** (Logistic Regression) - 基线模型\n")
        f.write("2. **随机森林** (Random Forest) - 集成学习模型\n")
        f.write("3. **梯度提升** (Gradient Boosting) - 高性能集成模型\n")
        f.write("4. **多任务学习** (Multi-task Learning) - 联合预测模型\n\n")
        
        f.write("## 数据处理\n\n")
        f.write("- 使用SMOTE技术处理类别不平衡问题\n")
        f.write("- 标准化特征数据\n")
        f.write("- 80/20 训练测试集分割\n")
        f.write("- 基于现有健康指标推导新疾病标签\n\n")
        
        f.write("## 新疾病标签生成逻辑\n\n")
        f.write("### 抑郁症\n")
        f.write("- 年龄和性别风险因素（40岁以上女性，65岁以上）\n")
        f.write("- 慢性疾病相关风险（糖尿病、心脏病、肾病）\n")
        f.write("- 生活方式因素（吸烟、酗酒、肥胖、睡眠问题）\n\n")
        
        f.write("### 焦虑症\n")
        f.write("- 年龄和性别风险因素（18-35岁女性，60岁以上）\n")
        f.write("- 心血管疾病风险（心脏病、房颤、高血压）\n")
        f.write("- 代谢疾病风险（糖尿病、甲状腺疾病）\n")
        f.write("- 生活方式因素（吸烟、咖啡因、睡眠不足、BMI异常）\n\n")
        
        f.write("### 阿尔茨海默病\n")
        f.write("- 主要年龄风险因素（75岁以上，65岁以上女性）\n")
        f.write("- 心血管疾病风险（长期糖尿病、高血压、心脏病、脑卒中史）\n")
        f.write("- 代谢因素（高胆固醇、肥胖）\n")
        f.write("- 生活方式因素（吸烟、酗酒）\n")
        f.write("- 遗传和教育因素（家族史、教育水平）\n\n")
        
        f.write("## 下一步计划\n\n")
        f.write("1. 对新增疾病模型进行超参数调优\n")
        f.write("2. 评估8种疾病预测系统的整体性能\n")
        f.write("3. 更新风险报告生成器\n")
        f.write("4. 生成综合评估报告\n")
    
    logger.info(f"训练报告已保存到: {report_path}")

if __name__ == '__main__':
    main()