# 智能多疾病预测系统

## 项目概述

本项目是一个基于机器学习的智能医疗预测系统，支持14种常见疾病的风险评估。系统集成了天气和空气质量数据，通过分析多维度健康指标和环境因素，为用户提供精准的疾病风险预测和个性化健康建议。

## 🏥 支持的疾病预测

系统支持以下14种疾病的风险评估：

1. **脑卒中** (Stroke) - 主要预测模型
2. **糖尿病** (Diabetes)
3. **心律不齐** (Arrhythmia)
4. **高血压** (Hypertension)
5. **肾脏疾病** (Kidney Disease)
6. **抑郁症** (Depression)
7. **焦虑症** (Anxiety)
8. **阿尔茨海默病** (Alzheimer)
9. **冠心病** (Coronary Heart Disease)
10. **痛风** (Gout)
11. **帕金森病** (Parkinson)
12. **慢性心力衰竭** (Heart Failure)
13. **支气管哮喘** (Bronchial Asthma)
14. **支气管扩张** (Bronchiectasis)

## ✨ 功能特点

### 🔬 核心预测功能
- **多疾病同时预测**：一次输入，获得14种疾病的风险评估
- **智能数据填充**：自动处理缺失值，使用合理默认值
- **风险等级分层**：低风险、中风险、高风险、极高风险四级分类
- **个性化建议**：基于风险等级提供针对性的健康干预建议

### 🌤️ 环境数据集成
- **天气数据获取**：实时获取未来5天天气预报
- **空气质量监测**：集成AQI、PM2.5等空气质量指标
- **环境影响分析**：将环境因素纳入疾病风险评估模型
- **季节性分析**：考虑季节变化对疾病风险的影响

### 🖥️ Web界面功能
- **直观的用户界面**：现代化的响应式Web设计
- **实时数据展示**：动态显示天气和空气质量信息
- **交互式表单**：用户友好的数据输入界面
- **结果可视化**：图表展示预测结果和风险分布

### 🔧 技术特点
- **模块化架构**：清晰的代码结构，易于维护和扩展
- **RESTful API**：提供标准化的API接口
- **容错处理**：完善的错误处理和异常恢复机制
- **性能优化**：高效的数据处理和模型推理

## 📁 项目结构

```
stroke_prediction/
├── 📁 data/                    # 数据存储目录
│   ├── 📁 processed/           # 预处理后的数据
│   └── 📁 raw/                 # 原始数据
├── 📁 models/                  # 训练好的模型文件
│   ├── stroke_model.joblib     # 脑卒中预测模型
│   ├── diabetes_model.joblib   # 糖尿病预测模型
│   └── ...                     # 其他疾病模型
├── 📁 src/                     # 核心源代码
│   ├── data_processing.py      # 数据预处理模块
│   ├── feature_eng.py          # 特征工程模块
│   ├── model_training.py       # 模型训练模块
│   ├── model_evaluation.py     # 模型评估模块
│   ├── risk_stratification.py  # 风险分层模块
│   └── 📁 utils/               # 工具函数
├── 📁 templates/               # Web界面模板
│   ├── index.html              # 主页面
│   ├── results.html            # 结果展示页面
│   └── base.html               # 基础模板
├── 📁 results/                 # 结果输出目录
├── 📁 logs/                    # 日志文件
├── app.py                      # Flask Web应用主程序
├── weather_service.py          # 天气和空气质量服务
├── main.py                     # 命令行主程序
├── requirements.txt            # 项目依赖
└── README.md                   # 项目说明文档
```

## 🚀 快速开始

### 环境要求

- **Python**: 3.8 或更高版本
- **操作系统**: Windows, macOS, Linux
- **内存**: 建议 4GB 以上
- **存储**: 至少 2GB 可用空间

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd stroke_prediction
```

2. **创建虚拟环境**（推荐）
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **启动Web应用**
```bash
python -m flask --app api.app run --host 127.0.0.1 --port 5008
```

5. **访问系统**
   
   打开浏览器访问：`http://localhost:5008`

## 💻 使用方法

### Web界面使用

1. **访问主页**：在浏览器中打开 `http://localhost:5008`
2. **填写健康信息**：在表单中输入个人健康数据
3. **查看预测结果**：系统将显示14种疾病的风险评估
4. **获取健康建议**：根据风险等级获得个性化建议

### API接口使用

