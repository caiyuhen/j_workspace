import os
import re

# 读取原文件
files = [f for f in os.listdir(r'D:\doc') if '培训' in f and f.endswith('.html') and '增强' not in f]
filepath = os.path.join(r'D:\doc', files[0])
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

print(f'读取原文件：{filepath}')
print(f'原始长度：{len(content)} 字节')

# 创建新的幻灯片内容
new_slides = '''
<!-- ══════════ SLIDE 18 : 术语集详解 ══════════ -->
<div class="slide" id="s18" style="background:#0d1522;">
  <div class="slide-inner">
    <div class="section-tag" style="background:rgba(186,117,23,.15);color:#FAC775;">核心术语集</div>
    <div class="slide-title">医疗数据标准术语集详解</div>
    <div class="slide-lead">标准化的术语集是实现跨系统数据互操作的关键。以下介绍 CDISC 与 OMOP 中使用的主流术语集。</div>
    <div class="card-grid col2">
      <div class="card bg-blue">
        <div class="card-title"><span class="badge badge-blue">MedDRA</span></div>
        <div class="card-body">
          <strong>Medical Dictionary for Regulatory Activities</strong><br>
          FDA/EMA 等监管机构要求使用的不良事件编码系统<br>
          · 层级结构:HLG → PT → LLT (5 层)<br>
          · 覆盖领域：疾病、手术、检验、药品<br>
          · CDISC 标准:AE/CM域必用
        </div>
      </div>
      <div class="card bg-teal">
        <div class="card-title"><span class="badge badge-teal">LOINC</span></div>
        <div class="card-body">
          <strong>Logical Observation Identifiers Names and Codes</strong><br>
          实验室检查、生命体征观测的国际标准编码<br>
          · 覆盖 58 万 + 观测项目<br>
          · 包含：名称、成分、性质、时间点、方法<br>
          · OMOP 核心:MEASUREMENT 表必用
        </div>
      </div>
      <div class="card bg-purple">
        <div class="card-title"><span class="badge badge-purple">RxNorm</span></div>
        <div class="card-body">
          <strong>Drug Name Repository</strong><br>
          美国国家医学图书馆 (NLM) 维护的标准药物编码<br>
          · 覆盖 24 万 + 药物概念<br>
          · 支持：药品成分、剂量、剂型、给药途径<br>
          · OMOP 核心:DRUG_EXPOSURE 表必用
        </div>
      </div>
      <div class="card bg-amber">
        <div class="card-title"><span class="badge badge-amber">SNOMED-CT</span></div>
        <div class="card-body">
          <strong>Systematized Nomenclature of Medicine Clinical Terms</strong><br>
          全球最全面的临床医学术语集<br>
          · 35 万 + 临床概念，82 万 + 术语<br>
          · 覆盖诊断、症状、手术、设备<br>
          · OMOP 核心:CONDITION_OCCURRENCE 表必用
        </div>
      </div>
      <div class="card bg-coral">
        <div class="card-title"><span class="badge badge-amber">ICD-9/10/11</span></div>
        <div class="card-body">
          <strong>International Classification of Diseases</strong><br>
          WHO 发布的疾病分类标准<br>
          · ICD-10: 1.2 万 + 疾病代码<br>
          · ICD-11: 2022 年启用，支持电子健康记录<br>
          · 医保报销、流行病学统计必用
        </div>
      </div>
      <div class="card bg-green">
        <div class="card-title"><span class="badge badge-teal">NCI CTCAE</span></div>
        <div class="card-body">
          <strong>Common Terminology Criteria for Adverse Events</strong><br>
          美国国家癌症研究所不良事件分级标准<br>
          · 5 级严重程度分级 (1-5)<br>
          · 覆盖肿瘤治疗常见不良事件<br>
          · CDISC 标准：肿瘤试验 AETOXGR 字段
        </div>
      </div>
    </div>
  </div>
</div>

<!-- ══════════ SLIDE 19 : 术语集映射 ══════════ -->
<div class="slide" id="s19" style="background:#0d1522;">
  <div class="slide-inner">
    <div class="section-tag" style="background:rgba(186,117,23,.15);color:#FAC775;">术语集映射机制</div>
    <div class="slide-title">跨术语集的映射策略与工具</div>
    <div class="slide-lead">源系统中的本地编码需要通过映射工具转换到标准术语集，这是实现数据互操作的核心环节。</div>
    <div class="two-col">
      <div>
        <div style="font-size:13px;font-weight:500;margin-bottom:12px;color:rgba(255,255,255,.7);">映射层级与关系类型</div>
        <table class="data-table">
          <thead><tr><th>关系类型</th><th>含义</th><th>示例</th></tr></thead>
          <tbody>
            <tr><td><span class="badge badge-blue">EXACT_MATCH</span></td><td>精确匹配，语义完全等价</td><td>ICD-10 J06.9 ↔ SNOMED 199595004</td></tr>
            <tr><td><span class="badge badge-teal">BROAD_MATCH</span></td><td>源概念范围宽于目标</td><td>"感染"涵盖"肺炎"、"尿路感染"</td></tr>
            <tr><td><span class="badge badge-amber">NARROW_MATCH</span></td><td>源概念范围窄于目标</td><td>"链球菌肺炎"是"肺炎"的子集</td></tr>
            <tr><td><span class="badge badge-purple">RELATED_TO</span></td><td>相关但不等价</td><td>"高血压"相关"ACEI 类药物治疗"</td></tr>
          </tbody>
        </table>
        <div class="highlight-box" style="background:rgba(186,117,23,.1);border-color:#BA7517;margin-top:14px;">
          <div class="hb-title" style="color:#FAC775;">⚠️ 映射原则</div>
          <div class="hb-body">① 优先保留原始编码 (source_code) ② 映射质量标注 (match_quality) ③ 支持一对多映射 ④ 可追溯映射来源 (mapping_source)</div>
        </div>
      </div>
      <div>
        <div style="font-size:13px;font-weight:500;margin-bottom:12px;color:rgba(255,255,255,.7);">常见映射路径</div>
        <div class="vocab-mapping">
          <div class="map-row"><span class="map-source">ICD-10</span><span class="map-arrow">→</span><span class="map-target">SNOMED-CT</span></div>
          <div class="map-row"><span class="map-source">院内代码</span><span class="map-arrow">→</span><span class="map-target">LOINC</span></div>
          <div class="map-row"><span class="map-source">药品说明书</span><span class="map-arrow">→</span><span class="map-target">RxNorm</span></div>
          <div class="map-row"><span class="map-source">MedDRA</span><span class="map-arrow">→</span><span class="map-target">SNOMED-CT</span></div>
        </div>
        <div style="font-size:13px;font-weight:500;margin:18px 0 12px;color:rgba(255,255,255,.7);">映射工具</div>
        <table class="data-table">
          <thead><tr><th>工具</th><th>功能</th></tr></thead>
          <tbody>
            <tr><td><span class="badge badge-teal">OHDSI Usagi</span></td><td>源编码→OMOP concept 映射</td></tr>
            <tr><td><span class="badge badge-blue">NCI Metathesaurus</span></td><td>跨词库统一查询</td></tr>
            <tr><td><span class="badge badge-amber">MapMan</span></td><td>手动映射编辑工具</td></tr>
            <tr><td><span class="badge badge-purple">IBM Cloud</span></td><td>医学术语映射云服务</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</div>

<!-- ══════════ SLIDE 20 : CDISC 数据质量管理 ══════════ -->
<div class="slide" id="s20" style="background:#0d1522;">
  <div class="slide-inner">
    <div class="section-tag" style="background:rgba(55,138,221,.15);color:#85B7EB;">CDISC 数据质量管理</div>
    <div class="slide-title">CDISC：侧重于数据管理合规</div>
    <div class="slide-lead">CDISC 的数据质量要求围绕监管申报展开，强调数据从采集到提交的全过程可追溯性与合规性。</div>
    <div class="two-col">
      <div>
        <div style="font-size:13px;font-weight:500;margin-bottom:12px;color:rgba(255,255,255,.7);">核心质量维度 (ALCOA+)</div>
        <ul class="rule-list">
          <li><span class="bullet" style="background:rgba(55,138,221,.25);color:#85B7EB;">A</span><div><strong>Attributable</strong> (可归因)<br>每条数据可追溯到原始记录与录入人</div></li>
          <li><span class="bullet" style="background:rgba(55,138,221,.25);color:#85B7EB;">L</span><div><strong>Legible</strong> (清晰可辨)<br>数据格式标准化，无歧义表达</div></li>
          <li><span class="bullet" style="background:rgba(55,138,221,.25);color:#85B7EB;">C</span><div><strong>Contemporaneous</strong> (同步记录)<br>数据采集与试验进程时间同步</div></li>
          <li><span class="bullet" style="background:rgba(55,138,221,.25);color:#85B7EB;">O</span><div><strong>Original</strong> (原始记录)<br>保留数据最初记录形态</div></li>
          <li><span class="bullet" style="background:rgba(55,138,221,.25);color:#85B7EB;">A</span><div><strong>Accurate</strong> (准确无误)<br>通过双重录入、逻辑检核确保准确性</div></li>
        </ul>
        <div class="highlight-box" style="background:rgba(55,138,221,.1);border-color:#378ADD;margin-top:14px;">
          <div class="hb-title" style="color:#85B7EB;">数据管理工具链</div>
          <div class="hb-body">① CDISC Validator 自动检查 SDTM/ADaM 合规性 · ② Define.xml 描述数据集结构 · ③ Data Review Initiative (DRI) 人工审核 · ④ CDMP 流程文档化</div>
        </div>
      </div>
      <div>
        <div style="font-size:13px;font-weight:500;margin-bottom:12px;color:rgba(255,255,255,.7);">CDISC 质量检核重点</div>
        <table class="data-table">
          <thead><tr><th>检核点</th><th>规则示例</th></tr></thead>
          <tbody>
            <tr><td>完整性</td><td>USUBJID、STUDYID 不能缺失</td></tr>
            <tr><td>一致性</td><td>AESTDTC ≤ AEENDTC</td></tr>
            <tr><td>受控术语</td><td>AESER 只能用 Y/N</td></tr>
            <tr><td>日期格式</td><td>YYYY-MM-DD (ISO 8601)</td></tr>
            <tr><td>派生规则</td><td>ADaM 必须能回溯到 SDTM</td></tr>
            <tr><td>异常值</td><td>LBORRES 超出正常范围需注释</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</div>

<!-- ══════════ SLIDE 21 : OMOP 数据评估 ══════════ -->
<div class="slide" id="s21" style="background:#0d1522;">
  <div class="slide-inner">
    <div class="section-tag" style="background:rgba(29,158,117,.15);color:#5DCAA5;">OMOP 数据评估体系</div>
    <div class="slide-title">OMOP：侧重于数据质量评估</div>
    <div class="slide-lead">OMOP CDM 的数据评估方法更加系统化、自动化，通过 ACHILLES 和 DQD 工具实现大规模数据的快速质量诊断。</div>
    <div class="two-col">
      <div>
        <div style="font-size:13px;font-weight:500;margin-bottom:12px;color:rgba(255,255,255,.7);">数据质量评估五维度</div>
        <table class="data-table">
          <thead><tr><th>维度</th><th>指标示例</th></tr></thead>
          <tbody>
            <tr><td><span class="badge badge-teal">完整性</span></td><td>NULL 值比例、必填字段缺失率</td></tr>
            <tr><td><span class="badge badge-blue">有效性</span></td><td>概念编码有效性、外键约束</td></tr>
            <tr><td><span class="badge badge-amber">一致性</span></td><td>性别与出生性别一致性</td></tr>
            <tr><td><span class="badge badge-purple">及时性</span></td><td>数据更新延迟天数</td></tr>
            <tr><td><span class="badge badge-teal">准确性</span></td><td>逻辑矛盾检测 (死亡日期 < 出生日期)</td></tr>
          </tbody>
        </table>
        <div class="highlight-box" style="background:rgba(29,158,117,.1);border-color:#1D9E75;margin-top:14px;">
          <div class="hb-title" style="color:#5DCAA5;">OHDSI 数据质量工具</div>
          <div class="hb-body">① <strong>ACHILLES</strong>：数据特征描述，生成数据分布报告 · ② <strong>DQD</strong>：Data Quality Dashboard，自动运行 360+ 质量规则 · ③ <strong>WhiteRabbit</strong>：源数据扫描与映射建议</div>
        </div>
      </div>
      <div>
        <div style="font-size:13px;font-weight:500;margin-bottom:12px;color:rgba(255,255,255,.7);">典型 DQD 质量规则</div>
        <ul class="rule-list">
          <li><span class="bullet" style="background:rgba(29,158,117,.25);color:#5DCAA5;">✓</span><div><strong>Concept Validity</strong><br>所有 concept_id 必须在 CONCEPT 表中存在</div></li>
          <li><span class="bullet" style="background:rgba(29,158,117,.25);color:#5DCAA5;">✓</span><div><strong>Visit Consistency</strong><br>visit_end_date ≥ visit_start_date</div></li>
          <li><span class="bullet" style="background:rgba(29,158,117,.25);color:#5DCAA5;">✓</span><div><strong>Gender Consistency</strong><br>gender_concept_id 必须为 8507 (男) 或 8532 (女)</div></li>
          <li><span class="bullet" style="background:rgba(29,158,117,.25);color:#5DCAA5;">✓</span><div><strong>Age Plausibility</strong><br>age_at_visit 应在 0-120 岁范围内</div></li>
          <li><span class="bullet" style="background:rgba(29,158,117,.25);color:#5DCAA5;">✓</span><div><strong>Drug Dosage Validity</strong><br>dosage_unit_concept_id 必须为标准单位</div></li>
        </ul>
        <div class="highlight-box" style="background:rgba(29,158,117,.1);border-color:#1D9E75;margin-top:14px;">
          <div class="hb-title" style="color:#5DCAA5;">分布式评估能力</div>
          <div class="hb-body">OHDSI 支持跨多个 OMOP 数据库同时运行 DQD，生成对比报告，识别数据源之间的质量差异。</div>
        </div>
      </div>
    </div>
  </div>
</div>

<!-- ══════════ SLIDE 22 : CDISC vs OMOP 质量对比 ══════════ -->
<div class="slide" id="s22" style="background:#0d1522;">
  <div class="slide-inner">
    <div class="section-tag" style="background:rgba(186,117,23,.15);color:#FAC775;">质量管理对比</div>
    <div class="slide-title">CDISC vs OMOP：质量管理差异对比</div>
    <div class="slide-lead">两者都重视数据质量，但 CDISC 侧重合规与管理，OMOP 侧重评估与诊断，形成互补。</div>
    <table class="data-table" style="margin-bottom:16px;">
      <thead><tr><th>维度</th><th>CDISC (数据管理侧重)</th><th>OMOP (数据评估侧重)</th></tr></thead>
      <tbody>
        <tr><td><strong>质量目标</strong></td><td>监管申报合规，确保数据可追溯</td><td>观察性研究可重复，数据可横向对比</td></tr>
        <tr><td><strong>核心方法</strong></td><td>ALCOA+ 原则 + 人工审核</td><td>DQD 自动检核 + ACHILLES 特征分析</td></tr>
        <tr><td><strong>检核规则</strong></td><td>CDISC Validator 预定义规则</td><td>360+ DQD 可配置规则</td></tr>
        <tr><td><strong>问题处理</strong></td><td>数据质疑 (Query)→修复→重新验证</td><td>质量报告→数据源反馈→ETL 修正</td></tr>
        <tr><td><strong>文档化要求</strong></td><td>Define.xml + 数据管理计划 (CDMP)</td><td>ETL 文档 + ACHILLES 报告</td></tr>
        <tr><td><strong>适用场景</strong></td><td>临床试验 (RCT) 数据申报</td><td>真实世界 (RWE) 多中心研究</td></tr>
        <tr><td><strong>可扩展性</strong></td><td>针对单一试验的深度验证</td><td>跨数百数据库的分布式评估</td></tr>
        <tr><td><strong>技术工具</strong></td><td>SAS、R、CDISC Validator</td><td>ATLAS、DQD、ACHILLES、WhiteRabbit</td></tr>
      </tbody>
    </table>
    <div class="highlight-box" style="background:rgba(186,117,23,.1);border-color:#BA7517;">
      <div class="hb-title" style="color:#FAC775;">💡 融合趋势</div>
      <div class="hb-body">FDA Sentinel 项目同时使用 CDISC 和 OMOP 标准：临床试验数据按 CDISC 提交，真实世界数据按 OMOP 建模，两者通过映射实现联合分析。</div>
    </div>
  </div>
</div>
'''

