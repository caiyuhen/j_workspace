import { Router } from 'express';
import { userController } from '../controllers/user.controller';
import { authenticate } from '../middleware/auth';
import { authorize } from '../middleware/authorization';

const router = Router();

// All user routes require authentication
router.use(authenticate);

/**
 * @route   GET /api/v1/users
 * @desc    List all users (admin only)
 * @access  Private
 */
router.get(
  '/',
  authorize({ resource: 'user', action: 'read' }),
  userController.listUsers
);

/**
 * @route   GET /api/v1/users/:userId
 * @desc    Get user details
 * @access  Private
 */
router.get(
  '/:userId',
  authorize({ resource: 'user', action: 'read' }),
  userController.getUserDetail
);

/**
 * @route   PUT /api/v1/users/:userId
 * @desc    Update user information
 * @access  Private
 */
router.put(
  '/:userId',
  authorize({ resource: 'user', action: 'update' }),
  userController.updateUser
);

/**
 * @route   PUT /api/v1/users/:userId/status
 * @desc    Update user status
 * @access  Private
 */
router.put(
  '/:userId/status',
  authorize({ resource: 'user', action: 'update' }),
  userController.updateUserStatus
);

/**
 * @route   DELETE /api/v1/users/:userId
 * @desc    Delete user
 * @access  Private
 */
router.delete(
  '/:userId',
  authorize({ resource: 'user', action: 'delete' }),
  userController.deleteUser
);

/**
 * @route   POST /api/v1/users/:userId/reset-password
 * @desc    Force reset user password (admin only)
 * @access  Private
 */
router.post(
  '/:userId/reset-password',
  authorize({ resource: 'user', action: 'update' }),
  userController.resetUserPassword
);

export default router;
