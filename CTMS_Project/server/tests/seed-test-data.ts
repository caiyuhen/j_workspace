/**
 * CTMS+EDC v4.0 测试数据生成脚本
 * 生成有完整业务逻辑关联的测试数据
 *
 * 数据关系：
 * Organization → User(角色) → Project → Site → Subject → Visit → CrfData → DataQuery
 *                                              → Subject → AdverseEvent → SaeReport
 *                                    → Timesheet → TimesheetEntry
 *                                    → FinancialIncome / FinancialExpense
 *                                    → MonitoringPlan → MonitoringVisit
 *                                    → EdcTemplate → CrfForm
 *                                    → WorkflowDefinition → WorkflowInstance → WorkflowTask
 */

import { PrismaClient } from '@prisma/client';
<<<<<<< HEAD
<<<<<<< HEAD
import * as bcrypt from 'bcryptjs';
=======
import * as bcrypt from 'bcrypt';
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
=======
import * as bcrypt from 'bcrypt';
>>>>>>> origin/main

const prisma = new PrismaClient();

// ========== 工具函数 ==========
async function hashPwd(password: string): Promise<string> {
  return bcrypt.hash(password, 10);
}

function daysFromNow(days: number): Date {
  const d = new Date();
  d.setDate(d.getDate() + days);
  return d;
}

function daysAgo(days: number): Date {
  return daysFromNow(-days);
}

