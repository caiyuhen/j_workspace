import { Request, Response } from 'express';
import { logger } from '../utils/logger';
import { userService } from '../services/user.service';
import { userUpdateSchema } from '../dto/auth.dto';

/**
 * User Controller
 * Handles user management endpoints
 */
export class UserController {
  /**
   * GET /api/v1/users
   * List all users with pagination and filtering
   */
  async listUsers(req: Request, res: Response) {
    try {
      const page = parseInt(req.query.page as string) || 1;
      const limit = parseInt(req.query.limit as string) || 20;
      const search = req.query.search as string;
      const status = req.query.status as string;

      logger.info('Listing users', {
        userId: req.user!.id,
        tenantId: req.user!.tenantId,
        page,
        limit,
        search,
        status,
      });

      const result = await userService.getUsers(
        req.user!.tenantId,
        { page, limit, search, status }
      );

      res.json({
        success: true,
        data: result,
      });
    } catch (error) {
      logger.error('Failed to list users', {
        userId: req.user!.id,
        error: error instanceof Error ? error.message : 'Unknown error',
      });
      res.status(500).json({
        success: false,
        message: 'Failed to list users',
      });
    }
  }

  /**
   * GET /api/v1/users/:userId
   * Get user details by ID
   */
  async getUserDetail(req: Request, res: Response) {
    try {
      const { userId } = req.params;

      logger.info('Getting user detail', {
        userId: req.user!.id,
        targetUserId: userId,
      });

      const user = await userService.getUserById(req.user!.tenantId, userId);

      if (!user) {
        res.status(404).json({
          success: false,
          message: 'User not found',
        });
        return;
      }

      res.json({
        success: true,
        data: user,
      });
    } catch (error) {
      logger.error('Failed to get user detail', {
        userId: req.user!.id,
        error: error instanceof Error ? error.message : 'Unknown error',
      });
      res.status(500).json({
        success: false,
        message: 'Failed to get user detail',
      });
    }
  }

  /**
   * PUT /api/v1/users/:userId
   * Update user information
   */
  async updateUser(req: Request, res: Response) {
    try {
      const { userId } = req.params;
      const data = userUpdateSchema.parse(req.body);

      logger.info('Updating user', {
        userId: req.user!.id,
        targetUserId: userId,
        updates: Object.keys(data),
      });

      const user = await userService.updateUser(req.user!.tenantId, userId, data);

      res.json({
        success: true,
        message: 'User updated successfully',
        data: user,
      });
    } catch (error) {
      if (error instanceof Error && error.message.includes('ZodError')) {
        res.status(400).json({
          success: false,
          message: 'Invalid request data',
          details: error.message,
        });
        return;
      }

      logger.error('Failed to update user', {
        userId: req.user!.id,
        error: error instanceof Error ? error.message : 'Unknown error',
      });
      res.status(500).json({
        success: false,
        message: 'Failed to update user',
      });
    }
  }

  /**
   * PUT /api/v1/users/:userId/status
   * Update user status (activate, deactivate, suspend, unlock)
   */
  async updateUserStatus(req: Request, res: Response) {
    try {
      const { userId } = req.params;
      const { status } = req.body;

      logger.info('Updating user status', {
        userId: req.user!.id,
        targetUserId: userId,
        newStatus: status,
      });

      const user = await userService.updateUserStatus(req.user!.tenantId, userId, status);

      res.json({
        success: true,
        message: 'User status updated successfully',
        data: user,
      });
    } catch (error) {
      logger.error('Failed to update user status', {
        userId: req.user!.id,
        error: error instanceof Error ? error.message : 'Unknown error',
      });
      res.status(500).json({
        success: false,
        message: 'Failed to update user status',
      });
    }
  }

  /**
   * DELETE /api/v1/users/:userId
   * Soft delete a user
   */
  async deleteUser(req: Request, res: Response) {
    try {
      const { userId } = req.params;

      logger.warn('Deleting user', {
        userId: req.user!.id,
        targetUserId: userId,
      });

      await userService.deleteUser(req.user!.tenantId, userId);

      res.json({
        success: true,
        message: 'User deleted successfully',
      });
    } catch (error) {
      logger.error('Failed to delete user', {
        userId: req.user!.id,
        error: error instanceof Error ? error.message : 'Unknown error',
      });
      res.status(500).json({
        success: false,
        message: 'Failed to delete user',
      });
    }
  }

  /**
   * POST /api/v1/users/:userId/reset-password
   * Force reset user password (admin only)
   */
  async resetUserPassword(req: Request, res: Response) {
    try {
      const { userId } = req.params;
      const { newPassword } = req.body;

      logger.warn('Resetting user password', {
        userId: req.user!.id,
        targetUserId: userId,
      });

      // This would be implemented in userService
      // For now, return not implemented
      res.status(501).json({
        success: false,
        message: 'Not implemented yet',
      });
    } catch (error) {
      logger.error('Failed to reset user password', {
        userId: req.user!.id,
        error: error instanceof Error ? error.message : 'Unknown error',
      });
      res.status(500).json({
        success: false,
        message: 'Failed to reset user password',
      });
    }
  }
}

export const userController = new UserController();
