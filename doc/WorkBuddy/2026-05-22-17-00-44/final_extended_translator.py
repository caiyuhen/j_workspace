#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终扩展翻译器 - 覆盖剩余的未翻译术语
"""

class FinalExtendedTranslator:
    def __init__(self):
        # ========== 生物标本事件 ==========
        self.biospecimen_terms = {
            'SHIPPING': '运输',
            'STAINING': '染色',
            'STORING': '储存',
            'THAWING': '解冻',
            'COLLECTION': '采集',
            'PROCESSING': '处理',
            'FREEZING': '冷冻',
            'CENTRIFUGATION': '离心',
            'ALIQUOTING': '分装',
            'LABELING': '标记',
            'PACKING': '包装',
            'SHIPMENT': '运输',
            'RECEIPT': '接收',
            'ACCEPTANCE': '验收',
            'REJECTION': '拒绝',
            'DISCARD': '丢弃',
            'DESTROY': '销毁',
        }
        
        # ========== 心脏程序指征 ==========
        self.cardiac_indication_terms = {
            'CANDIDATE TO RECEIVE CARDIAC TRANSPLANT': '心脏移植候选者',
            'CARDIAC ARREST': '心脏骤停',
            'CARDIAC ARREST/ARRHYTHMIA ETIOLOGY': '心脏骤停/心律失常病因',
            'CARDIOMYOPATHY': '心肌病',
            'CHRONIC TOTAL OCCLUSION': '慢性完全闭塞',
            'DONOR FOR CARDIAC TRANSPLANT': '心脏移植供体',
            'END OF EXPECTED BATTERY LIFE': '预期电池寿命结束',
            'FAULTY CONNECTOR/HEADER': '连接器/导线头故障',
            'GENERATOR IS BEING REPLACED AT TIME OF DEVICE EXPIRATION': '设备到期时更换脉冲发生器',
            'GENERATOR MALFUNCTION': '脉冲发生器故障',
            'IMMEDIATE PERCUTANEOUS CORONARY INTERVENTION': '紧急经皮冠状动脉介入治疗',
            'INFECTION': '感染',
            'LEAD EROSION': '导线侵蚀',
            'LEFT VENTRICULAR SYSTOLIC DYSFUNCTION': '左心室收缩功能障碍',
            'MANUFACTURER RECALL': '制造商召回',
            'MANUFACTURER RECOGNIZED A RECURRENT OR CONTINUING PROBLEM': '制造商确认的重复或持续问题',
            'MEDICAL CONDITION OR PROCEDURE AFTER IMPLANT': '植入后的医疗状况或程序',
            'MEDICAL OR SURGICAL PROCEDURE REQUIRING TEMPORARY DEACTIVATION': '需要临时关闭的医疗或外科手术',
            'PERCUTANEOUS CORONARY INTERVENTION': '经皮冠状动脉介入治疗',
            'POST-CARDIAC TRANSPLANT': '心脏移植后',
            'PRE-OPERATIVE EVALUATION FOR NON-CARDIAC SURGERY': '非心脏手术术前评估',
            'PRIMARY PREVENTION': '一级预防',
            'RESCUE PERCUTANEOUS CORONARY INTERVENTION': '挽救性经皮冠状动脉介入治疗',
            'SECONDARY PREVENTION': '二级预防',
            'SPONTANEOUS SUSTAINED VENTRICULAR TACHYCARDIA': '自发性持续性室性心动过速',
            'STAGED PERCUTANEOUS CORONARY INTERVENTION': '分阶段经皮冠状动脉介入治疗',
            'SYNCOPE WITH HIGH RISK CHARACTERISTICS': '具有高风险特征的心动过速',
            'SYNCOPE WITH INDUCIBLE VENTRICULAR TACHYCARDIA': '可诱发性室性心动过速伴心动过速',
            'UPGRADE TO A DEVICE WITH ADDITIONAL THERAPIES': '升级至具有额外治疗功能的设备',
            'VENTRICULAR FIBRILLATION': '室性颤动',
        }
        
        # ========== 心动过缓设备故障表现 ==========
        self.cardiac_failure_terms = {
            'ATRIAL PACING MALFUNCTION': '心房起搏故障',
            'DEFIBRILLATION MALFUNCTION': '除颤故障',
            'LEFT VENTRICULAR PACING MALFUNCTION': '左心室起搏故障',
            'RIGHT VENTRICULAR PACING MALFUNCTION': '右心室起搏故障',
            'CARDIOVERSION MALFUNCTION': '复律故障',
            'SENsing MALFUNCTION': '感知故障',
            'OUTPUT MALFUNCTION': '输出故障',
            'BATTERY MALFUNCTION': '电池故障',
            'WIRE MALFUNCTION': '导线故障',
        }
        
        # ========== 心血管检查项目 ==========
        self.cardiovascular_terms = {
            'ANGIOGRAPHY': '血管造影',
            'AUGMENTATION OF ORAL DIURETIC THERAPY': '口服利尿剂治疗增强',
            'AUTOPSY': '尸检',
            'CLINICALLY SIGNIFICANT OR RAPID Worsening OF HEART FAILURE': '临床显著或快速恶化心力衰竭',
            'CORONARY LESION ON ANGIOGRAPHY': '血管造影冠状动脉病变',
            'CORONARY REVASCULARIZATION': '冠状动脉血运重建',
            'DECREASED EXERCISE TOLERANCE': '运动耐量降低',
            'DYSPNEA': '呼吸困难',
            'ANGINA PECTORIS': '心绞痛',
            'MYOCARDIAL INFARCTION': '心肌梗死',
            'HEART FAILURE': '心力衰竭',
            'ARRHYTHMIA': '心律失常',
            'CARDIAC ARREST': '心脏骤停',
        }
        
        # ========== ECG 结果 ==========
        self.ecg_terms = {
            'NORMAL': '正常',
            'ABNORMAL': '异常',
            'ST SEGMENT ELEVATION': 'ST 段抬高',
            'ST SEGMENT DEPRESSION': 'ST 段压低',
            'T WAVE INVERSION': 'T 波倒置',
            'Q WAVE': 'Q 波',
            'LEFT BUNDLE BRANCH BLOCK': '左束支传导阻滞',
            'RIGHT BUNDLE BRANCH BLOCK': '右束支传导阻滞',
            'ATRIAL FIBRILLATION': '心房颤动',
            'ATRIAL FLUTTER': '心房扑动',
            'VENTRICULAR TACHYCARDIA': '室性心动过速',
            'VENTRICULAR FIBRILLATION': '室性颤动',
            'SUPRAVENTRICULAR TACHYCARDIA': '室上性心动过速',
            'FIRST DEGREE AV BLOCK': '一度房室传导阻滞',
            'SECOND DEGREE AV BLOCK': '二度房室传导阻滞',
            'THIRD DEGREE AV BLOCK': '三度房室传导阻滞',
        }
        
        # ========== Holter ECG 结果 ==========
        self.holter_terms = {
            'NORMAL': '正常',
            'ABNORMAL': '异常',
            'ATRIAL PREMATURE BEATS': '房性早搏',
            'VENTRICULAR PREMATURE BEATS': '室性早搏',
            'ATRIAL TACHYCARDIA': '房性心动过速',
            'VENTRICULAR TACHYCARDIA': '室性心动过速',
            'ATRIAL FIBRILLATION': '心房颤动',
            'ATRIAL FLUTTER': '心房扑动',
            'FIRST DEGREE AV BLOCK': '一度房室传导阻滞',
            'SECOND DEGREE AV BLOCK TYPE 1': '二度 I 型房室传导阻滞',
            'SECOND DEGREE AV BLOCK TYPE 2': '二度 II 型房室传导阻滞',
            'THIRD DEGREE AV BLOCK': '三度房室传导阻滞',
            'SINUS BRADYCARDIA': '窦性心动过缓',
            'SINUS TACHYCARDIA': '窦性心动过速',
            'PAUSE': '停搏',
        }
        
        # ========== 剂型 ==========
        self.dosage_terms = {
            'TABLET': '片剂',
            'CAPSULE': '胶囊',
            'INJECTION': '注射液',
            'SOLUTION': '溶液',
            'SUSPENSION': '混悬剂',
            'SYRUP': '糖浆',
            'CREAM': '乳膏',
            'OINTMENT': '软膏',
            'GEL': '凝胶',
            'LOTION': '洗剂',
            'DROP': '滴剂',
            'INHALER': '吸入器',
            'SUPPOSITORY': '栓剂',
            'PATCH': '贴剂',
            'POWDER': '散剂',
            'GRANULE': '颗粒剂',
            'FILM': '膜剂',
            'SPRAY': '喷雾剂',
            'FOAM': '泡沫剂',
            'AEROSOL': '气雾剂',
        }
        
        # ========== 单位 ==========
        self.unit_terms = {
            'MG': '毫克',
            'G': '克',
            'KG': '千克',
            'UG': '微克',
            'NG': '纳克',
            'L': '升',
            'ML': '毫升',
            'UL': '微升',
            'MMOL': '毫摩尔',
            'UMOL': '微摩尔',
            'NMOL': '纳摩尔',
            'MOL': '摩尔',
            'PERCENT': '百分比',
            'RATIO': '比率',
            'COUNT': '计数',
            'SECOND': '秒',
            'MINUTE': '分钟',
            'HOUR': '小时',
            'DAY': '天',
            'WEEK': '周',
            'MONTH': '月',
            'YEAR': '年',
        }
        
        # ========== 肿瘤学反应评估 ==========
        self.oncology_terms = {
            'COMPLETE RESPONSE': '完全缓解',
            'PARTIAL RESPONSE': '部分缓解',
            'STABLE DISEASE': '疾病稳定',
            'PROGRESSIVE DISEASE': '疾病进展',
            'NOT EVALUABLE': '无法评估',
            'BEST OVERALL RESPONSE': '最佳总体反应',
            'DISEASE CONTROL': '疾病控制',
            'OBJECTIVE RESPONSE': '客观缓解',
            'CONFIRMED RESPONSE': '确认缓解',
            'UNCONFIRMED RESPONSE': '未确认缓解',
        }
        
        # ========== 通用医学词汇 ==========
        self.common_terms = {
            'PERFORMED': '已执行',
            'SCHEDULED': '计划中',
            'COMPLETED': '已完成',
            'NOT PERFORMED': '未执行',
            'NOT PERFORMED/NOT DONE': '未执行',
            'NOT DONE': '未完成',
            'CANCELLED': '已取消',
            'SUSPENDED': '已暂停',
            'TERMINATED': '已终止',
            'DISCONTINUED': '已停止',
            'WITHDRAWN': '已撤回',
            'ONGOING': '进行中',
            'PENDING': '待处理',
            'REQUIRED': '需要',
            'OPTIONAL': '可选',
            'MANDATORY': '强制',
            'ROUTINE': '常规',
            'EMERGENCY': '紧急',
            'URGENT': '紧急',
            'ROUTINE FOLLOW-UP': '常规随访',
            'SPECIAL FOLLOW-UP': '特殊随访',
        }
    
    def translate(self, term, codelist_name=None):
        """翻译术语"""
        if not term:
            return None
        
        term_upper = term.upper().strip()
        
        # 根据 codelist_name 选择翻译策略
        if codelist_name:
            if 'Biospecimen' in codelist_name:
                if term_upper in self.biospecimen_terms:
                    return self.biospecimen_terms[term_upper]
            elif 'Cardiac Procedure Indication' in codelist_name:
                if term_upper in self.cardiac_indication_terms:
                    return self.cardiac_indication_terms[term_upper]
            elif 'Cardiac Rhythm Device Failure' in codelist_name:
                if term_upper in self.cardiac_failure_terms:
                    return self.cardiac_failure_terms[term_upper]
            elif 'Cardiovascular Findings' in codelist_name:
                if term_upper in self.cardiovascular_terms:
                    return self.cardiovascular_terms[term_upper]
            elif 'ECG Result' in codelist_name:
                if term_upper in self.ecg_terms:
                    return self.ecg_terms[term_upper]
            elif 'Holter ECG' in codelist_name:
                if term_upper in self.holter_terms:
                    return self.holter_terms[term_upper]
            elif 'Dosage Form' in codelist_name:
                if term_upper in self.dosage_terms:
                    return self.dosage_terms[term_upper]
            elif 'Unit' in codelist_name and 'PK' not in codelist_name:
                if term_upper in self.unit_terms:
                    return self.unit_terms[term_upper]
            elif 'Oncology Response' in codelist_name:
                if term_upper in self.oncology_terms:
                    return self.oncology_terms[term_upper]
        
        # 通用查找策略
        if term_upper in self.biospecimen_terms:
            return self.biospecimen_terms[term_upper]
        if term_upper in self.cardiac_indication_terms:
            return self.cardiac_indication_terms[term_upper]
        if term_upper in self.cardiac_failure_terms:
            return self.cardiac_failure_terms[term_upper]
        if term_upper in self.cardiovascular_terms:
            return self.cardiovascular_terms[term_upper]
        if term_upper in self.ecg_terms:
            return self.ecg_terms[term_upper]
        if term_upper in self.holter_terms:
            return self.holter_terms[term_upper]
        if term_upper in self.dosage_terms:
            return self.dosage_terms[term_upper]
        if term_upper in self.unit_terms:
            return self.unit_terms[term_upper]
        if term_upper in self.oncology_terms:
            return self.oncology_terms[term_upper]
        if term_upper in self.common_terms:
            return self.common_terms[term_upper]
        
        # 未找到翻译时返回原术语
        return term

# 测试
if __name__ == '__main__':
    translator = FinalExtendedTranslator()
    
    test_cases = [
        ('SHIPPING', 'Biospecimen Events'),
        ('PERFORMED', 'BRIDG Activity Mood'),
        ('CARDIOMYOPATHY', 'Cardiac Procedure Indication'),
        ('ANGIOGRAPHY', 'Cardiovascular Findings'),
        ('ST SEGMENT ELEVATION', 'ECG Result'),
        ('TABLET', 'Dosage Form'),
        ('MG', 'Unit'),
        ('COMPLETE RESPONSE', 'Oncology Response'),
    ]
    
    for term, category in test_cases:
        result = translator.translate(term, category)
        print(f"{term:40} [{category:30}] -> {result}")