// ========== 主函数 ==========
async function main() {
  console.log('\n🌱 CTMS+EDC v4.0 测试数据生成开始...\n');

  // ===== STEP 1: 组织机构 =====
  console.log('📦 创建组织机构...');
  const orgSponsor = await prisma.organization.upsert({
    where: { orgCode: 'ORG-SPONSOR-001' },
    update: {},
    create: {
      orgCode: 'ORG-SPONSOR-001',
      orgName: '华泰生物医药集团',
      orgType: 'sponsor',
      contactEmail: 'contact@huatai-bio.com',
      contactPhone: '021-88888888',
      address: '上海市浦东新区张江高科技园区博云路2号',
      description: '专注于创新药物研发与临床试验管理',
    },
  });

  const orgCro = await prisma.organization.upsert({
    where: { orgCode: 'ORG-CRO-001' },
    update: {},
    create: {
      orgCode: 'ORG-CRO-001',
      orgName: '康达临床研究机构',
      orgType: 'cro',
      contactEmail: 'info@kangda-cro.com',
      contactPhone: '010-66666666',
      address: '北京市海淀区中关村科技园区',
      description: 'A级资质CRO机构，专业从事临床试验管理',
    },
  });

  const orgSite1 = await prisma.organization.upsert({
    where: { orgCode: 'ORG-SITE-001' },
    update: {},
    create: {
      orgCode: 'ORG-SITE-001',
      orgName: '北京协和医学院附属协和医院',
      orgType: 'site',
      contactEmail: 'research@pumch.cn',
      contactPhone: '010-69152114',
      address: '北京市东城区帅府园1号',
      description: '国家临床研究中心，三级甲等综合医院',
    },
  });

  const orgSite2 = await prisma.organization.upsert({
    where: { orgCode: 'ORG-SITE-002' },
    update: {},
    create: {
      orgCode: 'ORG-SITE-002',
      orgName: '上海瑞金医院',
      orgType: 'site',
      contactEmail: 'clinical@rjh.com.cn',
      contactPhone: '021-64370045',
      address: '上海市瑞金二路197号',
      description: '国家临床医学研究中心（代谢病），三级甲等综合医院',
    },
  });

  console.log('  ✅ 组织机构创建完成（申办方、CRO、2个研究中心）');

  // ===== STEP 2: 角色获取 =====
  const roles = await prisma.role.findMany({
    where: { roleCode: { in: ['SUPER_ADMIN', 'SPONSOR', 'PI', 'CRA', 'CRC', 'DM', 'PM'] } },
  });
  const roleMap = Object.fromEntries(roles.map(r => [r.roleCode, r]));

  // ===== STEP 3: 用户 =====
  console.log('👤 创建测试用户...');
  const users: Record<string, any> = {};

  const userDefs = [
    { username: 'zhangsan', email: 'zhangsan@huatai-bio.com', displayName: '张三（项目经理）', roleCode: 'PM', org: '华泰生物医药集团', title: '高级项目经理', dept: '临床研究部' },
    { username: 'lisi', email: 'lisi@pumch.cn', displayName: '李四（主要研究者）', roleCode: 'PI', org: '北京协和医院', title: '主任医师', dept: '内科' },
    { username: 'wangwu', email: 'wangwu@kangda-cro.com', displayName: '王五（临床监查员）', roleCode: 'CRA', org: '康达CRO', title: '高级CRA', dept: '监查部' },
    { username: 'zhaoliu', email: 'zhaoliu@pumch.cn', displayName: '赵六（临床协调员）', roleCode: 'CRC', org: '北京协和医院', title: 'CRC协调员', dept: '临床研究科' },
    { username: 'sunqi', email: 'sunqi@huatai-bio.com', displayName: '孙七（数据管理员）', roleCode: 'DM', org: '华泰生物医药集团', title: '数据经理', dept: '数据管理部' },
    { username: 'liuyi', email: 'liuyi@rjh.com.cn', displayName: '刘一（上海研究者）', roleCode: 'PI', org: '上海瑞金医院', title: '副主任医师', dept: '内分泌科' },
    { username: 'chenba', email: 'chenba@rjh.com.cn', displayName: '陈八（上海CRC）', roleCode: 'CRC', org: '上海瑞金医院', title: 'CRC', dept: '临床研究科' },
    { username: 'linjiuj', email: 'linjiu@kangda-cro.com', displayName: '林九（申办方代表）', roleCode: 'SPONSOR', org: '华泰生物医药集团', title: '临床研究总监', dept: '临床运营部' },
  ];

  for (const u of userDefs) {
    const existUser = await prisma.user.findUnique({ where: { username: u.username } });
    if (!existUser) {
      const created = await prisma.user.create({
        data: {
          username: u.username,
          email: u.email,
          displayName: u.displayName,
          passwordHash: await hashPwd('Test@2024'),
          phone: `138${Math.floor(Math.random() * 90000000 + 10000000)}`,
          title: u.title,
          department: u.dept,
          organization: u.org,
          status: 'active',
        },
      });
      users[u.username] = created;

      // 分配角色
      if (roleMap[u.roleCode]) {
        const existingRole = await prisma.userRole.findFirst({
          where: { userId: created.id, roleId: roleMap[u.roleCode].id, projectId: null, siteId: null },
        });
        if (!existingRole) {
          await prisma.userRole.create({
            data: { userId: created.id, roleId: roleMap[u.roleCode].id },
          });
        }
      }
    } else {
      users[u.username] = existUser;
    }
  }

  // 获取 admin 用户
  const adminUser = await prisma.user.findUnique({ where: { username: 'admin' } });
  if (adminUser) users['admin'] = adminUser;

  console.log(`  ✅ 创建/获取了 ${Object.keys(users).length} 个用户`);

  // ===== STEP 4: 供应商 =====
  console.log('🏢 创建供应商数据...');
  const vendorLab = await prisma.vendor.upsert({
    where: { vendorCode: 'VND-LAB-001' },
    update: {},
    create: {
      vendorCode: 'VND-LAB-001',
      vendorName: '华检医学检验所',
      vendorType: 'lab',
      contactPerson: '赵经理',
      contactPhone: '021-12345678',
      contactEmail: 'lab@huajian.com',
      address: '上海市闵行区',
      rating: 4.8,
      status: 'active',
      qualification: { certified: true, iso15189: true, capAccredited: false },
      createdBy: users['admin']?.id || 'system',
    },
  });

  const vendorIt = await prisma.vendor.upsert({
    where: { vendorCode: 'VND-IT-001' },
    update: {},
    create: {
      vendorCode: 'VND-IT-001',
      vendorName: '临证科技（EDC系统服务商）',
      vendorType: 'it',
      contactPerson: '钱总监',
      contactPhone: '010-87654321',
      contactEmail: 'support@linjian-tech.com',
      address: '北京市朝阳区',
      rating: 4.5,
      status: 'active',
      qualification: { cfr11Compliant: true, iso27001: true },
      createdBy: users['admin']?.id || 'system',
    },
  });

  console.log('  ✅ 供应商创建完成');

  // ===== STEP 5: 合同 =====
  console.log('📄 创建合同数据...');
  await prisma.contract.upsert({
    where: { contractCode: 'CTR-2024-001' },
    update: {},
    create: {
      contractCode: 'CTR-2024-001',
      contractName: '华泰-康达CRO服务合同',
      contractType: 'cro_service',
      vendorId: vendorIt.id,  // 使用 Vendor 记录的 ID
      amount: 5000000,
      currency: 'CNY',
      startDate: daysAgo(180),
      endDate: daysFromNow(365),
      signStatus: 'signed',
      description: '康达CRO为华泰公司II期临床试验提供监查、协调、数据管理等全面服务',
      createdBy: users['admin']?.id || 'system',
    },
  });

  console.log('  ✅ 合同数据创建完成');

  // ===== STEP 6: 项目 =====
  console.log('🔬 创建临床试验项目...');
  const projectHT001 = await prisma.project.upsert({
    where: { projectCode: 'HT-2024-001' },
    update: {},
    create: {
      projectCode: 'HT-2024-001',
      projectName: '华泰HT-2024-001号化合物治疗2型糖尿病的随机双盲平行对照II期临床试验',
      studyType: 'interventional',
      therapeuticArea: '内分泌代谢疾病',
      indication: '2型糖尿病',
      blindType: 'double_blind',
      phase: 'phase_ii',
      sampleSize: 240,
      totalBudget: 12000000,
      startDate: daysAgo(120),
      endDate: daysFromNow(450),
      status: 'recruiting',
      description: '评估HT-2024-001化合物与安慰剂相比，治疗成年2型糖尿病患者的有效性和安全性',
      createdBy: users['admin']?.id || users['zhangsan']?.id || 'system',
    },
  });

  const projectHT002 = await prisma.project.upsert({
    where: { projectCode: 'HT-2024-002' },
    update: {},
    create: {
      projectCode: 'HT-2024-002',
      projectName: '华泰HT-2024-002抗肿瘤新药I期剂量爬坡研究',
      studyType: 'interventional',
      therapeuticArea: '肿瘤学',
      indication: '晚期实体瘤',
      blindType: 'open',
      phase: 'phase_i',
      sampleSize: 30,
      totalBudget: 3500000,
      startDate: daysAgo(30),
      endDate: daysFromNow(300),
      status: 'active',
      description: '评估新型靶向抗肿瘤化合物在晚期实体瘤患者中的安全性、耐受性和药代动力学特征',
      createdBy: users['admin']?.id || users['zhangsan']?.id || 'system',
    },
  });

  console.log('  ✅ 项目创建完成（2个研究项目）');

  // ===== STEP 7: 里程碑 =====
  console.log('📅 创建项目里程碑...');
  const milestones = [
    { projectId: projectHT001.id, milestoneName: '研究启动', milestoneType: 'project_start', plannedDate: daysAgo(120), actualDate: daysAgo(115), status: 'completed' },
    { projectId: projectHT001.id, milestoneName: '首中心启动', milestoneType: 'site_init', plannedDate: daysAgo(90), actualDate: daysAgo(85), status: 'completed' },
    { projectId: projectHT001.id, milestoneName: '首例受试者入组', milestoneType: 'first_patient', plannedDate: daysAgo(60), actualDate: daysAgo(55), status: 'completed' },
    { projectId: projectHT001.id, milestoneName: '末例受试者完成', milestoneType: 'last_patient', plannedDate: daysFromNow(300), status: 'planned' },
    { projectId: projectHT001.id, milestoneName: '数据库锁定', milestoneType: 'db_lock', plannedDate: daysFromNow(330), status: 'planned' },
    { projectId: projectHT002.id, milestoneName: '研究启动', milestoneType: 'project_start', plannedDate: daysAgo(30), actualDate: daysAgo(28), status: 'completed' },
    { projectId: projectHT002.id, milestoneName: '首例受试者入组', milestoneType: 'first_patient', plannedDate: daysAgo(10), status: 'in_progress' },
  ];

  for (const m of milestones) {
    const existing = await prisma.milestone.findFirst({ where: { projectId: m.projectId, milestoneName: m.milestoneName } });
    if (!existing) {
      await prisma.milestone.create({
        data: {
          projectId: m.projectId,
          milestoneName: m.milestoneName,
          milestoneType: m.milestoneType as any,
          plannedDate: new Date(m.plannedDate),
          actualDate: m.actualDate ? new Date(m.actualDate) : null,
          status: m.status || 'planned',
        },
      });
    }
  }
  console.log('  ✅ 里程碑创建完成');

  // ===== STEP 8: 研究中心 =====
  console.log('🏥 创建研究中心...');
  const siteBeijing = await prisma.site.upsert({
    where: { projectId_siteCode: { projectId: projectHT001.id, siteCode: 'SITE-BJ-001' } },
    update: {},
    create: {
      projectId: projectHT001.id,
      siteCode: 'SITE-BJ-001',
      siteName: '北京协和医院研究中心',
      piUserId: users['lisi']?.id,
      address: '北京市东城区帅府园1号',
      contactPhone: '010-69152114',
      ethicsStatus: 'approved',
      contractStatus: 'signed',
      status: 'active',
    },
  });

  const siteShanghai = await prisma.site.upsert({
    where: { projectId_siteCode: { projectId: projectHT001.id, siteCode: 'SITE-SH-001' } },
    update: {},
    create: {
      projectId: projectHT001.id,
      siteCode: 'SITE-SH-001',
      siteName: '上海瑞金医院研究中心',
      piUserId: users['liuyi']?.id,
      address: '上海市瑞金二路197号',
      contactPhone: '021-64370045',
      ethicsStatus: 'approved',
      contractStatus: 'signed',
      status: 'active',
    },
  });

  // 绑定研究人员到中心
  for (const [userId, role] of [
    [users['lisi']?.id, 'PI'],
    [users['zhaoliu']?.id, 'CRC'],
    [users['wangwu']?.id, 'CRA'],
  ]) {
    if (userId) {
      await prisma.siteStaff.upsert({
        where: { siteId_userId: { siteId: siteBeijing.id, userId: userId as string } },
        update: {},
        create: { siteId: siteBeijing.id, userId: userId as string, roleAtSite: role as string, joinedAt: daysAgo(85), status: 'active' },
      });
    }
  }

  for (const [userId, role] of [
    [users['liuyi']?.id, 'PI'],
    [users['chenba']?.id, 'CRC'],
  ]) {
    if (userId) {
      await prisma.siteStaff.upsert({
        where: { siteId_userId: { siteId: siteShanghai.id, userId: userId as string } },
        update: {},
        create: { siteId: siteShanghai.id, userId: userId as string, roleAtSite: role as string, joinedAt: daysAgo(60), status: 'active' },
      });
    }
  }

  console.log('  ✅ 研究中心创建完成（北京/上海，含人员配置）');

  // ===== STEP 9: 受试者 =====
  console.log('👥 创建受试者数据...');
  const subjectsData = [
    // 北京协和 - 已完成受试者
    { siteId: siteBeijing.id, subjectCode: 'HT001-BJ-001', screeningNumber: 'SCR-BJ-001', status: 'completed', randomNum: 'R001', daysAgo: 55 },
    { siteId: siteBeijing.id, subjectCode: 'HT001-BJ-002', screeningNumber: 'SCR-BJ-002', status: 'ongoing', randomNum: 'R002', daysAgo: 50 },
    { siteId: siteBeijing.id, subjectCode: 'HT001-BJ-003', screeningNumber: 'SCR-BJ-003', status: 'ongoing', randomNum: 'R003', daysAgo: 45 },
    { siteId: siteBeijing.id, subjectCode: 'HT001-BJ-004', screeningNumber: 'SCR-BJ-004', status: 'ongoing', randomNum: null, daysAgo: 40 },
    { siteId: siteBeijing.id, subjectCode: 'HT001-BJ-005', screeningNumber: 'SCR-BJ-005', status: 'discontinued', randomNum: null, daysAgo: 35, disReason: '受试者要求退出' },
    { siteId: siteBeijing.id, subjectCode: 'HT001-BJ-006', screeningNumber: 'SCR-BJ-006', status: 'screening', randomNum: null, daysAgo: 5 },
    // 上海瑞金 - 在组受试者
    { siteId: siteShanghai.id, subjectCode: 'HT001-SH-001', screeningNumber: 'SCR-SH-001', status: 'ongoing', randomNum: 'R101', daysAgo: 48 },
    { siteId: siteShanghai.id, subjectCode: 'HT001-SH-002', screeningNumber: 'SCR-SH-002', status: 'ongoing', randomNum: 'R102', daysAgo: 42 },
    { siteId: siteShanghai.id, subjectCode: 'HT001-SH-003', screeningNumber: 'SCR-SH-003', status: 'enrolled', randomNum: null, daysAgo: 20 },
    { siteId: siteShanghai.id, subjectCode: 'HT001-SH-004', screeningNumber: 'SCR-SH-004', status: 'screening', randomNum: null, daysAgo: 7 },
  ];

  const subjectMap: Record<string, any> = {};
  for (const s of subjectsData) {
    const existing = await prisma.subject.findFirst({ where: { projectId: projectHT001.id, subjectCode: s.subjectCode } });
    const subj = existing || await prisma.subject.create({
      data: {
        projectId: projectHT001.id,
        siteId: s.siteId,
        subjectCode: s.subjectCode,
        screeningNumber: s.screeningNumber,
        enrollmentStatus: s.status as any,
        randomizationNumber: s.randomNum,
        discontinuationReason: (s as any).disReason,
        createdAt: daysAgo(s.daysAgo),
      },
    });
    subjectMap[s.subjectCode] = subj;
  }

  console.log(`  ✅ 受试者创建完成（${Object.keys(subjectMap).length} 例受试者）`);

  // ===== STEP 10: 随机化记录 =====
  console.log('🎲 创建随机化记录...');
  const randomizedSubjects = [
    { subjectCode: 'HT001-BJ-001', treatmentGroup: 'treatment', randomNum: 'R001' },
    { subjectCode: 'HT001-BJ-002', treatmentGroup: 'treatment', randomNum: 'R002' },
    { subjectCode: 'HT001-BJ-003', treatmentGroup: 'placebo', randomNum: 'R003' },
    { subjectCode: 'HT001-SH-001', treatmentGroup: 'treatment', randomNum: 'R101' },
    { subjectCode: 'HT001-SH-002', treatmentGroup: 'placebo', randomNum: 'R102' },
  ];

  for (const r of randomizedSubjects) {
    const subj = subjectMap[r.subjectCode];
    if (subj) {
      await prisma.edcRandomizationRecord.upsert({
        where: { randomizationNumber: r.randomNum },
        update: {},
        create: {
          subjectId: subj.id,
          projectId: projectHT001.id,
          randomizationNumber: r.randomNum,
          treatmentArm: r.treatmentGroup,
          stratifiedFactors: { bmi: 'normal', hba1c: r.treatmentGroup === 'treatment' ? 'high' : 'medium' },
          method: 'block_randomization',
          randomizationDate: daysAgo(parseInt(r.randomNum.replace('R', '').replace('R', '')) < 10 ? 50 : 40),
          randomizedBy: users['sunqi']?.id || users['admin']!.id,
        },
      });
    }
  }

  console.log('  ✅ 随机化记录创建完成');

  // ===== STEP 11: EDC 模板 =====
  console.log('📋 创建CRF模板...');
  const templateVital = await prisma.edcTemplate.upsert({
    where: { templateCode: 'TPL-VITAL-001' },
    update: {
      templateData: {
        fields: [
          { id: 'SYSBP', label: '收缩压(mmHg)', type: 'number', required: true, min: 60, max: 200 },
          { id: 'DIABP', label: '舒张压(mmHg)', type: 'number', required: true, min: 40, max: 130 },
          { id: 'HR', label: '心率(次/分)', type: 'number', required: true, min: 40, max: 180 },
          { id: 'TEMP', label: '体温(℃)', type: 'number', required: true, min: 35, max: 42 },
          { id: 'WEIGHT', label: '体重(kg)', type: 'number', required: true, min: 30, max: 200 },
        ],
      }
    },
    create: {
      templateCode: 'TPL-VITAL-001',
      templateName: '生命体征记录表',
      templateType: 'crf',
      version: '1.0',
      status: 'published',
      isSystemTemplate: true,
      isShared: true,
      templateData: {
        fields: [
          { id: 'SYSBP', label: '收缩压(mmHg)', type: 'number', required: true, min: 60, max: 200 },
          { id: 'DIABP', label: '舒张压(mmHg)', type: 'number', required: true, min: 40, max: 130 },
          { id: 'HR', label: '心率(次/分)', type: 'number', required: true, min: 40, max: 180 },
          { id: 'TEMP', label: '体温(℃)', type: 'number', required: true, min: 35, max: 42 },
          { id: 'WEIGHT', label: '体重(kg)', type: 'number', required: true, min: 30, max: 200 },
        ],
      },
      publishedAt: daysAgo(100),
    },
  });

  const templateHbA1c = await prisma.edcTemplate.upsert({
    where: { templateCode: 'TPL-HBA1C-001' },
    update: {
      templateData: {
        fields: [
          { id: 'HBA1C', label: 'HbA1c(%)', type: 'number', required: true, min: 4, max: 16 },
          { id: 'GLUC', label: '空腹血糖(mmol/L)', type: 'number', required: true, min: 2, max: 30 },
          { id: 'LBDAT', label: '检测日期', type: 'date', required: true },
          { id: 'LBNAM', label: '检测机构', type: 'text', required: true },
        ],
      }
    },
    create: {
      templateCode: 'TPL-HBA1C-001',
      templateName: '糖化血红蛋白检测表',
      templateType: 'lab_result',
      version: '1.0',
      status: 'published',
      projectId: projectHT001.id,
      isSystemTemplate: false,
      isShared: false,
      templateData: {
        fields: [
          { id: 'HBA1C', label: 'HbA1c(%)', type: 'number', required: true, min: 4, max: 16 },
          { id: 'GLUC', label: '空腹血糖(mmol/L)', type: 'number', required: true, min: 2, max: 30 },
          { id: 'LBDAT', label: '检测日期', type: 'date', required: true },
          { id: 'LBNAM', label: '检测机构', type: 'text', required: true },
        ],
      },
      publishedAt: daysAgo(90),
    },
  });

  const templateAe = await prisma.edcTemplate.upsert({
    where: { templateCode: 'TPL-AE-001' },
    update: {
      templateData: {
        fields: [
          { id: 'AETERM', label: '不良事件术语', type: 'text', required: true },
          { id: 'AESTDAT', label: '发生日期', type: 'datetime', required: true },
          { id: 'AESEV', label: '严重程度', type: 'select', options: ['轻度', '中度', '重度'], required: true },
          { id: 'AEREL', label: '因果关系', type: 'select', options: ['无关', '可能无关', '可能有关', '很可能有关', '肯定有关'], required: true },
          { id: 'AEOUT', label: '结局', type: 'select', options: ['痊愈', '好转中', '未痊愈', '死亡', '不明'], required: true },
        ],
      }
    },
    create: {
      templateCode: 'TPL-AE-001',
      templateName: '不良事件记录表',
      templateType: 'ae_report',
      version: '2.0',
      status: 'published',
      isSystemTemplate: true,
      isShared: true,
      templateData: {
        fields: [
          { id: 'AETERM', label: '不良事件术语', type: 'text', required: true },
          { id: 'AESTDAT', label: '发生日期', type: 'datetime', required: true },
          { id: 'AESEV', label: '严重程度', type: 'select', options: ['轻度', '中度', '重度'], required: true },
          { id: 'AEREL', label: '因果关系', type: 'select', options: ['无关', '可能无关', '可能有关', '很可能有关', '肯定有关'], required: true },
          { id: 'AEOUT', label: '结局', type: 'select', options: ['痊愈', '好转中', '未痊愈', '死亡', '不明'], required: true },
        ],
      },
      publishedAt: daysAgo(100),
    },
  });

  console.log('  ✅ CRF模板创建完成（3个模板）');

  // ===== STEP 12: CRF 数据录入 =====
  console.log('📊 创建CRF数据...');
  // CrfData 模型是按字段粒度存储的（每条记录一个字段值）
  const crfEntries = [
    // BJ-001 基线访视 - 生命体征
    { subjectCode: 'HT001-BJ-001', formCode: 'VITAL-BASELINE', fieldCode: 'SYSBP', fieldValue: '136', templateId: templateVital.id, visitType: 'baseline', daysAgo: 55 },
    { subjectCode: 'HT001-BJ-001', formCode: 'VITAL-BASELINE', fieldCode: 'DIABP', fieldValue: '84', templateId: templateVital.id, visitType: 'baseline', daysAgo: 55 },
    { subjectCode: 'HT001-BJ-001', formCode: 'VITAL-BASELINE', fieldCode: 'HR', fieldValue: '76', templateId: templateVital.id, visitType: 'baseline', daysAgo: 55 },
    { subjectCode: 'HT001-BJ-001', formCode: 'VITAL-BASELINE', fieldCode: 'WEIGHT', fieldValue: '72.5', templateId: templateVital.id, visitType: 'baseline', daysAgo: 55 },
    { subjectCode: 'HT001-BJ-001', formCode: 'VITAL-BASELINE', fieldCode: 'TEMP', fieldValue: '36.6', templateId: templateVital.id, visitType: 'baseline', daysAgo: 55 },
    // BJ-001 基线访视 - HbA1c
    { subjectCode: 'HT001-BJ-001', formCode: 'HBA1C-BASELINE', fieldCode: 'HBA1C', fieldValue: '8.2', templateId: templateHbA1c.id, visitType: 'baseline', daysAgo: 55 },
    { subjectCode: 'HT001-BJ-001', formCode: 'HBA1C-BASELINE', fieldCode: 'GLUC', fieldValue: '9.6', templateId: templateHbA1c.id, visitType: 'baseline', daysAgo: 55 },
    { subjectCode: 'HT001-BJ-001', formCode: 'HBA1C-BASELINE', fieldCode: 'LBDAT', fieldValue: daysAgo(55).toISOString(), templateId: templateHbA1c.id, visitType: 'baseline', daysAgo: 55 },
    { subjectCode: 'HT001-BJ-001', formCode: 'HBA1C-BASELINE', fieldCode: 'LBNAM', fieldValue: '北京协和医院检验科', templateId: templateHbA1c.id, visitType: 'baseline', daysAgo: 55 },
    // BJ-001 第12周 - HbA1c（疗效改善）
    { subjectCode: 'HT001-BJ-001', formCode: 'HBA1C-WEEK12', fieldCode: 'HBA1C', fieldValue: '7.1', templateId: templateHbA1c.id, visitType: 'week12', daysAgo: 23 },
    { subjectCode: 'HT001-BJ-001', formCode: 'HBA1C-WEEK12', fieldCode: 'GLUC', fieldValue: '7.8', templateId: templateHbA1c.id, visitType: 'week12', daysAgo: 23 },
    // BJ-002 基线 - 生命体征
    { subjectCode: 'HT001-BJ-002', formCode: 'VITAL-BASELINE', fieldCode: 'SYSBP', fieldValue: '142', templateId: templateVital.id, visitType: 'baseline', daysAgo: 50 },
    { subjectCode: 'HT001-BJ-002', formCode: 'VITAL-BASELINE', fieldCode: 'DIABP', fieldValue: '88', templateId: templateVital.id, visitType: 'baseline', daysAgo: 50 },
    { subjectCode: 'HT001-BJ-002', formCode: 'VITAL-BASELINE', fieldCode: 'WEIGHT', fieldValue: '85.0', templateId: templateVital.id, visitType: 'baseline', daysAgo: 50 },
    // BJ-002 第12周 - HbA1c（异常高值，引发质疑）
    { subjectCode: 'HT001-BJ-002', formCode: 'HBA1C-WEEK12', fieldCode: 'HBA1C', fieldValue: '14.5', templateId: templateHbA1c.id, visitType: 'week12', daysAgo: 16 },
    { subjectCode: 'HT001-BJ-002', formCode: 'HBA1C-WEEK12', fieldCode: 'GLUC', fieldValue: '18.2', templateId: templateHbA1c.id, visitType: 'week12', daysAgo: 16 },
    // SH-001 基线 - 生命体征
    { subjectCode: 'HT001-SH-001', formCode: 'VITAL-BASELINE', fieldCode: 'SYSBP', fieldValue: '138', templateId: templateVital.id, visitType: 'baseline', daysAgo: 48 },
    { subjectCode: 'HT001-SH-001', formCode: 'VITAL-BASELINE', fieldCode: 'WEIGHT', fieldValue: '78.0', templateId: templateVital.id, visitType: 'baseline', daysAgo: 48 },
    // AE 记录 (BJ-001)
    { subjectCode: 'HT001-BJ-001', formCode: 'AE-001', fieldCode: 'AETERM', fieldValue: '轻度头晕', templateId: templateAe.id, visitType: 'unscheduled', daysAgo: 20 },
    { subjectCode: 'HT001-BJ-001', formCode: 'AE-001', fieldCode: 'AESTDAT', fieldValue: daysAgo(22).toISOString(), templateId: templateAe.id, visitType: 'unscheduled', daysAgo: 20 },
    { subjectCode: 'HT001-BJ-001', formCode: 'AE-001', fieldCode: 'AESEV', fieldValue: '轻度', templateId: templateAe.id, visitType: 'unscheduled', daysAgo: 20 },
    { subjectCode: 'HT001-BJ-001', formCode: 'AE-001', fieldCode: 'AEREL', fieldValue: '可能有关', templateId: templateAe.id, visitType: 'unscheduled', daysAgo: 20 },
    { subjectCode: 'HT001-BJ-001', formCode: 'AE-001', fieldCode: 'AEOUT', fieldValue: '痊愈', templateId: templateAe.id, visitType: 'unscheduled', daysAgo: 20 },
  ];

  for (const e of crfEntries) {
    const subj = subjectMap[e.subjectCode];
    if (!subj) continue;
    await prisma.crfData.create({
      data: {
        subjectId: subj.id,
        formId: e.templateId,
        formCode: e.formCode,
        fieldId: `${e.templateId}-${e.fieldCode}`,
        fieldCode: e.fieldCode,
        fieldValue: e.fieldValue,
        formData: { visitType: e.visitType, value: parseFloat(e.fieldValue) },
        enteredBy: subj.siteId === siteBeijing.id ? (users['zhaoliu']?.id || users['admin']!.id) : (users['chenba']?.id || users['admin']!.id),
        enteredAt: daysAgo(e.daysAgo),
        updatedAt: daysAgo(e.daysAgo),
      },
    });
  }
  console.log('  ✅ CRF数据录入完成');

  // ===== STEP 13: 数据质疑 =====
  console.log('❓ 创建数据质疑...');
  const bjSubj002 = subjectMap['HT001-BJ-002'];
  const shSubj001 = subjectMap['HT001-SH-001'];

  const queries = [
    // 北京-BJ-002 HbA1c 异常值质疑
    {
      subjectId: bjSubj002?.id,
      title: 'HbA1c 值超出正常范围',
      description: '第12周随访HbA1c值为14.5%，超出方案允许的最高值(12%)，请核实是否录入错误，并提供原始实验室报告扫描件。',
      queryType: 'data_discrepancy',
      priority: 'high',
      status: 'open',
      assignedTo: users['zhaoliu']?.id,
    },
    // 北京-BJ-002 空腹血糖异常
    {
      subjectId: bjSubj002?.id,
      title: '空腹血糖值超出方案允许范围',
      description: '第12周空腹血糖18.2 mmol/L，请确认是否严格按方案执行空腹要求（禁食≥8小时），并提供实验室原始报告。',
      queryType: 'protocol_deviation',
      priority: 'high',
      status: 'open',
      assignedTo: users['zhaoliu']?.id,
    },
    // 上海-SH-001 访视窗口质疑
    {
      subjectId: shSubj001?.id,
      title: '访视日期超出方案允许窗口期',
      description: '基线访视日期距入组日期超过方案规定的±3天窗口期，请提供说明。',
      queryType: 'protocol_deviation',
      priority: 'medium',
      status: 'answered',
      assignedTo: users['chenba']?.id,
    },
    // 缺失数据质疑
    {
      subjectId: bjSubj002?.id,
      title: '体格检查数据缺失',
      description: '第4周随访缺少体格检查记录（生命体征表），请补充录入或说明未做原因。',
      queryType: 'missing_data',
      priority: 'medium',
      status: 'open',
      assignedTo: users['zhaoliu']?.id,
    },
  ];

  for (const q of queries) {
    if (!q.subjectId) continue;
    await prisma.dataQuery.create({
      data: {
        projectId: projectHT001.id,
        subjectId: q.subjectId,
        queryType: q.queryType as any,
        priority: q.priority as any,
        title: q.title,
        description: q.description,
        status: q.status as any,
        assignedTo: q.assignedTo,
        raisedBy: users['sunqi']?.id || users['admin']!.id,
        createdAt: daysAgo(10),
      },
    });
  }
  console.log('  ✅ 数据质疑创建完成（4条质疑）');

  // ===== STEP 14: AE/SAE 记录 =====
  console.log('⚠️  创建AE/SAE安全性记录...');
  const bjSubj001 = subjectMap['HT001-BJ-001'];

  const ae1 = await prisma.adverseEvent.create({
    data: {
      projectId: projectHT001.id,
      subjectId: bjSubj001.id,
      siteId: siteBeijing.id,
      reportCode: `AE-BJ001-${Date.now()}-1`,
      eventType: 'ae',
      termPreferred: '恶心',
      termCode: 'MedDRA-10028813',
      meddraCode: '10028813',
      onsetDate: daysAgo(45),
      endDate: daysAgo(42),
      isOngoing: false,
      severity: 'mild',
      seriousness: 'non_serious',
      seriousnessCriteria: [],
      causality: 'possible',
      causalityMethod: 'investigator_judgment',
      relationship: 'possibly_related',
      description: '受试者于用药后第10天出现轻度恶心，无呕吐，未予特殊处理，3天后自行缓解。',
      actionTaken: ['dose_not_changed'],
      outcome: 'resolved',
      status: 'closed',
      reporterId: users['zhaoliu']?.id || users['admin']!.id,
      reportedAt: daysAgo(44),
    },
  });

  const ae2 = await prisma.adverseEvent.create({
    data: {
      projectId: projectHT001.id,
      subjectId: bjSubj002.id,
      siteId: siteBeijing.id,
      reportCode: `AE-BJ002-${Date.now()}-2`,
      eventType: 'sae',
      termPreferred: '低血糖',
      termCode: 'MedDRA-10021005',
      meddraCode: '10021005',
      onsetDate: daysAgo(18),
      isOngoing: false,
      endDate: daysAgo(17),
      severity: 'severe',
      seriousness: 'serious',
      seriousnessCriteria: ['hospitalization', 'medically_significant'],
      causality: 'probable',
      causalityMethod: 'investigator_judgment',
      relationship: 'probably_related',
      description: '受试者于第12周随访后第2天晚间出现严重低血糖，血糖2.1mmol/L，伴意识障碍，急诊住院处理，次日好转出院。',
      actionTaken: ['dose_reduced', 'treatment_given'],
      outcome: 'resolved',
      status: 'open',
      reporterId: users['lisi']?.id || users['admin']!.id,
      reportedAt: daysAgo(17),
    },
  });

  // 为 SAE 创建报告
  await prisma.saeReport.create({
    data: {
      adverseEventId: ae2.id,
      reportType: 'initial',
      reportVersion: 'v1.0',
      regulatoryBody: '国家药品监督管理局',
      reportDate: daysAgo(14),
      status: 'submitted',
      reportContent: {
        reporterName: '李四',
        reporterTitle: '主任医师',
        studyProtocol: 'HT-2024-001',
        siteCode: 'SITE-BJ-001',
        narrativeSummary: '受试者出现严重低血糖事件，导致急诊住院...',
        causalityAssessment: '考虑与研究药物可能有关',
        clinicalOutcome: '24小时内完全恢复',
        actionTaken: '减量研究药物，加强血糖监测',
      },
      submittedTo: '国家药品监督管理局药品评审中心',
      submissionRef: 'NMPA-SAE-2024-00123',
    },
  });

  console.log('  ✅ AE/SAE记录创建完成（1个AE + 1个SAE，含SAE报告）');

  // ===== STEP 15: 监察访视 =====
  console.log('🔍 创建监察访视记录...');
  const monPlanBj = await prisma.monitoringPlan.create({
    data: {
      projectId: projectHT001.id,
      planName: '北京协和医院监察计划',
      frequency: 'monthly',
      description: '每月定期监察，重点关注受试者安全性和数据质量',
      status: 'active',
      createdBy: users['zhangsan']?.id || users['admin']!.id,
    },
  });

  await prisma.monitoringVisit.create({
    data: {
      planId: monPlanBj.id,
      projectId: projectHT001.id,
      siteId: siteBeijing.id,
      craUserId: users['wangwu']?.id || users['admin']!.id,
      visitType: 'routine',
      plannedDate: daysAgo(60),
      actualDate: daysAgo(58),
      status: 'completed',
      sdvPercentage: 95,
    },
  });

  await prisma.monitoringVisit.create({
    data: {
      planId: monPlanBj.id,
      projectId: projectHT001.id,
      siteId: siteBeijing.id,
      craUserId: users['wangwu']?.id || users['admin']!.id,
      visitType: 'routine',
      plannedDate: daysAgo(30),
      actualDate: daysAgo(28),
      status: 'completed',
      sdvPercentage: 88,
    },
  });

  await prisma.monitoringVisit.create({
    data: {
      planId: monPlanBj.id,
      projectId: projectHT001.id,
      siteId: siteBeijing.id,
      craUserId: users['wangwu']?.id || users['admin']!.id,
      visitType: 'routine',
      plannedDate: daysFromNow(2),
      status: 'scheduled',
    },
  });

  console.log('  ✅ 监察访视创建完成');

  // ===== STEP 16: 工时记录 =====
  console.log('⏱️  创建工时记录...');
  const timesheetDefs = [
    {
      userId: users['wangwu']?.id,
      weekStart: daysAgo(14),
      entries: [
        { date: daysAgo(13), hours: 8, type: 'monitoring', desc: '北京协和医院现场监查' },
        { date: daysAgo(12), hours: 8, type: 'monitoring', desc: '北京协和医院现场监查（续）' },
        { date: daysAgo(11), hours: 6, type: 'site_management', desc: '准备监查报告' },
        { date: daysAgo(10), hours: 4, type: 'meeting', desc: '项目例会' },
        { date: daysAgo(9), hours: 7, type: 'data_review', desc: '数据质疑处理' },
      ],
      status: 'approved',
    },
    {
      userId: users['zhaoliu']?.id,
      weekStart: daysAgo(14),
      entries: [
        { date: daysAgo(13), hours: 8, type: 'site_management', desc: '受试者随访协调' },
        { date: daysAgo(12), hours: 6, type: 'data_review', desc: 'CRF数据录入与核查' },
        { date: daysAgo(11), hours: 5, type: 'meeting', desc: '监查访视配合' },
        { date: daysAgo(10), hours: 8, type: 'data_review', desc: '质疑回复' },
        { date: daysAgo(9), hours: 7, type: 'site_management', desc: '新受试者筛查' },
      ],
      status: 'submitted',
    },
    {
      userId: users['wangwu']?.id,
      weekStart: daysAgo(7),
      entries: [
        { date: daysAgo(6), hours: 8, type: 'travel', desc: '出差前往上海' },
        { date: daysAgo(5), hours: 8, type: 'monitoring', desc: '上海瑞金医院监查' },
        { date: daysAgo(4), hours: 6, type: 'monitoring', desc: '上海瑞金医院监查（续）' },
        { date: daysAgo(3), hours: 8, type: 'travel', desc: '返程' },
        { date: daysAgo(2), hours: 5, type: 'project_management', desc: '监查报告撰写' },
      ],
      status: 'pending',
    },
  ];

  for (const ts of timesheetDefs) {
    if (!ts.userId) continue;
    const tsRecord = await prisma.timesheet.create({
      data: {
        userId: ts.userId,
        projectId: projectHT001.id,
        weekStartDate: new Date(ts.weekStart),
        totalHours: ts.entries.reduce((sum, e) => sum + e.hours, 0),
        status: ts.status as any,
        submittedAt: ts.status !== 'pending' ? daysAgo(7) : null,
        approvedAt: ts.status === 'approved' ? daysAgo(5) : null,
        approvedBy: ts.status === 'approved' ? users['zhangsan']?.id : null,
      },
    });

    for (const e of ts.entries) {
      await prisma.timesheetEntry.create({
        data: {
          timesheetId: tsRecord.id,
          workDate: new Date(e.date),
          hours: e.hours,
          workType: e.type as any,
          projectId: projectHT001.id,
          siteId: e.type === 'monitoring' ? (e.desc.includes('北京') ? siteBeijing.id : siteShanghai.id) : null,
          description: e.desc,
          isBillable: true,
        },
      });
    }
  }

  console.log('  ✅ 工时记录创建完成');

  // ===== STEP 17: 财务收支 =====
  console.log('💰 创建财务收支记录...');
  const incomes = [
    { code: 'INC-2024-001', type: 'milestone', amount: 1200000, desc: '签约款（合同总额的10%）', daysAgo: 180, status: 'received' },
    { code: 'INC-2024-002', type: 'milestone', amount: 2400000, desc: '启动款（首中心启动时）', daysAgo: 85, status: 'received' },
    { code: 'INC-2024-003', type: 'milestone', amount: 2400000, desc: '入组款（达到50%入组时）', daysAgo: 20, status: 'received' },
    { code: 'INC-2024-004', type: 'milestone', amount: 3600000, desc: '完成款（末例入组时）', daysAgo: -300, status: 'expected' },
    { code: 'INC-2024-005', type: 'milestone', amount: 2400000, desc: '结题款（数据库锁定时）', daysAgo: -330, status: 'expected' },
  ];

  for (const inc of incomes) {
    await prisma.financialIncome.upsert({
      where: { incomeCode: inc.code },
      update: {},
      create: {
        projectId: projectHT001.id,
        incomeCode: inc.code,
        incomeType: inc.type as any,
        amount: inc.amount,
        currency: 'CNY',
        expectedDate: daysAgo(inc.daysAgo),
        receivedDate: inc.status === 'received' ? daysAgo(inc.daysAgo) : null,
        status: inc.status as any,
        description: inc.desc,
      },
    });
  }

  const expenses = [
    { code: 'EXP-2024-001', type: 'personnel', amount: 180000, desc: 'CRA团队2024年Q1人力成本', daysAgo: 90, status: 'confirmed' },
    { code: 'EXP-2024-002', type: 'travel', amount: 35600, desc: 'CRA现场监查差旅费（北京-上海）', daysAgo: 28, status: 'confirmed', userId: users['wangwu']?.id },
    { code: 'EXP-2024-003', type: 'site_fee', amount: 480000, desc: '北京协和医院研究中心启动费', daysAgo: 85, status: 'confirmed' },
    { code: 'EXP-2024-004', type: 'site_fee', amount: 420000, desc: '上海瑞金医院研究中心启动费', daysAgo: 60, status: 'confirmed' },
    { code: 'EXP-2024-005', type: 'data_management', amount: 96000, desc: '数据管理服务费（Q1）', daysAgo: 90, status: 'confirmed' },
    { code: 'EXP-2024-006', type: 'other', amount: 12800, desc: '项目启动会场地及餐饮费用', daysAgo: 115, status: 'confirmed' },
    { code: 'EXP-2024-007', type: 'travel', amount: 8500, desc: 'CRA出差差旅费报销（待审核）', daysAgo: 3, status: 'draft', userId: users['wangwu']?.id },
  ];

  for (const exp of expenses) {
    await prisma.financialExpense.upsert({
      where: { expenseCode: exp.code },
      update: {},
      create: {
        projectId: projectHT001.id,
        expenseCode: exp.code,
        expenseType: exp.type as any,
        amount: exp.amount,
        currency: 'CNY',
        expenseDate: daysAgo(exp.daysAgo),
        description: exp.desc,
        submittedBy: exp.userId || users['zhangsan']?.id,
        status: exp.status as any,
        reimbursementStatus: exp.status === 'confirmed' ? 'reimbursed' : 'pending',
      },
    });
  }

  console.log('  ✅ 财务收支记录创建完成');

  // ===== STEP 18: 工作流定义 =====
  console.log('🔄 创建工作流定义...');
  const wfDefProject = await prisma.workflowDefinition.upsert({
    where: { workflowCode: 'WF-PRJ-APPROVAL' },
    update: {},
    create: {
      workflowCode: 'WF-PRJ-APPROVAL',
      workflowName: '临床试验方案修订审批流程',
      workflowType: 'protocol_amendment',
      stages: [
        { id: 'stage_1', name: '申办方提交', approverRole: 'SPONSOR', nodeType: 'submit' },
        { id: 'stage_2', name: '医学监查员审核', approverRole: 'MM', nodeType: 'review', esigRequired: true },
        { id: 'stage_3', name: '主要研究者批准', approverRole: 'PI', nodeType: 'approve', esigRequired: true },
        { id: 'stage_4', name: '项目经理授权', approverRole: 'PM', nodeType: 'authorize', esigRequired: true },
      ],
      allowDelegate: true,
      notificationEnabled: true,
      isActive: true,
    },
  });

  const wfDefBudget = await prisma.workflowDefinition.upsert({
    where: { workflowCode: 'WF-BUDGET-REVIEW' },
    update: {},
    create: {
      workflowCode: 'WF-BUDGET-REVIEW',
      workflowName: '项目预算变更审批流程',
      workflowType: 'budget_review',
      stages: [
        { id: 'stage_1', name: '项目经理提交', approverRole: 'PM', nodeType: 'submit' },
        { id: 'stage_2', name: '申办方审批', approverRole: 'SPONSOR', nodeType: 'approve', esigRequired: true },
      ],
      allowDelegate: false,
      notificationEnabled: true,
      isActive: true,
    },
  });

  // ===== STEP 19: 工作流实例 =====
  const wfInstance1 = await prisma.workflowInstance.create({
    data: {
      definitionId: wfDefProject.id,
      workflowType: 'protocol_amendment',
      projectId: projectHT001.id,
      initiatorId: users['linjiuj']?.id || users['admin']!.id,
      status: 'in_progress',
      currentStageIndex: 1,
      businessData: {
        amendmentVersion: 'v2.0',
        amendmentReason: '根据安全性数据调整AE报告窗口期',
        affectedSections: ['3.2 AE报告', '5.1 安全监测'],
      },
    },
  });

  // 创建审批任务
  await prisma.workflowTask.create({
    data: {
      instanceId: wfInstance1.id,
      stageId: 'stage_1',
      stageName: '申办方提交',
      assignedTo: users['linjiuj']?.id || users['admin']!.id,
      approverRole: 'SPONSOR',
      status: 'completed',
      action: 'approve',
      comment: '提交方案修订申请，修订版本v2.0',
      completedAt: daysAgo(5),
    },
  });

  await prisma.workflowTask.create({
    data: {
      instanceId: wfInstance1.id,
      stageId: 'stage_2',
      stageName: '医学监查员审核',
      assignedTo: users['lisi']?.id || users['admin']!.id,
      approverRole: 'MM',
      esigRequired: true,
      status: 'pending',
    },
  });

  console.log('  ✅ 工作流定义与实例创建完成');

  // ===== STEP 20: 通知记录 =====
  console.log('🔔 创建通知记录...');
  const notifications = [
    { userId: users['zhaoliu']?.id, title: '新质疑待处理', content: '您有3条数据质疑需要回复，请尽快处理。', businessType: 'DATA_QUERY' },
    { userId: users['lisi']?.id, title: '有待您审批的工作流', content: '临床试验方案修订 v2.0 待您审核，请及时处理。', businessType: 'WORKFLOW' },
    { userId: users['wangwu']?.id, title: 'SAE 安全性报告已提交', content: '受试者 HT001-BJ-002 的严重不良事件报告已提交药监局。', businessType: 'SAE_REPORT' },
    { userId: users['zhangsan']?.id, title: '工时待审批', content: '王五提交的工时记录（2024年第12周）待您审批。', businessType: 'TIMESHEET' },
    { userId: users['sunqi']?.id, title: '数据质量提醒', content: '北京协和医院中心BJ-002受试者存在2条高优先级数据质疑未处理。', businessType: 'DATA_QUERY' },
  ];

  for (const n of notifications) {
    if (!n.userId) continue;
    await prisma.notification.create({
      data: {
        recipientId: n.userId,
        title: n.title,
        content: n.content,
        businessType: n.businessType,
        channel: 'in_app',
        status: 'sent',
        sentAt: daysAgo(1),
      },
    });
  }

  console.log('  ✅ 通知记录创建完成');

  // ===== STEP 21: 伦理审批 =====
  console.log('⚖️  创建伦理审批记录...');
  await prisma.ethicsApproval.create({
    data: {
      projectId: projectHT001.id,
      siteId: siteBeijing.id,
      approvalType: 'initial',
      approvalNumber: 'PUMCH-IRB-2024-088',
      ethicsCommittee: '中国医学科学院北京协和医院伦理委员会',
      submissionDate: daysAgo(150),
      approvalDate: daysAgo(100),
      expiryDate: daysFromNow(265),
      approvalStatus: 'approved',
      notes: '建议每年提交年度报告，重大方案修订需重新审批',
      createdBy: users['admin']?.id || 'system',
    },
  });

  await prisma.ethicsApproval.create({
    data: {
      projectId: projectHT001.id,
      siteId: siteShanghai.id,
      approvalType: 'initial',
      approvalNumber: 'RJIRB-2024-095',
      ethicsCommittee: '上海交通大学医学院附属瑞金医院伦理委员会',
      submissionDate: daysAgo(120),
      approvalDate: daysAgo(75),
      expiryDate: daysFromNow(290),
      approvalStatus: 'approved',
      createdBy: users['admin']?.id || 'system',
    },
  });

  console.log('  ✅ 伦理审批记录创建完成');

  // ===== STEP 22: 知情同意 =====
  console.log('📝 创建知情同意记录...');
  const consentSubjects = [
    { subjectCode: 'HT001-BJ-001', version: 'v1.0', status: 'signed' },
    { subjectCode: 'HT001-BJ-002', version: 'v1.0', status: 'signed' },
    { subjectCode: 'HT001-SH-001', version: 'v1.0', status: 'signed' },
    { subjectCode: 'HT001-BJ-005', version: 'v1.0', status: 'withdrawn' },
  ];

  // 修正 ConsentRecord 字段
  for (const c of consentSubjects) {
    const subj = subjectMap[c.subjectCode];
    if (!subj) continue;
    await prisma.consentRecord.create({
      data: {
        projectId: projectHT001.id,
        subjectId: subj.id,
        siteId: subj.siteId,
        consentVersion: c.version,
        signeeType: 'subject',
        signeeName: `受试者-${c.subjectCode}`,
        consentDate: daysAgo(c.subjectCode.includes('BJ') ? 55 : 48),
        status: c.status as any,
        reconsentReason: c.status === 'withdrawn' ? '个人原因，主动要求退出研究' : null,
      },
    });
  }

  console.log('  ✅ 知情同意记录创建完成');

  // ===== STEP 23: SDV 核查记录 =====
  console.log('🔎 创建SDV源数据核查记录...');
  const bjCrfData = await prisma.crfData.findFirst({
    where: { subjectId: bjSubj001.id },
  });

  if (bjCrfData) {
    const sdvRecord = await prisma.sdvRecord.create({
      data: {
        projectId: projectHT001.id,
        siteId: siteBeijing.id,
        subjectId: bjSubj001.id,
        craUserId: users['wangwu']?.id || users['admin']!.id,
        sdvDate: daysAgo(28),
        totalItems: 5,
        verifiedItems: 5,
        discrepancyItems: 0,
        percentage: 100,
        status: 'completed',
        notes: '所有数据与源文件一致，无差异',
        completedAt: daysAgo(28),
      },
    });

    // 核查项目（crfDataId 为必填字段，使用已找到的 bjCrfData.id）
    const sdvFields = [
      { code: 'sbp', crfVal: '136' },
      { code: 'dbp', crfVal: '84' },
      { code: 'hr', crfVal: '76' },
      { code: 'hba1c', crfVal: '8.2' },
      { code: 'fasting_glucose', crfVal: '9.6' },
    ];
    for (const field of sdvFields) {
      await prisma.sdvItem.create({
        data: {
          sdvRecordId: sdvRecord.id,
          crfDataId: bjCrfData.id,
          fieldCode: field.code,
          crfValue: field.crfVal,
          sourceValue: field.crfVal,
          isVerified: true,
          isMatch: true,
        },
      });
    }
  }

  console.log('  ✅ SDV核查记录创建完成');

  // ===== STEP 24: 药物管理 =====
  console.log('💊 创建药物管理记录...');
  const drug1 = await prisma.drug.upsert({
    where: { projectId_drugCode: { projectId: projectHT001.id, drugCode: 'DRUG-HT001-A' } },
    update: {},
    create: {
      projectId: projectHT001.id,
      drugCode: 'DRUG-HT001-A',
      drugName: 'HT-2024-001化合物（研究药物）',
      genericName: 'HT001-compound',
      dosageForm: '口服片剂',
      strength: '10mg',
      manufacturer: '华泰生物医药集团研发中心',
      storageCondition: '2-8℃避光保存',
      isBlinded: true,
      description: '研究药物，口服给药，双盲设计',
      status: 'active',
    },
  });

  const drug2 = await prisma.drug.upsert({
    where: { projectId_drugCode: { projectId: projectHT001.id, drugCode: 'DRUG-HT001-P' } },
    update: {},
    create: {
      projectId: projectHT001.id,
      drugCode: 'DRUG-HT001-P',
      drugName: '安慰剂（外观与研究药物一致）',
      genericName: 'placebo',
      dosageForm: '口服片剂',
      strength: '0mg',
      manufacturer: '华泰生物医药集团研发中心',
      storageCondition: '室温避光保存',
      isBlinded: true,
      description: '安慰剂，与研究药物外观相同',
      status: 'active',
    },
  });

  // 发运记录（DrugShipment 通过 drugId 关联，无直接 projectId/siteId）
  await prisma.drugShipment.upsert({
    where: { shipmentCode: 'SHIP-BJ-20240115-001' },
    update: {},
    create: {
      drugId: drug1.id,
      shipmentCode: 'SHIP-BJ-20240115-001',
      fromLocation: '华泰生物医药集团研发中心（上海）',
      toSiteId: siteBeijing.id,
      toLocation: '北京协和医院临床研究药房',
      quantity: 500,
      batchNumber: 'HT001-A-2024-01',
      expiryDate: daysFromNow(365),
      shippedDate: daysAgo(85),
      receivedDate: daysAgo(83),
      temperatureOk: true,
      courier: '顺丰冷链快递',
      trackingNumber: 'SF20240115001234',
      status: 'received',
      notes: '冷链运输，温度符合要求',
    },
  });

  // 库存记录（DrugInventory 无 projectId，通过 drugId 关联）
  await prisma.drugInventory.create({
    data: {
      drugId: drug1.id,
      siteId: siteBeijing.id,
      location: '北京协和医院临床研究药房A区',
      batchNumber: 'HT001-A-2024-01',
      expiryDate: daysFromNow(365),
      quantityOnHand: 285,
      quantityReserved: 80,
      quantityDispensed: 135,
      lastCountDate: daysAgo(2),
      status: 'normal',
      notes: '库存充足，定期盘点',
    },
  });

  console.log('  ✅ 药物管理记录创建完成');

  // ===== STEP 25: 系统配置 =====
  console.log('⚙️  创建系统配置...');
  const configs = [
    { key: 'system.name', value: 'CTMS+EDC v4.0', type: 'string', description: '系统名称' },
    { key: 'system.version', value: '4.0.0', type: 'string', description: '系统版本' },
    { key: 'query.auto_close_days', value: '30', type: 'number', description: '质疑自动关闭天数' },
    { key: 'ae.sae_report_deadline_days', value: '7', type: 'number', description: 'SAE报告提交截止天数' },
    { key: 'timesheet.approval_required', value: 'true', type: 'boolean', description: '工时是否需要审批' },
    { key: 'audit.retention_years', value: '15', type: 'number', description: '审计日志保留年限' },
  ];

  for (const c of configs) {
    await prisma.systemConfig.upsert({
      where: { configKey: c.key },
      update: {},
      create: {
        configKey: c.key,
        configValue: c.value,
        configType: c.type as any,
        description: c.description,
        isEncrypted: false,
        scope: 'global',
      },
    });
  }

  console.log('  ✅ 系统配置创建完成');

  // ===== 数据汇总 =====
  const summary = {
    organizations: await prisma.organization.count(),
    users: await prisma.user.count(),
    projects: await prisma.project.count(),
    sites: await prisma.site.count(),
    subjects: await prisma.subject.count(),
    randomizationRecords: await prisma.edcRandomizationRecord.count(),
    crfData: await prisma.crfData.count(),
    dataQueries: await prisma.dataQuery.count(),
    adverseEvents: await prisma.adverseEvent.count(),
    monitoringVisits: await prisma.monitoringVisit.count(),
    timesheets: await prisma.timesheet.count(),
    financialIncomes: await prisma.financialIncome.count(),
    financialExpenses: await prisma.financialExpense.count(),
    workflowInstances: await prisma.workflowInstance.count(),
    notifications: await prisma.notification.count(),
    drugs: await prisma.drug.count(),
    consentRecords: await prisma.consentRecord.count(),
    vendors: await prisma.vendor.count(),
    contracts: await prisma.contract.count(),
  };

  console.log('\n✅ 测试数据生成完成！数据汇总：');
  console.table(summary);
}

main()
  .then(async () => {
    await prisma.$disconnect();
    console.log('\n🎉 所有测试数据已成功生成！\n');
  })
  .catch(async (e) => {
    console.error('❌ 测试数据生成失败:', e);
    await prisma.$disconnect();
    process.exit(1);
  });
