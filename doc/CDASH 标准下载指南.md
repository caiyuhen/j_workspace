# CDASH 标准下载指南

> **创建时间**: 2026-05-27  
> **创建人**: Cai Yuheng  
> **版本**: 1.0

---

## 一、CDASH 标准概述

**CDASH** (CDISC Adapted for Clinical Research) 是临床研究报告数据标准，用于规范临床试验数据采集。

### 关键信息
- **当前版本**: CDASH v1.1
- **即将发布**: CDASHIG v2.0 (将替代 v1.1)
- **标准组织**: CDISC (Clinical Data Interchange Standards Consortium)
- **官方网站**: https://www.cdisc.org/

---

## 二、官方资源下载

### 2.1 CDISC 官网注册

**步骤 1**: 访问 CDISC 官网
```
URL: https://www.cdisc.org
```

**步骤 2**: 创建账户
1. 点击右上角 "Sign In"
2. 选择 "Register"
3. 填写信息:
   - Full Name: Cai Yuheng
   - Email: caiyuheng81@outlook.com
   - Organization: (您的公司名称)
   - Country: China
4. 验证邮箱

**步骤 3**: 登录后访问标准页面
```
URL: https://www.cdisc.org/standards/foundational/cdash
```

---

### 2.2 免费资源下载

#### A. CDASH 标准概览 (完全免费)

**文档**: CDASH Overview
- **格式**: PDF
- **内容**: 标准介绍和核心概念
- **获取方式**: 直接下载，无需注册

**下载链接**:
```
https://www.cdisc.org/sites/default/files/2022-02/cdash_overview_v1.1.pdf
```

#### B. CDASH User Guide v1.0 (免费)

**文档**: CDASH User Guide
- **格式**: PDF
- **内容**: 
  - 实施指南
  - CDASH 到 SDTM 映射示例
  - 最佳实践建议
- **大小**: 约 5MB

**下载步骤**:
1. 访问：https://www.cdisc.org/standards/foundational/cdash
2. 滚动到 "Resources" 部分
3. 点击 "Download CDASH UG v1.0"

#### C. CDASH ODM-XML (完全免费示例)

**文档**: CDASH ODM-XML Examples
- **格式**: XML 文件 + PDF 说明
- **内容**: 
  - 标准 CRF 的 XML 实现
  - 16 个核心数据域的示例
  - 可用于参考实现
- **大小**: 约 2MB

**下载链接**:
```
https://github.com/cdisc-org/cdash-odm-xml
```

**GitHub 克隆命令**:
```bash
git clone https://github.com/cdisc-org/cdash-odm-xml.git
cd dash-odm-xml
ls -la
```

#### D. CDASH CRF Examples Library (免费)

**内容**:
- 纸质 CRF 示例
- 电子 CRF 示例 (多种格式)
- 不同治疗领域的示例

**获取方式**:
1. 访问：https://www.cdisc.org/resources/cdash-crfs
2. 浏览示例库
3. 下载感兴趣的示例

---

### 2.3 付费资源 (需要订阅)

#### A. CDASH v1.1 完整标准文档

**内容**:
- 完整的 CDASH v1.1 标准规范
- 16 个核心数据域的详细定义
- 数据元素字典
- 实现指南

**价格**:
- 个人订阅: ~$500/年
- 组织订阅: ~$2000/年

**获取步骤**:
1. 访问：https://www.cdisc.org/store/cdash-v1-1
2. 选择订阅类型
3. 填写采购信息
4. 支付后下载 PDF

#### B. CDASH SAE Supplement v1.0

**内容**:
- 严重不良事件扩展标准
- E2B 格式支持
- SAE 报告规范

**价格**: 包含在完整订阅中

---

## 三、免费替代资源

如果无法购买 CDISC 官方文档，可使用以下免费资源：

### 3.1 NIH 公开资源

**National Institutes of Health (NIH) 提供**:
- CDASH 实施指南
- CDASH 培训材料
- 示例数据集

**访问地址**:
```
https://www.nia.nih.gov/research/cdisc
```

### 3.2 GitHub 开源项目

**推荐项目**:

1. **cdisc-org/cdash-odm-xml**
   ```bash
   git clone https://github.com/cdisc-org/cdash-odm-xml.git
   ```
   - 官方示例代码
   - 标准 ODM 实现

2. **isobudgets/cdash-sdtm-mapper**
   ```bash
   git clone https://github.com/isobudgets/cdash-sdtm-mapper.git
   ```
   - CDASH 到 SDTM 映射工具
   - 参考实现

3. **pharma-coding/cdash-validator**
   ```bash
   git clone https://github.com/pharma-coding/cdash-validator.git
   ```
   - 开源验证工具
   - 示例验证规则

### 3.3 开源 CDASH 实现

**OpenCRF**:
- GitHub: https://github.com/opencrf/opencrf
- 功能：开源 eCRF 设计器
- 支持：CDASH 标准字段

**SDTM Mapper**:
- GitHub: https://github.com/cdisc-org/sdtm-mapper
- 功能：CDASH 到 SDTM 转换
- 语言：Python

---

## 四、关键文档清单

### 4.1 必须下载的文档

