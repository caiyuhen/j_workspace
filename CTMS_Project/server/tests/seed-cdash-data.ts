/**
 * CDASH/SDTM标准测试数据生成器
 * 生成 100 个受试者的完整 CDASH 标准数据
 */

import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

const CDISC_DOMAINS = [
  // Special Purpose
  { code: 'DM', name: 'Demographics', domainClass: 'Special Purpose' },
  { code: 'CO', name: 'Comments', domainClass: 'Special Purpose' },
  { code: 'SE', name: 'Subject Elements', domainClass: 'Special Purpose' },
  { code: 'SV', name: 'Subject Visits', domainClass: 'Special Purpose' },

  // Interventions
  { code: 'CM', name: 'Concomitant Medications', domainClass: 'Interventions' },
  { code: 'EX', name: 'Exposure', domainClass: 'Interventions' },
  { code: 'SU', name: 'Substance Use', domainClass: 'Interventions' },
  { code: 'PR', name: 'Procedures', domainClass: 'Interventions' },

  // Events
  { code: 'AE', name: 'Adverse Events', domainClass: 'Events' },
  { code: 'CE', name: 'Clinical Events', domainClass: 'Events' },
  { code: 'DS', name: 'Disposition', domainClass: 'Events' },
  { code: 'MH', name: 'Medical History', domainClass: 'Events' },
  { code: 'DV', name: 'Protocol Deviations', domainClass: 'Events' },
  { code: 'HO', name: 'Healthcare Encounters', domainClass: 'Events' },

  // Findings
  { code: 'VS', name: 'Vital Signs', domainClass: 'Findings' },
  { code: 'LB', name: 'Laboratory Test Results', domainClass: 'Findings' },
  { code: 'EG', name: 'ECG Test Results', domainClass: 'Findings' },
  { code: 'PE', name: 'Physical Examination', domainClass: 'Findings' },
  { code: 'QS', name: 'Questionnaires', domainClass: 'Findings' },
  { code: 'DA', name: 'Drug Accountability', domainClass: 'Findings' },
  { code: 'IE', name: 'Inclusion/Exclusion Criteria', domainClass: 'Findings' },
  { code: 'MB', name: 'Microbiology Specimen', domainClass: 'Findings' },
  { code: 'MS', name: 'Microbiology Susceptibility', domainClass: 'Findings' },
  { code: 'PC', name: 'Pharmacokinetics Concentrations', domainClass: 'Findings' },
  { code: 'PP', name: 'Pharmacokinetics Parameters', domainClass: 'Findings' },
  { code: 'SC', name: 'Subject Characteristics', domainClass: 'Findings' },
  { code: 'TU', name: 'Tumor Identification', domainClass: 'Findings' },
  { code: 'TR', name: 'Tumor Results', domainClass: 'Findings' },
  { code: 'RS', name: 'Disease Response', domainClass: 'Findings' },
  { code: 'UR', name: 'Urinalysis', domainClass: 'Findings' }
];

// CDASH 代码表数据
const CDASH_CODELISTS = [
  {
    oid: 'AESEV',
    name: 'Adverse Event Severity',
    domain: 'AE',
    items: [
      { code: 'MILD', decoded: 'Mild', order: 1 },
      { code: 'MODERATE', decoded: 'Moderate', order: 2 },
      { code: 'SEVERE', decoded: 'Severe', order: 3 }
    ]
  },
  {
    oid: 'AESER',
    name: 'Adverse Event Seriousness',
    domain: 'AE',
    items: [
      { code: 'Y', decoded: 'Yes', order: 1 },
      { code: 'N', decoded: 'No', order: 2 }
    ]
  },
  {
    oid: 'AEREL',
    name: 'Adverse Event Relationship',
    domain: 'AE',
    items: [
      { code: 'NOT_Related', decoded: 'Not Related', order: 1 },
      { code: 'UNLIKELY', decoded: 'Unlikely', order: 2 },
      { code: 'POSSIBLE', decoded: 'Possible', order: 3 },
      { code: 'PROBABLE', decoded: 'Probable', order: 4 },
      { code: 'DEFINITE', decoded: 'Definite', order: 5 }
    ]
  },
  {
    oid: 'AEOUT',
    name: 'Adverse Event Outcome',
    domain: 'AE',
    items: [
      { code: 'RESOLVED', decoded: 'Resolved', order: 1 },
      { code: 'RESOLVING', decoded: 'Resolving', order: 2 },
      { code: 'NOT_RESOLVED', decoded: 'Not Resolved', order: 3 },
      { code: 'FATAL', decoded: 'Fatal', order: 4 }
    ]
  },
  {
    oid: 'SEX',
    name: 'Sex',
    domain: 'DM',
    items: [
      { code: 'M', decoded: 'Male', order: 1 },
      { code: 'F', decoded: 'Female', order: 2 },
      { code: 'U', decoded: 'Unknown', order: 3 }
    ]
  },
  {
    oid: 'LBNRIND',
    name: 'Laboratory Normal Range Indicator',
    domain: 'LB',
    items: [
      { code: 'L', decoded: 'Low', order: 1 },
      { code: 'N', decoded: 'Normal', order: 2 },
      { code: 'H', decoded: 'High', order: 3 }
    ]
  }
];

