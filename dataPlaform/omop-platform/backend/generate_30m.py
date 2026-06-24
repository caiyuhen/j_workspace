import os
import time

output_dir = r"d:\workspace\dataPlaform\omop-platform\inputdata"
os.makedirs(output_dir, exist_ok=True)
output_file = os.path.join(output_dir, "emr_30m_test.csv")

TOTAL_RECORDS = 30_000_000
BATCH_SIZE = 1_000_000

# Pre-compute modulo lookup tables for maximum performance
genders = ["M", "F", "男", "女", "1", "2", "未知"]
depts = ["内科", "外科", "1001", "急诊", "儿科", "骨科"]
diagnoses = ["J06.9", "E11.9", "I10", "I15.9"]

print(f"Starting generation of {TOTAL_RECORDS} records to {output_file}...")
start_time = time.time()

with open(output_file, "w", encoding="utf-8-sig") as f:
    f.write("patient_id,patient_name,gender,birth_date,visit_date,department,diagnosis\n")
    
    buffer = []
    for i in range(1, TOTAL_RECORDS + 1):
        # Extremely fast string formatting
        buffer.append(f"P{i:08d},Patient_{i},{genders[i%7]},19{40+(i%60)}-01-01,20{20+(i%4)}-{(i%12)+1:02d}-15,{depts[i%6]},{diagnoses[i%4]}\n")
        
        if len(buffer) >= BATCH_SIZE:
            f.write("".join(buffer))
            buffer.clear()
            print(f"Generated {i} records... elapsed: {time.time() - start_time:.2f}s")
            
    if buffer:
        f.write("".join(buffer))

print(f"✅ Successfully generated {TOTAL_RECORDS} records.")
print(f"Total time: {time.time() - start_time:.2f}s")
print(f"File size: {os.path.getsize(output_file) / (1024*1024):.2f} MB")
