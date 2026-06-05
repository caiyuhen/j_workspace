import { Request, Response, NextFunction } from 'express';
import { documentService } from './document.service';
import {
  createDocumentSchema, updateDocumentSchema,
  uploadDocumentVersionSchema, updateDocumentStatusSchema,
  bulkUpdateStatusSchema,
} from './document.dto';

async function create(req: Request, res: Response, next: NextFunction) {
  try {
    const input = createDocumentSchema.parse(req.body);
    const userId = (req as any).user?.userId;
    const result = await documentService.create(input, userId);
    res.status(201).json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function list(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await documentService.getList(req.query as Record<string, any>);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function getById(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await documentService.getById(req.params.id);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function update(req: Request, res: Response, next: NextFunction) {
  try {
    const input = updateDocumentSchema.parse(req.body);
    const result = await documentService.update(req.params.id, input);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function remove(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await documentService.remove(req.params.id);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

// 版本管理
async function uploadVersion(req: Request, res: Response, next: NextFunction) {
  try {
    const input = uploadDocumentVersionSchema.parse(req.body);
    const userId = (req as any).user?.userId;
    const result = await documentService.uploadVersion(req.params.id, input, userId);
    res.status(201).json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function getVersions(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await documentService.getVersions(req.params.id);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function getVersionDetail(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await documentService.getVersionDetail(req.params.id, req.params.version);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

// 状态管理
async function updateStatus(req: Request, res: Response, next: NextFunction) {
  try {
    const input = updateDocumentStatusSchema.parse(req.body);
    const userId = (req as any).user?.userId;
    const result = await documentService.updateStatus(req.params.id, input, userId);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function bulkUpdateStatus(req: Request, res: Response, next: NextFunction) {
  try {
    const input = bulkUpdateStatusSchema.parse(req.body);
    const userId = (req as any).user?.userId;
    const result = await documentService.bulkUpdateStatus(input, userId);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

// 统计
async function getCompletionStats(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await documentService.getCompletionStats(req.query.projectId as string);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

export const documentController = {
  create, list, getById, update, remove,
  uploadVersion, getVersions, getVersionDetail,
  updateStatus, bulkUpdateStatus, getCompletionStats,
};
