# Medical RAG Service (Retrieval-Augmented Generation)

这是一个独立的医学知识检索微服务，旨在为大模型提供精准、实时的多源外部知识支持。

## 核心能力

本服务通过统一的 HTTP 接口 (`POST /search`) 对外提供检索能力，集成了以下六大知识源，并具备强大的**查询理解与转换能力**：

1.  **多格式素材解析与上下文关联 (Multi-format Material Context)**
    *   **内容**: 支持用户传入多种格式的素材文件（文档如 PDF, DOCX, Markdown, TXT, Excel，图像如 JPG, BMP, DICOM等），作为额外上下文关联。
    *   **大模型自动调用**: 支持通过 `summarize` 参数，基于检索和上传素材内容自动调用底层大模型进行信息提炼和内容总结。

2.  **Milvus (Local Knowledge) - Unified Vector Search**
    *   **内容**: 本地索引的医学指南、教科书、私有文档 (PDF/Markdown)。
    *   **技术**: 向量检索 (Dense Retrieval)，支持 **Milvus Standalone** (高性能) 与 **Milvus Lite** (本地文件回退) 双模式切换。
    *   **统一存储库**: 所有的本地知识（包括《乳腺癌疾病管理路径》、通用医学指南、肺癌专库等）已通过数据清洗与重构，统一转化为 512 维向量并合并至单一的 `medical_rag` 主库中，彻底摒弃了此前低效且有损的跨维度多库检索（384维切片映射），大幅提升了查询速度与检索精确度。

2.  **PubMed (Literature)**
    *   **内容**: 全球生物医学文献摘要 (2024-2025 最新文献)。
    *   **技术**: 实时调用 NCBI E-Utilities API，支持 `Date Range` 过滤。

3.  **Ensembl (Genomics)**
    *   **内容**: 基因、蛋白质功能、序列信息及同源物。
    *   **技术**: 实时调用 Ensembl REST API (`/lookup/symbol`)。

4.  **ChEMBL (Pharmacology)**
    *   **内容**: 药物分子结构 (SMILES)、靶点 (Target)、IC50 活性数据。
    *   **技术**: 实时调用 ChEMBL Web Services。

5.  **FDA (Adverse Events)**
    *   **内容**: 药物不良事件报告 (FAERS)，包含副作用统计。
    *   **技术**: 实时调用 openFDA API。
    *   **特性**: **自动翻译** (Auto-Translation)，支持中文药名自动转英文查询 (如 "阿司匹林" -> "ASPIRIN")。

6.  **ClinicalTrials.gov (Studies)**
    *   **内容**: 全球临床试验注册信息（状态、干预措施、结果）。
    *   **技术**: 实时调用 ClinicalTrials.gov API v2。
    *   **特性**: **关键词提取** (Keyword Extraction)，从自然语言查询中提取核心疾病/药物词 (如 "GLP-1" 提取)。

## 架构设计

### 1. 整体架构 (Architecture)
本服务采用模块化微服务架构，以 `RAG Engine` 为中枢，通过 `AsyncIO` 并发调度六大知识源。

```mermaid
graph LR
    API[HTTP API (:8001)] --> Engine[RAG Engine]
    
    subgraph "Query Processing"
        Engine -->|1. Analysis| NLP[NLP Processor]
        NLP -->|Extract| KW[Keyword Extraction]
        NLP -->|Translate| Trans[Term Translation]
    end

    subgraph "Knowledge Sources (Parallel Retrieval)"
        Engine -->|2. Search| Milvus[(Milvus Vector DB)]
        Engine -->|Fallback| MilvusLite[(Milvus Lite DB)]
        
        Engine -->|2. Search| PubMed[PubMed Client]
        PubMed --> External_PubMed[NCBI API]
        
        Engine -->|2. Search| Ensembl[Ensembl Client]
        Ensembl --> External_Ensembl[Ensembl API]
        
        Engine -->|2. Search| ChEMBL[ChEMBL Client]
        ChEMBL --> External_ChEMBL[ChEMBL API]
    
        Engine -->|2. Search| FDA[FDA Client]
        FDA --> External_FDA[openFDA API]
    
        Engine -->|2. Search| ClinicalTrials[ClinicalTrials Client]
        ClinicalTrials --> External_CT[ClinicalTrials.gov API]
    end

    subgraph "Fusion Layer"
        Engine -->|3. Rerank| Ranker[Reranker]
        Ranker -->|4. Top-K| Context[Context Builder]
    end
```

