import { Router } from 'express';
import { formController } from './form.controller';
import { requirePermission } from '../../../shared/middleware/rbac';

const router = Router();

// 表单 CRUD
router.get('/', formController.list as any);
router.post('/', requirePermission('edc:form:create') as any, formController.create as any);
router.get('/:id', formController.getById as any);
router.put('/:id', requirePermission('edc:form:update') as any, formController.update as any);
router.delete('/:id', requirePermission('edc:form:delete') as any, formController.remove as any);

// 字段管理
router.post('/:id/fields', requirePermission('edc:form:design') as any, formController.addField as any);
router.put('/:id/fields/:fieldId', requirePermission('edc:form:design') as any, formController.updateField as any);
router.delete('/:id/fields/:fieldId', requirePermission('edc:form:design') as any, formController.removeField as any);

// 编辑核查规则
router.get('/:id/edit-check-rules', formController.getEditCheckRules as any);
router.post('/:id/edit-check-rules', requirePermission('edc:form:design') as any, formController.createEditCheckRule as any);
router.put('/:id/edit-check-rules/:ruleId', requirePermission('edc:form:design') as any, formController.updateEditCheckRule as any);
router.delete('/:id/edit-check-rules/:ruleId', requirePermission('edc:form:design') as any, formController.removeEditCheckRule as any);

// 版本与发布
router.post('/:id/publish', requirePermission('edc:form:publish') as any, formController.publish as any);
router.get('/:id/versions', formController.getVersions as any);
router.get('/:id/versions/:version', formController.getVersionDetail as any);
router.get('/:id/publications', formController.getPublications as any);

export default router;
