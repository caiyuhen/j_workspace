import prisma from '../../config/database';
import { CreateNotificationInput, BatchCreateInput } from './notification.dto';
import { parsePagination, buildPaginatedResult, prismaPagination } from '../../shared/utils/pagination';
import { parseSort } from '../../shared/utils/sort';
import { NotFoundError, BadRequestError } from '../../shared/errors/AppError';
import logger from '../../shared/utils/logger';

const ALLOWED_SORT_FIELDS = ['status', 'channel', 'createdAt', 'sentAt', 'readAt'];

// ======= 渠道发送器 =======

interface SendResult {
  success: boolean;
  messageId?: string;
  error?: string;
}

/** 应用内通知 — 直接更新数据库状态 */
async function sendInApp(_recipientId: string, _title: string, _content: string): Promise<SendResult> {
  // 应用内通知已通过数据库记录存在，此处可扩展 WebSocket 推送
  return { success: true, messageId: `inapp_${Date.now()}` };
}

/** 微信模板消息发送（对接内网大模型接口的微信通知通道） */
async function sendWechat(recipientId: string, title: string, content: string): Promise<SendResult> {
  try {
    // 查询用户微信绑定
    const binding = await prisma.wechatUserBinding.findFirst({
      where: { userId: recipientId, channel: 'wechat', bindStatus: 'active' },
    });
    if (!binding?.openId) {
      return { success: false, error: '用户未绑定微信' };
    }

    // 实际对接微信模板消息 API（需配置 WECHAT_APPID / WECHAT_SECRET）
    // 此处为预留接口
    logger.info('WeChat notification queued', { openId: binding.openId, title });
    return { success: true, messageId: `wechat_${Date.now()}` };
  } catch (err: any) {
    return { success: false, error: err.message };
  }
}

/** 企业微信消息发送 */
async function sendWechatWork(recipientId: string, title: string, content: string): Promise<SendResult> {
  try {
    const binding = await prisma.wechatUserBinding.findFirst({
      where: { userId: recipientId, channel: 'wechat_work', bindStatus: 'active' },
    });
    if (!binding?.wecomUserId) {
      return { success: false, error: '用户未绑定企业微信' };
    }

    // 实际对接企业微信 API（需配置 WECOM_CORPID / WECOM_AGENTID / WECOM_SECRET）
    logger.info('WeCom notification queued', { wecomUserId: binding.wecomUserId, title });
    return { success: true, messageId: `wecom_${Date.now()}` };
  } catch (err: any) {
    return { success: false, error: err.message };
  }
}

/** 邮件发送（预留 SMTP 接口） */
async function sendEmail(recipientId: string, title: string, content: string): Promise<SendResult> {
  try {
    const user = await prisma.user.findUnique({
      where: { id: recipientId },
      select: { email: true, displayName: true },
    });
    if (!user?.email) {
      return { success: false, error: '用户无邮箱地址' };
    }

    // 实际对接 SMTP 服务（需配置 SMTP_HOST / SMTP_PORT / SMTP_USER / SMTP_PASS）
    logger.info('Email notification queued', { to: user.email, title });
    return { success: true, messageId: `email_${Date.now()}` };
  } catch (err: any) {
    return { success: false, error: err.message };
  }
}

/** 短信发送（预留接口） */
async function sendSms(recipientId: string, title: string, content: string): Promise<SendResult> {
  try {
    const user = await prisma.user.findUnique({
      where: { id: recipientId },
      select: { phone: true },
    });
    if (!user?.phone) {
      return { success: false, error: '用户无手机号码' };
    }

    logger.info('SMS notification queued', { phone: user.phone, title });
    return { success: true, messageId: `sms_${Date.now()}` };
  } catch (err: any) {
    return { success: false, error: err.message };
  }
}

/** 渠道路由 */
const channelSenders: Record<string, (recipientId: string, title: string, content: string) => Promise<SendResult>> = {
  in_app: sendInApp,
  wechat: sendWechat,
  wechat_work: sendWechatWork,
  email: sendEmail,
  sms: sendSms,
};

// ======= 通知 CRUD =======

async function create(input: CreateNotificationInput) {
  const notification = await prisma.notification.create({
    data: {
      recipientId: input.recipientId,
      channel: input.channel || 'in_app',
      title: input.title,
      content: input.content,
      businessType: input.businessType,
      businessId: input.businessId,
      status: 'pending',
    },
  });

  return notification;
}

async function batchCreate(input: BatchCreateInput) {
  const notifications = await prisma.notification.createMany({
    data: input.recipientIds.map(recipientId => ({
      recipientId,
      channel: input.channel,
      title: input.title,
      content: input.content,
      businessType: input.businessType,
      businessId: input.businessId,
      status: 'pending',
    })),
  });

  return { count: notifications.count };
}

