#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
乳腺癌患者院外日常管理方案 - 分词与 RAG 数据准备脚本
"""
import json
import re
from typing import List, Dict, Any
import jieba

# 读取完整文档
with open(r'C:\Users\Administrator\WorkBuddy\2026-05-12-task-2\breast_cancer_plan.txt', 'r', encoding='utf-8') as f:
    text = f.read()

print("开始分词处理...")

# 1. 医疗术语词典
medical_terms = [
    # 疾病分期
    "乳腺癌", "导管原位癌", "DCIS", "浸润癌", "炎性乳腺癌",
    "0 期", "I 期", "II 期", "III 期", "IV 期", "TisN0M0",
    
    # 治疗方式
    "手术", "保乳手术", "全乳切除", "乳房重建", "放疗", "化疗",
    "靶向治疗", "内分泌治疗", "抗 HER2 治疗", "新辅助治疗",
    "蒽环类", "免疫治疗", "MDT",
    
    # 分子分型
    "HR 阳性", "HER2 阳性", "HR-", "HER2-", "TNBC", "激素受体",
    
    # 并发症与症状
    "淋巴水肿", "皮下积液", "血肿", "浆液肿", "腋网综合征",
    "骨髓抑制", "发热性中性粒细胞减少", "贫血", "血小板减少",
    "放射性肺炎", "心包炎", "复发转移",
    
    # 检查项目
    "乳房 X 线", "乳腺超声", "血常规", "生化", "心功能", "LVEF",
    "病理分期", "肿瘤分期", "双侧上肢周径",
    
    # 管理动作
    "功能锻炼", "握拳", "伸指", "屈腕", "爬墙训练", "肩关节活动度",
    "术后康复", "随访", "复诊", "建档", "患者教育",
    
    # 时间概念
    "术后", "出院", "切口愈合后", "终身随访", "治疗期"
]

# 2. 自定义分词函数
def custom_segment(text: str) -> List[str]:
    """自定义分词，优先匹配医疗术语"""
    # 先加载自定义词典
    for term in medical_terms:
        jieba.add_word(term)
    
    # 分词
    words = list(jieba.cut(text))
    
    # 过滤掉无意义字符
    filtered_words = [w.strip() for w in words if w.strip() and len(w.strip()) > 0]
    
    return filtered_words

# 3. 提取关键词
def extract_keywords(text: str, top_k: int = 50) -> List[str]:
    """提取关键词"""
    words = custom_segment(text)
    
    # 过滤停用词和标点符号
    stop_words = {
        '的', '了', '在', '是', '我', '有', '和', '就', '不', '人',
        '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去',
        '你', '会', '着', '没有', '看', '好', '自己', '这', '中', '为',
        '他', '时', '要', '等', '及', '与', '或', '、', '；', '。', '/', '，', '：',
        '）', '（', '-', '\x07', '!', '?', '!', '?', ';', '；'
    }
    
    # 统计词频
    word_freq = {}
    for word in words:
        if word not in stop_words and len(word) >= 1:
            word_freq[word] = word_freq.get(word, 0) + 1
    
    # 按频率排序
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    
    return [word for word, freq in sorted_words[:top_k]]

# 4. 生成段落级别的索引
def create_paragraph_index(text: str) -> List[Dict[str, Any]]:
    """创建段落级别的索引，用于 RAG 检索"""
    # 按段落分割
    paragraphs = re.split(r'\n\s*\n', text)
    
    index = []
    for i, para in enumerate(paragraphs):
        if len(para.strip()) < 20:
            continue
            
        words = custom_segment(para)
        keywords = extract_keywords(para, top_k=10)
        
        index.append({
            "paragraph_id": f"para_{i+1:03d}",
            "content": para.strip(),
            "tokens": words[:100],  # 前 100 个词
            "keywords": keywords,
            "word_count": len(words),
            "char_count": len(para)
        })
    
    return index

# 5. 生成句子级别的索引
def create_sentence_index(text: str) -> List[Dict[str, Any]]:
    """创建句子级别的索引，用于精确检索"""
    # 按句子分割
    sentences = re.split(r'(?<=[。！？!?;；])\s*', text)
    
    index = []
    for i, sent in enumerate(sentences):
        if len(sent.strip()) < 10:
            continue
            
        words = custom_segment(sent)
        
        # 判断句子类型
        sentence_type = "general"
        if any(t in sent for t in ['术后', '天', '周', '月']):
            sentence_type = "timeline"
        elif any(t in sent for t in ['期', 'DCIS', '分期']):
            sentence_type = "stage"
        elif any(t in sent for t in ['监测', '评估', '观察', '测量']):
            sentence_type = "monitoring"
        elif any(t in sent for t in ['锻炼', '训练', '功能']):
            sentence_type = "rehabilitation"
        
        index.append({
            "sentence_id": f"sent_{i+1:03d}",
            "content": sent.strip(),
            "tokens": words,
            "sentence_type": sentence_type,
            "char_count": len(sent)
        })
    
    return index

# 执行处理
print("\n1. 生成段落索引...")
paragraph_index = create_paragraph_index(text)
print(f"   生成 {len(paragraph_index)} 个段落")

print("\n2. 生成句子索引...")
sentence_index = create_sentence_index(text)
print(f"   生成 {len(sentence_index)} 个句子")

print("\n3. 提取全局关键词...")
global_keywords = extract_keywords(text, top_k=100)
print(f"   提取 {len(global_keywords)} 个关键词")

print("\n4. 生成术语表...")
# 生成术语表
terminology = []
for term in medical_terms:
    if term in text:
        # 找到术语出现的位置
        positions = []
        for match in re.finditer(re.escape(term), text):
            positions.append(match.start())
        
        terminology.append({
            "term": term,
            "occurrences": len(positions),
            "positions": positions[:5]  # 前 5 个位置
        })

terminology = sorted(terminology, key=lambda x: x['occurrences'], reverse=True)
print(f"   生成 {len(terminology)} 个术语")

# 保存 RAG 数据
rag_data = {
    "metadata": {
        "document_name": "乳腺癌患者院外日常管理方案_分期分治疗执行版",
        "total_characters": len(text),
        "total_paragraphs": len(paragraph_index),
        "total_sentences": len(sentence_index),
        "total_keywords": len(global_keywords),
        "total_terms": len(terminology),
        "processing_date": "2026-05-12",
        "description": "乳腺癌管理方案分词数据，用于 RAG 检索"
    },
    "global_keywords": global_keywords,
    "terminology": terminology[:50],  # 前 50 个高频术语
    "paragraph_index": paragraph_index,
    "sentence_index": sentence_index
}

# 保存完整数据
with open(r'C:\Users\Administrator\WorkBuddy\2026-05-12-task-2\breast_cancer_rag_data.json', 'w', encoding='utf-8') as f:
    json.dump(rag_data, f, ensure_ascii=False, indent=2)

print("\n" + "="*80)
print("RAG 数据处理完成!")
print(f"段落索引：{len(paragraph_index)} 条")
print(f"句子索引：{len(sentence_index)} 条")
print(f"全局关键词：{len(global_keywords)} 个")
print(f"术语表：{len(terminology)} 个")
print("\n文件已保存至：breast_cancer_rag_data.json")

# 打印前 20 个关键词
print("\n前 20 个全局关键词:")
print(global_keywords[:20])