### 2. 核心算法与流程 (Algorithms & Flow)

#### 2.1 查询理解：关键词提取与自动翻译 (Query Understanding)
在检索前，系统首先对用户 Query 进行深度解析，以解决跨语言和非结构化查询的难题：

*   **自动翻译 (Automatic Translation)**:
    *   **背景**: FDA, ChEMBL, PubMed 等国际数据库仅支持英文检索，而用户常使用中文。
    *   **机制**: 维护高频医学术语映射字典 (`term_mapping`)。
    *   **流程**: `Input("阿司匹林副作用")` -> `Regex Match("阿司匹林")` -> `Map("ASPIRIN")` -> `Generate Query("ASPIRIN adverse events")` -> `Call openFDA`.
*   **关键词提取 (Keyword Extraction)**:
    *   **基因/蛋白质**: 使用正则 `r"[A-Z][A-Z0-9]+"` 识别大写基因符号 (如 `BRCA1`, `TP53`)，直接路由至 Ensembl。
    *   **临床试验**: 针对 "关于 X 的临床试验" 句式，利用 NLP 规则提取核心实体 `X` (如 "GLP-1")，去除 "最新", "研究" 等停用词。

#### 2.2 混合检索策略 (Hybrid Retrieval Strategy)
系统采用 **"规则路由 (Rule-Based Routing) + 向量检索 (Dense Retrieval) + 关键词搜索 (Keyword Search)"** 的多路混合策略：

1.  **意图识别与路由 (Intent Routing)**:
    *   **Gene Intent**: 命中基因符号 -> **Ensembl** (权重 1.0)。
    *   **Drug Intent**: 短文本 (<50 chars) 或命中药物名 -> **ChEMBL** & **FDA** (权重 0.9)。
    *   **General Intent**: 复杂自然语言问题 -> **Milvus** (向量相似度) + **PubMed** (关键词匹配) 并行执行。
    *   **Trial Intent**: 命中 "临床试验" 关键词 -> **ClinicalTrials.gov**。

2.  **向量检索 (Vector Retrieval)**:
    *   **Embedding 模型**: `BAAI/bge-small-zh-v1.5` (微调版)，针对医学 Query-Document 对进行了 Contrastive Learning 微调。
    *   **索引算法**: Milvus `IVF_FLAT` (Inverted File with Flat)。
        *   `nlist`: 1024 (聚类中心数)。
        *   `nprobe`: 16 (检索时扫描的聚类桶数，平衡精度与速度)。
    *   **Metric**: `L2` (欧氏距离) 或 `IP` (内积/余弦相似度)。

3.  **结果重排序与融合 (Reranking & Fusion)**:
    *   **Score Normalization**: 将不同源的分数 (如 Milvus 距离、PubMed 匹配度) 归一化到 `[0, 1]` 区间。
    *   **Weighted Fusion**: `Final_Score = w1 * Vector_Score + w2 * API_Reliability_Score`.
    *   **去重**: 根据内容哈希去除重复的检索结果。

### 3. 数据与记忆 (Data & Context)

#### 3.1 向量数据库 Schema (Milvus Details)
当前系统支持多个集合 (Collections) 并行检索：

*   **medical_rag (统一主库)**:
    *   **Primary Fields**:
        *   `id` (Int64): 唯一主键，Auto-ID。
        *   `embedding` (FloatVector, dim=512): 文本向量（强制使用统一的 512 维 BAAI/bge-small-zh-v1.5 模型，已废弃所有 Mock Fallback 生成假向量的机制）。
        *   `text` (VarChar, max=65535): 原始知识切片。
    *   **Knowledge Graph Metadata (用于结构化过滤)**:
        *   `stages`: 适用分期 (e.g., "IV期", "术后")。
        *   `diagnoses`: 关联诊断 (e.g., "NSCLC", "高血压")。
        *   `western_medicines`: 提及的西药实体。
        *   `tcm_medicines`: 提及的中药/方剂。
        *   `gene_mutations`: 提及的基因突变 (e.g., "EGFR 19-del")。

*   **medical_knowledge (异构集合) - 已废弃**:
    *   (由于维度不匹配和性能问题，该库的数据已重新转化为 512 维并合入 `medical_rag` 中，不再维护单独的异构查询)。

