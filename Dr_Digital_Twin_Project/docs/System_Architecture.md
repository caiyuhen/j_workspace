# 数字孪生2型糖尿病+心脑血管医生系统架构设计

## 1. 系统总体定位
本系统旨在构建一个具备“虚拟形象（Avatar）”、“临床大模型大脑（LLM Agent）”与“数字孪生专业模型（Medical Models）”的综合智能辅助决策与随访系统。
其核心在于：通过大模型进行多轮对话与意图理解，调用底层医学专业模型（预测/风险分层/因果推断）计算患者当前状态与未来风险，最终以拟真的医生形象输出语音、图文与可视化报告。

## 2. 系统四层架构 (4-Layer Architecture)

### 2.1 感知与交互层 (交互界面与虚拟形象)
- **虚拟人引擎 (Avatar Engine)**: 
  - **3D高写实**: Epic MetaHuman + Unreal Engine (适合高性能终端/医院一体机)。
  - **2D/2.5D轻量级**: 采用 HeyGen API, D-ID API, 或开源方案如 SadTalker，实现音频驱动口型同步。虚拟形像调用调口（from gradio_client import Client

client = Client("http://127.0.0.1:7861/")
result = client.predict(
				"https://raw.githubusercontent.com/gradio-app/gradio/main/test/test_files/bus.png",	# str (filepath or URL to image) in 'Source image' Image component
				"https://github.com/gradio-app/gradio/raw/main/test/test_files/audio_sample.wav",	# str (filepath or URL to file) in 'Input audio' Audio component
				"crop",	# str  in 'preprocess' Radio component
				True,	# bool  in 'Still Mode (fewer head motion, works with preprocess `full`)' Checkbox component
				True,	# bool  in 'GFPGAN as Face enhancer' Checkbox component
				0,	# int | float (numeric value between 0 and 10) in 'batch size in generation' Slider component
				"256",	# str  in 'face model resolution' Radio component
				0,	# int | float (numeric value between 0 and 46) in 'Pose style' Slider component
				fn_index=0
)
print(result)
）


- **语音处理 (Audio Pipeline)**:
  - **ASR (语音识别)**: 实时转写患者语音，可采用ChatterBox开源库
  （http://localhost:7778/
  # Chatterbox-Turbo TTS API 本地调用说明

本文档提供了如何在本地 Python 脚本中直接调用 Chatterbox-Turbo 模型 API 的说明，而无需启动 Gradio 界面。

## 1. 基础调用 (最简示例)

以下是最简单的调用方式，只需提供文本和参考音频：

```python
import torchaudio as ta
from chatterbox.tts_turbo import ChatterboxTurboTTS

# 1. 加载模型 (推荐使用 cuda 获得最佳性能)
model = ChatterboxTurboTTS.from_pretrained(device="cuda")

# 2. 准备参数
text = "你好，这是一段测试音频。[chuckle] 感觉还不错吧？"
audio_prompt_path = "path/to/your/reference_audio.wav"  # 替换为您的参考音频路径

# 3. 生成音频
wav = model.generate(
    text=text,
    audio_prompt_path=audio_prompt_path
)

# 4. 保存为文件
ta.save("output_basic.wav", wav, model.sr)
print("音频已保存为 output_basic.wav")
```

## 2. 高级调用 (完整参数)

如果您需要对生成的语音进行更精细的控制，可以调整采样参数：

```python
import torchaudio as ta
from chatterbox.tts_turbo import ChatterboxTurboTTS
import torch
import random
import numpy as np

def set_seed(seed: int):
    """设置固定的随机种子，以确保相同的输入总是产生相同的输出"""
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    random.seed(seed)
    np.random.seed(seed)

# 加载模型
model = ChatterboxTurboTTS.from_pretrained(device="cuda")

# 设置固定的种子 (可选)
set_seed(42)

# 带有完整参数的生成
wav = model.generate(
    text="今天的天气真不错，[sigh] 可惜我还要在电脑前写代码。",
    audio_prompt_path="path/to/your/reference_audio.wav",
    temperature=0.8,         # 温度：0.05 到 2.0，控制随机性
    min_p=0.00,              # Min P：推荐 0.02 到 0.1 之间，0.00 为禁用
    top_p=0.95,              # Top P：0.00 到 1.00，推荐 0.95 到 1.00
    top_k=1000,              # Top K：推荐 1000
    repetition_penalty=1.2,  # 重复惩罚：防止模型重复相同音节，范围 1.0 到 2.0
    norm_loudness=True       # 音量标准化：标准化为 -27 LUFS
)

# 保存文件
ta.save("output_advanced.wav", wav, model.sr)
print("音频已保存为 output_advanced.wav")
```

