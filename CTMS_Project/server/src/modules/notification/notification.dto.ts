import { z } from 'zod';

// ========== 通知管理 DTO ==========

export const createNotificationSchema = z.object({
  recipientId: z.string().uuid(),
  channel: z.enum(['in_app', 'email', 'wechat', 'wechat_work', 'sms']).optional().default('in_app'),
  title: z.string().min(1, '通知标题不能为空'),
  content: z.string().min(1, '通知内容不能为空'),
  businessType: z.string().optional(),
  businessId: z.string().uuid().optional(),
});
export type CreateNotificationInput = z.infer<typeof createNotificationSchema>;

export const batchCreateSchema = z.object({
  recipientIds: z.array(z.string().uuid()).min(1),
  channel: z.enum(['in_app', 'email', 'wechat', 'wechat_work', 'sms']).optional().default('in_app'),
  title: z.string().min(1),
  content: z.string().min(1),
  businessType: z.string().optional(),
  businessId: z.string().uuid().optional(),
});
export type BatchCreateInput = z.infer<typeof batchCreateSchema>;