async function seedCodeLists() {
  console.log('📚 创建 CDISC 域主数据...');
  for (const domain of CDISC_DOMAINS) {
    await prisma.cdiscDomain.upsert({
      where: { domainCode: domain.code },
      update: { domainName: domain.name, domainClass: domain.domainClass, isActive: true },
      create: {
        domainCode: domain.code,
        domainName: domain.name,
        domainClass: domain.domainClass,
        standardName: 'CDISC',
        standardVersion: '2.1',
        isActive: true,
      }
    });
  }

  console.log('📋 创建 CDISC 代码表...');
  for (const list of CDASH_CODELISTS) {
    await prisma.cdiscCodeList.upsert({
      where: { codeListOid: list.oid },
      update: {
        codeListName: list.name,
        domain: list.domain,
        items: list.items,
        isActive: true
      },
      create: {
        codeListOid: list.oid,
        codeListName: list.name,
        domain: list.domain,
        items: list.items,
        isActive: true
      }
    });
  }
  console.log(`  ✅ 已创建 ${CDASH_CODELISTS.length} 个代码表`);
}

async function seedCDASHData() {
  console.log('\n🧪 生成 100 个 CDASH 标准受试者数据...\n');

  // 获取已有项目和中心
  const project = await prisma.project.findFirst({
    where: { projectCode: { startsWith: 'PRJ' } }
  });
  
  if (!project) {
    console.log('⚠️  未找到项目，跳过数据生成');
    return;
  }

  const sites = await prisma.site.findMany({
    where: { projectId: project.id }
  });

  if (sites.length === 0) {
    // 自动创建一个测试中心
    const site = await prisma.site.create({
      data: {
        projectId: project.id,
        siteCode: 'SITE-CDASH-01',
        siteName: 'CDASH 测试中心'
      }
    });
    sites.push(site);
  }

  const site = sites[0]; // 使用第一个中心
  const studyId = project.projectCode;

  // 生成 100 个受试者
  for (let i = 1; i <= 100; i++) {
    const subjectCode = `${studyId}-${String(i).padStart(4, '0')}`;
    const age = 25 + Math.floor(Math.random() * 40); // 25-65 岁
    const sex = Math.random() > 0.5 ? 'M' : 'F';
    const bmi = 18.5 + Math.random() * 15; // 18.5-33.5

    // 创建或获取受试者
    const subject = await prisma.subject.upsert({
      where: {
        projectId_subjectCode: {
          projectId: project.id,
          subjectCode: subjectCode
        }
      },
      update: {},
      create: {
        subjectCode,
        projectId: project.id,
        siteId: site.id,
        enrolledAt: new Date(2026, 0, 1 + i),
        randomizationNumber: `RAND-${i}`,
        enrollmentStatus: 'enrolled'
      }
    });

    // 生成 DM 域数据 (人口学)
    await prisma.crfData.create({
      data: {
        subjectId: subject.id,
        formId: 'dm-form',
        formCode: 'DM',
        fieldId: 'dm-subjid',
        fieldCode: 'SUBJID',
        fieldValue: subjectCode,
        cdiscDomain: 'DM',
        cdashDataset: 'DM',
        cdashVariable: 'SUBJID',
        sdtmVariable: 'USUBJID',
        collectionVersion: 'CDASH 2.1',
        enteredBy: 'system',
        enteredAt: new Date()
      }
    });

    // 生成 VS 域数据 (生命体征)
    const visits = [0, 4, 8, 12, 24]; // 访视周次
    for (const visitWeek of visits) {
      const visitDate = new Date(subject.enrolledAt || new Date());
      visitDate.setDate(visitDate.getDate() + visitWeek * 7);

      const sbp = 110 + Math.floor(Math.random() * 30); // 110-140
      const dbp = 70 + Math.floor(Math.random() * 20);  // 70-90
      const hr = 60 + Math.floor(Math.random() * 20);   // 60-80

      await prisma.crfData.createMany({
        data: [
          {
            subjectId: subject.id,
            formId: 'vs-form',
            formCode: 'VS',
            fieldId: 'vs-vstestcd',
            fieldCode: 'VSTESTCD',
            fieldValue: 'SBP',
            cdiscDomain: 'VS',
            cdashDataset: 'VS',
            cdashVariable: 'VSTESTCD',
            sdtmVariable: 'VSTESTCD',
            collectionVersion: 'CDASH 2.1',
            enteredBy: 'crc_user',
            enteredAt: visitDate
          },
          {
            subjectId: subject.id,
            formId: 'vs-form',
            formCode: 'VS',
            fieldId: 'vs-vsorres',
            fieldCode: 'VSORRES',
            fieldValue: sbp.toString(),
            cdiscDomain: 'VS',
            cdashDataset: 'VS',
            cdashVariable: 'VSORRES',
            sdtmVariable: 'VSORRES',
            collectionVersion: 'CDASH 2.1',
            enteredBy: 'crc_user',
            enteredAt: visitDate
          },
          {
            subjectId: subject.id,
            formId: 'vs-form',
            formCode: 'VS',
            fieldId: 'vs-vsorresu',
            fieldCode: 'VSORRESU',
            fieldValue: 'mmHg',
            cdiscDomain: 'VS',
            cdashDataset: 'VS',
            cdashVariable: 'VSORRESU',
            sdtmVariable: 'VSORRESU',
            collectionVersion: 'CDASH 2.1',
            enteredBy: 'crc_user',
            enteredAt: visitDate
          }
        ]
      });
    }

    // 生成 LB 域数据 (实验室检查)
    const hba1c = 5.5 + Math.random() * 3; // 5.5-8.5
    const glucose = 4.0 + Math.random() * 5; // 4.0-9.0

    await prisma.crfData.createMany({
      data: [
        {
          subjectId: subject.id,
          formId: 'lb-form',
          formCode: 'LB',
          fieldId: 'lb-lbtestcd',
          fieldCode: 'LBTESTCD',
          fieldValue: 'HBA1C',
          cdiscDomain: 'LB',
          cdashDataset: 'LB',
          cdashVariable: 'LBTESTCD',
          sdtmVariable: 'LBTESTCD',
          collectionVersion: 'CDASH 2.1',
          enteredBy: 'lab_user',
          enteredAt: new Date()
        },
        {
          subjectId: subject.id,
          formId: 'lb-form',
          formCode: 'LB',
          fieldId: 'lb-lborres',
          fieldCode: 'LBORRES',
          fieldValue: hba1c.toFixed(1),
          cdiscDomain: 'LB',
          cdashDataset: 'LB',
          cdashVariable: 'LBORRES',
          sdtmVariable: 'LBORRES',
          collectionVersion: 'CDASH 2.1',
          enteredBy: 'lab_user',
          enteredAt: new Date()
        },
        {
          subjectId: subject.id,
          formId: 'lb-form',
          formCode: 'LB',
          fieldId: 'lb-lbcat',
          fieldCode: 'LBCAT',
          fieldValue: 'GLYCEMIC CONTROL',
          cdiscDomain: 'LB',
          cdashDataset: 'LB',
          cdashVariable: 'LBCAT',
          sdtmVariable: 'LBCAT',
          collectionVersion: 'CDASH 2.1',
          enteredBy: 'lab_user',
          enteredAt: new Date()
        }
      ]
    });

    // 生成 AE 域数据 (不良事件) - 约 30% 受试者有 AE
    if (Math.random() < 0.3) {
      const aeTerms = ['头痛', '恶心', '疲劳', '失眠', '食欲下降'];
      const aeTerm = aeTerms[Math.floor(Math.random() * aeTerms.length)];
      const severity = ['MILD', 'MODERATE', 'SEVERE'][Math.floor(Math.random() * 3)];
      
      await prisma.adverseEvent.upsert({
        where: { reportCode: `AE-${subjectCode}-01` },
        update: {},
        create: {
          reportCode: `AE-${subjectCode}-01`,
          eventType: 'ae',
          reporterId: 'system',
          projectId: project.id,
          subjectId: subject.id,
          termPreferred: aeTerms[Math.floor(Math.random() * aeTerms.length)],
          onsetDate: new Date(subject.enrolledAt || new Date()),
          severity: ['mild', 'moderate', 'severe'][Math.floor(Math.random() * 3)] as any,
          seriousness: 'N',
          description: '生成的标准AE测试数据',
          outcome: 'recovered',
          causality: 'possible'
        }
      });
    }

    // 进度输出
    if (i % 20 === 0) {
      console.log(`  📊 已生成 ${i}/100 个受试者的 CDASH 标准数据`);
    }
  }

  console.log('\n✅ 100 个受试者的 CDASH 标准数据生成完成！');
  console.log('   - DM 域：人口学数据');
  console.log('   - VS 域：生命体征 (5 次访视)');
  console.log('   - LB 域：实验室检查 (HbA1c)');
  console.log('   - AE 域：不良事件 (约 30 个)');
}

async function main() {
  try {
    await seedCodeLists();
    await seedCDASHData();
    console.log('\n🎉 CDASH/SDTM 标准测试数据生成完成！');
  } catch (error) {
    console.error('❌ 数据生成失败:', error);
    throw error;
  } finally {
    await prisma.$disconnect();
  }
}

main();
