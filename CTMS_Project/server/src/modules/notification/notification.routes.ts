import { Router } from 'express';
import { notificationController } from './notification.controller';

const router = Router();

// 通知列表
router.get('/', notificationController.list as any);
// 未读数量
router.get('/unread-count', notificationController.getUnreadCount as any);
// 通知统计
router.get('/stats', notificationController.getStats as any);
// 全部已读
router.post('/mark-all-read', notificationController.markAllAsRead as any);
// 创建通知（系统/管理员操作）
router.post('/', notificationController.create as any);
// 批量创建
router.post('/batch', notificationController.batchCreate as any);
// 批量发送待发通知
router.post('/send-pending', notificationController.sendPending as any);
// 清理过期通知
router.post('/clean-expired', notificationController.cleanExpired as any);
// 发送单条通知
router.post('/:id/send', notificationController.send as any);
// 通知详情
router.get('/:id', notificationController.getById as any);
// 标记已读
router.post('/:id/read', notificationController.markAsRead as any);
// 删除通知
router.delete('/:id', notificationController.remove as any);

export default router;