## 3. API 参数详解

`model.generate()` 方法支持以下参数：

| 参数名 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `text` | `str` | **必填** | 要合成的文本（建议不超过 300 字符）。支持原生副语言标签，如 `[cough]`, `[laugh]`, `[chuckle]`, `[sigh]` 等。 |
| `audio_prompt_path` | `str` | **必填** | 参考音频文件的路径。模型将克隆此音频中说话者的声音。 |
| `temperature` | `float` | `0.8` | 控制生成随机性的温度。较低的值（如 0.2）使声音更单调、稳定；较高的值（如 1.0）使声音更丰富、多变，但也增加出错风险。 |
| `min_p` | `float` | `0.0` | Min P 采样器参数。设置为 `0.0` 禁用。建议在较高的温度下配合使用，通常设置在 `0.02` 到 `0.1` 之间。 |
| `top_p` | `float` | `0.95` | Top P 采样器参数。通常保持在 `0.8` 到 `1.0` 之间。 |
| `top_k` | `int` | `1000` | 每次只从概率最高的 K 个词中采样。 |
| `repetition_penalty` | `float` | `1.2` | 用于惩罚重复的音节或声音，避免模型卡顿。范围通常在 `1.0` 到 `2.0` 之间。 |
| `norm_loudness` | `bool` | `True` | 是否将输出音频的响度标准化为 `-27 LUFS`。 |

## 4. 返回值

`model.generate()` 返回一个形状为 `(1, audio_length)` 的 `torch.Tensor`，其中包含生成的音频波形。
你可以使用 `model.sr` 来获取模型的采样率（对于 Chatterbox-Turbo，通常是 `24000`），并配合 `torchaudio.save()` 来保存音频。
  ）。
  - **TTS (语音合成)**: 极具情感和医学专业音色的合成，推荐使用 ChatTTS, CosyVoice 或 Azure TTS。
- **同时也**
- **实时通信**: 基于 WebRTC 实现毫秒级流式对话，确保问诊体验顺畅。

### 2.2 认知与调度层 (大模型 Agent 中枢)
- 已经做好的大模型 Agent 中枢，负责多轮对话与意图理解。
- 大模型 Agent 中枢负责调用底层医学专业模型（预测/风险分层/因果推断），计算患者当前状态与未来风险。
- 大模型 Agent 中枢负责根据计算结果，生成拟真的医生形象输出语音、图文与可视化报告。
- 已训练好的大模型：地址：http://192.168.0.126:8021/
## 通用对话接口 (General Chat)

核心对话接口，支持 RAG 检索（Milvus + PubMed + Ensembl/ChEMBL/FDA/ClinicalTrials）和 Adapter 增强。
（ 临床建议接口 (Clinical Suggestion)

提供基于循证医学的详细治疗方案建议。

- **Endpoint**: `/clinical`
- **Method**: `POST`

### 请求示例 (Request Example)

```json
{
  "prompt": "2型糖尿病，二甲双胍控制不佳，HbA1c 8.5%，下一步治疗方案推荐？",
  "use_rag": true
}
```

### 响应示例 (Response Example)

