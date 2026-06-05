#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
乳腺癌患者院外日常管理方案 - 管理规则提取脚本
"""
import json
import re
from typing import List, Dict, Any

# 读取完整文档
with open(r'C:\Users\Administrator\WorkBuddy\2026-05-12-task-2\breast_cancer_plan.txt', 'r', encoding='utf-8') as f:
    text = f.read()

print("文档总长度:", len(text))
print("\n" + "="*80 + "\n")

# 定义管理规则的 JSON Schema
schema = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "rule_id": {"type": "string", "description": "规则唯一标识"},
            "rule_name": {"type": "string", "description": "规则名称"},
            "trigger_condition": {"type": "string", "description": "触发条件"},
            "time_range": {"type": "string", "description": "时间范围"},
            "management_actions": {"type": "array", "items": {"type": "string"}, "description": "管理动作列表"},
            "monitoring_indicators": {"type": "array", "items": {"type": "string"}, "description": "监控指标列表"},
            "applicable_patients": {"type": "string", "description": "适用患者群体"},
            "follow_up_content": {"type": "string", "description": "随访复查内容"},
            "reminders_and_actions": {"type": "string", "description": "提醒与处置措施"}
        },
        "required": ["rule_id", "rule_name", "trigger_condition", "time_range", "management_actions", "monitoring_indicators"]
    }
}

# 分析文档并提取管理规则
rules = []

# 1. 分期管理规则
stage_rules = [
    {
        "rule_id": "STAGE_0",
        "rule_name": "0 期 DCIS 患者管理",
        "trigger_condition": "诊断为 0 期 DCIS/TisN0M0",
        "time_range": "终身随访",
        "management_actions": [
            "伤口管理",
            "保乳术后放疗皮肤反应监测",
            "患肢功能锻炼",
            "HR 阳性患者内分泌治疗管理",
            "对侧乳腺风险监测"
        ],
        "monitoring_indicators": [
            "伤口愈合情况",
            "皮肤反应程度",
            "肩关节活动度",
            "内分泌治疗不良反应",
            "乳房 X 线检查结果"
        ],
        "applicable_patients": "0 期导管原位癌患者",
        "follow_up_content": "每 6-12 个月病情随访和体格检查，持续 5 年后每年 1 次；每 12 个月乳房 X 线检查",
        "reminders_and_actions": "保乳手术放疗后每 6-12 个月乳房 X 线及乳腺超声"
    },
    {
        "rule_id": "STAGE_I",
        "rule_name": "I 期早期浸润癌患者管理",
        "trigger_condition": "诊断为 I 期早期浸润癌",
        "time_range": "终身随访",
        "management_actions": [
            "术后康复管理",
            "患肢功能评估",
            "淋巴水肿早期识别",
            "内分泌治疗依从性管理",
            "化疗/抗 HER2 治疗毒性监测"
        ],
        "monitoring_indicators": [
            "患肢肿胀程度",
            "肩关节活动度",
            "骨髓抑制指标",
            "肝肾功能",
            "心功能 (LVEF)"
        ],
        "applicable_patients": "I 期早期浸润癌患者",
        "follow_up_content": "术后 2 年内每 3 个月 1 次，术后 3-5 年每 6 个月 1 次，术后 5 年以上每年 1 次",
        "reminders_and_actions": "异常情况随时就诊"
    },
    {
        "rule_id": "STAGE_II",
        "rule_name": "II 期早期浸润癌患者管理",
        "trigger_condition": "诊断为 II 期早期浸润癌",
        "time_range": "终身随访",
        "management_actions": [
            "化疗毒性监测",
            "抗 HER2 治疗心功能监测",
            "放疗后皮肤/肺/心脏风险评估",
            "淋巴水肿长期管理",
            "骨健康管理",
            "体重和运动管理"
        ],
        "monitoring_indicators": [
            "血常规 (骨髓抑制)",
            "发热性中性粒细胞减少",
            "贫血指标",
            "血小板计数",
            "肝肾功能",
            "心功能 (LVEF)",
            "淋巴水肿周径"
        ],
        "applicable_patients": "II 期早期浸润癌患者",
        "follow_up_content": "同早期乳腺癌总原则，治疗期按每周期/方案要求查血常规、生化、心功能",
        "reminders_and_actions": "化疗期重点监测，抗 HER2 治疗重点监测心功能"
    },
    {
        "rule_id": "STAGE_III",
        "rule_name": "III 期局部晚期乳腺癌患者管理",
        "trigger_condition": "诊断为 III 期局部晚期或炎性乳腺癌",
        "time_range": "强化随访期 + 终身随访",
        "management_actions": [
            "MDT 多学科管理",
            "新辅助治疗监测",
            "治疗毒性强化管理",
            "复发转移症状筛查",
            "营养与体能支持",
            "心理支持",
            "淋巴水肿管理"
        ],
        "monitoring_indicators": [
            "治疗反应评估",
            "复发转移信号",
            "营养指标",
            "体能状态",
            "放射性肺炎/心包炎"
        ],
        "applicable_patients": "III 期局部晚期/炎性乳腺癌患者",
        "follow_up_content": "治疗期按方案高频评估；术后 2 年内每 3 个月、3-5 年每 6 个月、5 年后每年",
        "reminders_and_actions": "新辅助治疗期间按疗程进行临床和影像评估"
    }
]

# 2. 时间节点管理规则
timeline_rules = [
    {
        "rule_id": "TL_PRE_DISCHARGE",
        "rule_name": "出院前管理",
        "trigger_condition": "出院/开始院外治疗前",
        "time_range": "出院时",
        "management_actions": [
            "确认伤口敷料固定",
            "确认引流管通畅",
            "镇痛方案评估",
            "患侧肢体保护指导",
            "活动禁忌宣教",
            "患者教育",
            "建立健康档案",
            "基础评估"
        ],
        "monitoring_indicators": [
            "伤口状况",
            "引流管通畅性",
            "疼痛评分",
            "体温",
            "伤口出血/感染/分泌物"
        ],
        "applicable_patients": "所有术后患者，重点关注带引流管、接受腋窝手术或乳房重建的患者",
        "follow_up_content": "建档：出院诊断、肿瘤分期、手术方式、腋窝淋巴结处理方式、保乳/乳房重建情况、后续治疗计划、药物过敏史、基础疾病及出院带药清单",
        "reminders_and_actions": "居家监测体温；出现伤口出血、感染、脓性分泌物、高热等异常，及时就诊"
    },
    {
        "rule_id": "TL_POSTOP_1_2D",
        "rule_name": "术后 1-2 天管理",
        "trigger_condition": "手术后 1-2 天",
        "time_range": "术后 1-2 天",
        "management_actions": [
            "术后功能锻炼：握拳、伸指、屈腕",
            "疼痛观察",
            "患肢肿胀观察",
            "手指活动评估",
            "伤口观察",
            "引流管观察"
        ],
        "monitoring_indicators": [
            "疼痛程度",
            "患肢肿胀程度",
            "手指活动度",
            "伤口情况",
            "引流量和性质"
        ],
        "applicable_patients": "所有术后患者",
        "follow_up_content": "观察疼痛、患肢肿胀、手指活动情况；按医嘱观察伤口和引流",
        "reminders_and_actions": "禁止肩关节大幅外展和上举"
    },
    {
        "rule_id": "TL_POSTOP_3_4D",
        "rule_name": "术后 3-4 天管理",
        "trigger_condition": "手术后 3-4 天且切口稳定",
        "time_range": "术后 3-4 天",
        "management_actions": [
            "握拳、伸指、屈腕锻炼",
            "增加前臂伸屈运动",
            "引流量观察",
            "皮下积液/血肿评估",
            "患肢肿胀评估"
        ],
        "monitoring_indicators": [
            "引流量变化",
            "皮下积液表现",
            "血肿表现",
            "患肢肿胀或沉重感"
        ],
        "applicable_patients": "切口稳定患者",
        "follow_up_content": "观察引流量变化、皮下积液/血肿表现、患肢肿胀或沉重感",
        "reminders_and_actions": "皮下积液或超过术后 1 周引流管未拔除时，应减少功能锻炼次数及肩关节活动幅度"
    },
    {
        "rule_id": "TL_POSTOP_5_7D",
        "rule_name": "术后 5-7 天管理",
        "trigger_condition": "手术后 5-7 天且切口稳定",
        "time_range": "术后 5-7 天",
        "management_actions": [
            "患侧手摸对侧肩",
            "患侧手摸同侧耳",
            "肩关节活动度评估",
            "腋窝牵拉感评估"
        ],
        "monitoring_indicators": [
            "肩关节活动度",
            "腋窝牵拉感",
            "腋窝紧绷感",
            "腋窝疼痛",
            "活动受限程度"
        ],
        "applicable_patients": "切口稳定患者",
        "follow_up_content": "肩关节活动度评估、腋窝牵拉感评估 (判断腋网综合征)",
        "reminders_and_actions": "术后 7 天内限制肩关节外展"
    },
    {
        "rule_id": "TL_POSTOP_8_10D",
        "rule_name": "术后 8-10 天管理",
        "trigger_condition": "手术后 8-10 天且切口愈合较好",
        "time_range": "术后 8-10 天",
        "management_actions": [
            "肩关节抬高至 90 度",
            "肩关节伸直至 90 度",
            "肩关节屈曲至 90 度",
            "伤口评估和换药",
            "引流管观察",
            "血肿/浆液肿评估",
            "双侧上肢周径测量"
        ],
        "monitoring_indicators": [
            "伤口愈合情况",
            "引流管状态",
            "皮下积液",
            "血肿",
            "双侧上肢周径差值"
        ],
        "applicable_patients": "切口愈合较好患者",
        "follow_up_content": "伤口评估、引流管观察、血肿评估、双侧上肢周径测量",
        "reminders_and_actions": "禁止突然负重；术后 2-4 周患侧一般不超过 500g 负重"
    },
    {
        "rule_id": "TL_POSTOP_1_2W",
        "rule_name": "术后 1-2 周门诊复诊",
        "trigger_condition": "手术后 1-2 周",
        "time_range": "术后 1-2 周",
        "management_actions": [
            "门诊复诊",
            "病理报告解读",
            "伤口评估/换药",
            "术区超声检查",
            "生成个体化随访日历"
        ],
        "monitoring_indicators": [
            "病理分期",
            "伤口愈合",
            "积液/血肿",
            "后续治疗方案"
        ],
        "applicable_patients": "所有术后患者",
        "follow_up_content": "明确病理、分期、后续放疗/化疗/靶向/内分泌计划",
        "reminders_and_actions": "生成个体化随访日历：治疗周期、复查节点、用药提醒、联系人"
    },
    {
        "rule_id": "TL_REHAB_1M",
        "rule_name": "切口愈合后 1 个月内康复",
        "trigger_condition": "切口愈合后",
        "time_range": "切口愈合后 1 个月",
        "management_actions": [
            "爬墙训练",
            "器械辅助训练",
            "逐步恢复肩关节活动",
            "肩关节活动度评估",
            "疼痛评估",
            "患肢肿胀评估",
            "双侧上肢周径测量"
        ],
        "monitoring_indicators": [
            "肩关节活动度",
            "疼痛程度",
            "患肢肿胀",
            "功能达标情况",
            "双侧上肢周径差值"
        ],
        "applicable_patients": "乳腺癌术后需进行患肢功能康复者",
        "follow_up_content": "评估肩关节活动度、疼痛、患肢肿胀、功能达标情况",
        "reminders_and_actions": "目标：切口愈合后 1 个月患肢伸直抬高绕头摸到对侧耳；一般 1-2 个月内恢复至术前或对侧水平"
    },
    {
        "rule_id": "TL_REHAB_1_2M",
        "rule_name": "切口愈合后 1-2 个月康复",
        "trigger_condition": "切口愈合后 1-2 个月",
        "time_range": "切口愈合后 1-2 个月及以后",
        "management_actions": [
            "每日功能锻炼",
            "有氧运动",
            "抗阻训练",
            "淋巴水肿预防教育",
            "患肢症状问询",
            "关节活动度评估",
            "肢体感觉评估",
            "双侧上肢周径测量"
        ],
        "monitoring_indicators": [
            "患肢肿胀",
            "患肢沉重感",
            "患肢紧绷感",
            "患肢疼痛",
            "活动受限",
            "关节活动度",
            "肢体感觉",
            "双侧上肢周径差值"
        ],
        "applicable_patients": "术后康复期患者，尤其腋窝手术/放疗后高风险患者",
        "follow_up_content": "问询患肢症状、查体评估关节活动度、可行双侧上肢周径对照测量",
        "reminders_and_actions": "患侧较健侧周径<3cm 为轻度水肿，3-5cm 为中度，>5cm 为重度"
    }
]

# 合并所有规则
rules = stage_rules + timeline_rules

# 输出 JSON
output = {
    "schema": schema,
    "metadata": {
        "document_name": "乳腺癌患者院外日常管理方案_分期分治疗执行版",
        "total_rules": len(rules),
        "stage_rules": len(stage_rules),
        "timeline_rules": len(timeline_rules),
        "extraction_date": "2026-05-12",
        "description": "乳腺癌患者院外管理规则 JSON 化，包含分期管理规则和时间节点管理规则"
    },
    "rules": rules
}

# 保存 JSON
with open(r'C:\Users\Administrator\WorkBuddy\2026-05-12-task-2\breast_cancer_management_rules.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"成功生成 {len(rules)} 条管理规则")
print("JSON 文件已保存至：breast_cancer_management_rules.json")
print("\n规则分类:")
print(f"  - 分期管理规则：{len(stage_rules)} 条")
print(f"  - 时间节点管理规则：{len(timeline_rules)} 条")
