import { Request, Response } from 'express';
import { logger } from '../utils/logger';
import { roleService } from '../services/role.service';
import { createRoleSchema, updateRoleSchema } from '../dto/auth.dto';

/**
 * Role Controller
 * Handles role management endpoints
 */
export class RoleController {
  /**
   * POST /api/v1/roles
   * Create a new role
   */
  async createRole(req: Request, res: Response) {
    try {
      const data = createRoleSchema.parse(req.body);

      logger.info('Creating role', {
        userId: req.user!.id,
        tenantId: req.user!.tenantId,
        role: data.name,
      });

      const role = await roleService.createRole(req.user!.tenantId, data);

      res.status(201).json({
        success: true,
        message: 'Role created successfully',
        data: role,
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

      logger.error('Failed to create role', {
        userId: req.user!.id,
        error: error instanceof Error ? error.message : 'Unknown error',
      });
      res.status(500).json({
        success: false,
        message: 'Failed to create role',
      });
    }
  }

  /**
   * GET /api/v1/roles
   * List all roles
   */
  async listRoles(req: Request, res: Response) {
    try {
      logger.info('Listing roles', {
        userId: req.user!.id,
        tenantId: req.user!.tenantId,
      });

      const roles = await roleService.getRoles(req.user!.tenantId);

      res.json({
        success: true,
        data: roles,
      });
    } catch (error) {
      logger.error('Failed to list roles', {
        userId: req.user!.id,
        error: error instanceof Error ? error.message : 'Unknown error',
      });
      res.status(500).json({
        success: false,
        message: 'Failed to list roles',
      });
    }
  }

  /**
   * GET /api/v1/roles/:roleId
   * Get role details by ID
   */
  async getRoleDetail(req: Request, res: Response) {
    try {
      const { roleId } = req.params;

      logger.info('Getting role detail', {
        userId: req.user!.id,
        roleId,
      });

      const roles = await roleService.getRoles(req.user!.tenantId);
      const role = roles.find((r) => r.id === roleId);

      if (!role) {
        res.status(404).json({
          success: false,
          message: 'Role not found',
        });
        return;
      }

      res.json({
        success: true,
        data: role,
      });
    } catch (error) {
      logger.error('Failed to get role detail', {
        userId: req.user!.id,
        error: error instanceof Error ? error.message : 'Unknown error',
      });
      res.status(500).json({
        success: false,
        message: 'Failed to get role detail',
      });
    }
  }

  /**
   * PUT /api/v1/roles/:roleId
   * Update role
   */
  async updateRole(req: Request, res: Response) {
    try {
      const { roleId } = req.params;
      const data = updateRoleSchema.parse(req.body);

      logger.info('Updating role', {
        userId: req.user!.id,
        roleId,
        updates: Object.keys(data),
      });

      const role = await roleService.updateRole(req.user!.tenantId, roleId, data);

      res.json({
        success: true,
        message: 'Role updated successfully',
        data: role,
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

      logger.error('Failed to update role', {
        userId: req.user!.id,
        error: error instanceof Error ? error.message : 'Unknown error',
      });
      res.status(500).json({
        success: false,
        message: 'Failed to update role',
      });
    }
  }

  /**
   * DELETE /api/v1/roles/:roleId
   * Delete a role (soft delete - first revoke from all users)
   */
  async deleteRole(req: Request, res: Response) {
    try {
      const { roleId } = req.params;

      logger.warn('Deleting role', {
        userId: req.user!.id,
        roleId,
      });

      // Note: This would need implementation in roleService
      // For now, return not implemented
      res.status(501).json({
        success: false,
        message: 'Not implemented yet',
      });
    } catch (error) {
      logger.error('Failed to delete role', {
        userId: req.user!.id,
        error: error instanceof Error ? error.message : 'Unknown error',
      });
      res.status(500).json({
        success: false,
        message: 'Failed to delete role',
      });
    }
  }

  /**
   * POST /api/v1/roles/:roleId/assign
   * Assign role to a user
   */
  async assignRole(req: Request, res: Response) {
    try {
      const { roleId } = req.params;
      const { userId } = req.body;

      logger.info('Assigning role to user', {
        userId: req.user!.id,
        roleId,
        targetUserId: userId,
      });

      await roleService.assignRole(req.user!.tenantId, userId, roleId);

      res.json({
        success: true,
        message: 'Role assigned successfully',
      });
    } catch (error) {
      logger.error('Failed to assign role', {
        userId: req.user!.id,
        error: error instanceof Error ? error.message : 'Unknown error',
      });
      res.status(500).json({
        success: false,
        message: 'Failed to assign role',
      });
    }
  }

  /**
   * DELETE /api/v1/roles/:roleId/revoke
   * Revoke role from a user
   */
  async revokeRole(req: Request, res: Response) {
    try {
      const { roleId } = req.params;
      const { userId } = req.body;

      logger.info('Revoking role from user', {
        userId: req.user!.id,
        roleId,
        targetUserId: userId,
      });

      await roleService.revokeRole(req.user!.tenantId, userId, roleId);

      res.json({
        success: true,
        message: 'Role revoked successfully',
      });
    } catch (error) {
      logger.error('Failed to revoke role', {
        userId: req.user!.id,
        error: error instanceof Error ? error.message : 'Unknown error',
      });
      res.status(500).json({
        success: false,
        message: 'Failed to revoke role',
      });
    }
  }

  /**
   * GET /api/v1/users/:userId/roles
   * Get all roles for a specific user
   */
  async getUserRoles(req: Request, res: Response) {
    try {
      const { userId } = req.params;

      logger.info('Getting user roles', {
        userId: req.user!.id,
        targetUserId: userId,
      });

      const roles = await roleService.getUserRoles(req.user!.tenantId, userId);

      res.json({
        success: true,
        data: roles,
      });
    } catch (error) {
      logger.error('Failed to get user roles', {
        userId: req.user!.id,
        error: error instanceof Error ? error.message : 'Unknown error',
      });
      res.status(500).json({
        success: false,
        message: 'Failed to get user roles',
      });
    }
  }
}

export const roleController = new RoleController();
