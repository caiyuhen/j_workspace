import os
import time
import csv
import io
import random

output_dir = r"d:\workspace\dataPlaform\omop-platform\inputdata"
os.makedirs(output_dir, exist_ok=True)
output_file = os.path.join(output_dir, "comprehensive_emr_3m.csv")

TOTAL_RECORDS = 10_000
BATCH_SIZE = 10_000

# ----------------- 数据池 (预计算取模数组，极致提升性能) -----------------
# 1. 患者基本信息
names_prefix = ["张", "李", "王", "赵", "陈", "刘", "孙", "周", "吴", "郑"]
names_suffix = ["伟", "芳", "娜", "敏", "静", "强", "磊", "军", "洋", "勇"]
genders = ["男", "女"]
allergies = ["无", "青霉素过敏", "头孢过敏", "磺胺类过敏", "海鲜过敏", "花粉过敏"]

# 2. 既往健康史
past_history = ["无特殊", "高血压5年", "2型糖尿病", "冠心病病史", "阑尾炎术后", "慢性胃炎"]
family_history = ["无特殊", "父亲有高血压", "母亲有糖尿病", "家族有心脏病史", "无家族遗传病史"]
lifestyle = ["不吸烟不饮酒", "吸烟10年", "偶尔饮酒", "熬夜", "缺乏运动", "饮食规律"]
immunization = ["按规程接种", "新冠疫苗3针", "乙肝疫苗接种", "流感疫苗接种", "未见异常接种史"]

# 3. 门（急）诊诊疗记录
chief_complaint = ["发热伴咳嗽3天", "胸闷胸痛2小时", "腹痛伴恶心呕吐半天", "头晕伴视物旋转1天", "关节疼痛1周", "心悸气短3天"]
hpi = ["患者3天前受凉后出现发热，最高38.5度...", "患者2小时前突发心前区压榨性疼痛...", "半天前吃不洁食物后出现腹痛...", "1天前起床时突发头晕...", "1周前无明显诱因出现右膝关节疼痛...", "3天前活动后心悸气短..."]
physical_exam = ["T:38.5 P:90 R:20 BP:120/80 咽红", "T:36.5 P:110 R:22 BP:160/100 痛苦面容", "T:37.0 P:80 R:18 BP:110/70 腹部压痛", "查体无殊", "专科查体：未见异常", "心律齐，各瓣膜未闻及杂音"]
diagnoses = ["J06.9 急性上呼吸道感染", "I20.9 心绞痛", "K35.9 急性阑尾炎", "I10.x 原发性高血压", "E11.9 2型糖尿病", "M10.9 骨关节炎"]
prescriptions = ["阿莫西林胶囊 0.5g tid", "阿司匹林肠溶片 100mg qd", "左氧氟沙星片 0.5g qd", "氨氯地平片 5mg qd", "二甲双胍片 0.5g bid", "布洛芬缓释胶囊 0.3g prn"]
treatment_plans = ["抗感染、对症支持治疗", "完善相关检查，必要时手术", "降压、扩冠治疗", "控制血糖，饮食指导", "休息，随诊", "门诊手术：签署知情同意书"]

# 4. 住院全流程记录
admission_records = ["患者因上述症状入院，病案首页建档，神志清，精神可，平车推入病房", "步行入院，首次病程记录完成，生命体征平稳", "急诊平车推入，立即给予心电监护及吸氧", "轮椅推入病房，家属陪同，交代病情", "门诊拟收治入院，完善常规检查", "患者一般情况可，无特殊不适主诉"]
daily_course = ["日常病程：患者诉症状好转；上级查房：继续目前治疗", "阶段小结：患者偶有发热，最高37.8度，嘱多饮水", "复查指标好转，今日停用心电监护", "会诊记录：请心内科会诊，建议完善冠脉CTA", "抢救记录：突发室颤，立即心肺复苏...", "转科记录：转入ICU进一步监护治疗"]
discharge_summaries = ["出院小结：治愈出院；随访计划：嘱门诊随访", "好转出院，出院医嘱：注意休息，按时服药", "病情平稳，带药出院", "临床治愈，建议1月后复查", "患者及家属要求自动出院，已告知风险", "死亡记录：抢救无效，临床死亡；已行死亡病例讨论"]

