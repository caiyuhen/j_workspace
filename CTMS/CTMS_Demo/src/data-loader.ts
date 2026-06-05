
import type { RoleStageData, Task } from './types';

// Generate some sample data for the matrix
export const MATRIX_DATA: RoleStageData[] = [];

// Helper to add data
const addData = (roleId: string, stageId: string, keyFocus: string, tasks: Partial<Task>[]) => {
  MATRIX_DATA.push({
    roleId,
    stageId,
    keyFocus,
    tasks: tasks.map((t, i) => ({
      id: `${roleId}-${stageId}-${i}`,
      title: t.title || '',
      description: t.description || '',
      ctmsSupport: t.ctmsSupport || '',
      gcpReference: t.gcpReference || '',
      requiredDocs: t.requiredDocs || [],
      ...t
    } as Task))
  });
};

// ==========================================
// 1. 项目经理 (PM)
// ==========================================

// 1.1 项目启动前
addData('pm', 'initiation', '确保方案科学性与伦理合规', [
  { 
    title: '步骤1：项目立项申请', 
    description: '提交项目申请（方案摘要、预算、时间表、预期入组数），关联研究方案、知情同意书（ICF）等文件，提交给伦理委员会（IRB）和申办方管理层审批。',
    ctmsSupport: '项目管理模块（创建项目、上传文件、审批流程）、文档管理（版本控制）。',
    gcpReference: '方案需符合伦理原则（受试者保护、风险效益比），需伦理批准。',
    requiredDocs: ['Protocol', 'ICF', 'Budget']
  },
  { 
    title: '步骤2：研究中心筛选', 
    description: '筛选符合方案要求的研究中心（资质、入组能力、既往经验），评估其IRB批准流程，谈判合同（如CRO或研究预算）。',
    ctmsSupport: '研究中心管理模块（筛选中心、查看资质文件）、合同管理模块（记录合同条款）。',
    gcpReference: '研究中心需具备GCP资质，合同需明确各方责任（如数据SDV、AE/SAE报告要求）。'
  },
  { 
    title: '步骤3：伦理与机构批准', 
    description: '跟踪IRB对方案的审批进展，收集IRB批准函、机构批件（FESP），确认中心资质文件齐全。',
    ctmsSupport: '伦理审查模块（关联IRB审批记录）、文件管理（存储机构批件）。',
    gcpReference: '试验必须获得IRB批准后方可入组受试者（ICH GCP 3.1.2）。',
    requiredDocs: ['IRB Approval', 'FESP']
  }
]);

// 1.2 筛选与启动 (Selection)
addData('pm', 'selection', '中心资质与培训确认', [
  { 
    title: '步骤4：Site Initiation Visit（SIV）安排', 
    description: '协调CRA与研究中心安排SIV，确认SIV时间、参会人员（研究者、机构管理员、CRA），准备SIV材料（方案、CRF、ICF、监查清单）。',
    ctmsSupport: '任务管理模块（创建SIV任务、分配人员）、文件管理（下载SIV材料）。',
    gcpReference: 'SIV需确保研究者理解方案，确保试验顺利启动（ICH GCP 5.19.3）。'
  },
  { 
    title: '步骤5：研究中心培训', 
    description: '通过CTMS向研究中心发送GCP培训材料（线上课程或文档），确认研究者完成培训并获取证书，记录培训状态。',
    ctmsSupport: '培训管理模块（分配培训、记录完成状态）、学员管理（存储培训证书）。',
    gcpReference: '所有参与试验的人员需完成GCP培训（ICH GCP 2.8）。',
    requiredDocs: ['GCP Certificate']
  }
]);

// 1.3 试验进行中 (Conduct)
addData('pm', 'conduct', '进度监控与偏差管理', [
  { 
    title: '步骤6：进度监控', 
    description: '通过CTMS仪表盘查看各中心的入组进度（vs 目标）、数据完整性（EDC填写率）、AE/SAE发生率，识别高风险中心（如入组滞后、数据质量差），调整监查计划。',
    ctmsSupport: '仪表盘（可视化进度、数据质量、风险指标）、项目管理（更新进度）。',
    gcpReference: '定期监控试验进展，及时解决偏差（如入组不足）（ICH GCP 5.18.3）。'
  },
  { 
    title: '步骤7：偏差管理', 
    description: '收集CRA、DM提交的偏差（如数据缺失、方案偏离），分配给相关人员（如研究者、DM）解决，跟踪解决进度，记录根本原因。',
    ctmsSupport: '偏差跟踪模块（创建偏差、分配任务、设置截止日期）、根本原因分析工具（RCA）。',
    gcpReference: '偏差需及时记录、调查和纠正（ICH GCP 1.5）。'
  }
]);

