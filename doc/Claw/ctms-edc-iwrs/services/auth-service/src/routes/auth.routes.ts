import { Router } from 'express';
import { authController } from '../controllers/auth.controller';
import { authenticate, optionalAuth } from '../middleware/auth';
import { authorize } from '../middleware/authorization';

const router = Router();

/**
 * @route   POST /api/v1/auth/register
 * @desc    Register a new user
 * @access  Public
 */
router.post('/register', optionalAuth, authController.register);

/**
 * @route   POST /api/v1/auth/login
 * @desc    Login and get access token
 * @access  Public
 */
router.post('/login', authController.login);

/**
 * @route   POST /api/v1/auth/refresh
 * @desc    Refresh access token
 * @access  Public (requires refresh token)
 */
router.post('/refresh', authController.refreshToken);

/**
 * @route   POST /api/v1/auth/logout
 * @desc    Logout and invalidate refresh token
 * @access  Private
 */
router.post('/logout', authenticate, authController.logout);

/**
 * @route   GET /api/v1/auth/profile
 * @desc    Get current user profile
 * @access  Private
 */
router.get('/profile', authenticate, authController.getProfile);

/**
 * @route   PUT /api/v1/auth/profile
 * @desc    Update current user profile
 * @access  Private
 */
router.put('/profile', authenticate, authController.updateProfile);

/**
 * @route   POST /api/v1/auth/change-password
 * @desc    Change current user password
 * @access  Private
 */
router.post('/change-password', authenticate, authController.changePassword);

/**
 * @route   POST /api/v1/auth/forgot-password
 * @desc    Request password reset token
 * @access  Public
 */
router.post('/forgot-password', authController.forgotPassword);

/**
 * @route   POST /api/v1/auth/reset-password
 * @desc    Reset password with token
 * @access  Public (requires valid reset token)
 */
router.post('/reset-password', authController.resetPassword);

export default router;
