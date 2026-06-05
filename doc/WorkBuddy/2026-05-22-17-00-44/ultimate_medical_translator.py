#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
终极扩展医学翻译器
专门覆盖剩余 1,000 条未翻译术语
"""

class UltimateMedicalTranslator:
    def __init__(self):
        # PK 单位完整翻译映射
        self.pk_units = {
            # 浓度单位
            'NG/MC': '纳升/微升',
            'NG/ML': '纳克/毫升',
            'MCG/MC': '微克/微升',
            'MCG/ML': '微克/毫升',
            'MCGR/ML': '微克/毫升',
            'MG/MC': '毫克/微升',
            'MG/ML': '毫克/毫升',
            'MG/L': '毫克/升',
            'MOL/L': '摩尔/升',
            'MMOL/L': '毫摩尔/升',
            'NMOL/L': '纳摩尔/升',
            'PMOL/L': '皮摩尔/升',
            'FMOL/L': '飞摩尔/升',
            'UMOL/L': '微摩尔/升',
            'NMOL/MC': '纳摩尔/微升',
            'NMOL/ML': '纳摩尔/毫升',
            'PMOL/ML': '皮摩尔/毫升',
            'FMOL/ML': '飞摩尔/毫升',
            'AMOL/ML': '阿摩尔/毫升',
            
            # 时间单位
            'HR': '小时',
            'HRS': '小时',
            'MIN': '分钟',
            'MINS': '分钟',
            'SEC': '秒',
            'SECS': '秒',
            'DAYS': '天',
            'WEEKS': '周',
            'MONTHS': '月',
            'YEARS': '年',
            
            # 速度单位
            'NG/HR': '纳克/小时',
            'NG/ML/HR': '纳克/毫升/小时',
            'MCG/HR': '微克/小时',
            'MCG/ML/HR': '微克/毫升/小时',
            'MG/HR': '毫克/小时',
            'MG/ML/HR': '毫克/毫升/小时',
            'MMOL/HR': '毫摩尔/小时',
            'NMOL/HR': '纳摩尔/小时',
            
            # 清除率单位
            'ML/HR': '毫升/小时',
            'ML/MIN': '毫升/分钟',
            'L/HR': '升/小时',
            'L/MIN': '升/分钟',
            'L/MIN/KG': '升/分钟/千克',
            'L/HR': '升/小时',
            
            # 面积单位
            'HOUR': '小时',
            'HOURS': '小时',
            'DAY': '天',
            'DAYS': '天',
            
            # 百分比
            'PCT': '百分比',
            '%': '百分比',
            'PERCENT': '百分比',
            
            # 体积单位
            'MC': '微升',
            'ML': '毫升',
            'L': '升',
            
            # 质量单位
            'NG': '纳克',
            'MCG': '微克',
            'MG': '毫克',
            'G': '克',
            'KG': '千克',
            
            # 比率
            'RATIO': '比率',
            
            # 分子量大小的单位
            'MW': '分子量',
            'DALTON': '道尔顿',
            'KDA': '千道尔顿',
        }
        
        # 剂型完整翻译映射
        self.dosage_forms = {
            # 溶液剂型
            'FOR SOLUTION': '用于溶液',
            'FOR SOLUTION FOR INJECTION': '用于注射液',
            'FOR SOLUTION FOR INFUSION': '用于输注液',
            'SOLUTION': '溶液',
            'SOLUTION FOR INJECTION': '注射液',
            'SOLUTION FOR INFUSION': '输注液',
            'OPHTHALMIC SOLUTION': '眼用溶液',
            'NASAL SOLUTION': '鼻用溶液',
            'ORAL SOLUTION': '口服溶液',
            'PARENTERAL SOLUTION': '肠外溶液',
            'TOPICAL SOLUTION': '外用溶液',
            
            # 混悬剂型
            'FOR SUSPENSION': '用于混悬液',
            'FOR SUSPENSION, EXTENDED RELEASE': '用于缓释混悬液',
            'SUSPENSION': '混悬液',
            'SUSPENSION FOR INJECTION': '注射用混悬液',
            'ORAL SUSPENSION': '口服混悬液',
            'TOPICAL SUSPENSION': '外用混悬液',
            
            # 粉末剂型
            'FOR INJECTION': '用于注射',
            'FOR INFUSION': '用于输注',
            'POWDER FOR INJECTION': '注射用粉末',
            'POWDER FOR INFUSION': '输注用粉末',
            'POWDER FOR ORAL SOLUTION': '口服溶液用粉末',
            'POWDER FOR ORAL SUSPENSION': '口服混悬液用粉末',
            'LYOPHILIZED POWDER': '冻干粉末',
            
            # 缓释剂型
            'EXTENDED RELEASE': '缓释',
            'CONTROLLED RELEASE': '控释',
            'DELAYED RELEASE': '迟释',
            'SUSTAINED RELEASE': '长效释放',
            
            # 胶囊剂型
            'CAPSULE': '胶囊',
            'HARD CAPSULE': '硬胶囊',
            'SOFT CAPSULE': '软胶囊',
            'ENTERIC-COATED CAPSULE': '肠溶胶囊',
            'EXTENDED-RELEASE CAPSULE': '缓释胶囊',
            
            # 片剂剂型
            'TABLET': '片剂',
            'FILM-COATED TABLET': '薄膜衣片',
            'ENTERIC-COATED TABLET': '肠溶片',
            'EXTENDED-RELEASE TABLET': '缓释片',
            'CONTROLLED-RELEASE TABLET': '控释片',
            'ORODISPERSIBLE TABLET': '口腔崩解片',
            'CHWABLE TABLET': '咀嚼片',
            'EFFERVESCENT TABLET': '泡腾片',
            
            # 其他剂型
            'INJECTABLE': '注射剂',
            'INFUSION': '输注剂',
            'ORAL': '口服',
            'TOPICAL': '外用',
            'TRANSDERMAL': '透皮',
            'SUBCUTANEOUS': '皮下',
            'INTRAMUSCULAR': '肌内',
            'INTRAVENOUS': '静脉',
        }
        
        # ECG 结果完整翻译映射
        self.ecg_results = {
            # 心肌梗死相关
            'ACUTE EXTENSIVE ANTERIOR WALL MYOCARDIAL INFARCTION': '急性广泛前壁心肌梗死',
            'ACUTE MYOCARDIAL INFARCTION': '急性心肌梗死',
            'ANTERIOR WALL MYOCARDIAL INFARCTION': '前壁心肌梗死',
            'INFERIOR WALL MYOCARDIAL INFARCTION': '下壁心肌梗死',
            'LATERAL WALL MYOCARDIAL INFARCTION': '侧壁心肌梗死',
            'POSTERIOR WALL MYOCARDIAL INFARCTION': '后壁心肌梗死',
            'SEPTAL WALL MYOCARDIAL INFARCTION': '间隔壁心肌梗死',
            
            # ECG 异常
            'ALL PRECORDIAL ELECTRODES DISCONNECTED': '所有胸前导联电极断开',
            'ARTIFACT': '伪影',
            'ST SEGMENT ELEVATION': 'ST 段抬高',
            'ST SEGMENT DEPRESSION': 'ST 段压低',
            'T WAVE INVERSION': 'T 波倒置',
            'Q WAVE ABNORMALITY': 'Q 波异常',
            
            # 心律失常
            'ATRIAL FIBRILLATION': '心房颤动',
            'ATRIAL FLUTTER': '心房扑动',
            'VENTRICULAR TACHYCARDIA': '室性心动过速',
            'VENTRICULAR FIBRILLATION': '室性纤维颤动',
            'SUPRAVENTRICULAR TACHYCARDIA': '室上性心动过速',
            'ATRIOVENTRICULAR BLOCK': '房室传导阻滞',
            'FIRST DEGREE AV BLOCK': '一度房室传导阻滞',
            'SECOND DEGREE AV BLOCK': '二度房室传导阻滞',
            'THIRD DEGREE AV BLOCK': '三度房室传导阻滞',
            'LEFT BUNDLE BRANCH BLOCK': '左束支传导阻滞',
            'RIGHT BUNDLE BRANCH BLOCK': '右束支传导阻滞',
            
            # 正常 ECG
            'NORMAL ECG': '正常心电图',
            'NORMAL VARIANT': '正常变异',
            
            # ECG 质量
            'UNINTERPRETABLE': '无法解读',
            'POOR QUALITY': '质量差',
        }
        
        # 评估者完整翻译映射
        self.evaluators = {
            'ADJUDICATION COMMITTEE': '裁决委员会',
            'ADJUDICATOR': '裁决者',
            'AUDIOLOGIST': '听力学家',
            'CARDIOLOGIST': '心脏科医生',
            'CLINICAL INVESTIGATOR': '临床研究者',
            'DERMATOLOGIST': '皮肤科医生',
            'ENDOCRINOLOGIST': '内分泌科医生',
            'GA Strologist': '胃肠科医生',
            'HEMATOLOGIST': '血液科医生',
            'IMAGING READER': '影像判读者',
            'INVESTIGATOR': '研究者',
            'LABORATORY': '实验室',
            'NEUROLOGIST': '神经科医生',
            'NURSE': '护士',
            'ONCOLOGIST': '肿瘤科医生',
            'OPHTHALMOLOGIST': '眼科医生',
            'ORTHOPEDIC SURGEON': '骨科外科医生',
            'PATHOLOGIST': '病理学家',
            'PHARMACIST': '药剂师',
            'PHYSICIAN': '医生',
            'PRIMARY CARE PHYSICIAN': '初级保健医生',
            'PSYCHIATRIST': '精神科医生',
            'PULMONOLOGIST': '肺科医生',
            'RADIOLOGIST': '放射科医生',
            'RESEARCHER': '研究人员',
            'RHEUMATOLOGIST': '风湿科医生',
            'SUBJECT': '受试者',
            'SURGEON': '外科医生',
            'URROLOGIST': '泌尿科医生',
        }
        
        # 显微镜检查细节翻译
        self.microscopic_findings = {
            'BACTERIA': '细菌',
            'YEAST': '酵母菌',
            'FUNGI': '真菌',
            'PARASITES': '寄生虫',
            'RBC': '红细胞',
            'WBC': '白细胞',
            'EPITHELIAL CELLS': '上皮细胞',
            'CASTS': '管型',
            'CRYSTALS': '结晶',
            'MUCUS': '粘液',
            'NEGATIVE': '阴性',
            'POSITIVE': '阳性',
            'SPORADIC': '散在',
            'MODERATE': '中等',
            'ABUNDANT': '大量',
        }
        
        # Holter ECG 结果翻译
        self.holter_results = {
            'ATRIAL FIBRILLATION': '心房颤动',
            'ATRIAL FLUTTER': '心房扑动',
            'ATRIAL TACHYCARDIA': '房性心动过速',
            'VENTRICULAR TACHYCARDIA': '室性心动过速',
            'VENTRICULAR PREMATURE BEATS': '室性早搏',
            'ATRIAL PREMATURE BEATS': '房性早搏',
            'FIRST DEGREE AV BLOCK': '一度房室传导阻滞',
            'SECOND DEGREE AV BLOCK TYPE 1': '二度 I 型房室传导阻滞',
            'SECOND DEGREE AV BLOCK TYPE 2': '二度 II 型房室传导阻滞',
            'THIRD DEGREE AV BLOCK': '三度房室传导阻滞',
            'SINUS BRADYCARDIA': '窦性心动过缓',
            'SINUS TACHYCARDIA': '窦性心动过速',
            'NORMAL': '正常',
        }
        
        # 肿瘤学反应评估翻译
        self.oncology_response = {
            'COMPLETE RESPONSE': '完全缓解',
            'PARTIAL RESPONSE': '部分缓解',
            'STABLE DISEASE': '疾病稳定',
            'PROGRESSIVE DISEASE': '疾病进展',
            'NOT EVALUABLE': '无法评估',
            'PROLONGED STABLE DISEASE': '延长稳定疾病',
            'MINOR RESPONSE': '微小反应',
            'NO RESPONSE': '无反应',
        }
        
        # ECG 导联翻译
        self.ecg_leads = {
            'LEAD aVF': '导联 aVF',
            'LEAD aVL': '导联 aVL',
            'LEAD aVR': '导联 aVR',
            'LEAD I': '导联 I',
            'LEAD II': '导联 II',
            'LEAD III': '导联 III',
            'LEAD V1': '导联 V1',
            'LEAD V2': '导联 V2',
            'LEAD V3': '导联 V3',
            'LEAD V4': '导联 V4',
            'LEAD V5': '导联 V5',
            'LEAD V6': '导联 V6',
            'LEAD aV6': '导联 aV6',
            'LEAD aVF-VENTRAL': '导联 aVF-腹侧',
        }
        
        # ECG 分析方法翻译
        self.ecg_analysis_methods = {
            'GLOBAL MEDIAN BEAT METHOD': '全局中值拍方法',
            'MEAN SINGLE BEAT SINGLE LEAD METHOD': '平均单拍单导联方法',
            'MEAN SINGLE BEAT SUPERIMPOSED LEADS METHOD': '平均单拍叠加导联方法',
            'MULTIPLE BEAT ENSEMBLE AVERAGING METHOD': '多拍集平均方法',
        }
        
        # ECG 读图方法翻译
        self.ecg_read_methods = {
            'AUTOMATIC': '自动',
            'MANUAL': '手动',
            'SEMI-AUTOMATIC': '半自动',
        }
        
        # ECG 测试方法翻译
        self.ecg_test_methods = {
            '12 LEAD CONTINUOUS ECG': '12 导联连续心电图',
            '12 LEAD ECG EXTRACTED FROM 12 LEAD CONTINUOUS ECG RECORDING': '从 12 导联连续心电图记录中提取的 12 导联心电图',
            '15 LEAD INCLUDING V3R-V5R': '15 导联包括 V3R-V5R',
            '18 LEAD INCLUDING V3R-V5R AND V7-V9': '18 导联包括 V3R-V5R 和 V7-V9',
        }
        
        # 频率翻译
        self.frequency = {
            '2 TIMES PER CYCLE': '每周期 2 次',
            '3 TIMES PER CYCLE': '每周期 3 次',
            'EVERY 10 YEARS': '每 10 年',
            'EVERY 5 YEARS': '每 5 年',
            'EVERY 2 YEARS': '每 2 年',
            'EVERY YEAR': '每年',
            'TWICE A YEAR': '每年 2 次',
            'THREE TIMES A YEAR': '每年 3 次',
            'MONTHLY': '每月',
            'WEEKLY': '每周',
            'DAILY': '每日',
            'TWICE DAILY': '每日 2 次',
            'THREE TIMES DAILY': '每日 3 次',
            'HOURLY': '每小时',
        }
        
        # 就业状态翻译
        self.employment_status = {
            'EMPLOYED': '已就业',
            'FULL-TIME': '全职',
            'NOT EMPLOYED': '未就业',
            'PART-TIME': '兼职',
            'UNEMPLOYED': '失业',
            'RETIRED': '退休',
            'STUDENT': '学生',
            'HOMemaker': '家庭主妇',
        }
        
        # 环境设置翻译
        self.environmental_setting = {
            'CHILD CARE CENTER': '托儿中心',
            'CLINIC': '诊所',
            'FARM': '农场',
            'HOSPITAL': '医院',
            'HOME': '家庭',
            'NURSING HOME': '养老院',
            'RESIDENTIAL FACILITY': '居住设施',
            'SCHOOL': '学校',
            'WORKPLACE': '工作场所',
        }
        
        # 研究阶段翻译
        self.epoch = {
            'BASELINE': '基线',
            'BLINDED TREATMENT': '盲态治疗',
            'FOLLOW-UP': '随访',
            'SCREENING': '筛选',
            'TREATMENT': '治疗',
            'POST-TREATMENT': '治疗后',
            'RECOVERY': '恢复',
            'SALVAGE TREATMENT': '挽救治疗',
        }
        
        # 种族民族翻译
        self.ethnicity = {
            'ASHKENAZI JEW': '阿什肯纳兹犹太人',
            'CENTRAL AMERICAN': '中美洲人',
            'CUBAN AMERICAN': '古巴裔美国人',
            'HISPANIC': '西班牙裔',
            'LATINO': '拉丁裔',
            'MEXICAN AMERICAN': '墨西哥裔美国人',
            'PUERTO RICAN': '波多黎各人',
            'SOUTH AMERICAN': '南美洲人',
        }
        
        # 性别认同翻译
        self.gender_identity = {
            'AGENDER': '无性别',
            'BIGENDER': '双性别',
            'GENDER FLUID': '性别流动',
            'GENDERQUEER': '性别酷儿',
            'MALE': '男性',
            'FEMALE': '女性',
            'NON-BINARY': '非二元',
            'TRANS GENDER': '跨性别',
        }
        
        # 基因组样本类型翻译
        self.genetic_sample_type = {
            'GERMLINE DNA': '种系 DNA',
            'SOMATIC DNA': '体细胞 DNA',
            'BLOOD DNA': '血液 DNA',
            'TISSUE DNA': '组织 DNA',
            'TUMOR DNA': '肿瘤 DNA',
            'NORMAL TISSUE DNA': '正常组织 DNA',
        }
        
        # 基因组分析方法翻译
        self.genomic_analysis = {
            'ADME VARIANT PROFILE': 'ADME 变异谱',
            'COLORADO SCORING METHOD FOR EGFR GENE AMPLIFICATION 2006 ALGORITHM': 'EGFR 基因扩增 2006 算法科罗拉多评分方法',
            'COLORADO SCORING METHOD FOR EGFR GENE AMPLIFICATION 2009 ALGORITHM': 'EGFR 基因扩增 2009 算法科罗拉多评分方法',
            'DUAL ISH METHOD': '双 ISH 方法',
            'IHC METHOD': 'IHC 方法',
            'NGS METHOD': 'NGS 方法',
            'PCR METHOD': 'PCR 方法',
        }
        
        # FDA 技术规格翻译
        self.fda_spec = {
            'Clinical Endpoint BE Studies v1.0': '临床终点 BE 研究 v1.0',
            'HIV Technical Specifications Guidance v1.0': 'HIV 技术规格指南 v1.0',
            'Study Data Technical Conformance Guide v4.2.1': '研究数据技术一致性指南 v4.2.1',
        }

    def translate(self, term, codelist_name):
        """
        根据类别翻译术语
        
        Args:
            term: 需要翻译的术语
            codelist_name: 术语类别名称
            
        Returns:
            翻译结果或原术语
        """
        if not term:
            return term
        
        term_upper = term.upper() if term else ''
        
        # 根据类别选择翻译策略
        if codelist_name == 'PK Units of Measure':
            return self.pk_units.get(term, self.pk_units.get(term_upper, term))
            
        elif codelist_name == 'Dosage Form':
            return self.dosage_forms.get(term, self.dosage_forms.get(term_upper, term))
            
        elif codelist_name == 'ECG Result':
            return self.ecg_results.get(term, self.ecg_results.get(term_upper, term))
            
        elif codelist_name == 'Evaluator':
            return self.evaluators.get(term, self.evaluators.get(term_upper, term))
            
        elif codelist_name == 'Microscopic Findings Test Details':
            return self.microscopic_findings.get(term, self.microscopic_findings.get(term_upper, term))
            
        elif codelist_name == 'Holter ECG Results':
            return self.holter_results.get(term, self.holter_results.get(term_upper, term))
            
        elif codelist_name == 'Oncology Response Assessment Result':
            return self.oncology_response.get(term, self.oncology_response.get(term_upper, term))
            
        elif codelist_name == 'ECG Lead':
            return self.ecg_leads.get(term, self.ecg_leads.get(term_upper, term))
            
        elif codelist_name == 'ECG Analysis Method':
            return self.ecg_analysis_methods.get(term, self.ecg_analysis_methods.get(term_upper, term))
            
        elif codelist_name == 'ECG Read Method Response':
            return self.ecg_read_methods.get(term, self.ecg_read_methods.get(term_upper, term))
            
        elif codelist_name == 'ECG Test Method':
            return self.ecg_test_methods.get(term, self.ecg_test_methods.get(term_upper, term))
            
        elif codelist_name == 'Frequency':
            return self.frequency.get(term, self.frequency.get(term_upper, term))
            
        elif codelist_name == 'Employment Status':
            return self.employment_status.get(term, self.employment_status.get(term_upper, term))
            
        elif codelist_name == 'Environmental Setting':
            return self.environmental_setting.get(term, self.environmental_setting.get(term_upper, term))
            
        elif codelist_name == 'Epoch':
            return self.epoch.get(term, self.epoch.get(term_upper, term))
            
        elif codelist_name == 'Ethnicity As Collected':
            return self.ethnicity.get(term, self.ethnicity.get(term_upper, term))
            
        elif codelist_name == 'Gender Identity Response':
            return self.gender_identity.get(term, self.gender_identity.get(term_upper, term))
            
        elif codelist_name == 'Genetic Sample Type':
            return self.genetic_sample_type.get(term, self.genetic_sample_type.get(term_upper, term))
            
        elif codelist_name == 'Genomic Findings Analytical Method Calculation Formula':
            return self.genomic_analysis.get(term, self.genomic_analysis.get(term_upper, term))
            
        elif codelist_name == 'FDA Technical Specification Response':
            return self.fda_spec.get(term, self.fda_spec.get(term_upper, term))
        
        # 如果类别不在映射中，返回原术语
        return term
