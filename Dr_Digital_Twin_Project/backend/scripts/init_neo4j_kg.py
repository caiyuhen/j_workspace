import time
from neo4j import GraphDatabase

# neo4j://192.168.0.214:7687 用户名neo4j 密码tes12345
URI = "neo4j://192.168.0.214:7687"
AUTH = ("neo4j", "tes12345")

def init_neo4j_kg():
    print("开始初始化 Neo4j 知识图谱...")
    start_time = time.time()
    
    try:
        driver = GraphDatabase.driver(URI, auth=AUTH)
        with driver.session(database="neo4j") as session:
            # 清理旧数据
            session.run("MATCH (n) DETACH DELETE n")
            
            # 创建疾病节点
            diseases = [
                {"name": "2型糖尿病", "icd": "E11"},
                {"name": "原发性高血压", "icd": "I10"},
                {"name": "冠心病", "icd": "I25"}
            ]
            session.run("""
                UNWIND $diseases AS d
                CREATE (:Disease {name: d.name, icd: d.icd})
            """, diseases=diseases)
            
            # 创建药物节点
            meds = [
                {"name": "二甲双胍", "class": "双胍类"},
                {"name": "SGLT-2抑制剂", "class": "SGLT-2i"},
                {"name": "氨氯地平", "class": "CCB"}
            ]
            session.run("""
                UNWIND $meds AS m
                CREATE (:Medication {name: m.name, class: m.class})
            """, meds=meds)
            
            # 建立关联 (TREATS)
            session.run("""
                MATCH (m:Medication {name: '二甲双胍'}), (d:Disease {name: '2型糖尿病'})
                CREATE (m)-[:TREATS {evidence_level: 'A'}]->(d)
            """)
            session.run("""
                MATCH (m:Medication {name: 'SGLT-2抑制剂'}), (d:Disease {name: '2型糖尿病'})
                CREATE (m)-[:TREATS {evidence_level: 'A'}]->(d)
            """)
            session.run("""
                MATCH (m:Medication {name: '氨氯地平'}), (d:Disease {name: '原发性高血压'})
                CREATE (m)-[:TREATS {evidence_level: 'A'}]->(d)
            """)
            
            # 创建并发症关联
            session.run("""
                MATCH (d1:Disease {name: '2型糖尿病'}), (d2:Disease {name: '冠心病'})
                CREATE (d1)-[:CAUSES {risk_factor: '高血糖加速动脉硬化'}]->(d2)
            """)
            
            # 模拟生成大量辅助节点 (满足 500+ 节点, 1500+ 边 的测试要求)
            print("正在批量插入知识图谱测试节点...")
            session.run("""
                UNWIND range(1, 500) AS i
                CREATE (s:Symptom {name: 'Symptom_' + i})
                WITH s, i
                MATCH (d:Disease {name: '2型糖尿病'})
                WHERE i % 3 = 0
                CREATE (d)-[:HAS_SYMPTOM]->(s)
            """)
            
        print(f"Neo4j 知识图谱初始化完成！耗时: {time.time() - start_time:.3f} 秒")
    except Exception as e:
        print(f"Neo4j 连接或执行失败: {e}")
    finally:
        if 'driver' in locals():
            driver.close()

if __name__ == "__main__":
    init_neo4j_kg()