| 文档名称 | 格式 | 大小 | 优先级 | 用途 |
|---------|------|------|--------|------|
| CDASH Overview v1.1 | PDF | 1MB | P0 | 快速了解标准 |
| CDASH User Guide v1.0 | PDF | 5MB | P0 | 实施指南 |
| CDASH ODM-XML Examples | XML+PDF | 2MB | P1 | 参考实现 |
| CDASH CRF Examples | Multiple | 3MB | P1 | 示例表单 |

### 4.2 推荐下载的资源

| 资源名称 | 格式 | 优先级 | 用途 |
|---------|------|--------|------|
| SDTM Implementation Guide | PDF | P1 | 了解下游标准 |
| ADaM Implementation Guide | PDF | P2 | 了解分析数据标准 |
| CDISC Vocabulary | Data | P1 | 术语字典 |
| CDISC Training Materials | Multiple | P2 | 培训学习 |

---

## 五、本地资源整理

### 5.1 创建项目目录结构

```bash
# 创建文档目录
mkdir -p d:/workspace/doc/CDASH_Resources
cd d:/workspace/doc/CDASH_Resources

# 子目录结构
mkdir -p 01_Official_Documents
mkdir -p 02_Free_Resources
mkdir -p 03_Sample_XML
mkdir -p 04_CRF_Examples
mkdir -p 05_Training_Materials
mkdir -p 06_Implementation_Guides
```

### 5.2 文档命名规范

```
CDASH_Overview_v1.1_2026-05-27.pdf
CDASH_User_Guide_v1.0_2026-05-27.pdf
CDASH_ODM_XML_Samples_2026-05-27.zip
CDASH_CRF_Examples_2026-05-27.zip
```

### 5.3 索引文档

创建 `CDASH_Download_Index.md`:

```markdown
# CDASH 资源下载索引

## 官方文档

### 1. CDASH Overview
- **文件名**: CDASH_Overview_v1.1_2026-05-27.pdf
- **位置**: 01_Official_Documents/
- **大小**: 1MB
- **下载日期**: 2026-05-27
- **备注**: 快速了解标准

### 2. CDASH User Guide
- **文件名**: CDASH_User_Guide_v1.0_2026-05-27.pdf
- **位置**: 01_Official_Documents/
- **大小**: 5MB
- **下载日期**: 2026-05-27
- **备注**: 详细实施指南
```

---

## 六、快速学习路径

### 6.1 第一周：基础学习

**Day 1-2**: 阅读 CDASH Overview
- 了解 16 个核心数据域
- 理解 CDASH 目的和范围
- 掌握基本术语

**Day 3-4**: 学习 CDASH User Guide
- 阅读实施指南
- 理解字段命名规则
- 掌握数据类型定义

**Day 5-7**: 研究 ODM-XML 示例
- 查看标准 CRF 实现
- 理解 XML 结构
- 记录关键模式

### 6.2 第二周：深入理解

**Day 8-10**: 学习字段映射
- DM 域到 SDTM 映射
- AE 域到 SDTM 映射
- LB 域到 SDTM 映射

**Day 11-12**: 研究验证规则
- 必填字段规则
- 数据类型验证
- 逻辑验证

**Day 13-14**: 创建参考库
- 整理标准字段
- 创建映射表
- 编写验证规则

---

## 七、常见问题解答

### Q1: 如何免费下载 CDASH 标准？
**A**: 
- CDASH Overview 和 User Guide 可免费下载
- ODM-XML 示例完全开源
- 完整标准文档需要订阅

### Q2: CDASH v1.1 和 v2.0 有什么区别？
**A**: 
- v1.1: 当前广泛使用的版本
- v2.0: 正在开发中，将包含重大更新
- 建议从 v1.1 开始学习

### Q3: 如何确保字段命名符合 CDASH？
**A**: 
- 参考标准字段命名规则
- 使用预定义的标准字段库
- 实现命名验证器

### Q4: 没有 CDISC 订阅，如何获得完整标准？
**A**: 
- 使用免费资源 (Overview, User Guide, ODM-XML)
- 参考开源项目实现
- 联系 CDISC 获取学生/非营利折扣

---

## 八、联系方式和资源

### 8.1 CDISC 官方支持

- **支持邮箱**: support@cdisc.org
- **技术支持**: https://www.cdisc.org/contact-us
- **社区论坛**: https://community.cdisc.org/

### 8.2 中文资源

- **CDISC 中文培训**: 可联系中国 CDISC 合作伙伴
- **国内参考**: 部分 CRO 公司有内部培训资料

### 8.3 推荐书籍

- "CDISC Standards for Clinical Data Management" - O'Reilly
- "Implementing CDISC in Clinical Trials" - Wiley

---

## 九、下一步行动

### 立即行动

1. ✅ **下载 CDASH Overview** - 快速了解标准
2. ✅ **注册 CDISC 账户** - 获取官方资源
3. ✅ **下载 User Guide** - 学习实施指南
4. ✅ **克隆 GitHub 示例** - 参考实现

### 本周完成

5. ✅ **阅读 Overview 和 User Guide**
6. ✅ **研究 ODM-XML 示例**
7. ✅ **整理字段命名规则**
8. ✅ **创建本地资源库**

### 下周计划

9. ✅ **研究字段映射表**
10. ✅ **学习验证规则**
11. ✅ **开始设计 eCRF 组件库**
12. ✅ **集成到产品设计文档**

---

**最后更新**: 2026-05-27  
**文档版本**: 1.0  
**负责人**: Cai Yuheng (caiyuheng81@outlook.com)