// 1.4 数据管理与统计 (Data)
addData('pm', 'data', '数据与统计方案确认', [
  { 
    title: '步骤8：数据管理计划确认', 
    description: '确认DM的数据管理计划（DMP），包括CRF设计、数据核查规则、Edc（电子数据采集）系统对接，确保DMP符合方案和监管要求。',
    ctmsSupport: '数据管理模块（上传DMP、关联方案）。',
    gcpReference: 'DMP需预先定义（ICH E6 R2 5.5.1）。',
    requiredDocs: ['DMP']
  },
  { 
    title: '步骤9：统计方案审批', 
    description: '审核统计师的统计方案（SAP），确认分析集（全集、符合方案集、可评价集）、统计方法（如ITT/PP分析），提交申办方审批。',
    ctmsSupport: '文档管理（存储SAP）、审批流程（关联申办方PI）。',
    gcpReference: 'SAP需预先定义分析策略（ICH E9 2.1）。',
    requiredDocs: ['SAP']
  }
]);

// 1.6 试验关闭 (Closeout)
addData('pm', 'closeout', '文件归档与总结', [
  { 
    title: '步骤10：文件归档准备', 
    description: '收集所有试验文件（方案、CRF、监查报告、伦理批件、AE/SAE报告），检查文件完整性（是否齐全、版本正确），准备归档（如申办方存档、监管机构提交）。',
    ctmsSupport: '文档管理（文件清单、版本检查）、存档模块（生成归档报告）。',
    gcpReference: '试验文件需完整保存至试验结束后5年（ICH GCP 8.3）。'
  },
  { 
    title: '步骤11：关闭中心', 
    description: '通知研究中心关闭账户，确认所有数据（EDC）、报告（AE/SAE、监查）已提交，解决剩余问题（如未完成的访视）。',
    ctmsSupport: '任务管理（创建关闭任务）、研究中心管理（更新中心状态）。',
    gcpReference: '关闭中心前需确认所有试验活动完成（ICH GCP 8.2）。'
  }
]);


// ==========================================
// 2. 临床监查员 (CRA)
// ==========================================

// 2.2 筛选与启动 (CRA)
addData('cra', 'selection', '现场核查与启动', [
  { 
    title: '中心筛选 (SSU)', 
    description: 'Site Selection Visit - 评估中心设施与人员',
    ctmsSupport: '研究中心管理模块',
    gcpReference: '评估研究者是否有足够的时间和资源 (ICH GCP 4.2)'
  },
  { 
    title: '收集首批必备文件', 
    description: '收集CV, License, Lab Cert等',
    ctmsSupport: '文件管理模块',
    requiredDocs: ['CV', 'Medical License', 'Lab Cert'] 
  },
  { 
    title: '中心启动访视 (SIV)', 
    description: 'Site Initiation Visit - 确保团队培训到位', 
    ctmsSupport: '访视管理模块',
    requiredDocs: ['SIV Report'],
    gcpReference: '确保所有人员熟悉方案 (ICH GCP 5.18)'
  }
]);