/**
 * 发送通知 — 实际调用对应渠道发送器
 */
async function send(id: string) {
  const notification = await prisma.notification.findUnique({ where: { id } });
  if (!notification) throw new NotFoundError('Notification', id);

  const sender = channelSenders[notification.channel];
  if (!sender) throw new BadRequestError(`不支持的通知渠道: ${notification.channel}`);

  const result = await sender(notification.recipientId, notification.title, notification.content);

  if (result.success) {
    const updated = await prisma.notification.update({
      where: { id },
      data: { status: 'sent', sentAt: new Date() },
    });

    logger.info('Notification sent', {
      eventType: 'NOTIFICATION_SENT',
      channel: notification.channel,
      recipientId: notification.recipientId,
      message: `发送通知到用户 ${notification.recipientId}: ${notification.title}`,
    });

    return updated;
  } else {
    await prisma.notification.update({
      where: { id },
      data: { status: 'failed' },
    });

    logger.error('Notification send failed', {
      notificationId: id,
      channel: notification.channel,
      error: result.error,
    });

    throw new BadRequestError(`通知发送失败: ${result.error}`);
  }
}

/**
 * 批量发送待发通知
 */
async function sendPending(channel?: string) {
  const where: any = { status: 'pending' };
  if (channel) where.channel = channel;

  const pending = await prisma.notification.findMany({
    where,
    take: 100,
    orderBy: { createdAt: 'asc' },
  });

  const results = await Promise.allSettled(
    pending.map(n => send(n.id))
  );

  const succeeded = results.filter(r => r.status === 'fulfilled').length;
  const failed = results.filter(r => r.status === 'rejected').length;

  return { total: pending.length, succeeded, failed };
}

async function getList(query: Record<string, any>) {
  const pagination = parsePagination(query);
  const sort = parseSort(query, ALLOWED_SORT_FIELDS, 'createdAt', 'desc');

  const where: any = {};
  if (query.recipientId) where.recipientId = query.recipientId;
  if (query.status) where.status = query.status;
  if (query.channel) where.channel = query.channel;
  if (query.businessType) where.businessType = query.businessType;
  if (query.isUnread !== undefined) {
    where.readAt = query.isUnread === 'true' ? null : { not: null };
  }

  const [notifications, total] = await Promise.all([
    prisma.notification.findMany({
      where, ...prismaPagination(pagination),
      include: {
        user: { select: { id: true, username: true, displayName: true } },
      },
      orderBy: sort.orderBy,
    }),
    prisma.notification.count({ where }),
  ]);

  return buildPaginatedResult(notifications, total, pagination);
}

async function getById(id: string) {
  const notification = await prisma.notification.findUnique({
    where: { id },
    include: { user: { select: { id: true, username: true, displayName: true } } },
  });
  if (!notification) throw new NotFoundError('Notification', id);
  return notification;
}

async function markAsRead(id: string) {
  const notification = await prisma.notification.findUnique({ where: { id } });
  if (!notification) throw new NotFoundError('Notification', id);

  return prisma.notification.update({
    where: { id },
    data: { status: 'delivered', readAt: new Date() },
  });
}

async function markAllAsRead(recipientId: string) {
  const result = await prisma.notification.updateMany({
    where: { recipientId, readAt: null },
    data: { status: 'delivered', readAt: new Date() },
  });

  return { count: result.count };
}

async function remove(id: string) {
  const notification = await prisma.notification.findUnique({ where: { id } });
  if (!notification) throw new NotFoundError('Notification', id);

  await prisma.notification.delete({ where: { id } });
  return { message: '通知已删除' };
}

async function getUnreadCount(recipientId: string) {
  return prisma.notification.count({
    where: { recipientId, readAt: null },
  });
}

/**
 * 按业务类型统计通知数量
 */
async function getStatsByBusinessType(projectId?: string) {
  const where: any = {};
  if (projectId) where.businessId = projectId;

  const stats = await prisma.notification.groupBy({
    by: ['businessType', 'channel', 'status'],
    where,
    _count: true,
  });

  return stats;
}

/**
 * 清理过期通知（超过指定天数）
 */
async function cleanExpired(days: number = 90) {
  const threshold = new Date();
  threshold.setDate(threshold.getDate() - days);

  const result = await prisma.notification.deleteMany({
    where: {
      createdAt: { lt: threshold },
      status: { in: ['delivered', 'failed'] },
    },
  });

  logger.info('Expired notifications cleaned', { count: result.count, days });
  return { count: result.count };
}

export const notificationService = {
  create, batchCreate, send, sendPending,
  getList, getById, markAsRead, markAllAsRead, remove, getUnreadCount,
  getStatsByBusinessType, cleanExpired,
};