# 5. 医技检查与检验结果
lab_results = ["血常规：WBC: 10.5 NE%: 75%", "生化：ALT: 25 AST: 30 Cr: 80", "免疫：乙肝表面抗体阳性", "空腹血糖: 6.5, 餐后血糖: 8.0趋势平稳", "尿常规：WBC(+)", "大便常规正常"]
imaging_reports = ["放射(CT): 肺部未见明显实质性病变", "放射(MRI): 脑内散在缺血灶", "超声: 脂肪肝，胆囊息肉", "心电图：窦性心律，正常心电图", "放射(X光)：骨质未见明显异常", "病理切片：符合(胃窦)慢性萎缩性胃炎伴肠化"]
critical_values = ["无", "无", "无", "无", "无", "无", "无", "无", "危急值预警：血钾 2.5 mmol/L (已电话反馈并处理)", "危急值预警：肌钙蛋白阳性 (已急诊PCI)"]


print(f"Starting generation of {TOTAL_RECORDS} comprehensive records to {output_file}...")
start_time = time.time()

with open(output_file, "w", encoding="utf-8-sig", newline="") as f:
    writer = csv.writer(f)
    headers = [
        "patient_id", "patient_name", "gender", "age", "id_card", "contact", 
        "allergy_history", "past_medical_history", "family_history", "lifestyle", "immunization_record",
        "chief_complaint", "history_of_present_illness", "physical_examination", "icd_diagnosis", "electronic_prescription", "treatment_plan",
        "admission_record", "daily_course_record", "discharge_summary",
        "lab_results", "imaging_reports", "critical_values"
    ]
    writer.writerow(headers)
    
    buffer = io.StringIO()
    csv_buffer = csv.writer(buffer)
    
    for i in range(1, TOTAL_RECORDS + 1):
        # Generate demographic fields
        n_p = random.choice(names_prefix)
        n_s = random.choice(names_suffix)
        name = f"{n_p}{n_s}{random.randint(1, 99)}"
        age = random.randint(10, 89)
        id_card = f"11010519{random.randint(40, 99):02d}{random.randint(1, 12):02d}{random.randint(1, 28):02d}{random.randint(0, 9999):04d}"
        contact = f"138{random.randint(0, 99999999):08d}"
        
        # 20% error rate logic
        is_error = (random.random() < 0.2) # 20% chance
        
        # If error, break the CSV structure (e.g. miss some columns)
        if is_error:
            # We omit a few columns at the end to trigger the column mismatch error
            row = [
                f"P{i:08d}", name, random.choice(genders), str(age), id_card, contact,
                random.choice(allergies), random.choice(past_history), random.choice(family_history), random.choice(lifestyle), random.choice(immunization),
                random.choice(chief_complaint), random.choice(hpi), random.choice(physical_exam), random.choice(diagnoses), random.choice(prescriptions), random.choice(treatment_plans),
                random.choice(admission_records)
            ]
        else:
            row = [
                f"P{i:08d}", name, random.choice(genders), str(age), id_card, contact,
                random.choice(allergies), random.choice(past_history), random.choice(family_history), random.choice(lifestyle), random.choice(immunization),
                random.choice(chief_complaint), random.choice(hpi), random.choice(physical_exam), random.choice(diagnoses), random.choice(prescriptions), random.choice(treatment_plans),
                random.choice(admission_records), random.choice(daily_course), random.choice(discharge_summaries),
                random.choice(lab_results), random.choice(imaging_reports), random.choice(critical_values)
            ]
        
        # Fast append to buffer
        csv_buffer.writerow(row)
        
        # Check buffer size by lines roughly
        if i % BATCH_SIZE == 0:
            f.write(buffer.getvalue())
            buffer.seek(0)
            buffer.truncate(0)
            print(f"Generated {i} records... elapsed: {time.time() - start_time:.2f}s")
            
    if buffer.getvalue():
        f.write(buffer.getvalue())

print(f"✅ Successfully generated {TOTAL_RECORDS} comprehensive records.")
print(f"Total time: {time.time() - start_time:.2f}s")
print(f"File size: {os.path.getsize(output_file) / (1024*1024):.2f} MB")
