
export const ROLES = [
  { key: 'pm', label: '项目经理 (PM)', description: '整体项目管控（方案制定、中心筛选、预算、进度、合规）' },
  { key: 'cra', label: '临床监查员 (CRA)', description: '现场监查（研究中心核查、数据SDV、方案依从性、问题解决）' },
  { key: 'dm', label: '数据管理专员 (DM)', description: '数据核查、清理、锁定（确保数据完整性）' },
  { key: 'stat', label: '统计师 (Stat)', description: '统计方案设计、数据分析、报告生成' },
  { key: 'pv', label: '药物警戒专员 (PV)', description: 'SAE/SUSAR收集、评估、报告（保护受试者安全）' },
  { key: 'qa', label: '质量保证专员 (QA)', description: '审计、合规检查（确保GCP符合性）' },
  { key: 'site', label: '研究者/机构管理员', description: '现场试验执行（受试者管理、数据记录、AE报告）' },
  { key: 'irb', label: '伦理委员会 (IRB)', description: '试验伦理审查、监督试验进展' },
];

export const STAGES = [
  { key: 'initiation', label: '1. 项目启动前', description: '明确研究需求，完成方案设计、伦理/机构批准' },
  { key: 'selection', label: '2. 筛选与启动', description: '筛选研究中心，完成Site Initiation（SIV），启动试验' },
  { key: 'conduct', label: '3. 试验进行中', description: '监查进度、数据收集、方案依从性管理' },
  { key: 'data', label: '4. 数据管理', description: '数据核查、清理、锁定（确保数据准确）' },
  { key: 'pv', label: '5. 药物警戒', description: 'SAE/SUSAR收集、评估、报告（及时响应安全风险）' },
  { key: 'closeout', label: '6. 试验关闭与总结', description: '文件归档、数据锁定、总结报告、关闭中心' },
];
