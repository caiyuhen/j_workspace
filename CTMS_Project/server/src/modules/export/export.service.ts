import prisma from '../../config/database';
import { ExportDataInput } from './export.dto';
import { NotFoundError, BadRequestError } from '../../shared/errors/AppError';
import logger from '../../shared/utils/logger';

/**
 * 将嵌套对象扁平化为单层键值对
 * 对嵌套对象使用 "parent.child" 格式的键名
 * 对数组类型的值使用 JSON 序列化
 */
function flattenObject(obj: Record<string, any>, prefix = '', result: Record<string, any> = {}): Record<string, any> {
  for (const [key, value] of Object.entries(obj)) {
    const newKey = prefix ? `${prefix}.${key}` : key;
    if (value === null || value === undefined) {
      result[newKey] = '';
    } else if (Array.isArray(value)) {
      result[newKey] = JSON.stringify(value);
    } else if (typeof value === 'object' && !(value instanceof Date)) {
      flattenObject(value as Record<string, any>, newKey, result);
    } else if (value instanceof Date) {
      result[newKey] = value.toISOString();
    } else {
      result[newKey] = value;
    }
  }
  return result;
}

/**
 * 将数据数组转换为 CSV 格式字符串
 * 自动提取所有字段的键名作为表头
 * 处理包含逗号、引号、换行的特殊字符
 */
function convertToCsv(data: Record<string, any>[]): string {
  if (data.length === 0) return '';

  // 扁平化所有行并收集所有列
  const flatRows = data.map(row => flattenObject(row));
  const headerSet = new Set<string>();
  for (const row of flatRows) {
    for (const key of Object.keys(row)) {
      headerSet.add(key);
    }
  }
  const headers = Array.from(headerSet);

  // CSV 行转义：包裹含逗号/引号/换行的字段
  const escapeField = (field: string): string => {
    const str = String(field);
    if (str.includes(',') || str.includes('"') || str.includes('\n') || str.includes('\r')) {
      return `"${str.replace(/"/g, '""')}"`;
    }
    return str;
  };

  // BOM + 表头行 + 数据行
  const lines: string[] = [];
  lines.push(headers.map(escapeField).join(','));

  for (const row of flatRows) {
    const values = headers.map(h => {
      const val = row[h] !== undefined ? row[h] : '';
      return escapeField(val);
    });
    lines.push(values.join(','));
  }

  // 添加 UTF-8 BOM 以确保 Excel 正确识别中文编码
  return '\uFEFF' + lines.join('\n');
}