// 2.3 试验进行中 (Conduct)
addData('cra', 'conduct', '现场监查与方案依从性', [
  { 
    title: '步骤1：监查计划查看', 
    description: '通过CTMS项目管理模块查看分配的监查计划（时间、中心、监查重点，如入组率、数据SDV、AE/SAE报告），准备监查材料（方案、CRF、知情同意书）。',
    ctmsSupport: '监查计划模块（查看任务）、文件管理（下载材料）。',
    gcpReference: '监查需覆盖所有关键流程（如受试者招募、数据记录）（ICH GCP 5.18.1）。'
  },
  { 
    title: '步骤2：Site Monitoring Visit（SMV）执行', 
    description: '核查研究中心资质；核对受试者数据（SDV）；检查方案依从性；记录发现（监查报告）。',
    ctmsSupport: '监查报告模块（填写报告、关联偏差）、EDC集成（实时数据查看）。',
    gcpReference: '监查需关注受试者权益和数据可靠性（ICH GCP 5.18.2）。',
    requiredDocs: ['Monitoring Report']
  },
  { 
    title: '步骤3：偏差跟进', 
    description: '跟踪监查报告中提出的问题（如数据缺失），联系研究者或DM解决，确认问题关闭（如补充数据）。',
    ctmsSupport: '任务管理（查看偏差状态）、消息通知（提醒解决）。',
    gcpReference: '偏差需及时纠正（ICH GCP 1.5）。'
  },
  {
    title: '步骤4：AE/SAE收集',
    description: '从研究者处收集AE/SAE报告（如受试者不良事件描述、严重性、因果关系），上传至CTMS药物警戒模块。',
    ctmsSupport: '药物警戒模块（上传AE/SAE报告、关联受试者信息）。',
    gcpReference: 'AE/SAE需及时记录（ICH E2A 4.1）。' 
  },
  {
    title: '步骤5：SUSAR报告',
    description: '若AE/SAE为严重且非预期（SUSAR），需在24小时内（ICH E2A 4.2）提交给申办方PV，通过CTMS记录报告状态（如“已提交”“待审批”）。',
    ctmsSupport: '药物警戒模块（SUSAR模板、报告状态跟踪）。',
    gcpReference: 'SUSAR需快速报告（ICH E2A 4.2）。'
  }
]);

// 2.6 Closeout (CRA)
addData('cra', 'closeout', '中心关闭与归档', [
  { 
    title: '中心关闭访视 (COV)', 
    description: '药品销毁，文件归档', 
    ctmsSupport: '访视管理模块',
    requiredDocs: ['COV Report'],
    gcpReference: '确认所有数据已收集，药品已处理'
  }
]);


// ==========================================
// 3. 数据管理专员 (DM)
// ==========================================

// 3.3 试验进行中 (Conduct)
addData('dm', 'conduct', '数据核查与清理', [
  { 
    title: '步骤1：数据接收', 
    description: '从EDC/CTMS导出入口数据，确认数据格式正确，记录导出时间。',
    ctmsSupport: '数据管理模块（导出数据、格式验证）。',
    gcpReference: '数据需可追溯（ICH GCP 8.2）。'
  },
  { 
    title: '步骤2：数据核查执行', 
    description: '运行逻辑检查，标记异常数据，创建偏差（CTMS偏差模块），告知CRA和研究者。',
    ctmsSupport: '数据核查工具（逻辑检查、偏差标记）、偏差跟踪（分配任务）。',
    gcpReference: '数据需完整、准确（ICH GCP 5.5.1）。'
  },
  { 
    title: '步骤3：偏差解决', 
    description: '联系CRA或研究者解决偏差，跟踪解决进度，确认偏差关闭。',
    ctmsSupport: '任务管理（查看偏差状态）、消息通知。',
    gcpReference: '偏差需及时纠正（ICH GCP 1.5）。'
  }
]);

// 3.4 数据管理与统计 (Data)
addData('dm', 'data', '数据锁定与提交', [
  { 
    title: '步骤4：数据清理', 
    description: '解决所有偏差后，清理数据，确保数据无重大偏差。',
    ctmsSupport: '数据清理工具（数据修复、删除）。',
    gcpReference: '数据锁定前需完成清理（ICH GCP 8.3）。'
  },
  { 
    title: '步骤5：数据锁定', 
    description: '生成数据锁定报告，提交给PM和统计师，确认锁定。',
    ctmsSupport: '数据锁定工具（锁定数据、生成报告）。',
    gcpReference: '数据锁定需签核（ICH GCP 8.3）。',
    requiredDocs: ['DB Lock Report']
  },
  { 
    title: '步骤6：数据提交', 
    description: '将锁定数据导出，提交给统计师（CTMS统计模块），关联SAP。',
    ctmsSupport: '数据导出工具（锁定数据提交）、统计模块（关联SAP）。',
    gcpReference: '数据需用于统计分析（ICH E9 2.1）。'
  }
]);


// ==========================================
// 4. 统计师 (Stat)
// ==========================================

// 4.1 项目启动前 (Initiation)
addData('stat', 'initiation', '统计学设计合理性', [
  { title: '计算样本量', description: '基于主要终点 (Primary Endpoint)', gcpReference: 'ICH E9' },
  { title: '制定统计分析计划 (SAP) 初稿', description: '' }
]);

