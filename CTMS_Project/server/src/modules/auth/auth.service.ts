import prisma from '../../config/database';
import { LoginInput, RegisterInput } from './auth.dto';
import { generateAccessToken, generateRefreshToken, verifyRefreshToken, JwtPayload } from '../../shared/utils/jwt';
import { hashPassword, comparePassword } from '../../shared/utils/hash';
import { UnauthorizedError, ConflictError, BadRequestError } from '../../shared/errors/AppError';
import logger from '../../shared/utils/logger';

/**
 * 用户登录
 * 21 CFR Part 11 合规：记录登录事件到审计日志
 */
async function login(input: LoginInput, ip: string) {
  const { username, password } = input;

  // 查找用户
  const user = await prisma.user.findUnique({
    where: { username },
    include: { userRoles: { include: { role: { include: { rolePermissions: { include: { permission: true } } } } } } },
  });

  if (!user) {
    logger.warn('Login failed: user not found', { username, ip });
    throw new UnauthorizedError('用户名或密码错误');
  }

  if (user.status === 'locked') {
    throw new UnauthorizedError('账号已被锁定，请联系管理员');
  }

  // 验证密码
  const isValid = await comparePassword(password, user.passwordHash);
  if (!isValid) {
    logger.warn('Login failed: invalid password', { userId: user.id, username, ip });
    throw new UnauthorizedError('用户名或密码错误');
  }

  // 收集角色和权限
  const roles = user.userRoles.map(ur => ur.role.roleCode);
  const permissions = user.userRoles.flatMap(ur =>
    ur.role.rolePermissions.map(rp => rp.permission.permissionCode)
  );
  // 去重
  const uniquePermissions = [...new Set(permissions)];

  // 生成 Token
  const payload: JwtPayload = {
    userId: user.id,
    username: user.username,
    roles,
    permissions: uniquePermissions,
  };
  const accessToken = generateAccessToken(payload);
  const refreshToken = generateRefreshToken(user.id);

  // 更新最后登录时间
  await prisma.user.update({
    where: { id: user.id },
    data: { lastLoginAt: new Date() },
  });

  // 21 CFR Part 11 审计日志
  logger.info('User login', {
    audit: true,
    userId: user.id,
    username: user.username,
    eventType: 'AUTH_LOGIN',
    ipAddress: ip,
    message: `用户 ${user.username} 登录成功`,
  });

  return {
    user: {
      id: user.id,
      username: user.username,
      email: user.email,
      displayName: user.displayName,
      roles,
      permissions: uniquePermissions,
    },
    accessToken,
    refreshToken,
  };
}

/**
 * 用户注册
 */
async function register(input: RegisterInput) {
  const { username, email, password, displayName, phone } = input;

  // 检查用户名唯一
  const existingUser = await prisma.user.findFirst({
    where: { OR: [{ username }, { email }] },
  });
  if (existingUser) {
    throw new ConflictError('用户名或邮箱已存在');
  }

  // 哈希密码
  const passwordHash = await hashPassword(password);

  // 创建用户
  const user = await prisma.user.create({
    data: {
      username,
      email,
      passwordHash,
      displayName,
      phone,
      status: 'active',
    },
  });

  logger.info('User registered', { userId: user.id, username });

  return {
    id: user.id,
    username: user.username,
    email: user.email,
    displayName: user.displayName,
  };
}

/**
 * 刷新 Token
 */
async function refreshTokens(refreshTokenStr: string) {
  const { userId } = verifyRefreshToken(refreshTokenStr);

  const user = await prisma.user.findUnique({
    where: { id: userId },
    include: { userRoles: { include: { role: { include: { rolePermissions: { include: { permission: true } } } } } } },
  });

  if (!user || user.status !== 'active') {
    throw new UnauthorizedError('用户不存在或已被禁用');
  }

  const roles = user.userRoles.map(ur => ur.role.roleCode);
  const permissions = [...new Set(
    user.userRoles.flatMap(ur => ur.role.rolePermissions.map(rp => rp.permission.permissionCode))
  )];

  const payload: JwtPayload = {
    userId: user.id,
    username: user.username,
    roles,
    permissions,
  };

  const newAccessToken = generateAccessToken(payload);
  const newRefreshToken = generateRefreshToken(user.id);

  return { accessToken: newAccessToken, refreshToken: newRefreshToken };
}

/**
 * 获取当前用户信息
 */
async function getCurrentUser(userId: string) {
  const user = await prisma.user.findUnique({
    where: { id: userId },
    include: { userRoles: { include: { role: { include: { rolePermissions: { include: { permission: true } } } } } } },
  });

  if (!user) {
    throw new UnauthorizedError('用户不存在');
  }

  const roles = user.userRoles.map(ur => ur.role.roleCode);
  const permissions = user.userRoles.flatMap(ur =>
    ur.role.rolePermissions?.map(rp => rp.permission.permissionCode) || []
  );

  return {
    id: user.id,
    username: user.username,
    email: user.email,
    displayName: user.displayName,
    phone: user.phone,
    title: user.title,
    department: user.department,
    organization: user.organization,
    avatarUrl: user.avatarUrl,
    status: user.status,
    roles,
    permissions: [...new Set(permissions)],
    lastLoginAt: user.lastLoginAt,
  };
}

/**
 * 修改密码
 */
async function changePassword(userId: string, oldPassword: string, newPassword: string) {
  const user = await prisma.user.findUnique({ where: { id: userId } });
  if (!user) {
    throw new UnauthorizedError('用户不存在');
  }

  const isValid = await comparePassword(oldPassword, user.passwordHash);
  if (!isValid) {
    throw new BadRequestError('原密码不正确');
  }

  const newHash = await hashPassword(newPassword);
  await prisma.user.update({
    where: { id: userId },
    data: { passwordHash: newHash, passwordChangedAt: new Date() },
  });

  logger.info('Password changed', { userId });
}

export const authService = {
  login,
  register,
  refreshTokens,
  getCurrentUser,
  changePassword,
};