#### 疾病风险预测
```bash
curl -X POST http://localhost:5008/api/predict \
  -H "Content-Type: application/json" \
  -H "X-Model-Variant: A" \
  -d '{
    "model_type": "xgb_multi",
    "records": [
      {
        "patient_id": "P_TEST_001",
        "exam_date": "2026-03-23",
        "age": 56,
        "gender": 1,
        "ethnicity": 1,
        "education_years": 12,
        "socioeconomic_score": 6,
        "atrial_fibrillation": 0,
        "previous_stroke": 0,
        "previous_tia": 0,
        "heart_disease": 0,
        "diabetes_years": 3,
        "hypertension_years": 5,
        "hypertension_controlled": 1,
        "chronic_kidney_disease": 0,
        "peripheral_artery_disease": 0,
        "family_stroke_history": 1,
        "family_heart_disease": 1,
        "genetic_risk_score": 5,
        "carotid_plaque": 0,
        "white_matter_lesions": 0,
        "systolic_bp": 132,
        "diastolic_bp": 82,
        "total_cholesterol": 192,
        "hdl_cholesterol": 48,
        "ldl_cholesterol": 118,
        "triglycerides": 150,
        "fasting_glucose": 107,
        "hba1c": 6.1,
        "bmi": 26.2,
        "waist_circumference": 92,
        "waist_hip_ratio": 0.93,
        "heart_rate": 74,
        "alcohol_units_week": 2,
        "physical_activity_days": 4,
        "mediterranean_diet_score": 8,
        "sleep_hours": 7,
        "crp": 1.7,
        "fibrinogen": 320,
        "left_ventricular_ejection": 60,
        "avg_systolic_bp_24h": 128,
        "bp_variability": 9,
        "heart_rate_variability": 28,
        "daily_steps": 7800,
        "sleep_efficiency": 83,
        "air_quality": 56,
        "season": 1
      }
    ]
  }'
```

#### 健康检查
```bash
curl http://localhost:5008/health
```

> 当前版本主要对外提供 `GET /health` 与 `POST /api/predict`。

### 命令行使用

#### 训练新模型
```bash
python scripts/train.py --data_path input/train.csv --output_dir models --variants A --model_types xgb_multi --horizons 7 30 --imbalance_strategy none
```

#### 生成测试数据
```bash
python stroke_data_generator.py --n_samples 1000 --output data/raw/test_data.csv
```

#### 批量预测
```bash
python -m flask --app api.app run --host 127.0.0.1 --port 5008
```

## 🔧 技术栈

### 后端技术
- **Web框架**: Flask 2.0+ - 轻量级Python Web框架
- **机器学习**: 
  - scikit-learn 1.0+ - 核心机器学习库
  - XGBoost 1.4+ - 梯度提升算法
  - LightGBM 3.2+ - 高效梯度提升框架
  - imbalanced-learn 0.8+ - 处理不平衡数据集
- **数据处理**:
  - NumPy 1.20+ - 数值计算
  - Pandas 1.3+ - 数据分析和处理
  - joblib 1.1+ - 模型序列化

### 前端技术
- **HTML5 + CSS3** - 现代Web标准
- **JavaScript (ES6+)** - 交互式用户界面
- **Bootstrap** - 响应式UI框架
- **Chart.js** - 数据可视化

### 可视化和分析
- **Matplotlib 3.4+** - 基础绘图库
- **Seaborn 0.11+** - 统计数据可视化
- **Plotly 5.3+** - 交互式图表
- **SHAP 0.40+** - 模型解释性分析

### 开发工具
- **Python 3.8+** - 编程语言
- **Jupyter Notebook** - 数据探索和原型开发
- **Git** - 版本控制
- **Docker** - 容器化部署（可选）

## 📊 输入特征说明

系统支持以下健康指标输入：

### 基本信息
| 特征名称 | 中文名称 | 数据类型 | 说明 |
|---------|---------|---------|------|
| age | 年龄 | 数值 | 患者年龄（岁） |
| gender | 性别 | 分类 | 0-女性，1-男性 |
| bmi | BMI指数 | 数值 | 身体质量指数 |
| ever_married | 婚姻状况 | 分类 | 0-未婚，1-已婚 |
| education_level | 教育水平 | 分类 | 教育程度等级 |

### 生活方式
| 特征名称 | 中文名称 | 数据类型 | 说明 |
|---------|---------|---------|------|
| smoking_status | 吸烟状况 | 分类 | 0-从不，1-曾经，2-目前 |
| alcohol_consumption | 饮酒情况 | 数值 | 每周饮酒量 |
| exercise_frequency | 运动频率 | 数值 | 每周运动次数 |
| sleep_hours | 睡眠时间 | 数值 | 每日睡眠小时数 |
| diet_quality | 饮食质量 | 数值 | 饮食质量评分 |

### 临床指标
| 特征名称 | 中文名称 | 数据类型 | 说明 |
|---------|---------|---------|------|
| systolic_bp | 收缩压 | 数值 | 收缩压（mmHg） |
| diastolic_bp | 舒张压 | 数值 | 舒张压（mmHg） |
| heart_rate | 心率 | 数值 | 心率（次/分钟） |
| avg_glucose_level | 平均血糖 | 数值 | 平均血糖水平 |
| cholesterol | 胆固醇 | 数值 | 总胆固醇水平 |
| triglycerides | 甘油三酯 | 数值 | 甘油三酯水平 |

### 医疗史
| 特征名称 | 中文名称 | 数据类型 | 说明 |
|---------|---------|---------|------|
| heart_disease | 心脏病史 | 分类 | 0-无，1-有 |
| family_history | 家族病史 | 分类 | 0-无，1-有 |
| medication_count | 用药数量 | 数值 | 当前用药种类数 |
| stress_level | 压力水平 | 数值 | 压力评分（1-10） |

