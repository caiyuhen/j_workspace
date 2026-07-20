import os
import sys
from pymongo import MongoClient
import json
import logging
import uuid

# Ensure we can import from the local directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from vector_store import MilvusStore
import config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 1. MongoDB Setup
<<<<<<< HEAD
MONGO_URI = os.getenv("MONGO_URI", "mongodb://jdjd:JdJdllmix2308@mongodb:27017/")
=======
MONGO_URI = "mongodb://jdjd:JdJdllmix2308@localhost:27017/"
>>>>>>> origin/main
try:
    mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    mongo_client.server_info()
    db = mongo_client["medical_rules_db"]
    rules_collection = db["breast_cancer_rules"]
    logger.info("Connected to MongoDB.")
except Exception as e:
    logger.error(f"MongoDB connection failed: {e}")
    sys.exit(1)

# 2. Milvus Setup
milvus_store = MilvusStore()
milvus_store.connect()
milvus_store.init_collection()

# 3. LLM Parsing Setup
from pydantic import BaseModel, Field
from typing import List
import requests

class MedicalRule(BaseModel):
    rule_id: str = Field(description="Unique ID for the rule")
    priority: int = Field(description="1 for emergency/red alert, 2 for warning/yellow, 3 for normal/green")
    treatment_phase: str = Field(description="E.g., CHEMO, POST_OP, RADIO, MAINTENANCE")
    trigger_conditions: List[str] = Field(description="List of exact symptoms or triggers")
    management_action: str = Field(description="Strict action to take, e.g., 立即就医")
    reasoning: str = Field(description="Medical reasoning behind the action")

def parse_text_with_llm(text_chunk):
    # This calls our local LLM service to parse the markdown tables into JSON
    # For a robust implementation, we will use a regex/heuristic parser here tailored to the markdown tables
    # because local LLMs without strict JSON enforcing might fail to output valid JSON consistently.
    pass