#### 3.2 基于向量库的知识图谱实现 (Vector-Native Knowledge Graph)
本项目并未引入繁重的图数据库 (Neo4j)，而是创新性地利用 **Milvus 标量字段 (Scalar Fields)** 实现了**"轻量级知识图谱"**，即 **Graph-in-Vector** 架构。

1.  **实体即标签 (Entities as Tags)**:
    在构建索引阶段，系统对每个医学文本块 (Chunk) 进行 **NER (命名实体识别)**，提取关键医学实体，并将其作为元数据存储在 Milvus 中：
    *   **节点 (Nodes)**: 映射为 Milvus 的 Scalar Fields。
        *   `diagnoses`: 疾病节点 (e.g., ["肺腺癌", "NSCLC"])
        *   `western_medicines`: 药物节点 (e.g., ["吉非替尼", "奥希替尼"])
        *   `gene_mutations`: 基因节点 (e.g., ["EGFR 19-del", "T790M"])
        *   `stages`: 属性节点 (e.g., ["IV期", "晚期"])
    *   **边 (Edges)**: 隐含在 **"Chunk-Entity"** 的共现关系中。如果 Chunk A 同时包含 "肺癌" 和 "吉非替尼"，则建立了 "肺癌 --(治疗)--> 吉非替尼" 的隐式关联。

2.  **混合过滤与多跳推理 (Hybrid Filtering & Multi-hop)**:
    利用 Milvus 强大的 **混合检索 (Hybrid Search)** 能力，实现类图查询：
    *   **结构化过滤 (Structured Filtering)**:
        用户问 "吉非替尼治疗肺癌的效果？"，系统生成过滤表达式：
        `expr = "western_medicines like '%吉非替尼%' && diagnoses like '%肺癌%'"`
        这相当于在图谱中锁定了特定子图，大大缩小了向量检索的范围 (Search Space)，提高了精度。
    *   **隐式多跳 (Implicit Multi-hop)**:
        1.  检索 "EGFR突变" 相关文档。
        2.  从文档元数据中发现高频共现药物 "奥希替尼"。
        3.  再次检索 "奥希替尼" 的详细机制。

这种设计避免了维护复杂的图谱 Schema，同时保留了知识图谱的**精确性**和向量检索的**泛化性**。

#### 3.3 上下文构建与 Embedding (Context Engineering)
*   **Semantic Chunking**:
    *   策略: 基于段落 (Paragraph) 和 语义完整性 进行切分。
    *   参数: `Chunk Size = 512 tokens`, `Overlap = 50 tokens`。
*   **Context Injection**:
    *   检索到的 Top-K (默认 K=5) 结果被格式化为 XML 风格的 Prompt 片段：
        ```xml
        <context>
            <source_1 type="Milvus">...</source_1>
            <source_2 type="PubMed">...</source_2>
        </context>
        ```
    *   这种结构帮助大模型区分不同来源的知识可信度。

### 4. Embedding 模型构建与优化 (Embedding Pipeline)

为了提升在医学垂直领域的检索效果，我们没有直接使用通用模型，而是基于私有医学语料构建了完整的 Embedding 训练流水线。

#### 4.1 数据准备 (Data Preparation)
*   **数据源**: `/data` 目录下的 Markdown 格式医学指南、教材与临床笔记。
*   **清洗 (Cleaning)**: `DataProcessor` 负责去除空字节、多余换行及非文本噪声。
*   **切片 (Chunking)**: 使用 `TextChunker` 进行滑动窗口切分。
    *   **训练切片**: `Chunk Size = 384` (较短，专注句子级语义)。
    *   **推理切片**: `Chunk Size = 512` (较长，包含完整上下文)。
    *   **过滤**: 剔除长度小于 50 字符的碎片，保证训练数据的语义完整性。

#### 4.2 模型训练 (Model Training)
采用 **TSDAE (Transformer-based Denoising AutoEncoder)** 无监督领域自适应技术，无需人工标注的正负样本对即可在私有领域微调模型。

*   **基座模型 (Base Model)**: `BAAI/bge-small-zh-v1.5` (512维，中文语义理解能力强)。
*   **训练架构**:
    *   **Encoder**: BERT-based Transformer，将含噪输入 (Corrupted Input) 编码为向量。
    *   **Decoder**: 尝试从向量中重建原始文本。
