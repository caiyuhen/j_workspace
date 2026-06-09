import prisma from '../../../config/database';
import { Prisma } from '@prisma/client';
import {
  CreateDocumentInput, UpdateDocumentInput,
  UploadDocumentVersionInput, UpdateDocumentStatusInput, BulkUpdateStatusInput,
} from './document.dto';
import { parsePagination, buildPaginatedResult, prismaPagination } from '../../../shared/utils/pagination';
import { parseSort } from '../../../shared/utils/sort';
import { NotFoundError, ConflictError } from '../../../shared/errors/AppError';
import logger from '../../../shared/utils/logger';

const ALLOWED_SORT_FIELDS = ['documentName', 'documentCode', 'tmfSection', 'documentType', 'status', 'createdAt', 'updatedAt'];

// ========== 文档 CRUD ==========

async function create(input: CreateDocumentInput, userId: string) {
  const project = await prisma.project.findUnique({ where: { id: input.projectId } });
  if (!project) throw new NotFoundError('Project', input.projectId);

  const existing = await prisma.tmfDocument.findUnique({
    where: { projectId_documentCode: { projectId: input.projectId, documentCode: input.documentCode } },
  });
  if (existing) throw new ConflictError('文档编码已存在');

  const doc = await prisma.tmfDocument.create({
    data: {
      ...input,
      createdBy: userId,
      tags: input.tags || [],
      metadata: (input.metadata as any) || Prisma.JsonNull,
    },
  });

  logger.info('TMF document created', {
    audit: true, eventType: 'TMF_DOC_CREATE', projectId: input.projectId,
    message: `创建文档: ${input.documentName} [${input.tmfSection}]`,
  });

  return doc;
}

async function getList(query: Record<string, any>) {
  const pagination = parsePagination(query);
  const sort = parseSort(query, ALLOWED_SORT_FIELDS);

  const where: any = {};
  if (query.projectId) where.projectId = query.projectId;
  if (query.tmfSection) where.tmfSection = query.tmfSection;
  if (query.documentType) where.documentType = query.documentType;
  if (query.status) where.status = query.status;
  if (query.isRequired !== undefined) where.isRequired = query.isRequired === 'true';
  if (query.siteId) where.siteId = query.siteId;
  if (query.keyword) {
    where.OR = [
      { documentName: { contains: query.keyword, mode: 'insensitive' } },
      { documentCode: { contains: query.keyword, mode: 'insensitive' } },
      { description: { contains: query.keyword, mode: 'insensitive' } },
    ];
  }

  const [documents, total] = await Promise.all([
    prisma.tmfDocument.findMany({
      where, ...prismaPagination(pagination),
      include: {
        _count: { select: { versions: true } },
      },
      orderBy: sort.orderBy,
    }),
    prisma.tmfDocument.count({ where }),
  ]);

<<<<<<< HEAD
  const userIds = [...new Set(documents.map(d => d.uploadedBy || d.createdBy).filter(Boolean))];
  const users = await prisma.user.findMany({ where: { id: { in: userIds as string[] } }, select: { id: true, displayName: true } });
    const userMap = Object.fromEntries(users.map(u => [u.id, u.displayName]));

  const mappedDocuments = documents.map(d => ({
    ...d,
    uploadedBy: userMap[d.uploadedBy || d.createdBy] || d.uploadedBy || d.createdBy,
  }));

  return buildPaginatedResult(mappedDocuments, total, pagination);
=======
  return buildPaginatedResult(documents, total, pagination);
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
}

async function getById(id: string) {
  const doc = await prisma.tmfDocument.findUnique({
    where: { id },
    include: {
      versions: { orderBy: { uploadedAt: 'desc' } },
    },
  });

  if (!doc) throw new NotFoundError('TmfDocument', id);
  return doc;
}

async function update(id: string, input: UpdateDocumentInput) {
  const doc = await prisma.tmfDocument.findUnique({ where: { id } });
  if (!doc) throw new NotFoundError('TmfDocument', id);

  const updated = await prisma.tmfDocument.update({
    where: { id },
    data: input,
  });

  logger.info('TMF document updated', {
    audit: true, eventType: 'TMF_DOC_UPDATE', projectId: doc.projectId,
    message: `更新文档: ${doc.documentName}`,
  });

  return updated;
}

async function remove(id: string) {
  const doc = await prisma.tmfDocument.findUnique({ where: { id } });
  if (!doc) throw new NotFoundError('TmfDocument', id);
  if (doc.status === 'approved') throw new ConflictError('已审批的文档不能删除，请先归档');

  await prisma.tmfDocument.delete({ where: { id } });

  logger.info('TMF document deleted', {
    audit: true, eventType: 'TMF_DOC_DELETE', projectId: doc.projectId,
    message: `删除文档: ${doc.documentName}`,
  });

  return { success: true };
}

// ========== 版本管理 ==========