def parse_markdown_to_rules(file_path):
    """
    Parse the specific breast cancer markdown file to extract rules.
    We target specific sections like '二、分期与治疗方式决定院外管理重点', '四、运动管理', '五、饮食管理', '七、不良反应/并发症管理', '八、复查/随访管理', '十、红色预警'
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    rules = []
    
    lines = content.split('\n')
    in_adverse_table = False
    in_red_alert_table = False
    in_diet_table = False
    in_exercise_table = False
    in_followup_table = False
    in_phase_table = False
    in_scope_table = False
    in_timeline_table = False
    
    for line in lines:
        # Detect sections
        if "一、适用范围与执行原则" in line:
            in_scope_table = True
            continue
        elif "二、分期与治疗方式决定院外管理重点" in line:
            in_scope_table = False
            in_phase_table = True
            continue
        elif "三、院外管理总时间表" in line:
            in_phase_table = False
            in_timeline_table = True
            continue
        elif "四、运动管理" in line:
            in_timeline_table = False
            continue
        elif "七、不良反应/并发症管理" in line:
            in_adverse_table = True
            continue
        elif "八、复查/随访管理" in line:
            in_adverse_table = False
            in_followup_table = True
            continue
        elif "九、药物依从性管理" in line:
            in_followup_table = False
            continue
        elif "十、红色预警" in line:
            in_red_alert_table = True
            continue
        elif "十一、院外管理表单模板" in line:
            in_red_alert_table = False
            continue
        elif "五、饮食管理" in line:
            in_diet_table = True
            continue
        elif "六、危险因素管理" in line:
            in_diet_table = False
            continue
        elif "4.1 术后患肢功能锻炼SOP" in line or "十五、“4.2 有氧和抗阻运动方案”运动类型拆分" in line:
            in_exercise_table = True
            continue
        elif "4.2 有氧和抗阻运动方案" in line or "参考文献" in line:
            in_exercise_table = False
            continue

        # 0.1 Parse "一、适用范围与执行原则" List
        if in_scope_table and line.startswith('-'):
            parts = line.replace('- ', '').split('：')
            if len(parts) == 2:
                target, action = parts[0].strip(), parts[1].strip()
                rule = {
                    "rule_id": f"rule_scope_{uuid.uuid4().hex[:8]}",
                    "priority": 3,
                    "metadata": {
                        "applicable_stages": ["0期", "I期", "II期", "III期", "IV期"],
                        "treatment_phase": "ALL",
                        "time_window_days": [0, 3650]
                    },
                    "trigger_conditions": [target, "原则", "执行", "目标", "责任"],
                    "management_action": action,
                    "reasoning": f"院外管理顶层设计原则：{target}。"
                }
                rules.append(rule)

        # 0.2 Parse "二、分期与治疗方式决定院外管理重点" Table
        if in_phase_table and line.startswith('|') and not "分层" in line and not "---" in line:
            parts = [p.strip() for p in line.split('|') if p.strip()]
            if len(parts) >= 4:
                layer, common_treatment, focus, intensity = parts[:4]
                rule = {
                    "rule_id": f"rule_phase_{uuid.uuid4().hex[:8]}",
                    "priority": 3,
                    "metadata": {
                        "applicable_stages": [layer.split('期')[0] + "期" if "期" in layer else layer],
                        "treatment_phase": "ALL",
                        "time_window_days": [0, 3650]
                    },
                    "trigger_conditions": [layer, "管理重点", "随访强度", "分期"],
                    "management_action": f"管理重点：{focus}。随访强度：{intensity}",
                    "reasoning": f"基于分期和常见治疗({common_treatment})的院外管理核心原则。"
                }
                rules.append(rule)

        # 0.3 Parse "三、院外管理总时间表" (Since the table is marked as [TABLE], we will add a fallback logic if needed, but assuming it refers to concrete lists below it like *1, *2, *3)
        if in_timeline_table and line.startswith('\\*') or line.startswith('*'):
            # E.g. *1“切口稳定患者”定义：无活动性出血；...
            clean_line = line.replace('\\*', '').replace('*', '').strip()
            parts = clean_line.split('：', 1)
            if len(parts) == 2:
                concept, definition = parts[0].strip(), parts[1].strip()
                rule = {
                    "rule_id": f"rule_timeline_{uuid.uuid4().hex[:8]}",
                    "priority": 3,
                    "metadata": {
                        "applicable_stages": ["0期", "I期", "II期", "III期", "IV期"],
                        "treatment_phase": "ALL",
                        "time_window_days": [0, 365]
                    },
                    "trigger_conditions": [concept, "定义", "判断标准", "评估"],
                    "management_action": definition,
                    "reasoning": f"院外管理时间表/评估的补充定义：{concept}。"
                }
                rules.append(rule)

        # 1. Parse "七、不良反应/并发症管理" Table
        if in_adverse_table and line.startswith('|') and not "问题" in line and not "---" in line:
            parts = [p.strip() for p in line.split('|') if p.strip()]
            if len(parts) >= 6:
                problem, timing, risk, symptoms, action, red_flag = parts[:6]
                if action and action != "-":
                    rule = {
                        "rule_id": f"rule_adverse_{uuid.uuid4().hex[:8]}",
                        "priority": 2,
                        "metadata": {
                            "applicable_stages": ["0期", "I期", "II期", "III期", "IV期"],
                            "treatment_phase": timing,
                            "time_window_days": [0, 365]
                        },
                        "trigger_conditions": [s.strip() for s in symptoms.replace('、', '，').split('，')],
                        "management_action": action,
                        "reasoning": f"应对不良反应/并发症：{problem}。风险因素：{risk}。"
                    }
                    rules.append(rule)
                
                if red_flag and red_flag != "-" and red_flag != "需立即就医/升级条件":
                    rule = {
                        "rule_id": f"rule_red_{uuid.uuid4().hex[:8]}",
                        "priority": 1,
                        "metadata": {
                            "applicable_stages": ["0期", "I期", "II期", "III期", "IV期"],
                            "treatment_phase": timing,
                            "time_window_days": [0, 365]
                        },
                        "trigger_conditions": [s.strip() for s in red_flag.replace('、', '，').split('，')],
                        "management_action": "立即就医",
                        "reasoning": f"严重不良反应/并发症红色预警：{problem}"
                    }
                    rules.append(rule)

        # 2. Parse "十、红色预警" Table
        if in_red_alert_table and line.startswith('|') and not "类别" in line and not "---" in line:
            parts = [p.strip() for p in line.split('|') if p.strip()]
            if len(parts) >= 3:
                category, symptoms, action = parts[:3]
                rule = {
                    "rule_id": f"rule_alert_{uuid.uuid4().hex[:8]}",
                    "priority": 1,
                    "metadata": {
                        "applicable_stages": ["0期", "I期", "II期", "III期", "IV期"],
                        "treatment_phase": category,
                        "time_window_days": [0, 365]
                    },
                    "trigger_conditions": [s.strip() for s in symptoms.replace('；', '，').split('，')],
                    "management_action": action,
                    "reasoning": f"{category} 阶段红色预警，属于急症或严重并发症信号。"
                }
                rules.append(rule)
                
        # 3. Parse "五、饮食管理" Table
        if in_diet_table and line.startswith('|') and not "阶段/治疗" in line and not "---" in line:
            parts = [p.strip() for p in line.split('|') if p.strip()]
            if len(parts) >= 4:
                phase, goal, how_to_eat, avoid = parts[:4]
                rule = {
                    "rule_id": f"rule_diet_{uuid.uuid4().hex[:8]}",
                    "priority": 3, # Green/Normal advice
                    "metadata": {
                        "applicable_stages": ["0期", "I期", "II期", "III期", "IV期"],
                        "treatment_phase": phase,
                        "time_window_days": [0, 365]
                    },
                    "trigger_conditions": [phase, "饮食", "吃什么", "忌口"],
                    "management_action": f"建议进食：{how_to_eat}；避免/限制：{avoid}",
                    "reasoning": f"饮食目标：{goal}"
                }
                rules.append(rule)

        # 4. Parse "四、运动管理" Tables (4.1 and 15)
        if in_exercise_table and line.startswith('|') and not "时间" in line and not "阶段/人群" in line and not "---" in line:
            parts = [p.strip() for p in line.split('|') if p.strip()]
            if len(parts) >= 3:
                # Handle 4.1 SOP table
                if len(parts) == 5:
                    timing, exercise, how_to, duration, avoid = parts
                    rule = {
                        "rule_id": f"rule_exercise_{uuid.uuid4().hex[:8]}",
                        "priority": 3,
                        "metadata": {
                            "applicable_stages": ["0期", "I期", "II期", "III期", "IV期"],
                            "treatment_phase": "术后康复",
                            "time_window_days": [0, 180]
                        },
                        "trigger_conditions": [timing, "运动", "锻炼"],
                        "management_action": f"适合运动：{exercise}。方法：{how_to}。时长频次：{duration}。禁忌与暂停：{avoid}",
                        "reasoning": "术后患肢功能锻炼SOP，预防淋巴水肿和恢复肩臂功能。"
                    }
                    rules.append(rule)
                # Handle 15 table
                elif len(parts) == 4:
                    phase, aerobic, resistance, other = parts
                    rule = {
                        "rule_id": f"rule_exercise_type_{uuid.uuid4().hex[:8]}",
                        "priority": 3,
                        "metadata": {
                            "applicable_stages": ["0期", "I期", "II期", "III期", "IV期"],
                            "treatment_phase": phase,
                            "time_window_days": [0, 365]
                        },
                        "trigger_conditions": [phase, "有氧", "抗阻", "运动"],
                        "management_action": f"有氧运动：{aerobic}。抗阻运动：{resistance}。其他任务（柔韧/呼吸等）：{other}",
                        "reasoning": f"{phase} 阶段的有氧与抗阻运动建议。"
                    }
                    rules.append(rule)
                    
        # 5. Parse "八、复查/随访管理" (Since the table is marked as [TABLE] in the file, we simulate extraction based on section 12 logic which is text based)
        # Note: In the provided text, 8.1 says [TABLE], but section 12 has concrete rules.
        if "十二、信息系统随访提醒规则建议" in line:
            in_followup_table = True
            continue
        if "十三、附：分期分治疗路径快速索引" in line:
            in_followup_table = False
            continue
            
        if in_followup_table and line.startswith('•'):
            parts = line.split('：')
            if len(parts) == 2:
                target = parts[0].replace('•', '').strip()
                action = parts[1].strip()
                rule = {
                    "rule_id": f"rule_followup_{uuid.uuid4().hex[:8]}",
                    "priority": 2, # Reminder/Warning
                    "metadata": {
                        "applicable_stages": ["0期", "I期", "II期", "III期", "IV期"],
                        "treatment_phase": target,
                        "time_window_days": [0, 365]
                    },
                    "trigger_conditions": [target, "复查", "随访", "提醒"],
                    "management_action": action,
                    "reasoning": f"{target} 的标准随访与复查提醒规则。"
                }
                rules.append(rule)
                
    return rules

# 4. Ingestion Process
def ingest():
    logger.info("Starting Full Ingestion Process...")
<<<<<<< HEAD

    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data/guanli/乳腺癌疾病管理路径.md")
=======
    
    file_path = "/mnt/disk3/home/pg/RAG_Project/data/guanli/乳腺癌.md"
>>>>>>> origin/main
    rules_data = parse_markdown_to_rules(file_path)
    logger.info(f"Parsed {len(rules_data)} rules from markdown document.")
    
    if not rules_data:
        logger.warning("No rules extracted. Exiting.")
        return
        
    # A. MongoDB Insertion
    rules_collection.delete_many({})
    result = rules_collection.insert_many(rules_data)
    logger.info(f"Inserted {len(result.inserted_ids)} rules into MongoDB.")
    
    # B. Milvus Insertion
    chunks = []
    for rule in rules_data:
        text_content = f"治疗阶段：{rule['metadata']['treatment_phase']}。触发条件：{', '.join(rule['trigger_conditions'])}。处理建议：{rule['management_action']}。理由：{rule['reasoning']}"
        
        chunk = {
            "text": text_content,
            "source": f"Breast_Cancer_Rule_{rule['rule_id']}",
            "stages": rule['metadata']['applicable_stages'],
            "syndromes": [],
            "principles": [],
            "western_medicines": [],
            "tcm_medicines": [],
            "diagnoses": [],
            "pathology_types": [],
            "diagnostic_features": [],
            "gene_mutations": [],
            "cytology_checks": [],
            "surgeries": [],
            "radiotherapies": [],
            "initial_treatments": [],
            "adjuvant_treatments": []
        }
        chunks.append(chunk)
    
    if chunks:
        milvus_store.insert_chunks(chunks)
        logger.info("Successfully inserted rule embeddings into Milvus.")

if __name__ == "__main__":
    ingest()
