# 卒中预测模型 - 数据处理模块

import pandas as pd
import numpy as np
import os
import logging
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataProcessor:
    """数据处理类，负责数据加载、清洗和预处理"""
    
    def __init__(self, data_path=None):
        """初始化数据处理器
        
        参数:
            data_path (str): 数据文件路径
        """
        self.data_path = data_path
        self.data = None
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        self.preprocessor = None
        self.categorical_features = None
        self.numerical_features = None
        
    def load_data(self, data_path=None):
        """加载数据集
        
        参数:
            data_path (str): 数据文件路径，如果为None则使用初始化时的路径
            
        返回:
            pandas.DataFrame: 加载的数据集
        """
        if data_path is not None:
            self.data_path = data_path
            
        if self.data_path is None:
            raise ValueError("数据路径未指定")
            
        try:
            # 根据文件扩展名确定加载方法
            if self.data_path.endswith('.csv'):
                self.data = pd.read_csv(self.data_path)
            elif self.data_path.endswith('.xlsx') or self.data_path.endswith('.xls'):
                self.data = pd.read_excel(self.data_path)
            else:
                raise ValueError(f"不支持的文件格式: {self.data_path}")
                
            logger.info(f"成功加载数据，形状: {self.data.shape}")
            return self.data
            
        except Exception as e:
            logger.error(f"加载数据时出错: {str(e)}")
            raise
    
    def explore_data(self):
        """探索性数据分析，返回数据基本统计信息
        
        返回:
            dict: 包含数据统计信息的字典
        """
        if self.data is None:
            logger.warning("数据尚未加载，无法进行探索性分析")
            return None
        
        # 基本统计信息
        stats = {
            'shape': self.data.shape,
            'columns': list(self.data.columns),
            'dtypes': self.data.dtypes.to_dict(),
            'missing_values': self.data.isnull().sum().to_dict(),
            'missing_percentage': (self.data.isnull().sum() / len(self.data) * 100).to_dict(),
            'numerical_stats': self.data.describe().to_dict(),
            'target_distribution': self.data['stroke'].value_counts().to_dict() if 'stroke' in self.data.columns else None,
            'target_percentage': (self.data['stroke'].value_counts() / len(self.data) * 100).to_dict() if 'stroke' in self.data.columns else None
        }
        
        logger.info("完成数据探索性分析")
        return stats
    
    def clean_data(self, df=None):
        """清洗数据，处理缺失值、异常值等
        
        参数:
            df (pandas.DataFrame): 要清洗的数据集，如果为None则使用self.data
            
        返回:
            pandas.DataFrame: 清洗后的数据集
        """
        if df is None:
            if self.data is None:
                logger.warning("数据尚未加载，无法进行数据清洗")
                return None
            df = self.data.copy()
        else:
            df = df.copy()
        
        # 记录原始数据形状
        original_shape = df.shape
        logger.info(f"开始数据清洗，原始数据形状: {original_shape}")
        
        # 1. 处理重复行
        df = df.drop_duplicates()
        logger.info(f"删除重复行后的数据形状: {df.shape}")
        
        # 2. 检查并处理异常值（这里仅示例，实际应根据具体数据特点调整）
        # 例如，处理年龄的异常值
        if 'age' in df.columns:
            df = df[(df['age'] >= 18) & (df['age'] <= 100)]
            logger.info(f"处理年龄异常值后的数据形状: {df.shape}")
        
        # 3. 处理血压异常值
        if 'systolic_bp' in df.columns:
            df = df[(df['systolic_bp'] >= 80) & (df['systolic_bp'] <= 220)]
            logger.info(f"处理收缩压异常值后的数据形状: {df.shape}")
            
        if 'diastolic_bp' in df.columns:
            df = df[(df['diastolic_bp'] >= 40) & (df['diastolic_bp'] <= 130)]
            logger.info(f"处理舒张压异常值后的数据形状: {df.shape}")
        
        # 4. 处理BMI异常值
        if 'bmi' in df.columns:
            df = df[(df['bmi'] >= 15) & (df['bmi'] <= 50)]
            logger.info(f"处理BMI异常值后的数据形状: {df.shape}")
        
        # 记录清洗后的数据形状
        final_shape = df.shape
        logger.info(f"数据清洗完成，最终数据形状: {final_shape}")
        logger.info(f"清洗过程中移除了 {original_shape[0] - final_shape[0]} 行数据")
        
        self.data = df
        return df
    
    def identify_feature_types(self, df=None):
        """识别数据集中的分类特征和数值特征
        
        参数:
            df (pandas.DataFrame): 要识别特征类型的数据集，如果为None则使用self.data
            
        返回:
            tuple: (numerical_features, categorical_features)
        """
        if df is None:
            if self.data is None:
                logger.warning("数据尚未加载，无法识别特征类型")
                return None, None
            df = self.data
        
        # 排除目标变量
        features = [col for col in df.columns if col != 'stroke']
        
        # 识别分类特征和数值特征
        categorical_features = []
        numerical_features = []
        
        for col in features:
            # 检查列是否包含非数值数据
            try:
                # 尝试将列转换为浮点数
                pd.to_numeric(df[col])
                # 如果成功，检查唯一值数量
                if df[col].nunique() < 10:
                    categorical_features.append(col)
                else:
                    numerical_features.append(col)
            except (ValueError, TypeError):
                # 如果转换失败，说明列包含非数值数据，归类为分类特征
                categorical_features.append(col)
        
        self.categorical_features = categorical_features
        self.numerical_features = numerical_features
        
        logger.info(f"识别出 {len(categorical_features)} 个分类特征和 {len(numerical_features)} 个数值特征")
        return numerical_features, categorical_features
    
    def create_preprocessor(self, numerical_features=None, categorical_features=None):
        """创建数据预处理管道
        
        参数:
            numerical_features (list): 数值特征列表，如果为None则使用self.numerical_features
            categorical_features (list): 分类特征列表，如果为None则使用self.categorical_features
            
        返回:
            ColumnTransformer: 预处理转换器
        """
        if numerical_features is None or categorical_features is None:
            if self.categorical_features is None or self.numerical_features is None:
                self.identify_feature_types()
            
            if numerical_features is None:
                numerical_features = self.numerical_features
            
            if categorical_features is None:
                categorical_features = self.categorical_features
        
        # 数值特征处理管道：缺失值填充 + 标准化
        numerical_transformer = Pipeline(steps=[
            ('imputer', SimpleImputer(strategy='median')),
            ('scaler', StandardScaler())
        ])
        
        # 分类特征处理管道：缺失值填充 + 独热编码
        categorical_transformer = Pipeline(steps=[
            ('imputer', SimpleImputer(strategy='most_frequent')),
            ('onehot', OneHotEncoder(handle_unknown='ignore'))
        ])
        
        # 组合转换器
        self.preprocessor = ColumnTransformer(
            transformers=[
                ('num', numerical_transformer, numerical_features),
                ('cat', categorical_transformer, categorical_features)
            ])
        
        logger.info("创建数据预处理管道完成")
        return self.preprocessor
    
    def split_data(self, df=None, test_size=0.2, random_state=42):
        """将数据集分割为训练集和测试集
        
        参数:
            df (pandas.DataFrame): 要分割的数据集，如果为None则使用self.data
            test_size (float): 测试集比例
            random_state (int): 随机种子
            
        返回:
            tuple: (X_train, X_test, y_train, y_test)
        """
        # 如果传入了df参数，则使用传入的数据集，否则使用self.data
        data = df if df is not None else self.data
        
        if data is None:
            logger.warning("数据尚未加载，无法进行数据分割")
            return None, None, None, None
        
        if 'stroke' not in data.columns:
            logger.error("数据集中缺少目标变量'stroke'")
            raise ValueError("数据集中缺少目标变量'stroke'")
        
        # 分离特征和目标变量
        X = data.drop('stroke', axis=1)
        y = data['stroke']
        
        # 分割数据
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )
        
        logger.info(f"数据分割完成，训练集: {self.X_train.shape}, 测试集: {self.X_test.shape}")
        logger.info(f"训练集目标分布: {np.bincount(self.y_train)}")
        logger.info(f"测试集目标分布: {np.bincount(self.y_test)}")
        
        return self.X_train, self.X_test, self.y_train, self.y_test
    
    def apply_preprocessing(self, X_train, X_test, preprocessor=None):
        """对训练集和测试集应用预处理转换
        
        参数:
            X_train (pandas.DataFrame): 训练集特征
            X_test (pandas.DataFrame): 测试集特征
            preprocessor (ColumnTransformer): 预处理器，如果为None则使用self.preprocessor
            
        返回:
            tuple: (X_train_processed, X_test_processed)
        """
        if preprocessor is None:
            if self.preprocessor is None:
                logger.warning("预处理器尚未创建，将创建新的预处理器")
                self.create_preprocessor()
            preprocessor = self.preprocessor
        
        # 对训练数据进行拟合和转换
        X_train_processed = preprocessor.fit_transform(X_train)
        
        # 对测试数据进行转换
        X_test_processed = preprocessor.transform(X_test)
        
        logger.info(f"数据预处理完成，处理后训练集形状: {X_train_processed.shape}")
        logger.info(f"数据预处理完成，处理后测试集形状: {X_test_processed.shape}")
        
        return X_train_processed, X_test_processed

    def preprocess_data(self):
        """对训练集和测试集应用预处理转换
        
        返回:
            tuple: (X_train_processed, X_test_processed, feature_names)
        """
        if self.X_train is None or self.X_test is None:
            logger.warning("数据尚未分割，无法进行预处理")
            return None, None, None
        
        if self.preprocessor is None:
            self.create_preprocessor()
        
        # 使用apply_preprocessing方法处理数据
        X_train_processed, X_test_processed = self.apply_preprocessing(self.X_train, self.X_test, self.preprocessor)
        
        # 获取处理后的特征名称
        feature_names = self.get_feature_names(self.preprocessor)
        
        logger.info(f"数据预处理完成，处理后特征数量: {len(feature_names) if feature_names else X_train_processed.shape[1]}")
        
        return X_train_processed, X_test_processed, feature_names
        
    def get_feature_names(self, preprocessor=None):
        """获取预处理后的特征名称
        
        参数:
            preprocessor (ColumnTransformer): 预处理器，如果为None则使用self.preprocessor
            
        返回:
            list: 特征名称列表
        """
        if preprocessor is None:
            if self.preprocessor is None:
                logger.warning("预处理器尚未创建，无法获取特征名称")
                return None
            preprocessor = self.preprocessor
        
        # 获取数值特征名称
        num_features = self.numerical_features
        
        # 获取分类特征编码后的名称
        cat_features = []
        try:
            # 对于sklearn 0.24+版本
            cat_features = preprocessor.named_transformers_['cat']['onehot'].get_feature_names_out(self.categorical_features)
        except AttributeError:
            try:
                # 对于sklearn 0.23及以下版本
                cat_features = preprocessor.named_transformers_['cat']['onehot'].get_feature_names(self.categorical_features)
            except AttributeError:
                logger.warning("无法获取分类特征的编码名称")
        
        # 合并所有特征名称
        feature_names = list(num_features) + list(cat_features)
        
        return feature_names
    
    def save_preprocessor(self, preprocessor, output_path):
        """保存预处理器
        
        参数:
            preprocessor (ColumnTransformer): 预处理器
            output_path (str): 输出文件路径
            
        返回:
            bool: 是否成功保存
        """
        try:
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 保存预处理器
            from joblib import dump
            dump(preprocessor, output_path)
            
            logger.info(f"预处理器已保存至 {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"保存预处理器时出错: {str(e)}")
            return False
    
    def save_processed_data(self, output_dir):
        """保存处理后的数据
        
        参数:
            output_dir (str): 输出目录路径
            
        返回:
            bool: 是否成功保存
        """
        if self.X_train is None or self.X_test is None or self.y_train is None or self.y_test is None:
            logger.warning("数据尚未处理完成，无法保存")
            return False
        
        try:
            # 确保输出目录存在
            os.makedirs(output_dir, exist_ok=True)
            
            # 保存训练集和测试集
            np.save(os.path.join(output_dir, 'X_train.npy'), self.X_train)
            np.save(os.path.join(output_dir, 'X_test.npy'), self.X_test)
            np.save(os.path.join(output_dir, 'y_train.npy'), self.y_train)
            np.save(os.path.join(output_dir, 'y_test.npy'), self.y_test)
            
            # 保存预处理器
            if self.preprocessor is not None:
                from joblib import dump
                dump(self.preprocessor, os.path.join(output_dir, 'preprocessor.joblib'))
            
            logger.info(f"处理后的数据已保存至 {output_dir}")
            return True
            
        except Exception as e:
            logger.error(f"保存处理后的数据时出错: {str(e)}")
            return False

# 使用示例
def main():
    # 创建数据处理器实例
    processor = DataProcessor(data_path='../data/stroke_data.csv')
    
    # 加载数据
    data = processor.load_data()
    
    # 数据探索
    stats = processor.explore_data()
    print("数据统计信息:")
    for key, value in stats.items():
        if key != 'numerical_stats':  # 数值统计信息太多，不打印
            print(f"{key}: {value}")
    
    # 数据清洗
    cleaned_data = processor.clean_data()
    
    # 识别特征类型
    cat_features, num_features = processor.identify_feature_types()
    print(f"\n分类特征: {cat_features}")
    print(f"数值特征: {num_features}")
    
    # 创建预处理器
    preprocessor = processor.create_preprocessor()
    
    # 分割数据
    X_train, X_test, y_train, y_test = processor.split_data(test_size=0.2)
    
    # 预处理数据
    X_train_processed, X_test_processed, feature_names = processor.preprocess_data()
    print(f"\n处理后的特征数量: {len(feature_names) if feature_names else X_train_processed.shape[1]}")
    
    # 保存处理后的数据
    processor.save_processed_data('../data/processed')

if __name__ == "__main__":
    main()