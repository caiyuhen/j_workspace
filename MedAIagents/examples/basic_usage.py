"""
MedAIagents 基本使用示例
Basic Usage Examples
"""

import sys
import os

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from medai import MedicalAgent, ClinicalDecisionSupport, MedicalKnowledgeBase


def example_1_basic_chat():
    """示例1: 基础对话"""
    print("=" * 60)
    print("示例1: 基础对话")
    print("=" * 60)
    
    try:
        agent = MedicalAgent()
        
        # 提问一个医学问题
        question = "高血压的常见症状有哪些？"
        print(f"\n用户: {question}")
        
        response = agent.chat(question)
        print(f"\nMedAI: {response}")
        
    except Exception as e:
        print(f"错误: {e}")
        print("注意: 请先配置 LLM API 密钥才能使用此功能")


def example_2_diagnosis_support():
    """示例2: 诊断支持"""
    print("\n" + "=" * 60)
    print("示例2: 诊断支持")
    print("=" * 60)
    
    try:
        cdss = ClinicalDecisionSupport()
        
        symptoms = ["头痛", "头晕", "血压升高"]
        lab_results = {"血压": "160/100 mmHg"}
        
        print(f"\n症状: {symptoms}")
        print(f"检查结果: {lab_results}")
        
        result = cdss.diagnose(symptoms, lab_results)
        
        print("\n诊断结果:")
        if result.get('primary_diagnosis'):
            diag = result['primary_diagnosis']
            print(f"  - 可能诊断: {diag.get('disease', '未知')}")
            print(f"  - ICD-10: {diag.get('icd10', '未知')}")
        
        if result.get('recommended_tests'):
            print("\n建议检查:")
            for test in result['recommended_tests']:
                print(f"  - {test}")
        
    except Exception as e:
        print(f"错误: {e}")


def example_3_medication_safety():
    """示例3: 用药安全检查"""
    print("\n" + "=" * 60)
    print("示例3: 用药安全检查")
    print("=" * 60)
    
    try:
        cdss = ClinicalDecisionSupport()
        
        medications = ["华法林", "阿司匹林"]
        allergies = []
        
        print(f"\n检查药物: {medications}")
        
        result = cdss.check_medication_safety(medications, allergies)
        
        print(f"\n安全状态: {'安全' if result.get('is_safe') else '存在风险'}")
        
        if result.get('warnings'):
            print("\n警告:")
            for warning in result['warnings']:
                print(f"  - {warning.get('description', '未知')}")
        
        if result.get('recommendations'):
            print("\n建议:")
            for rec in result['recommendations']:
                print(f"  - {rec}")
        
    except Exception as e:
        print(f"错误: {e}")


def example_4_knowledge_search():
    """示例4: 医学知识库搜索"""
    print("\n" + "=" * 60)
    print("示例4: 医学知识库搜索")
    print("=" * 60)
    
    try:
        kb = MedicalKnowledgeBase()
        
        query = "高血压治疗"
        print(f"\n搜索: {query}")
        
        results = kb.search(query, limit=3)
        
        print(f"\n找到 {len(results)} 条结果:")
        for i, item in enumerate(results, 1):
            print(f"\n{i}. {item.get('title', '无标题')}")
            print(f"   来源: {item.get('source', '未知')}")
            content = item.get('content', '')[:150]
            print(f"   {content}...")
        
    except Exception as e:
        print(f"错误: {e}")


def example_5_icd10_lookup():
    """示例5: ICD-10编码查询"""
    print("\n" + "=" * 60)
    print("示例5: ICD-10编码查询")
    print("=" * 60)
    
    try:
        from medai.emr import ICD10Coder
        
        coder = ICD10Coder()
        
        diagnoses = ["2型糖尿病", "原发性高血压", "社区获得性肺炎"]
        
        for diagnosis in diagnoses:
            result = coder.get_icd10_code(diagnosis)
            if result:
                print(f"\n{diagnosis}: {result}")
            else:
                print(f"\n{diagnosis}: 未找到编码")
        
    except Exception as e:
        print(f"错误: {e}")


def example_6_security_compliance():
    """示例6: 安全与合规"""
    print("\n" + "=" * 60)
    print("示例6: 数据去标识化")
    print("=" * 60)
    
    try:
        from medai.security import DataDeidentifier
        
        deidentifier = DataDeidentifier()
        
        patient_data = {
            'name': '张三',
            'age': 55,
            'gender': '男',
            'diagnosis': '2型糖尿病',
            'phone': '138****1234',
            'address': '北京市海淀区'
        }
        
        print("\n原始数据:")
        for k, v in patient_data.items():
            print(f"  {k}: {v}")
        
        deidentified = deidentifier.deidentify(patient_data)
        
        print("\n去标识化后:")
        for k, v in deidentified.items():
            print(f"  {k}: {v}")
        
    except Exception as e:
        print(f"错误: {e}")


if __name__ == "__main__":
    print("MedAIagents 示例程序")
    print("面向医疗临床、科研、电子病历的专业AI代理框架\n")
    
    # 运行所有示例
    example_1_basic_chat()
    example_2_diagnosis_support()
    example_3_medication_safety()
    example_4_knowledge_search()
    example_5_icd10_lookup()
    example_6_security_compliance()
    
    print("\n" + "=" * 60)
    print("所有示例执行完成")
    print("=" * 60)
