# 卒中预测模型 - 风险分层模块

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import logging
import os
import json
from sklearn.calibration import CalibratedClassifierCV

# 导入matplotlib中文配置
from src.utils.matplotlib_config import configure_matplotlib_chinese

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RiskStratifier:
    """风险分层类，负责根据预测概率进行风险分层和干预方案生成"""
    
    def __init__(self, model=None, risk_thresholds=None, intervention_config=None):
        """初始化风险分层器
        
        参数:
            model: 训练好的模型
            risk_thresholds: 风险阈值字典，例如 {'low': 0.05, 'medium': 0.15, 'high': 0.3}
            intervention_config: 干预方案配置
        """
        self.model = model
        
        # 默认风险阈值
        self.risk_thresholds = risk_thresholds or {
            'low': 0.05,      # 低风险阈值（<5%）
            'medium': 0.15,   # 中等风险阈值（5-15%）
            'high': 0.3       # 高风险阈值（15-30%）
                                # >30%为极高风险
        }
        
        # 默认干预方案配置
        self.intervention_config = intervention_config or {
            'low': {
                'risk_level': '低风险',
                'probability_range': '<5%',
                'recommendations': ['生活方式干预', '健康饮食', '规律运动', '戒烟限酒'],
                'follow_up': '年度体检',
                'monitoring': '常规智能手表监测'
            },
            'medium': {
                'risk_level': '中等风险',
                'probability_range': '5-15%',
                'recommendations': ['药物治疗考虑', '严格控制血压', '调整血脂', '血糖管理'],
                'follow_up': '半年门诊',
                'monitoring': '加强智能手表监测'
            },
            'high': {
                'risk_level': '高风险',
                'probability_range': '15-30%',
                'recommendations': ['积极药物治疗', '多因素干预', '考虑抗血小板治疗', '严格控制所有危险因素'],
                'follow_up': '季度门诊',
                'monitoring': '连续监测+定期检查'
            },
            'very_high': {
                'risk_level': '极高风险',
                'probability_range': '>30%',
                'recommendations': ['住院评估', '强化药物治疗', '考虑手术干预', '全面风险因素管理'],
                'follow_up': '月度门诊',
                'monitoring': '密切监测+多学科会诊'
            }
        }
    
    def load_model(self, model_path):
        """加载模型
        
        参数:
            model_path: 模型文件路径
        """
        try:
            import joblib
            self.model = joblib.load(model_path)
            logger.info(f"模型已从 {model_path} 加载")
        except Exception as e:
            logger.error(f"加载模型时出错: {str(e)}")
    
    def set_risk_thresholds(self, risk_thresholds):
        """设置风险阈值
        
        参数:
            risk_thresholds: 风险阈值字典
        """
        self.risk_thresholds = risk_thresholds
        logger.info(f"风险阈值已更新: {risk_thresholds}")
    
    def set_intervention_config(self, intervention_config):
        """设置干预方案配置
        
        参数:
            intervention_config: 干预方案配置字典
        """
        self.intervention_config = intervention_config
        logger.info("干预方案配置已更新")
    
    def load_intervention_config(self, config_path):
        """从JSON文件加载干预方案配置
        
        参数:
            config_path: 配置文件路径
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.intervention_config = json.load(f)
            logger.info(f"干预方案配置已从 {config_path} 加载")
        except Exception as e:
            logger.error(f"加载干预方案配置时出错: {str(e)}")
    
    def save_intervention_config(self, config_path):
        """将干预方案配置保存为JSON文件
        
        参数:
            config_path: 配置文件保存路径
        """
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.intervention_config, f, indent=4, ensure_ascii=False)
            logger.info(f"干预方案配置已保存至 {config_path}")
        except Exception as e:
            logger.error(f"保存干预方案配置时出错: {str(e)}")
    
    def predict_risk(self, X, threshold=0.005):
        """预测风险概率
        
        参数:
            X: 特征数据
            threshold: 分类阈值，默认设为0.005以提高召回率
            
        返回:
            numpy.ndarray: 风险概率
        """
        if self.model is None:
            logger.warning("模型尚未加载，无法预测风险")
            return None
        
        try:
            # 预测概率
            if hasattr(self.model, 'predict_proba'):
                probabilities = self.model.predict_proba(X)[:, 1]
            else:
                logger.warning("模型不支持概率预测，将尝试校准模型")
                # 尝试校准模型
                calibrated_model = CalibratedClassifierCV(self.model, cv='prefit')
                calibrated_model.fit(X[:100], np.zeros(100))  # 仅用于初始化校准器
                probabilities = calibrated_model.predict_proba(X)[:, 1]
            
            # 记录使用的阈值
            logger.info(f"风险预测完成，样本数: {len(probabilities)}，使用阈值: {threshold}")
            self.threshold = threshold
            
            return probabilities
            
        except Exception as e:
            logger.error(f"预测风险时出错: {str(e)}")
            return None
    
    def stratify_risk(self, probabilities):
        """根据预测概率进行风险分层
        
        参数:
            probabilities: 预测概率数组
            
        返回:
            list: 风险等级列表
        """
        if probabilities is None:
            logger.warning("预测概率为空，无法进行风险分层")
            return None
        
        try:
            # 初始化风险等级列表
            risk_levels = []
            
            # 根据阈值进行分层
            for prob in probabilities:
                if prob < self.risk_thresholds['low']:
                    risk_levels.append('low')
                elif prob < self.risk_thresholds['medium']:
                    risk_levels.append('medium')
                elif prob < self.risk_thresholds['high']:
                    risk_levels.append('high')
                else:
                    risk_levels.append('very_high')
            
            logger.info("风险分层完成")
            return risk_levels
            
        except Exception as e:
            logger.error(f"进行风险分层时出错: {str(e)}")
            return None
    
    def generate_interventions(self, risk_levels):
        """根据风险等级生成干预方案
        
        参数:
            risk_levels: 风险等级列表
            
        返回:
            list: 干预方案列表
        """
        if risk_levels is None:
            logger.warning("风险等级为空，无法生成干预方案")
            return None
        
        try:
            # 初始化干预方案列表
            interventions = []
            
            # 根据风险等级生成干预方案
            for level in risk_levels:
                if level in self.intervention_config:
                    interventions.append(self.intervention_config[level])
                else:
                    logger.warning(f"未知的风险等级: {level}，将使用低风险干预方案")
                    interventions.append(self.intervention_config['low'])
            
            logger.info("干预方案生成完成")
            return interventions
            
        except Exception as e:
            logger.error(f"生成干预方案时出错: {str(e)}")
            return None
    
    def process_patients(self, X, patient_ids=None):
        """处理患者数据，预测风险并生成干预方案
        
        参数:
            X: 特征数据
            patient_ids: 患者ID列表，如果为None则使用索引
            
        返回:
            pandas.DataFrame: 包含患者ID、风险概率、风险等级和干预方案的DataFrame
        """
        try:
            # 预测风险概率
            probabilities = self.predict_risk(X)
            if probabilities is None:
                return None
            
            # 风险分层
            risk_levels = self.stratify_risk(probabilities)
            if risk_levels is None:
                return None
            
            # 生成干预方案
            interventions = self.generate_interventions(risk_levels)
            if interventions is None:
                return None
            
            # 准备患者ID
            if patient_ids is None:
                patient_ids = [f'患者_{i+1}' for i in range(len(probabilities))]
            
            # 创建结果DataFrame
            results = []
            for i, (patient_id, prob, level, intervention) in enumerate(zip(patient_ids, probabilities, risk_levels, interventions)):
                result = {
                    '患者ID': patient_id,
                    '风险概率': prob,
                    '风险等级': intervention['risk_level'],
                    '概率范围': intervention['probability_range'],
                    '建议': ', '.join(intervention['recommendations']),
                    '随访': intervention['follow_up'],
                    '监测': intervention['monitoring']
                }
                results.append(result)
            
            results_df = pd.DataFrame(results)
            logger.info(f"患者处理完成，共 {len(results_df)} 条记录")
            
            return results_df
            
        except Exception as e:
            logger.error(f"处理患者数据时出错: {str(e)}")
            return None
    
    def plot_risk_distribution(self, probabilities, save_path=None):
        """绘制风险分布图
        
        参数:
            probabilities: 预测概率数组
            save_path: 图表保存路径
        """
        if probabilities is None:
            logger.warning("预测概率为空，无法绘制风险分布图")
            return
        
        try:
            # 创建风险等级标签
            risk_labels = []
            for prob in probabilities:
                if prob < self.risk_thresholds['low']:
                    risk_labels.append('低风险')
                elif prob < self.risk_thresholds['medium']:
                    risk_labels.append('中等风险')
                elif prob < self.risk_thresholds['high']:
                    risk_labels.append('高风险')
                else:
                    risk_labels.append('极高风险')
            
            # 创建DataFrame
            df = pd.DataFrame({
                '风险概率': probabilities,
                '风险等级': risk_labels
            })
            
            # 绘制风险分布直方图
            plt.figure(figsize=(10, 6))
            sns.histplot(data=df, x='风险概率', hue='风险等级', bins=20, 
                         element='step', common_norm=False)
            
            # 添加阈值线
            plt.axvline(x=self.risk_thresholds['low'], color='green', linestyle='--', 
                        label=f"低风险阈值 ({self.risk_thresholds['low']*100}%)")
            plt.axvline(x=self.risk_thresholds['medium'], color='orange', linestyle='--', 
                        label=f"中等风险阈值 ({self.risk_thresholds['medium']*100}%)")
            plt.axvline(x=self.risk_thresholds['high'], color='red', linestyle='--', 
                        label=f"高风险阈值 ({self.risk_thresholds['high']*100}%)")
            
            plt.title('脑卒中风险分布')
            plt.xlabel('风险概率')
            plt.ylabel('频数')
            plt.legend()
            
            # 保存图表（如果需要）
            if save_path is not None:
                # 确保中文字体配置已应用
                configure_matplotlib_chinese()
                # 正确保存图表
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                logger.info(f"风险分布图已保存至 {save_path}")
            
            plt.show()
            logger.info("风险分布图已绘制")
            
        except Exception as e:
            logger.error(f"绘制风险分布图时出错: {str(e)}")
    
    def plot_risk_stratification(self, risk_levels, save_path=None):
        """绘制风险分层饼图
        
        参数:
            risk_levels: 风险等级列表
            save_path: 图表保存路径
        """
        if risk_levels is None:
            logger.warning("风险等级为空，无法绘制风险分层饼图")
            return
        
        try:
            # 计算各风险等级的数量
            risk_counts = {
                '低风险': risk_levels.count('low'),
                '中等风险': risk_levels.count('medium'),
                '高风险': risk_levels.count('high'),
                '极高风险': risk_levels.count('very_high')
            }
            
            # 设置颜色映射
            colors = ['green', 'orange', 'red', 'darkred']
            
            # 绘制饼图
            plt.figure(figsize=(10, 8))
            plt.pie(risk_counts.values(), labels=risk_counts.keys(), autopct='%1.1f%%', 
                    colors=colors, startangle=90, shadow=True)
            plt.axis('equal')  # 保持饼图为圆形
            plt.title('脑卒中风险分层分布')
            
            # 保存图表（如果需要）
            if save_path is not None:
                # 确保中文字体配置已应用
                configure_matplotlib_chinese()
                # 正确保存图表
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                logger.info(f"风险分层饼图已保存至 {save_path}")
            
            plt.show()
            logger.info("风险分层饼图已绘制")
            
        except Exception as e:
            logger.error(f"绘制风险分层饼图时出错: {str(e)}")

    def generate_patient_report(self, patient_id, probability, risk_level, intervention, 
                               patient_data=None, output_path=None):
        """生成患者风险报告
        
        参数:
            patient_id: 患者ID
            probability: 风险概率
            risk_level: 风险等级
            intervention: 干预方案
            patient_data: 患者数据字典
            output_path: 报告输出路径
            
        返回:
            str: 报告文本
        """
        try:
            # 生成报告文本
            report = f"脑卒中风险评估报告 - 患者ID: {patient_id}\n"
            report += "===========================================\n\n"
            
            # 风险评估结果
            report += "1. 风险评估结果\n"
            report += "------------------\n"
            report += f"风险等级: {intervention['risk_level']}\n"
            report += f"风险概率: {probability:.2%} ({intervention['probability_range']})\n\n"
            
            # 干预建议
            report += "2. 干预建议\n"
            report += "------------------\n"
            for i, rec in enumerate(intervention['recommendations'], 1):
                report += f"{i}. {rec}\n"
            report += "\n"
            
            # 随访和监测计划
            report += "3. 随访和监测计划\n"
            report += "------------------\n"
            report += f"随访计划: {intervention['follow_up']}\n"
            report += f"监测方案: {intervention['monitoring']}\n\n"
            
            # 患者数据（如果提供）
            if patient_data is not None:
                report += "4. 患者数据摘要\n"
                report += "------------------\n"
                for key, value in patient_data.items():
                    report += f"{key}: {value}\n"
                report += "\n"
            
            # 输出报告
            if output_path is not None:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(report)
                logger.info(f"患者风险报告已保存至 {output_path}")
            
            return report
            
        except Exception as e:
            logger.error(f"生成患者风险报告时出错: {str(e)}")
            return ""
    
    def batch_generate_reports(self, results_df, patient_data_df=None, output_dir=None):
        """批量生成患者风险报告
        
        参数:
            results_df: 结果DataFrame
            patient_data_df: 患者数据DataFrame
            output_dir: 报告输出目录
            
        返回:
            int: 成功生成的报告数量
        """
        if results_df is None or len(results_df) == 0:
            logger.warning("结果数据为空，无法生成报告")
            return 0
        
        try:
            # 创建输出目录（如果需要）
            if output_dir is not None:
                os.makedirs(output_dir, exist_ok=True)
            
            # 初始化计数器
            success_count = 0
            
            # 遍历结果生成报告
            for i, row in results_df.iterrows():
                patient_id = row['患者ID']
                probability = row['风险概率']
                risk_level = row['风险等级']
                
                # 构建干预方案字典
                intervention = {
                    'risk_level': row['风险等级'],
                    'probability_range': row['概率范围'],
                    'recommendations': row['建议'].split(', '),
                    'follow_up': row['随访'],
                    'monitoring': row['监测']
                }
                
                # 获取患者数据（如果有）
                patient_data = None
                if patient_data_df is not None and patient_id in patient_data_df['患者ID'].values:
                    patient_data = patient_data_df[patient_data_df['患者ID'] == patient_id].iloc[0].to_dict()
                
                # 设置输出路径
                output_path = None
                if output_dir is not None:
                    output_path = os.path.join(output_dir, f"{patient_id}_风险报告.txt")
                
                # 生成报告
                report = self.generate_patient_report(
                    patient_id, probability, risk_level, intervention, 
                    patient_data, output_path
                )
                
                if report:
                    success_count += 1
            
            logger.info(f"批量生成报告完成，成功: {success_count}/{len(results_df)}")
            return success_count
            
        except Exception as e:
            logger.error(f"批量生成报告时出错: {str(e)}")
            return 0

# 使用示例
def main():
    # 获取项目根目录的绝对路径
    import os
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 加载测试数据
    X_test_path = os.path.join(project_root, 'data', 'processed', 'X_test.npy')
    X_test = np.load(X_test_path, allow_pickle=True)
    
    # 尝试加载患者ID（如果有）
    try:
        patient_ids_path = os.path.join(project_root, 'data', 'processed', 'patient_ids.npy')
        patient_ids = np.load(patient_ids_path, allow_pickle=True)
    except:
        patient_ids = None
    
    # 加载模型
    model_path = os.path.join(project_root, 'models', 'gradient_boosting_model.joblib')
    
    # 创建风险分层器
    stratifier = RiskStratifier()
    stratifier.load_model(model_path)
    
    # 处理患者数据
    results_df = stratifier.process_patients(X_test, patient_ids)
    
    if results_df is not None:
        # 打印结果摘要
        print("\n风险分层结果摘要:")
        print(results_df[['患者ID', '风险概率', '风险等级', '随访']].head())
        
        # 计算各风险等级的数量
        risk_counts = results_df['风险等级'].value_counts()
        print("\n风险等级分布:")
        for level, count in risk_counts.items():
            print(f"{level}: {count} 人 ({count/len(results_df)*100:.1f}%)")
        
        # 保存结果
        results_path = os.path.join(project_root, 'models', 'risk_stratification_results.csv')
        results_df.to_csv(results_path, index=False)
        print(f"\n结果已保存至 '{results_path}'")
        
        # 绘制风险分布图
        distribution_path = os.path.join(project_root, 'models', 'risk_distribution.png')
        stratifier.plot_risk_distribution(results_df['风险概率'].values, distribution_path)
        
        # 生成示例患者报告
        if len(results_df) > 0:
            sample_row = results_df.iloc[0]
            intervention = {
                'risk_level': sample_row['风险等级'],
                'probability_range': sample_row['概率范围'],
                'recommendations': sample_row['建议'].split(', '),
                'follow_up': sample_row['随访'],
                'monitoring': sample_row['监测']
            }
            report_path = os.path.join(project_root, 'models', 'sample_patient_report.txt')
            report = stratifier.generate_patient_report(
                sample_row['患者ID'], sample_row['风险概率'], 
                sample_row['风险等级'], intervention, 
                output_path=report_path
            )
            print(f"\n示例患者报告已保存至 '{report_path}'")

if __name__ == "__main__":
    main()