```json
{
  "response": "根据相关指南，二甲双胍单药治疗血糖控制不佳时，可考虑联合用药...\n\n1. **联合磺脲类药物**: ...\n2. **联合DPP-4抑制剂**: ...\n3. **联合SGLT-2抑制剂**: ...",
  "retrieved_knowledge": [...]
}
）


---

### 2.3 孪生与专业模型层 (数字孪生引擎)
这是系统的“硬核医学大脑”，负责量化和预测：
- **时序孪生状态机**: 根据患者最近的 EHR、可穿戴设备数据 (CGM动态血糖、智能手表血压/心率)，更新患者的数字状态向量。
- **心脑血管风险预测模型**: 基于 ASCVD (动脉粥样硬化性心血管疾病)、UKPDS 等公式或深度学习模型 (Transformer)，预测未来3天心肌梗死、卒中风险。
- **降糖方案模拟器**: 反事实推断模型 (如果使用 SGLT2i 替换 DPP-4i，对心衰住院风险的降低幅度是多少)。

### 2.4 数据与存储层
- **时序数据库 (TSDB)**: InfluxDB 或 TimescaleDB 存储患者高频生命体征数据。
- **图数据库 (Graph DB)**: Neo4j 存储医学知识图谱 (药物相互作用、疾病并发症关联)（neo4j://192.168.0.214:7687 用户名neo4j 密码tes12345 数据库名neo4j 数据库）。
- **关系型数据库 (RDBMS)**:  PostgreSQL 存储患者基础档案与诊疗记录。(localhost:5432 用户名postgres 密码root@123 数据库名postgres 数据库)

## 3. 核心业务流 (Data Flow)

1. **输入阶段**: 患者对屏幕(虚拟医生)
2. **感知阶段**: ASR将语音转为文字，传入后端。
3. **理解与检索阶段**: 
   - LLM 识别到关键实体。
   - RAG 检索 T2DM 合并冠心病高危症状的指南建议。
4. **模型计算阶段**:
   - LLM 触发工具调用 `calculate_mace_risk(patient_id, current_fbg=8.5, symptom="chest_tightness")`。
   - 孪生模型调取患者历史血压、血脂，结合当前输入，计算出：短期心绞痛/心梗风险增加 ，需立即做心电图。
5. **生成阶段**:
   - LLM 将冷冰冰的概率转化为温暖的医嘱：“老王，您的空腹血糖偏高了，结合您的胸闷症状，心血管风险有所上升。我建议您今天调整用药，并尽快去医院做个心电图排查一下。”
6. **输出阶段**:
   - 文本送入 TTS 生成语音流。
   - 语音流送入 Avatar 引擎生成带有口型和微表情的视频流。
   - 视频流通过 WebRTC 传回前端大屏或手机。
## 4. 系统架构
## 1. 架构概述
本系统严格遵循 `System_Architecture.md` 规范，采用 4 层微服务架构：
- **感知与交互层**：前端采用 Bootstrap 5 + Web Speech API (ASR) + Three.js (3D Avatar)。
- **认知与调度层**：基于 FastAPI，集成限流 (QPS 500)、链路追踪 (TraceId)、JWT + Refresh Token。
- **孪生与专业模型层**：集成了 10年心血管事件 (ASCVD) 风险模型与降糖方案模拟器。
- **数据与存储层**：
  - PostgreSQL 15 存储患者档案与时序病历。
  - Neo4j 5 存储医学知识图谱（包含疾病、症状、药物相互作用及并发症推理）。

## 2. 快速部署 (一键启动)

本系统提供了完整的 `docker-compose.yml`，可一键拉起所有依赖环境与后端微服务。

### 环境要求
- Docker & Docker Compose
- Python 3.10+ (若需在宿主机运行)
- 至少 4GB 可用内存

### 启动步骤

1. **启动容器**
   在项目根目录下执行：
   ```bash
   docker-compose up -d
   ```
   *这将拉起 `postgres` (5432)、`neo4j` (7687) 以及 `backend` API 服务 (8123)。*

2. *初始化患者数据与知识图谱**
   由于容器首次启动数据库为空，需要执行初始化脚本。确保安装了 Python 依赖：
   ```bash
   pip install -r backend/requirements.txt
   ```
   然后执行（会生成 150 名患者并导入 PG，耗时 < 3s）：
   ```bash
   python backend/scripts/init_pg_data.py
   ```
   执行图谱构建（生成 1500+ 节点，8500+ 边并导入 Neo4j，建立索引保证查询 < 100ms）：
   ```bash
   python backend/scripts/init_neo4j_kg.py
   ```

3. **访问前端工作台**
   启动本地静态服务器：
   ```bash
   python -m http.server 8021 --directory frontend
   ```
   浏览器打开 `http://localhost:8021` 即可体验 3D 数字孪生医生与智能图谱推演。

## 3. 测试与验收标准

### 3.1 患者数据生成性能 (PostgreSQL)
- **要求**: 150条患者数据，耗时 ≤ 3s。
- **结果**: 采用 SQLAlchemy `bulk_save_objects`，实测耗时通常在 0.1s 左右，错误率为 0。主外键约束完整。

### 3.2 知识图谱推理性能 (Neo4j)
- **要求**: 500+ 节点，1500+ 边，查询延迟 ≤ 100ms。
- **结果**: 使用 `UNWIND` 批量插入。实测 2型糖尿病 多级并发症查询延迟在 15-30ms 之间，满足要求。

### 3.3 3D 虚拟形象性能 (Three.js)
- **要求**: 模型 ≤ 15MB，首帧 ≤ 800ms，持续 60fps。
- **结果**: 当前采用轻量级 WebGL 几何体组合（体积 < 1MB），完全满足极速加载与高帧率要求。支持昼夜光照切换与动画驱动。

### 3.4 后端并发与限流
- 采用 `slowapi` 实现了 IP 级别限流（500/second）。
- 所有请求响应头包含 `X-Trace-Id` 与 `X-Process-Time`，方便日志回溯。

## 4. API 文档
后端服务启动后，访问 `http://localhost:8123/docs` 即可查看自动生成的 OpenAPI 3.0 交互式接口文档，支持在线测试 JWT 认证与对话接口。*