### 环境因素
| 特征名称 | 中文名称 | 数据类型 | 说明 |
|---------|---------|---------|------|
| air_quality | 空气质量 | 数值 | AQI指数 |
| season | 季节 | 分类 | 0-春，1-夏，2-秋，3-冬 |

## 🎯 风险分层标准

系统根据预测概率将患者分为四个风险等级：

### 🟢 低风险 (< 30%)
- **风险描述**: 疾病发生概率较低
- **建议措施**: 
  - 保持健康的生活方式
  - 定期体检和健康监测
  - 适度运动和均衡饮食
- **随访频率**: 年度体检
- **监测方式**: 常规健康监测

### 🟡 中风险 (30% - 45%)
- **风险描述**: 存在一定的疾病风险
- **建议措施**:
  - 加强生活方式干预
  - 考虑药物预防治疗
  - 定期监测相关指标
- **随访频率**: 半年门诊复查
- **监测方式**: 加强健康监测

### 🟠 高风险 (45% - 60%)
- **风险描述**: 疾病发生风险较高
- **建议措施**:
  - 积极药物治疗
  - 严格控制危险因素
  - 专科医生定期评估
- **随访频率**: 季度门诊
- **监测方式**: 连续监测 + 定期检查

### 🔴 极高风险 (> 60%)
- **风险描述**: 疾病发生风险极高
- **建议措施**:
  - 立即医疗干预
  - 住院评估和治疗
  - 多学科团队会诊
- **随访频率**: 月度门诊
- **监测方式**: 密切监测 + 多学科会诊

## 📋 API文档
- 完整接口文档：`docs/api.md`
- 测试页请求与响应中英对照：`docs/api_test_page_bilingual_guide.md`
- 核心接口：
  - `GET /health`
  - `POST /api/predict`

## 🚀 部署指南

### Docker部署（推荐）

1. **构建Docker镜像**
```bash
docker build -t stroke-prediction .
```

2. **运行容器**
```bash
docker run -p 5008:5008 stroke-prediction
```

3. **使用Docker Compose**
```bash
docker-compose up -d
```

### 生产环境部署

1. **使用Gunicorn**
```bash
gunicorn -w 4 -b 0.0.0.0:5008 app:app
```

2. **配置Nginx反向代理**
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5008;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🔍 故障排除

### 常见问题

**Q: 模型加载失败**
```
A: 检查models/目录下是否存在所有模型文件，确保文件完整性
```

**Q: 天气API返回401错误**
```
A: 需要在weather_service.py中配置有效的OpenWeatherMap API密钥
```

**Q: 端口5008被占用**
```
A: 修改app.py中的端口号，或停止占用该端口的其他服务
```

**Q: 依赖安装失败**
```
A: 确保Python版本>=3.8，使用虚拟环境，更新pip到最新版本
```

## 🤝 贡献指南

我们欢迎社区贡献！请遵循以下步骤：

### 开发流程

1. **Fork项目**
```bash
git clone https://github.com/your-username/stroke-prediction.git
cd stroke-prediction
```

2. **创建开发分支**
```bash
git checkout -b feature/your-feature-name
```

3. **安装开发依赖**
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 如果存在
```

4. **运行测试**
```bash
python -m pytest tests/
```

5. **提交更改**
```bash
git add .
git commit -m "feat: add your feature description"
git push origin feature/your-feature-name
```

6. **创建Pull Request**

### 代码规范

- 遵循PEP 8 Python代码规范
- 添加适当的注释和文档字符串
- 为新功能编写单元测试
- 确保所有测试通过

### 贡献类型

- 🐛 Bug修复
- ✨ 新功能开发
- 📚 文档改进
- 🎨 代码优化
- 🧪 测试用例

## 📄 许可证

本项目采用 **MIT许可证** - 详情请参见 [LICENSE](LICENSE) 文件

## 📞 联系方式

- **项目维护者**: 智能医疗团队
- **技术支持**: support@medical-ai.com
- **问题反馈**: [GitHub Issues](https://github.com/your-repo/stroke-prediction/issues)
- **文档网站**: [项目文档](https://your-docs-site.com)

## 🙏 致谢

感谢以下开源项目和贡献者：

- [scikit-learn](https://scikit-learn.org/) - 机器学习核心库
- [Flask](https://flask.palletsprojects.com/) - Web框架
- [XGBoost](https://xgboost.readthedocs.io/) - 梯度提升算法
- [OpenWeatherMap](https://openweathermap.org/) - 天气数据API
- 所有为项目贡献代码和建议的开发者

## 📈 版本历史

### v1.0.0 (2024-01-15)
- ✨ 初始版本发布
- 🏥 支持14种疾病预测
- 🌤️ 集成天气和空气质量数据
- 🖥️ Web界面和API接口
- 📊 风险分层和个性化建议

---

**⭐ 如果这个项目对您有帮助，请给我们一个Star！**
