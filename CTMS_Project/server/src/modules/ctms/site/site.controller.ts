import { Request, Response, NextFunction } from 'express';
import { siteService } from './site.service';
import { createSiteSchema, updateSiteSchema, addSiteStaffSchema, updateSiteStaffSchema } from './site.dto';

// POST / - 创建中心
async function create(req: Request, res: Response, next: NextFunction) {
  try {
    const input = createSiteSchema.parse(req.body);
    const result = await siteService.create(input);
    res.status(201).json({ success: true, data: result });
  } catch (err) { next(err); }
}

// GET / - 中心列表
async function list(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await siteService.getList(req.query as Record<string, any>);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

// GET /:id - 中心详情
async function getById(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await siteService.getById(req.params.id);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

// PUT /:id - 更新中心
async function update(req: Request, res: Response, next: NextFunction) {
  try {
    const input = updateSiteSchema.parse(req.body);
    const result = await siteService.update(req.params.id, input);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

// DELETE /:id - 关闭中心
async function remove(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await siteService.remove(req.params.id);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

// POST /:id/staff - 添加中心人员
async function addStaff(req: Request, res: Response, next: NextFunction) {
  try {
    const input = addSiteStaffSchema.parse(req.body);
    const result = await siteService.addStaff(req.params.id, input);
    res.status(201).json({ success: true, data: result });
  } catch (err) { next(err); }
}

// PUT /:id/staff/:staffId - 更新中心人员
async function updateStaff(req: Request, res: Response, next: NextFunction) {
  try {
    const input = updateSiteStaffSchema.parse(req.body);
    const result = await siteService.updateStaff(req.params.id, req.params.staffId, input);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

// DELETE /:id/staff/:staffId - 移除中心人员
async function removeStaff(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await siteService.removeStaff(req.params.id, req.params.staffId);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

export const siteController = {
  create, list, getById, update, remove,
  addStaff, updateStaff, removeStaff,
};