// 4.4 数据管理与统计
addData('stat', 'data', '数据分析与报告', [
  { 
    title: '步骤1：统计方案审批', 
    description: '审核SAP，确认分析集、统计方法、alpha值，提交申办方PI审批。',
    ctmsSupport: '文档管理（SAP版本控制）、审批流程（关联PI）。',
    gcpReference: 'SAP需预先定义（ICH E9 2.1）。',
    requiredDocs: ['Approved SAP']
  },
  { 
    title: '步骤2：数据分析', 
    description: '从CTMS统计模块提取锁定数据，运行统计分析（如描述性统计、假设检验），生成统计输出。',
    ctmsSupport: '统计工具（集成SAS/R/SPSS，可视化输出）、数据提取工具（锁定数据访问）。',
    gcpReference: '分析需基于锁定数据（ICH GCP 8.3）。'
  },
  { 
    title: '步骤3：统计报告生成', 
    description: '编写统计分析报告（SAR），包括方法、结果、结论，关联SAP和锁定数据。',
    ctmsSupport: '报告模块（生成SAR、关联文档）。',
    gcpReference: '报告需清晰、准确（ICH E9 2.4）。',
    requiredDocs: ['SAR']
  }
]);


// ==========================================
// 5. 药物警戒专员 (PV)
// ==========================================

// 5.3 试验进行中 (Conduct)
addData('pv', 'conduct', 'AE/SAE/SUSAR收集与评估', [
  { 
    title: '步骤1：AE/SAE数据收集', 
    description: '从EDC/研究中心接收AE/SAE报告，确认数据完整性。',
    ctmsSupport: '药物警戒模块（AE/SAE模板、数据集成）、MedDRA编码（集成编码工具）。',
    gcpReference: 'AE/SAE需及时记录（ICH E2A 4.1）。'
  },
  { 
    title: '步骤2：AE/SAE评估', 
    description: '评估AE/SAE与试验药物的因果关系，判断是否为SUSAR。',
    ctmsSupport: '药物警戒模块（因果关系评估工具、SUSAR识别）。',
    gcpReference: 'SUSAR需快速报告（ICH E2A 4.2）。'
  }
]);

// 5.5 药物警戒管理 (PV Stage)
addData('pv', 'pv', '安全性报告与更新', [
  { 
    title: '步骤3：SUSAR报告', 
    description: '填写监管机构要求的SUSAR报告，提交给IRB和监管机构，记录提交状态。',
    ctmsSupport: '药物警戒模块（报告模板、提交流程）、监管机构管理（关联审批状态）。',
    gcpReference: 'SUSAR需在24小时内报告（ICH E2A 4.2）。',
    requiredDocs: ['SUSAR Report']
  },
  { 
    title: '步骤4：年度安全性更新报告', 
    description: '定期汇总AE/SAE数据，生成年度安全性更新报告（DSUR），提交给监管机构。',
    ctmsSupport: '药物警戒模块（DSUR模板、数据汇总）、报告模块（生成DSUR）。',
    gcpReference: 'DSUR需包含所有AE/SAE数据（ICH E2C 4.1）。',
    requiredDocs: ['DSUR']
  }
]);


// ==========================================
// 6. 质量保证专员 (QA)
// ==========================================

// 6.1 项目启动前 (Audit Planning)
addData('qa', 'initiation', '合规风险评估与计划', [
  { 
    title: '步骤1：审计计划制定', 
    description: '根据项目风险（如入组率低、数据质量差）和GCP要求，制定审计计划（如选择高风险中心、CRO），关联方案和监管要求。',
    ctmsSupport: '质量保证模块（审计计划工具、风险评分）。',
    gcpReference: '审计需覆盖所有关键流程（ICH GCP 5.18.1）。',
    requiredDocs: ['Audit Plan']
  }
]);

// 6.3 试验进行中 (Conduct)
addData('qa', 'conduct', '审计执行与整改', [
  { 
    title: '步骤2：审计执行', 
    description: '进行现场/远程审计，核对CTMS中的文件（如监查报告、培训记录、伦理批件），检查合规性，记录发现（如“培训记录缺失”）。',
    ctmsSupport: '质量保证模块（审计报告、不符合项记录）。',
    gcpReference: '审计需客观（ICH GCP 5.18.4）。',
    requiredDocs: ['Audit Report']
  },
  { 
    title: '步骤3：整改跟踪 (CAPA)', 
    description: '分配不符合项给相关人员（如研究中心、PM），设置截止日期，跟踪整改进度（如“培训记录已补充”）。',
    ctmsSupport: '任务管理（分配不符合项、跟踪状态）。',
    gcpReference: '不符合项需及时纠正（ICH GCP 1.5）。'
  },
  { 
    title: '步骤4：定期合规检查', 
    description: '通过CTMS仪表盘监控GCP培训状态、伦理批准状态、监查计划执行率，生成合规报告。',
    ctmsSupport: '仪表盘（合规指标可视化）、报表模块（合规报告）。',
    gcpReference: '需定期检查合规性（ICH GCP 5.19.1）。'
  }
]);


