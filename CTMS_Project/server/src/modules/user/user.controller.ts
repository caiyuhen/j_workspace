import { Request, Response, NextFunction } from 'express';
import { userService } from './user.service';
import { createUserSchema, updateUserSchema, assignRolesSchema, changeUserPasswordSchema } from './user.dto';

// POST / - 创建用户
async function create(req: Request, res: Response, next: NextFunction) {
  try {
    const input = createUserSchema.parse(req.body);
    const result = await userService.create(input);
    res.status(201).json({ success: true, data: result });
  } catch (err) { next(err); }
}

// GET / - 用户列表
async function list(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await userService.getList(req.query as Record<string, any>);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

// GET /:id - 用户详情
async function getById(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await userService.getUserById(req.params.id);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

// PUT /:id - 更新用户
async function update(req: Request, res: Response, next: NextFunction) {
  try {
    const input = updateUserSchema.parse(req.body);
    const result = await userService.update(req.params.id, input);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

// DELETE /:id - 删除用户（软删除）
async function remove(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await userService.remove(req.params.id);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

// POST /:id/roles - 分配角色
async function assignRoles(req: Request, res: Response, next: NextFunction) {
  try {
    const input = assignRolesSchema.parse(req.body);
    const result = await userService.assignRoles(req.params.id, input);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

// POST /:id/reset-password - 重置密码
async function resetPassword(req: Request, res: Response, next: NextFunction) {
  try {
    const input = changeUserPasswordSchema.parse(req.body);
    const result = await userService.resetPassword(req.params.id, input.newPassword);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

export const userController = { create, list, getById, update, remove, assignRoles, resetPassword };
