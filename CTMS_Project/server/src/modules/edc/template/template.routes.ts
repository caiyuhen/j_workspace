import { Router } from 'express';
import { templateController } from './template.controller';
import { requirePermission } from '../../../shared/middleware/rbac';

const router = Router();

// 模板列表
router.get('/', templateController.list as any);
// 创建模板
router.post('/', requirePermission('edc:template:create') as any, templateController.create as any);
// 模板详情
router.get('/:id', templateController.getById as any);
// 更新模板
router.put('/:id', requirePermission('edc:template:update') as any, templateController.update as any);
// 发布模板
router.post('/:id/publish', requirePermission('edc:template:publish') as any, templateController.publish as any);
// 废弃模板
router.post('/:id/deprecate', requirePermission('edc:template:publish') as any, templateController.deprecate as any);
// 克隆模板
router.post('/:id/clone', requirePermission('edc:template:create') as any, templateController.clone as any);

export default router;
