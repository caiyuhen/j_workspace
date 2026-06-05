import { Router } from 'express';
import { roleController } from '../controllers/role.controller';
import { authenticate } from '../middleware/auth';
import { authorize } from '../middleware/authorization';

const router = Router();

// All role routes require authentication
router.use(authenticate);

/**
 * @route   POST /api/v1/roles
 * @desc    Create a new role
 * @access  Private (admin only)
 */
router.post(
  '/',
  authorize({ resource: 'role', action: 'create' }),
  roleController.createRole
);

/**
 * @route   GET /api/v1/roles
 * @desc    List all roles
 * @access  Private
 */
router.get('/', roleController.listRoles);

/**
 * @route   GET /api/v1/roles/:roleId
 * @desc    Get role details
 * @access  Private
 */
router.get('/:roleId', roleController.getRoleDetail);

/**
 * @route   PUT /api/v1/roles/:roleId
 * @desc    Update role
 * @access  Private (admin only)
 */
router.put(
  '/:roleId',
  authorize({ resource: 'role', action: 'update' }),
  roleController.updateRole
);

/**
 * @route   DELETE /api/v1/roles/:roleId
 * @desc    Delete a role
 * @access  Private (admin only)
 */
router.delete(
  '/:roleId',
  authorize({ resource: 'role', action: 'delete' }),
  roleController.deleteRole
);

/**
 * @route   POST /api/v1/roles/:roleId/assign
 * @desc    Assign role to a user
 * @access  Private (admin only)
 */
router.post(
  '/:roleId/assign',
  authorize({ resource: 'role', action: 'update' }),
  roleController.assignRole
);

/**
 * @route   DELETE /api/v1/roles/:roleId/revoke
 * @desc    Revoke role from a user
 * @access  Private (admin only)
 */
router.delete(
  '/:roleId/revoke',
  authorize({ resource: 'role', action: 'update' }),
  roleController.revokeRole
);

/**
 * @route   GET /api/v1/users/:userId/roles
 * @desc    Get all roles for a specific user
 * @access  Private
 */
router.get('/users/:userId/roles', roleController.getUserRoles);

export default router;