// ==========================================
// 7. 研究者/机构管理员 (Site)
// ==========================================

// 7.2 筛选与启动 (Selection)
addData('site', 'selection', '方案接收与培训', [
  { 
    title: '步骤1：方案接收与培训', 
    description: '从CTMS接收方案、CRF、ICF等材料，完成GCP培训（CTMS培训模块），获取证书。',
    ctmsSupport: '研究中心模块（接收文件）、培训管理（完成培训）。',
    gcpReference: '研究者需理解方案（ICH GCP 4.1.2）。',
    requiredDocs: ['Protocol Training Log']
  }
]);

// 7.3 试验进行中 (Conduct)
addData('site', 'conduct', '受试者管理与数据记录', [
  { 
    title: '步骤2：受试者管理', 
    description: '筛选符合纳入排除标准的受试者，获取知情同意，入组受试者（CTMS录入入选信息）。',
    ctmsSupport: '受试者管理模块（入组登记、ICF签署）。',
    gcpReference: '知情同意需自愿、知情（ICH GCP 4.8.10）。',
    requiredDocs: ['Signed ICF']
  },
  { 
    title: '步骤3：数据记录', 
    description: '按方案收集数据（如实验室结果、访视记录），录入EDC/CTMS，保存源数据（SD）。',
    ctmsSupport: 'EDC集成（数据录入）、文件管理（存储SD）。',
    gcpReference: '源数据需真实、可追溯（ICH GCP 8.2）。'
  },
  { 
    title: '步骤4：AE/SAE报告', 
    description: '报告AE/SAE/SUSAR（CTMS药物警戒模块），确保报告及时、准确（如24小时内报告SUSAR）。',
    ctmsSupport: '药物警戒模块（AE/SAE报告模板）。',
    gcpReference: 'AE/SAE需及时报告（ICH E2A 4.1）。'
  }
]);


// ==========================================
// 8. 伦理委员会 (IRB)
// ==========================================

// 8.1 项目启动前 (Initiation)
addData('irb', 'initiation', '伦理审查与批准', [
  { 
    title: '步骤1：方案接收', 
    description: '收到申办方的试验方案、ICF、研究者手册等材料，录入CTMS，记录收到时间。',
    ctmsSupport: '伦理审查模块（接收文件、时间戳）。',
    gcpReference: 'IRB需审查所有试验材料（ICH GCP 3.1）。'
  },
  { 
    title: '步骤2：方案评估', 
    description: '评估方案的伦理合规性（如受试者保护措施、风险效益比、知情同意流程），判断是否批准。',
    ctmsSupport: '伦理审查模块（评估工具、意见记录）。',
    gcpReference: '方案需保护受试者（ICH GCP 3.2）。'
  },
  { 
    title: '步骤3：批准通知', 
    description: '通过CTMS向申办方发送批准通知（或修改意见），更新申办方CTMS中的IRB状态。',
    ctmsSupport: '伦理审查模块（批准通知、状态更新）。',
    gcpReference: '需书面通知申办方（ICH GCP 3.1.2）。',
    requiredDocs: ['IRB Approval Letter']
  }
]);

// 8.3 试验进行中 (Conduct/Oversight)
addData('irb', 'conduct', '持续监督与审查', [
  { 
    title: '步骤4：年度报告接收', 
    description: '接收申办方的年度安全性更新报告（DSUR），评估试验是否继续开展合理。',
    ctmsSupport: '伦理审查模块（DSUR接收、评估记录）。',
    gcpReference: '需定期监督试验进展（ICH GCP 3.1.4）。'
  },
  { 
    title: '步骤5：修订审查', 
    description: '若方案或ICF有修订（如增加风险），接收修订材料，重新审查，确认批准。',
    ctmsSupport: '伦理审查模块（修订材料接收、重新审查）。',
    gcpReference: '修订需重新审查（ICH GCP 4.2.5）。'
  }
]);