# 找到插入位置 (在 deck 结束前)
insert_marker = '</div><!-- /deck -->'
if insert_marker in content:
    insert_pos = content.find(insert_marker)
    content = content[:insert_pos] + new_slides + content[insert_pos:]
    print('✓ 成功插入新幻灯片 (5 页)')
else:
    print('✗ 未找到插入位置')

# 更新总结 slide 内容
old_summary = '③ CDISC'
new_summary = '③ CDISC · ④ OMOP CDM · ⑤ 术语集详解 (MedDRA/LOINC/RxNorm/SNOMED) · ⑥ 数据质量对比 (CDISC 管理 vs OMOP 评估)'
# 不修改原有总结，保持简洁

# 添加额外 CSS
extra_css = '''
.vocab-mapping { margin: 12px 0; }
.vocab-mapping .map-row { display: flex; align-items: center; gap: 8px; font-size: 11px; padding: 6px 0; }
.vocab-mapping .map-source { min-width: 80px; color: rgba(255,255,255,.7); }
.vocab-mapping .map-arrow { color: rgba(255,255,255,.35); }
.vocab-mapping .map-target { color: #85B7EB; font-weight: 500; }
'''
content = content.replace('</style>', extra_css + '</style>')
print('✓ 添加额外 CSS 样式')

# 保存增强版
output_path = r'D:\doc\数据培训 PPT_增强版.html'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f'\n✅ 增强版 PPT 已生成！')
print(f'输出文件：{output_path}')
print(f'文件大小：{len(content)} 字节')
print('\n新增内容:')
print('  - Slide 18: 术语集详解 (MedDRA/LOINC/RxNorm/SNOMED/ICD/CTCAE)')
print('  - Slide 19: 术语集映射机制 (关系类型 + 映射工具)')
print('  - Slide 20: CDISC 数据质量管理 (ALCOA+ 原则)')
print('  - Slide 21: OMOP 数据评估体系 (DQD/ACHILLES)')
print('  - Slide 22: CDISC vs OMOP 质量对比')