/** 导出 EDC 数据 */
async function exportData(input: ExportDataInput, userId: string) {
  const { exportType, projectId, siteId, format, filters } = input;

  let data: any[];
  let fileName: string;

  switch (exportType) {
    case 'subjects':
      data = await prisma.subject.findMany({
        where: { projectId, ...(siteId ? { siteId } : {}) },
        include: { visits: { select: { id: true, visitCode: true, status: true } } },
        orderBy: { createdAt: 'asc' },
      });
      fileName = `subjects_${projectId}_${new Date().toISOString().split('T')[0]}`;
      break;

    case 'crf_data': {
      // CrfData 通过 subject 关联项目，没有直接的 visit 关系
      const subjectIds = siteId
        ? (await prisma.subject.findMany({ where: { projectId, siteId }, select: { id: true } })).map(s => s.id)
        : (await prisma.subject.findMany({ where: { projectId }, select: { id: true } })).map(s => s.id);
      const crfWhere: any = { subjectId: { in: subjectIds } };
      if (filters?.formCode) crfWhere.formCode = filters.formCode;

      const [crfDataList, subjects] = await Promise.all([
        prisma.crfData.findMany({
          where: crfWhere,
          orderBy: { updatedAt: 'desc' },
          take: 10000,
        }),
        prisma.subject.findMany({
          where: { id: { in: subjectIds } },
          select: { id: true, subjectCode: true },
        }),
      ]);
      const subjectMap = new Map(subjects.map((s: any) => [s.id, s.subjectCode]));
      data = crfDataList.map((d: any) => ({ ...d, _subjectCode: subjectMap.get(d.subjectId) || '' }));
      fileName = `crf_data_${projectId}_${new Date().toISOString().split('T')[0]}`;
      break;
    }

    case 'adverse_events': {
      // AdverseEvent 没有 subject/reports 正向关联，只有 reports 反向关联
      const aeWhere: any = { projectId, ...(siteId ? { siteId } : {}) };
      const [aeList, aeSubjects] = await Promise.all([
        prisma.adverseEvent.findMany({ where: aeWhere, orderBy: { createdAt: 'desc' } }),
        prisma.subject.findMany({
          where: { projectId },
          select: { id: true, subjectCode: true },
        }),
      ]);
      const aeSubjectMap = new Map(aeSubjects.map((s: any) => [s.id, s.subjectCode]));
      data = aeList.map((ae: any) => ({ ...ae, _subjectCode: aeSubjectMap.get(ae.subjectId) || '' }));
      fileName = `ae_data_${projectId}_${new Date().toISOString().split('T')[0]}`;
      break;
    }

    case 'queries': {
      // DataQuery 有 subject 正向关联，但没有 assignee/raiser 关联（只有字符串 ID）
      const queryWhere: any = { projectId };
      data = await prisma.dataQuery.findMany({
        where: queryWhere,
        include: {
          subject: { select: { subjectCode: true } },
        },
        orderBy: { createdAt: 'desc' },
      });
      // 手动查询 assignee 和 raiser 的用户名
      const userIds = new Set<string>();
      for (const q of data as any[]) {
        if (q.assignedTo) userIds.add(q.assignedTo);
        if (q.raisedBy) userIds.add(q.raisedBy);
      }
      if (userIds.size > 0) {
        const users = await prisma.user.findMany({
          where: { id: { in: Array.from(userIds) } },
          select: { id: true, displayName: true },
        });
        const userMap = new Map(users.map((u: any) => [u.id, u.displayName]));
        data = (data as any[]).map((q: any) => ({
          ...q,
          _assigneeName: userMap.get(q.assignedTo) || '',
          _raiserName: userMap.get(q.raisedBy) || '',
          _subjectCode: q.subject?.subjectCode || '',
        }));
        // 移除 subject 嵌套对象以保持扁平结构
        data = (data as any[]).map(({ subject, ...rest }: any) => rest);
      }
      fileName = `queries_${projectId}_${new Date().toISOString().split('T')[0]}`;
      break;
    }

    case 'sdv': {
      // SdvRecord 有 items 关联，但没有 subject/cra 关联
      const sdvWhere: any = { projectId, ...(siteId ? { siteId } : {}) };
      const [sdvList, sdvSubjects, craUsers] = await Promise.all([
        prisma.sdvRecord.findMany({
          where: sdvWhere,
          include: { items: true },
          orderBy: { sdvDate: 'desc' },
        }),
        prisma.subject.findMany({
          where: { projectId },
          select: { id: true, subjectCode: true },
        }),
        prisma.user.findMany({
          where: { id: { in: (await prisma.sdvRecord.findMany({ where: sdvWhere, select: { craUserId: true }, distinct: ['craUserId'] })).map((r: any) => r.craUserId) } },
          select: { id: true, displayName: true },
        }),
      ]);
      const sdvSubjectMap = new Map(sdvSubjects.map((s: any) => [s.id, s.subjectCode]));
      const craMap = new Map(craUsers.map((u: any) => [u.id, u.displayName]));
      data = (sdvList as any[]).map((r: any) => ({
        ...r,
        _subjectCode: sdvSubjectMap.get(r.subjectId) || '',
        _craName: craMap.get(r.craUserId) || '',
      }));
      fileName = `sdv_${projectId}_${new Date().toISOString().split('T')[0]}`;
      break;
    }

    case 'randomization': {
      // EdcRandomizationRecord 有 randRecord 反向关联，没有 subject/site 关联
      const randList = await prisma.edcRandomizationRecord.findMany({
        where: { projectId },
        orderBy: { randomizationDate: 'asc' },
      });
      const [randSubjects, randSites] = await Promise.all([
        prisma.subject.findMany({
          where: { projectId },
          select: { id: true, subjectCode: true, siteId: true },
        }),
        prisma.site.findMany({
          where: { projectId },
          select: { id: true, siteName: true },
        }),
      ]);
      const randSubjectMap = new Map(randSubjects.map((s: any) => [s.id, { subjectCode: s.subjectCode, siteId: s.siteId }]));
      const randSiteMap = new Map(randSites.map((s: any) => [s.id, s.siteName]));
      data = randList.map((r: any) => {
        const subj = randSubjectMap.get(r.subjectId);
        return {
          ...r,
          _subjectCode: subj?.subjectCode || '',
          _siteName: subj?.siteId ? randSiteMap.get(subj.siteId) || '' : '',
        };
      });
      fileName = `randomization_${projectId}_${new Date().toISOString().split('T')[0]}`;
      break;
    }

    default:
      throw new BadRequestError(`不支持的导出类型: ${exportType}`);
  }

  // 根据 format 返回不同格式的数据
  let resultData: any;
  let contentType: string;
  let fileExtension: string;

  if (format === 'csv') {
    resultData = convertToCsv(data);
    contentType = 'text/csv; charset=utf-8';
    fileExtension = 'csv';
  } else {
    resultData = data;
    contentType = 'application/json';
    fileExtension = 'json';
  }

  logger.info('Data exported', {
    audit: true,
    eventType: 'DATA_EXPORT',
    projectId,
    exportType,
    recordCount: data.length,
    format,
    message: `用户 ${userId} 导出 ${exportType} 数据，共 ${data.length} 条`,
  });

  return {
    exportType,
    format,
    contentType,
    fileExtension,
    recordCount: data.length,
    fileName: `${fileName}.${fileExtension}`,
    data: resultData,
  };
}

/** 获取导出历史 */
async function getHistory(query: Record<string, any>) {
  // 从审计日志中获取导出记录
  const where: any = {
    eventType: 'DATA_EXPORT',
  };

  if (query.projectId) {
    where.projectId = query.projectId;
  }

  return prisma.auditLog.findMany({
    where,
    orderBy: { eventTimestamp: 'desc' },
    take: 50,
    select: {
      id: true,
      eventType: true,
      userId: true,
      project: { select: { projectCode: true, projectName: true } },
      action: true,
      eventTimestamp: true,
    },
  });
}

export const exportService = { exportData, getHistory };
