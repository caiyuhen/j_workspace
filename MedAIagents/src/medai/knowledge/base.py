"""
医学知识库模块
Medical Knowledge Base Module
"""

import os
import json
import requests
from typing import List, Dict, Any, Optional
from loguru import logger
from abc import ABC, abstractmethod
import sqlite3

from ..config import Config


class VectorDBBase(ABC):
    """向量数据库基类"""
    
    @abstractmethod
    def add_documents(self, documents: List[Dict[str, Any]]):
        """添加文档到向量数据库"""
        pass
    
    @abstractmethod
    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """搜索相似文档"""
        pass


class SimpleVectorDB(VectorDBBase):
    """简单的向量数据库实现（使用SQLite + TF-IDF）"""
    
    def __init__(self, storage_path: str, collection_name: str):
        self.storage_path = storage_path
        self.collection_name = collection_name
        os.makedirs(storage_path, exist_ok=True)
        
        db_path = os.path.join(storage_path, f"{collection_name}.db")
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        
        # 创建文档表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                content TEXT,
                source TEXT,
                category TEXT,
                keywords TEXT,
                created_at TIMESTAMP
            )
        ''')
        self.conn.commit()
    
    def add_documents(self, documents: List[Dict[str, Any]]):
        """添加文档"""
        for doc in documents:
            self.cursor.execute(
                '''INSERT INTO documents 
                   (title, content, source, category, keywords, created_at) 
                   VALUES (?, ?, ?, ?, ?, datetime('now'))''',
                (
                    doc.get('title', ''),
                    doc.get('content', ''),
                    doc.get('source', ''),
                    doc.get('category', ''),
                    ','.join(doc.get('keywords', []))
                )
            )
        self.conn.commit()
        logger.info(f"Added {len(documents)} documents to knowledge base")
    
    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """搜索文档（简单的关键词匹配）"""
        # 将查询分解为关键词
        keywords = query.lower().split()
        
        # 构建SQL查询（简单的LIKE匹配）
        if not keywords:
            self.cursor.execute(
                'SELECT id, title, content, source, category FROM documents ORDER BY created_at DESC LIMIT ?',
                (limit,)
            )
        else:
            conditions = ' OR '.join(['LOWER(content) LIKE ?' for _ in keywords])
            params = [f'%{k}%' for k in keywords]
            params.append(limit)
            
            self.cursor.execute(
                f'''SELECT id, title, content, source, category 
                    FROM documents 
                    WHERE {conditions} 
                    ORDER BY created_at DESC LIMIT ?''',
                params
            )
        
        rows = self.cursor.fetchall()
        results = []
        for row in rows:
            results.append({
                'id': row[0],
                'title': row[1],
                'content': row[2],
                'source': row[3],
                'category': row[4],
                'score': 1.0  # 简单的计分
            })
        
        return results
    
    def get_all_categories(self) -> List[str]:
        """获取所有分类"""
        self.cursor.execute('SELECT DISTINCT category FROM documents WHERE category != ""')
        rows = self.cursor.fetchall()
        return [row[0] for row in rows]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        self.cursor.execute('SELECT COUNT(*) FROM documents')
        total = self.cursor.fetchone()[0]
        
        self.cursor.execute('SELECT category, COUNT(*) FROM documents GROUP BY category')
        by_category = {row[0]: row[1] for row in self.cursor.fetchall()}
        
        return {
            'total_documents': total,
            'by_category': by_category
        }


class PubMedSearcher:
    """PubMed文献搜索器"""
    
    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    
    def __init__(self, email: str = None):
        self.email = email or "anonymous@example.com"
    
    def search(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """搜索PubMed文献
        
        Args:
            query: 搜索查询
            max_results: 最大结果数量
        
        Returns:
            文献列表
        """
        try:
            # 搜索ID
            search_url = f"{self.BASE_URL}/esearch.fcgi"
            params = {
                'db': 'pubmed',
                'term': query,
                'retmax': max_results,
                'retmode': 'json',
                'email': self.email
            }
            
            response = requests.get(search_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            id_list = data.get('esearchresult', {}).get('idlist', [])
            
            if not id_list:
                return []
            
            # 获取摘要
            fetch_url = f"{self.BASE_URL}/efetch.fcgi"
            params = {
                'db': 'pubmed',
                'id': ','.join(id_list),
                'retmode': 'xml',
                'rettype': 'abstract'
            }
            
            response = requests.get(fetch_url, params=params, timeout=10)
            response.raise_for_status()
            
            # 简单的XML解析（实际应该使用XML库）
            results = self._parse_pubmed_xml(response.text)
            return results
            
        except Exception as e:
            logger.error(f"PubMed search failed: {e}")
            return []
    
    def _parse_pubmed_xml(self, xml_text: str) -> List[Dict[str, Any]]:
        """简单解析PubMed XML响应"""
        import xml.etree.ElementTree as ET
        
        results = []
        root = ET.fromstring(xml_text)
        
        for article in root.findall('.//PubmedArticle'):
            try:
                medline = article.find('.//MedlineCitation')
                article_data = article.find('.//Article')
                
                title = article_data.findtext('.//ArticleTitle', '')
                abstract = article_data.findtext('.//AbstractText', '')
                
                # 作者
                authors = []
                for author in article_data.findall('.//Author'):
                    last_name = author.findtext('LastName', '')
                    first_name = author.findtext('ForeName', '')
                    if last_name:
                        authors.append(f"{last_name} {first_name}".strip())
                
                # 期刊
                journal = article_data.find('.//Journal')
                journal_title = journal.findtext('.//Title', '') if journal is not None else ''
                
                # 发表年份
                pub_date = article_data.find('.//PubDate')
                year = pub_date.findtext('Year', '') if pub_date is not None else ''
                
                # PMID
                pmid = medline.findtext('PMID', '') if medline is not None else ''
                
                results.append({
                    'title': title,
                    'abstract': abstract,
                    'authors': authors,
                    'journal': journal_title,
                    'year': year,
                    'pmid': pmid,
                    'source': 'PubMed'
                })
            except Exception as e:
                logger.warning(f"Failed to parse article: {e}")
                continue
        
        return results


class MedicalKnowledgeBase:
    """医学知识库主类"""
    
    def __init__(self, config: Config = None):
        self.config = config or Config()
        kb_config = self.config.get('medical_knowledge', {})
        
        # 向量数据库配置
        vector_db_config = kb_config.get('vector_db', {})
        self.db_provider = vector_db_config.get('provider', 'simple')
        self.collection_name = vector_db_config.get('collection_name', 'medical_knowledge')
        
        # 存储路径
        self.storage_path = kb_config.get('local_knowledge_path', './data/knowledge')
        os.makedirs(self.storage_path, exist_ok=True)
        
        # 初始化向量数据库
        self.vector_db = self._init_vector_db()
        
        # 初始化外部搜索器
        self.pubmed_searcher = PubMedSearcher(
            kb_config.get('data_sources', {}).get('pubmed', {}).get('email')
        )
        
        # 加载预置的医学知识
        self._load_builtin_knowledge()
        
        logger.info("Medical Knowledge Base initialized")
    
    def _init_vector_db(self) -> VectorDBBase:
        """初始化向量数据库"""
        if self.db_provider in ['simple', 'sqlite']:
            return SimpleVectorDB(self.storage_path, self.collection_name)
        else:
            logger.warning(f"Unsupported vector DB provider: {self.db_provider}, using simple")
            return SimpleVectorDB(self.storage_path, self.collection_name)
    
    def _load_builtin_knowledge(self):
        """加载预置的医学知识"""
        builtin_knowledge = [
            {
                'title': '2型糖尿病诊断标准',
                'content': '根据WHO和ADA指南，2型糖尿病的诊断标准包括：1. 空腹血糖≥7.0 mmol/L；2. OGTT 2小时血糖≥11.1 mmol/L；3. HbA1c≥6.5%；4. 随机血糖≥11.1 mmol/L且伴典型症状。',
                'source': 'WHO/ADA Guidelines',
                'category': '内分泌',
                'keywords': ['糖尿病', '2型糖尿病', '诊断标准', '血糖', 'HbA1c']
            },
            {
                'title': '高血压分级标准',
                'content': '根据中国高血压防治指南：正常血压<120/<80 mmHg；正常高值120-139/80-89 mmHg；1级高血压140-159/90-99 mmHg；2级高血压160-179/100-109 mmHg；3级高血压≥180/≥110 mmHg。',
                'source': '中国高血压防治指南',
                'category': '心血管',
                'keywords': ['高血压', '血压', '分级', '诊断']
            },
            {
                'title': '社区获得性肺炎(CAP)治疗',
                'content': '青壮年无基础疾病：青霉素类、第一代头孢菌素；老年人或有基础疾病：呼吸喹诺酮类、β-内酰胺类/β-内酰胺酶抑制剂；重症CAP：β-内酰胺类联合大环内酯类或呼吸喹诺酮类。',
                'source': '中国CAP指南',
                'category': '呼吸科',
                'keywords': ['肺炎', 'CAP', '抗生素', '治疗']
            },
            {
                'title': '急性心肌梗死诊断标准',
                'content': '急性心梗诊断需满足以下至少1项：1. 心肌肌钙蛋白升高/降低，至少1次超过99%参考值上限；2. 缺血症状；3. 新发ST-T改变或新发左束支传导阻滞；4. 病理性Q波；5. 影像学证据。',
                'source': 'ESC/ACC指南',
                'category': '心血管',
                'keywords': ['心梗', '心肌梗死', '肌钙蛋白', '心电图']
            },
            {
                'title': '脑梗死溶栓治疗时间窗',
                'content': '静脉溶栓时间窗：发病4.5小时内（rt-PA）；发病6小时内（尿激酶）。机械取栓时间窗：前循环大动脉闭塞发病6小时内，部分患者可延长至24小时。',
                'source': '中国卒中指南',
                'category': '神经科',
                'keywords': ['脑梗死', '溶栓', 'rt-PA', '取栓', '时间窗']
            }
        ]
        
        # 检查是否已加载
        stats = self.vector_db.get_statistics()
        if stats['total_documents'] == 0:
            self.vector_db.add_documents(builtin_knowledge)
            logger.info("Loaded builtin medical knowledge")
    
    def search(self, query: str, limit: int = 5, use_pubmed: bool = False) -> List[Dict[str, Any]]:
        """搜索医学知识
        
        Args:
            query: 搜索查询
            limit: 结果数量限制
            use_pubmed: 是否同时搜索PubMed
        
        Returns:
            医学知识条目列表
        """
        # 本地知识库搜索
        local_results = self.vector_db.search(query, limit)
        
        # PubMed搜索
        pubmed_results = []
        if use_pubmed:
            pubmed_results = self.pubmed_searcher.search(query, min(limit, 5))
            # 转换格式
            for r in pubmed_results:
                r['category'] = '文献'
                r['content'] = r.pop('abstract', '')
        
        return local_results + pubmed_results
    
    def add_document(self, document: Dict[str, Any]):
        """添加文档到知识库
        
        Args:
            document: 文档字典，包含title, content, source, category, keywords
        """
        self.vector_db.add_documents([document])
    
    def add_documents(self, documents: List[Dict[str, Any]]):
        """批量添加文档"""
        self.vector_db.add_documents(documents)
    
    def get_categories(self) -> List[str]:
        """获取所有分类"""
        return self.vector_db.get_all_categories()
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取知识库统计信息"""
        return self.vector_db.get_statistics()
