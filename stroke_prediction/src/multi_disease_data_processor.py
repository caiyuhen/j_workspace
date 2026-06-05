# 多疾病预测数据处理模块

import numpy as np
import pandas as pd
import logging
import os
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.impute import SimpleImputer
from typing import Tuple, Dict, List, Optional

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MultiDiseaseDataProcessor:
    """多疾病预测数据处理器"""
    
    def __init__(self, diseases: List[str] = None):
        """
        初始化多疾病数据处理器
        
        参数:
            diseases: 要处理的疾病列表，默认为8种疾病
        """
        if diseases is None:
            self.diseases = ['stroke', 'diabetes', 'arrhythmia', 'hypertension', 'kidney_disease', 'depression', 'anxiety', 'alzheimer']
        else:
            self.diseases = diseases
            
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.imputer = SimpleImputer(strategy='median')
        self.feature_names = []
        
        logger.info(f"初始化多疾病数据处理器，目标疾病: {self.diseases}")
    
    def load_data(self, data_path: str) -> pd.DataFrame:
        """加载数据
        
        参数:
            data_path: 数据文件路径
            
        返回:
            加载的数据框
        """
        try:
            if data_path.endswith('.csv'):
                df = pd.read_csv(data_path)
            elif data_path.endswith('.xlsx'):
                df = pd.read_excel(data_path)
            else:
                raise ValueError(f"不支持的文件格式: {data_path}")
            
            logger.info(f"数据加载成功，形状: {df.shape}")
            return df
        except Exception as e:
            logger.error(f"数据加载失败: {e}")
            raise
    
    def create_disease_labels(self, df: pd.DataFrame) -> pd.DataFrame:
        """创建多疾病标签
        
        参数:
            df: 原始数据框
            
        返回:
            包含疾病标签的数据框
        """
        logger.info("创建多疾病标签...")
        
        result_df = df.copy()
        
        # 糖尿病标签
        if 'diabetes' in self.diseases:
            diabetes_conditions = (
                (df.get('diabetes_years', 0) > 0) |
                (df.get('fasting_glucose', 0) >= 126) |
                (df.get('hba1c', 0) >= 6.5) |
                # 添加更多糖尿病风险因素
                ((df.get('age', 0) > 45) & (df.get('bmi', 0) > 30) & (df.get('fasting_glucose', 0) > 100)) |
                ((df.get('family_heart_disease', 0) == 1) & (df.get('bmi', 0) > 25) & (df.get('fasting_glucose', 0) > 110))
            )
            result_df['diabetes'] = diabetes_conditions.astype(int)
            
            # 添加一些随机性以增加真实性
            random_diabetes = np.random.random(len(df)) < 0.02  # 2%的随机糖尿病病例
            result_df.loc[random_diabetes, 'diabetes'] = 1
        
        # 心律失常标签
        if 'arrhythmia' in self.diseases:
            arrhythmia_conditions = (
                (df.get('atrial_fibrillation', 0) == 1) |
                (df.get('heart_rate', 70) < 50) |
                (df.get('heart_rate', 70) > 100) |
                (df.get('heart_rate_variability', 30) < 15) |
                # 添加更多心律失常风险因素
                ((df.get('age', 0) > 65) & (df.get('heart_disease', 0) == 1)) |
                ((df.get('hypertension_years', 0) > 10) & (df.get('heart_rate', 70) > 90)) |
                ((df.get('alcohol_units_week', 0) > 14) & (df.get('age', 0) > 50))
            )
            result_df['arrhythmia'] = arrhythmia_conditions.astype(int)
            
            # 添加随机性
            random_arrhythmia = np.random.random(len(df)) < 0.03  # 3%的随机心律失常病例
            result_df.loc[random_arrhythmia, 'arrhythmia'] = 1
        
        # 高血压标签
        if 'hypertension' in self.diseases:
            hypertension_conditions = (
                (df.get('hypertension_years', 0) > 0) |
                (df.get('systolic_bp', 120) >= 140) |
                (df.get('diastolic_bp', 80) >= 90) |
                (df.get('avg_systolic_bp_24h', 120) >= 135) |
                # 添加更多高血压风险因素
                ((df.get('age', 0) > 40) & (df.get('bmi', 0) > 30)) |
                ((df.get('sodium_intake', 0) > 2300) if 'sodium_intake' in df.columns else False) |
                ((df.get('family_heart_disease', 0) == 1) & (df.get('age', 0) > 35)) |
                ((df.get('alcohol_units_week', 0) > 21) & (df.get('age', 0) > 30))
            )
            result_df['hypertension'] = hypertension_conditions.astype(int)
            
            # 添加随机性
            random_hypertension = np.random.random(len(df)) < 0.05  # 5%的随机高血压病例
            result_df.loc[random_hypertension, 'hypertension'] = 1
        
        # 慢性肾病标签
        if 'kidney_disease' in self.diseases:
            kidney_conditions = (
                (df.get('chronic_kidney_disease', 0) == 1) |
                # 基于糖尿病和高血压的肾病风险
                ((df.get('diabetes_years', 0) > 10) & (df.get('systolic_bp', 120) > 140)) |
                ((df.get('age', 0) > 65) & (df.get('hypertension_years', 0) > 15)) |
                # 添加更多肾病风险因素
                ((df.get('diabetes_years', 0) > 5) & (df.get('hba1c', 0) > 8)) |
                ((df.get('age', 0) > 70) & (df.get('heart_disease', 0) == 1)) |
                ((df.get('systolic_bp', 120) > 160) & (df.get('age', 0) > 50))
            )
            result_df['kidney_disease'] = kidney_conditions.astype(int)
            
            # 添加随机性
            random_kidney = np.random.random(len(df)) < 0.015  # 1.5%的随机肾病病例
            result_df.loc[random_kidney, 'kidney_disease'] = 1
        
        # 确保stroke标签存在
        if 'stroke' in self.diseases and 'stroke' not in result_df.columns:
            # 如果没有stroke标签，基于风险因素创建
            stroke_conditions = (
                (df.get('previous_stroke', 0) == 1) |
                (df.get('previous_tia', 0) == 1) |
                (df.get('atrial_fibrillation', 0) == 1) |
                ((df.get('age', 0) > 65) & (df.get('systolic_bp', 120) > 160)) |
                ((df.get('diabetes_years', 0) > 10) & (df.get('age', 0) > 55)) |
                ((df.get('smoking_status', 'never') == 'current') & (df.get('age', 0) > 50))
            )
            result_df['stroke'] = stroke_conditions.astype(int)
            
            # 添加随机性
            random_stroke = np.random.random(len(df)) < 0.01  # 1%的随机脑卒中病例
            result_df.loc[random_stroke, 'stroke'] = 1
        
        # 抑郁症标签
        if 'depression' in self.diseases:
            depression_conditions = (
                # 基于年龄和性别的风险因素
                ((df.get('age', 0) > 40) & (df.get('gender', '') == 'female')) |
                ((df.get('age', 0) > 65)) |
                # 基于慢性疾病的抑郁风险
                ((df.get('diabetes_years', 0) > 5) & (df.get('age', 0) > 50)) |
                ((df.get('heart_disease', 0) == 1) & (df.get('age', 0) > 45)) |
                ((df.get('chronic_kidney_disease', 0) == 1)) |
                # 基于生活方式因素
                ((df.get('smoking_status', 'never') == 'current') & (df.get('age', 0) > 35)) |
                ((df.get('alcohol_units_week', 0) > 14) & (df.get('age', 0) > 30)) |
                ((df.get('bmi', 0) > 35)) |
                # 基于社会经济因素
                ((df.get('sleep_hours', 8) < 5) | (df.get('sleep_hours', 8) > 10)) |
                ((df.get('stress_level', 0) > 7) if 'stress_level' in df.columns else False)
            )
            result_df['depression'] = depression_conditions.astype(int)
            
            # 添加随机性
            random_depression = np.random.random(len(df)) < 0.08  # 8%的随机抑郁症病例
            result_df.loc[random_depression, 'depression'] = 1
        
        # 焦虑症标签
        if 'anxiety' in self.diseases:
            anxiety_conditions = (
                # 基于年龄和性别的风险因素
                ((df.get('age', 0) >= 18) & (df.get('age', 0) <= 35) & (df.get('gender', '') == 'female')) |
                ((df.get('age', 0) > 60)) |
                # 基于心血管疾病的焦虑风险
                ((df.get('heart_disease', 0) == 1)) |
                ((df.get('atrial_fibrillation', 0) == 1)) |
                ((df.get('systolic_bp', 120) > 160)) |
                # 基于代谢疾病的焦虑风险
                ((df.get('diabetes_years', 0) > 0) & (df.get('hba1c', 0) > 8)) |
                ((df.get('thyroid_disorder', 0) == 1) if 'thyroid_disorder' in df.columns else False) |
                # 基于生活方式因素
                ((df.get('smoking_status', 'never') == 'current')) |
                ((df.get('caffeine_intake', 0) > 400) if 'caffeine_intake' in df.columns else False) |
                ((df.get('sleep_hours', 8) < 6)) |
                # 基于其他健康指标
                ((df.get('bmi', 0) < 18.5) | (df.get('bmi', 0) > 30))
            )
            result_df['anxiety'] = anxiety_conditions.astype(int)
            
            # 添加随机性
            random_anxiety = np.random.random(len(df)) < 0.12  # 12%的随机焦虑症病例
            result_df.loc[random_anxiety, 'anxiety'] = 1
        
        # 阿尔茨海默病标签
        if 'alzheimer' in self.diseases:
            alzheimer_conditions = (
                # 主要基于年龄的风险因素
                ((df.get('age', 0) > 75)) |
                ((df.get('age', 0) > 65) & (df.get('gender', '') == 'female')) |
                # 基于心血管疾病的阿尔茨海默风险
                ((df.get('age', 0) > 60) & (df.get('diabetes_years', 0) > 15)) |
                ((df.get('age', 0) > 65) & (df.get('hypertension_years', 0) > 20)) |
                ((df.get('age', 0) > 70) & (df.get('heart_disease', 0) == 1)) |
                ((df.get('age', 0) > 65) & (df.get('previous_stroke', 0) == 1)) |
                # 基于代谢因素
                ((df.get('age', 0) > 60) & (df.get('total_cholesterol', 0) > 240)) |
                ((df.get('age', 0) > 65) & (df.get('bmi', 0) > 30)) |
                # 基于生活方式因素
                ((df.get('age', 0) > 60) & (df.get('smoking_status', 'never') == 'current')) |
                ((df.get('age', 0) > 65) & (df.get('alcohol_units_week', 0) > 21)) |
                # 基于家族史
                ((df.get('age', 0) > 55) & (df.get('family_alzheimer', 0) == 1) if 'family_alzheimer' in df.columns else False) |
                # 基于教育和认知因素
                ((df.get('age', 0) > 70) & (df.get('education_years', 12) < 8) if 'education_years' in df.columns else False)
            )
            result_df['alzheimer'] = alzheimer_conditions.astype(int)
            
            # 添加随机性
            random_alzheimer = np.random.random(len(df)) < 0.02  # 2%的随机阿尔茨海默病例
            result_df.loc[random_alzheimer, 'alzheimer'] = 1
        
        # 记录各疾病的患病率
        for disease in self.diseases:
            if disease in result_df.columns:
                prevalence = result_df[disease].mean()
                positive_cases = result_df[disease].sum()
                logger.info(f"{disease}: 患病率 {prevalence:.3f} ({positive_cases}/{len(result_df)})")
        
        return result_df
    
    def preprocess_features(self, df: pd.DataFrame, fit_transform: bool = True) -> Tuple[np.ndarray, List[str]]:
        """预处理特征数据
        
        参数:
            df: 数据框
            fit_transform: 是否拟合并转换（训练时为True，预测时为False）
            
        返回:
            处理后的特征数组和特征名称列表
        """
        logger.info("开始特征预处理...")
        
        # 复制数据框
        df_processed = df.copy()
        
        # 移除非特征列
        non_feature_cols = ['patient_id', 'exam_date'] + self.diseases
        feature_cols = [col for col in df_processed.columns if col not in non_feature_cols]
        
        # 处理分类变量
        categorical_cols = ['gender', 'ethnicity', 'smoking_status']
        for col in categorical_cols:
            if col in df_processed.columns:
                if fit_transform:
                    if col not in self.label_encoders:
                        self.label_encoders[col] = LabelEncoder()
                    df_processed[col] = self.label_encoders[col].fit_transform(df_processed[col].astype(str))
                else:
                    if col in self.label_encoders:
                        # 处理未见过的类别
                        unique_values = df_processed[col].astype(str).unique()
                        known_values = self.label_encoders[col].classes_
                        for val in unique_values:
                            if val not in known_values:
                                df_processed[col] = df_processed[col].replace(val, known_values[0])
                        df_processed[col] = self.label_encoders[col].transform(df_processed[col].astype(str))
        
        # 选择特征列
        X = df_processed[feature_cols]
        
        # 处理缺失值
        if fit_transform:
            X_imputed = self.imputer.fit_transform(X)
        else:
            X_imputed = self.imputer.transform(X)
        
        # 标准化
        if fit_transform:
            X_scaled = self.scaler.fit_transform(X_imputed)
            self.feature_names = feature_cols
        else:
            X_scaled = self.scaler.transform(X_imputed)
        
        logger.info(f"特征预处理完成，特征数量: {X_scaled.shape[1]}")
        
        return X_scaled, self.feature_names
    
    def split_data(self, df: pd.DataFrame, test_size: float = 0.2, random_state: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """分割数据集
        
        参数:
            df: 数据框
            test_size: 测试集比例
            random_state: 随机种子
            
        返回:
            训练集和测试集数据框
        """
        logger.info(f"分割数据集，测试集比例: {test_size}")
        
        # 基于主要疾病进行分层抽样
        stratify_col = 'stroke' if 'stroke' in df.columns else self.diseases[0]
        
        if stratify_col in df.columns:
            train_df, test_df = train_test_split(
                df, 
                test_size=test_size, 
                random_state=random_state,
                stratify=df[stratify_col]
            )
        else:
            train_df, test_df = train_test_split(
                df, 
                test_size=test_size, 
                random_state=random_state
            )
        
        logger.info(f"数据分割完成，训练集: {len(train_df)}, 测试集: {len(test_df)}")
        
        return train_df, test_df
    
    def prepare_multi_disease_data(self, data_path: str, test_size: float = 0.2) -> Tuple[np.ndarray, pd.DataFrame, np.ndarray, pd.DataFrame, List[str]]:
        """准备多疾病预测数据
        
        参数:
            data_path: 数据文件路径
            test_size: 测试集比例
            
        返回:
            X_train, y_train, X_test, y_test, feature_names
        """
        logger.info("开始准备多疾病预测数据...")
        
        # 加载数据
        df = self.load_data(data_path)
        
        # 创建疾病标签
        df_with_labels = self.create_disease_labels(df)
        
        # 分割数据
        train_df, test_df = self.split_data(df_with_labels, test_size=test_size)
        
        # 预处理特征
        X_train, feature_names = self.preprocess_features(train_df, fit_transform=True)
        X_test, _ = self.preprocess_features(test_df, fit_transform=False)
        
        # 准备标签
        y_train = train_df[self.diseases]
        y_test = test_df[self.diseases]
        
        logger.info("多疾病预测数据准备完成")
        logger.info(f"训练集形状: X={X_train.shape}, y={y_train.shape}")
        logger.info(f"测试集形状: X={X_test.shape}, y={y_test.shape}")
        
        return X_train, y_train, X_test, y_test, feature_names
    
    def save_preprocessor(self, save_path: str):
        """保存预处理器
        
        参数:
            save_path: 保存路径
        """
        import joblib
        
        preprocessor_data = {
            'scaler': self.scaler,
            'label_encoders': self.label_encoders,
            'imputer': self.imputer,
            'feature_names': self.feature_names,
            'diseases': self.diseases
        }
        
        joblib.dump(preprocessor_data, save_path)
        logger.info(f"预处理器已保存至: {save_path}")
    
    def load_preprocessor(self, save_path: str):
        """加载预处理器
        
        参数:
            save_path: 保存路径
        """
        import joblib
        
        preprocessor_data = joblib.load(save_path)
        
        self.scaler = preprocessor_data['scaler']
        self.label_encoders = preprocessor_data['label_encoders']
        self.imputer = preprocessor_data['imputer']
        self.feature_names = preprocessor_data['feature_names']
        self.diseases = preprocessor_data['diseases']
        
        logger.info(f"预处理器已从 {save_path} 加载")
    
    def get_data_summary(self, df: pd.DataFrame) -> Dict:
        """获取数据摘要
        
        参数:
            df: 数据框
            
        返回:
            数据摘要字典
        """
        summary = {
            'total_samples': len(df),
            'features': len([col for col in df.columns if col not in ['patient_id', 'exam_date'] + self.diseases]),
            'diseases': {}
        }
        
        for disease in self.diseases:
            if disease in df.columns:
                positive_cases = df[disease].sum()
                prevalence = df[disease].mean()
                summary['diseases'][disease] = {
                    'positive_cases': int(positive_cases),
                    'prevalence': float(prevalence),
                    'negative_cases': int(len(df) - positive_cases)
                }
        
        return summary
    
    def create_synthetic_risk_data(self, df: pd.DataFrame, n_high_risk: int = 100) -> pd.DataFrame:
        """创建合成的高风险数据样本
        
        参数:
            df: 原始数据框
            n_high_risk: 要创建的高风险样本数量
            
        返回:
            包含高风险样本的数据框
        """
        logger.info(f"创建 {n_high_risk} 个高风险合成样本...")
        
        # 基于现有数据创建高风险样本
        high_risk_samples = []
        
        for i in range(n_high_risk):
            # 随机选择一个基础样本
            base_sample = df.sample(1).iloc[0].copy()
            
            # 修改为高风险特征
            base_sample['age'] = np.random.uniform(65, 85)  # 高龄
            base_sample['systolic_bp'] = np.random.uniform(160, 200)  # 高血压
            base_sample['diastolic_bp'] = np.random.uniform(95, 120)  # 高舒张压
            base_sample['fasting_glucose'] = np.random.uniform(140, 250)  # 高血糖
            base_sample['hba1c'] = np.random.uniform(7.5, 12)  # 高糖化血红蛋白
            base_sample['bmi'] = np.random.uniform(30, 40)  # 肥胖
            base_sample['total_cholesterol'] = np.random.uniform(240, 350)  # 高胆固醇
            base_sample['smoking_status'] = np.random.choice(['current', 'former'])  # 吸烟史
            base_sample['diabetes_years'] = np.random.randint(5, 20)  # 糖尿病史
            base_sample['hypertension_years'] = np.random.randint(5, 25)  # 高血压史
            
            # 更新患者ID
            base_sample['patient_id'] = f'SYNTH_{i+1:06d}'
            
            high_risk_samples.append(base_sample)
        
        high_risk_df = pd.DataFrame(high_risk_samples)
        
        # 重新创建疾病标签
        high_risk_df = self.create_disease_labels(high_risk_df)
        
        logger.info("高风险合成样本创建完成")
        
        return high_risk_df