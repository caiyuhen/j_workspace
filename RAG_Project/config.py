import os

# Base Path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Paths
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
DATA_DIR = os.path.join(BASE_DIR, "data")
# Milvus Configuration
<<<<<<< HEAD
MILVUS_HOST = os.getenv("MILVUS_HOST", "127.0.0.1")
MILVUS_PORT = os.getenv("MILVUS_PORT", "19530")
=======
MILVUS_HOST = "127.0.0.1"
MILVUS_PORT = "19530"
>>>>>>> origin/main
COLLECTION_NAME = "medical_rag" # Renamed for general medical use
VECTOR_DIM = 512  # Updated to 512 dim to match loaded model output

# ... (Taxonomies remain same)

# Model Name
EMBEDDING_MODEL_NAME = "BAAI/bge-small-zh-v1.5" # Public model (default)
# EMBEDDING_MODEL_NAME = "/mnt/disk3/home/pg/RAG_Project/output/trained_model_384"
# 1. 药物体系
WESTERN_MEDICINES = [
    # 肿瘤药
    "单抗", "替尼", "抑制剂", "贝伐珠单抗", "吉非替尼", "奥希替尼", 
    # 心血管药
    "阿司匹林", "他汀", "美托洛尔", "硝苯地平", "ACEI", "ARB",
    # 内分泌药
    "二甲双胍", "胰岛素", "格列", 
    # 抗生素
    "头孢", "阿莫西林", "左氧氟沙星"
] 
TCM_MEDICINES = ["复方", "汤剂", "注射液", "胶囊", "颗粒", "中成药"]

# 2. 诊断体系 (Expanded)
DIAGNOSES = [
    # 肿瘤
    "肺癌", "小细胞肺癌", "非小细胞肺癌", "胃癌", "肝癌", "乳腺癌", "结直肠癌",
    # 心脑血管
    "高血压", "冠心病", "心肌梗死", "脑卒中", "心力衰竭", "心律失常",
    # 内分泌/代谢
    "糖尿病", "甲亢", "甲减", "高脂血症",
    # 呼吸系统
    "肺炎", "慢阻肺", "哮喘", "支气管炎",
    # 消化系统
    "胃炎", "溃疡", "肝炎", "肝硬化", "胰腺炎",
    # 神经系统
    "阿尔茨海默病", "帕金森", "癫痫",
    # 肾脏
    "肾炎", "肾衰竭", "尿毒症"
]

STAGES = [
    # 肿瘤分期
    "I期", "II期", "III期", "IV期", "TNM", 
    # 通用分期
    "早期", "中期", "晚期", "急性期", "慢性期", "恢复期", "终末期"
]

PATHOLOGY_TYPES = [
    # 肿瘤病理
    "腺癌", "鳞癌", "大细胞癌", "小细胞癌", 
    # 通用病理
    "炎症", "感染", "纤维化", "硬化", "坏死", "增生"
]

DIAGNOSTIC_FEATURES = [
    "结节", "占位", "磨玻璃", "胸腔积液", "腹水", "肿块", 
    "疼痛", "发热", "咳嗽", "呼吸困难", "水肿", "黄疸"
]

# 3. 分子生物学 / 检查指标
GENE_MUTATIONS = ["EGFR", "ALK", "KRAS", "ROS1", "MET", "BRAF", "HER2", "RET", "TP53"]
CYTOLOGY_CHECKS = [
    "细胞学", "病理", "穿刺", "活检", 
    "血常规", "生化", "肿瘤标志物", "CT", "MRI", "超声", "心电图"
]

# 4. 治疗手段
SURGERIES = [
    "切除术", "根治术", "微创手术", "介入治疗", "移植术", 
    "肺叶切除", "支架置入", "搭桥手术"
]
RADIOTHERAPIES = ["放疗", "立体定向", "伽马刀", "粒子植入", "射频消融"]
INITIAL_TREATMENTS = ["一线治疗", "初始治疗", "首诊治疗", "急诊处理"]
ADJUVANT_TREATMENTS = ["辅助治疗", "新辅助治疗", "术后辅助", "康复治疗", "随访"]


# Old Taxonomies (Kept for compatibility or merged if needed)
OLD_STAGES = [
    "围手术期", "放疗阶段", "化疗阶段", "靶向治疗", "单纯中医治疗"
]
# Merge old stages into a general treatment phase list if needed, or keep separate. 
# For now, we'll map "treatment_stage" to a combination of these.

SYNDROMES = [
    "气虚证", "阴虚证", "血虚证", "阳虚证",  # 虚证类
    "痰湿证", "血瘀证", "热毒证", "气滞证"   # 实证类
]

TREATMENT_PRINCIPLES = [
    "防护治疗", "加载治疗", "巩固治疗", "维持治疗"
]

# Model Name
EMBEDDING_MODEL_NAME = "BAAI/bge-small-zh-v1.5" # Public model (default)
# EMBEDDING_MODEL_NAME = os.path.join(BASE_DIR, "output", "trained_model_384") # Private fine-tuned model (uncomment after training)
# Note: Run 'python train_embedding.py' to generate the local model first.
# If the local model is missing, the system should fallback or you should switch this back to the public model.