async function uploadVersion(documentId: string, input: UploadDocumentVersionInput, userId: string) {
  const doc = await prisma.tmfDocument.findUnique({ where: { id: documentId } });
  if (!doc) throw new NotFoundError('TmfDocument', documentId);

  // 计算新版本号
  const versions = await prisma.tmfDocumentVersion.findMany({
    where: { documentId },
    orderBy: { uploadedAt: 'desc' },
    select: { version: true },
    take: 1,
  });

  const lastVersion = versions[0]?.version || '0.0';
  const parts = lastVersion.split('.');
  const newVersion = `${parseInt(parts[0] || '0')}.${parseInt(parts[1] || '0') + 1}`;

  const version = await prisma.tmfDocumentVersion.create({
    data: {
      documentId,
      version: newVersion,
      changeLog: input.changeLog || `上传版本 ${newVersion}`,
      fileUrl: input.fileUrl,
      fileSize: input.fileSize,
      mimeType: input.mimeType,
      uploadedBy: userId,
    },
  });

  // 更新主文档
  await prisma.tmfDocument.update({
    where: { id: documentId },
    data: {
      version: newVersion,
      fileUrl: input.fileUrl,
      fileSize: input.fileSize,
      mimeType: input.mimeType,
      uploadedBy: userId,
    },
  });

  logger.info('TMF document version uploaded', {
    audit: true, eventType: 'TMF_DOC_VERSION_UPLOAD', projectId: doc.projectId,
    message: `上传文档版本: ${doc.documentName} v${newVersion}`,
  });

  return version;
}

async function getVersionDetail(documentId: string, version: string) {
  const doc = await prisma.tmfDocument.findUnique({ where: { id: documentId } });
  if (!doc) throw new NotFoundError('TmfDocument', documentId);

  const versionData = await prisma.tmfDocumentVersion.findUnique({
    where: { documentId_version: { documentId, version } },
  });

  if (!versionData) throw new NotFoundError('TmfDocumentVersion', `${documentId}/${version}`);
  return versionData;
}

async function getVersions(documentId: string) {
  const doc = await prisma.tmfDocument.findUnique({ where: { id: documentId } });
  if (!doc) throw new NotFoundError('TmfDocument', documentId);

<<<<<<< HEAD
  const versions = await prisma.tmfDocumentVersion.findMany({
    where: { documentId },
    orderBy: { uploadedAt: 'desc' },
  });

  const userIds = [...new Set(versions.map(v => v.uploadedBy).filter(Boolean))];
  const users = await prisma.user.findMany({ where: { id: { in: userIds } }, select: { id: true, displayName: true } });
  const userMap = Object.fromEntries(users.map(u => [u.id, u.displayName]));

  return versions.map(v => ({
    ...v,
    uploadedBy: userMap[v.uploadedBy] || v.uploadedBy,
  }));
=======
  return prisma.tmfDocumentVersion.findMany({
    where: { documentId },
    orderBy: { uploadedAt: 'desc' },
  });
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
}

// ========== 状态管理（审批） ==========

async function updateStatus(id: string, input: UpdateDocumentStatusInput, userId: string) {
  const doc = await prisma.tmfDocument.findUnique({ where: { id } });
  if (!doc) throw new NotFoundError('TmfDocument', id);

  const updated = await prisma.tmfDocument.update({
    where: { id },
    data: { status: input.status },
  });

  logger.info('TMF document status updated', {
    audit: true, eventType: 'TMF_DOC_STATUS_CHANGE', projectId: doc.projectId,
    message: `文档状态变更: ${doc.documentName} → ${input.status}`,
  });

  return updated;
}

async function bulkUpdateStatus(input: BulkUpdateStatusInput, userId: string) {
  const result = await prisma.tmfDocument.updateMany({
    where: { id: { in: input.documentIds } },
    data: { status: input.status },
  });

  logger.info('TMF documents bulk status update', {
    audit: true, eventType: 'TMF_DOC_BULK_STATUS',
    message: `批量更新 ${result.count} 个文档状态为 ${input.status}`,
  });

  return { updatedCount: result.count };
}

// ========== 统计 ==========

async function getCompletionStats(projectId: string) {
  const project = await prisma.project.findUnique({ where: { id: projectId } });
  if (!project) throw new NotFoundError('Project', projectId);

  const [total, completed, pending, overdue] = await Promise.all([
    prisma.tmfDocument.count({ where: { projectId } }),
    prisma.tmfDocument.count({ where: { projectId, status: 'approved' } }),
    prisma.tmfDocument.count({ where: { projectId, status: { in: ['draft', 'pending_review'] } } }),
    prisma.tmfDocument.count({
      where: {
        projectId,
        status: { in: ['draft', 'pending_review'] },
        expectedDate: { lt: new Date() },
      },
    }),
  ]);

  return { total, completed, pending, overdue, completionRate: total > 0 ? (completed / total) * 100 : 0 };
}

export const documentService = {
  create, getList, getById, update, remove,
  uploadVersion, getVersionDetail, getVersions,
  updateStatus, bulkUpdateStatus,
  getCompletionStats,
};