*   **损失函数 (Loss Function)**: `DenoisingAutoEncoderLoss`。
    *   通过引入删除噪声 (Deletion Noise)，迫使 Encoder 学习更鲁棒的语义表征，而非简单的词汇匹配。
*   **超参数 (Hyperparameters)**:
    *   `Batch Size`: 16
    *   `Learning Rate`: 3e-5 (Constant Scheduler)
    *   `Pooling`: Mean Pooling
    *   `Precision`: Mixed Precision (AMP) 开启，加速训练。

#### 4.3 模型使用与推理 (Inference & Serving)
训练产物 (`output/trained_model_384`) 被直接集成到 `VectorStore` 中：

1.  **加载 (Loading)**: 使用 `sentence-transformers` 库加载微调后的权重。
2.  **编码 (Encoding)**:
    *   对输入文本进行 Tokenize 和 Forward Pass。
    *   执行 **L2 Normalization** (归一化)，使得向量的点积 (Dot Product) 等价于余弦相似度 (Cosine Similarity)。
3.  **索引 (Indexing)**:
    *   生成的 512维向量被存入 Milvus 的 `IVF_FLAT` 索引中，支持毫秒级检索。

### 5. 高可用与容错 (High Availability)
*   **双层向量存储 (Dual-Layer Vector Store)**:
    *   **L1 (Production)**: Milvus Distributed/Standalone，处理高并发。
    *   **L2 (Fallback)**: Milvus Lite (SQLite-based)，当 L1 连接超时 (>5s) 时自动接管，保证 99.99% 可用性。
*   **API 熔断与降级 (Circuit Breaker)**:
    *   对外部 API (PubMed/FDA) 设置 3秒超时。
    *   若连续失败 3 次，暂时熔断该数据源 60秒，避免阻塞主线程。

## 数据处理与自动化 (Data Pipeline)

为了方便向 Milvus 中持续灌入新的知识，系统提供了自动化的批处理与规则提取脚本：

1.  **文档批量向量化 (`batch_process_docs.py`)**:
    *   **功能**: 自动扫描 `data/sf/` 目录下的医学 PDF 和 Word (.doc/.docx) 文档。
    *   **流程**: 利用 LangChain 的 `PyPDFLoader` 与 `UnstructuredWordDocumentLoader` 提取文本 -> `RecursiveCharacterTextSplitter` 语义分块 -> 向量化写入 Milvus (`medical_rag` 库) -> 处理完成后自动移动至 `data/oldf/` 归档。
    *   **执行**: `PYTHONNOUSERSITE=1 /home/lfang/miniconda3/envs/rag/bin/python batch_process_docs.py`

2.  **专项 Markdown 文档向量化 (`ingest_md.py` / `ingest_guanli.py`)**:
    *   **功能**: `batch_process_docs.py` 默认不处理 `.md` 后缀的文档，因此补充了专门针对核心疾病管理指南（如《乳腺癌疾病管理路径.md》）的清洗与入库脚本。
    *   **流程**: 强制使用标准 512 维 Embedding -> 存入 `medical_rag`。

3.  **结构化规则提取 (`ingest_rules.py`)**:
    *   **功能**: 深度解析复杂的 Markdown 医学指南（如乳腺癌指南），通过正则表达式提取表格和列表中的临床决策规则。
    *   **流程**: 解析各章节（随访、饮食、用药等）-> 转换为 JSON 格式规则 -> 存入 MongoDB 用于精确命中 -> 存入 Milvus 用于语义检索。

## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 启动服务
```bash
python server.py
# 服务将运行在 http://0.0.0.0:8001
```

### 3. 接口调用示例
```python
import requests

response = requests.post("http://localhost:8001/search", json={
    "query": "最新关于GLP-1的临研究有哪些？",
    "top_k": 5
})
print(response.json())
```

## 目录结构

*   `rag_engine.py`: 核心检索引擎，负责调度各数据源。
*   `server.py`: FastAPI 服务入口。
*   `vector_store.py`: Milvus 数据库操作封装。
*   `pubmed_interface/`: PubMed API 客户端。
*   `ensembl_client.py`: Ensembl API 客户端。
*   `chembl_client.py`: ChEMBL API 客户端。
*   `fda_client.py`: FDA API 客户端。
*   `clinical_trials_client.py`: ClinicalTrials.gov API 客户端。
