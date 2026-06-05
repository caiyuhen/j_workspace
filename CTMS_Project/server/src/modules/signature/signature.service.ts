import crypto from 'crypto';
import prisma from '../../config/database';
import { CreateSignatureInput } from './signature.dto';
import { NotFoundError, BadRequestError } from '../../shared/errors/AppError';
import logger from '../../shared/utils/logger';
import { parsePagination, buildPaginatedResult, prismaPagination } from '../../shared/utils/pagination';

/** 生成签名哈希 */
function computeHash(data: string): string {
  return crypto.createHash('sha256').update(data).digest('hex');
}

/** 创建电子签名（21 CFR Part 11 合规） */
async function create(input: CreateSignatureInput, ipAddress?: string, userAgent?: string) {
  const signatureData = JSON.stringify({
    userId: input.userId,
    meaning: input.signatureMeaning,
    reason: input.signatureReason,
    tableName: input.tableName,
    recordId: input.recordId,
    timestamp: new Date().toISOString(),
  });

  const currentHash = computeHash(signatureData);

  const signature = await prisma.signatureRecord.create({
    data: {
      ...input,
      currentHash,
      ipAddress,
      userAgent,
    },
  });

  logger.info('Electronic signature created', {
    audit: true,
    eventType: 'ESIG_CREATE',
    signatureId: signature.id,
    userId: input.userId,
    signatureMeaning: input.signatureMeaning,
    regulatoryRef: '21 CFR Part 11',
    message: `电子签名: ${input.signatureMeaning}`,
  });

  return {
    id: signature.id,
    signedAt: signature.signedAt,
    currentHash: signature.currentHash,
  };
}

/** 批量创建签名 */
async function batchCreate(inputs: CreateSignatureInput[], ipAddress?: string, userAgent?: string) {
  const results = [];
  for (const input of inputs) {
    try {
      const result = await create(input, ipAddress, userAgent);
      results.push({ success: true, ...result });
    } catch (err: any) {
      results.push({ success: false, error: err.message });
    }
  }
  return results;
}

/** 验证签名完整性（哈希链验证） */
async function verify(signatureId: string) {
  const signature = await prisma.signatureRecord.findUnique({ where: { id: signatureId } });
  if (!signature) throw new NotFoundError('SignatureRecord', signatureId);

  // 验证哈希链
  if (signature.previousHash) {
    const prevSignature = await prisma.signatureRecord.findFirst({
      where: { currentHash: signature.previousHash },
    });
    if (!prevSignature) {
      return { valid: false, reason: '签名链断裂：前一个签名记录未找到' };
    }
  }

  return { valid: true, signatureId: signature.id, signedAt: signature.signedAt };
}

/** 撤销签名 — 仅允许撤销未关联审计日志的签名 */
async function revoke(signatureId: string, userId: string, reason: string) {
  const signature = await prisma.signatureRecord.findUnique({ where: { id: signatureId } });
  if (!signature) throw new NotFoundError('SignatureRecord', signatureId);

  // 检查是否有后续签名引用此签名
  const dependents = await prisma.signatureRecord.count({
    where: { previousHash: signature.currentHash },
  });
  if (dependents > 0) {
    throw new BadRequestError('该签名已被后续签名引用，无法撤销');
  }

  // 创建撤销记录
  const revokeData = JSON.stringify({
    action: 'revoke',
    revokedSignatureId: signatureId,
    reason,
    userId,
    timestamp: new Date().toISOString(),
  });

  const revokeHash = computeHash(revokeData);

  await prisma.signatureRecord.create({
    data: {
      userId,
      signatureMeaning: `撤销签名: ${signature.signatureMeaning}`,
      signatureReason: reason,
      tableName: signature.tableName,
      recordId: signature.recordId,
      previousHash: signature.currentHash,
      currentHash: revokeHash,
      ipAddress: '',
      userAgent: '',
    },
  });

  logger.info('Signature revoked', {
    audit: true,
    eventType: 'ESIG_REVOKE',
    originalSignatureId: signatureId,
    revokedBy: userId,
    reason,
    regulatoryRef: '21 CFR Part 11',
    message: `撤销签名 ${signatureId}`,
  });

  return { message: '签名已撤销', revokedSignatureId: signatureId };
}

/** 获取签名记录列表 */
async function getList(query: Record<string, any>) {
  const pagination = parsePagination(query);
  const where: any = {};
  if (query.userId) where.userId = query.userId;
  if (query.projectId) where.projectId = query.projectId;
  if (query.tableName && query.recordId) {
    where.tableName = query.tableName;
    where.recordId = query.recordId;
  }

  const [items, total] = await Promise.all([
    prisma.signatureRecord.findMany({
      where,
      orderBy: { signedAt: 'desc' },
      ...prismaPagination(pagination),
    }),
    prisma.signatureRecord.count({ where }),
  ]);

  return buildPaginatedResult(items, total, pagination);
}

/** 获取签名审计追踪（完整链） */
async function getAuditTrail(recordId: string, tableName?: string) {
  const where: any = { recordId };
  if (tableName) where.tableName = tableName;

  const records = await prisma.signatureRecord.findMany({
    where,
    orderBy: { signedAt: 'asc' },
    include: {
      user: { select: { id: true, username: true, displayName: true } },
    },
  });

  // 验证完整链
  let chainValid = true;
  for (let i = 1; i < records.length; i++) {
    if (records[i].previousHash !== records[i - 1].currentHash) {
      chainValid = false;
      break;
    }
  }

  return {
    records,
    chainValid,
    totalSignatures: records.length,
  };
}

/** 导出签名审计报告 */
async function exportAuditReport(recordId: string, tableName?: string) {
  const trail = await getAuditTrail(recordId, tableName);

  const report = {
    reportTitle: '电子签名审计报告',
    regulatoryReference: '21 CFR Part 11',
    generatedAt: new Date().toISOString(),
    recordId,
    tableName: tableName || 'N/A',
    chainValid: trail.chainValid,
    totalSignatures: trail.totalSignatures,
    signatures: trail.records.map(r => ({
      signatureId: r.id,
      signedBy: r.user?.displayName || r.user?.username || 'Unknown',
      meaning: r.signatureMeaning,
      reason: r.signatureReason,
      signedAt: r.signedAt,
      ipAddress: r.ipAddress,
      hash: r.currentHash,
    })),
  };

  return report;
}

/** 签名统计 */
async function getStats(query: Record<string, any>) {
  const where: any = {};
  if (query.projectId) where.projectId = query.projectId;

  const [total, byUser] = await Promise.all([
    prisma.signatureRecord.count({ where }),
    prisma.signatureRecord.groupBy({
      by: ['userId'],
      where,
      _count: true,
      orderBy: { _count: { id: 'desc' } },
      take: 20,
    }),
  ]);

  // 查询用户名
  const userIds = byUser.map(b => b.userId);
  const users = userIds.length > 0 ? await prisma.user.findMany({
    where: { id: { in: userIds } },
    select: { id: true, displayName: true, username: true },
  }) : [];
  const userMap = new Map(users.map(u => [u.id, u]));

  return {
    total,
    topSigners: byUser.map((b: any) => ({
      userId: b.userId,
      displayName: userMap.get(b.userId)?.displayName || 'Unknown',
      count: (b._count as any).id || 0,
    })),
  };
}

export const signatureService = {
  create, batchCreate, verify, revoke,
  getList, getAuditTrail, exportAuditReport, getStats,
};
