import express, { Express, Request, Response, NextFunction } from 'express';
import cors from 'cors';
import helmet from 'helmet';
import rateLimit from 'express-rate-limit';
import bodyParser from 'body-parser';
import config from './config/env';
import logger from './shared/utils/logger';
import { requestIdMiddleware } from './shared/middleware/request-id';
import { authMiddleware } from './shared/middleware/auth';
import { errorHandler, notFoundHandler } from './shared/middleware/error-handler';
import prisma, { checkDatabaseHealth } from './config/database';

const app: Express = express();

// =========== 基础中间件链 ===========

// 请求ID（第一个，确保所有日志有requestId）
app.use(requestIdMiddleware() as any);

// 安全头（helmet）
app.use(helmet() as any);

// CORS 配置（21 CFR Part 11 合规：不允许随意origin）
app.use(cors({
  origin: config.corsOrigin,
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'X-Request-ID'],
}) as any);

// 请求限流（防止暴力破解）
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15分钟
  max: 1000, // 每窗口最多1000请求
  message: { success: false, error: { code: 'RATE_LIMITED', message: 'Too many requests' } },
  standardHeaders: true,
  legacyHeaders: false,
});
app.use(limiter as any);

// 请求体解析
app.use(bodyParser.json({ limit: '10mb' }));
app.use(bodyParser.urlencoded({ extended: true, limit: '10mb' }));

// =========== 健康检查端点 ===========

app.get('/health', async (req: Request, res: Response) => {
  res.json({
    status: 'ok',
    service: 'ctms-edc-api',
    version: '4.0.0',
    timestamp: new Date().toISOString(),
  });
});

app.get('/ready', async (req: Request, res: Response) => {
  const dbHealth = await checkDatabaseHealth();
  const isReady = dbHealth.status === 'ok';
  
  res.status(isReady ? 200 : 503).json({
    status: isReady ? 'ready' : 'not_ready',
    checks: {
      database: dbHealth,
    },
    timestamp: new Date().toISOString(),
  });
});

// =========== API 路由 ===========

// 认证路由（公开）
import authRoutes from './modules/auth/auth.routes';
app.use('/api/auth', authRoutes as any);

// 需要认证的路由
const apiRouter = express.Router();

// 用户管理
import userRoutes from './modules/user/user.routes';
apiRouter.use('/users', authMiddleware() as any, userRoutes as any);

// 角色管理
import roleRoutes from './modules/role/role.routes';
apiRouter.use('/roles', authMiddleware() as any, roleRoutes as any);

// 项目管理
import projectRoutes from './modules/ctms/project/project.routes';
apiRouter.use('/projects', authMiddleware() as any, projectRoutes as any);

// 中心管理
import siteRoutes from './modules/ctms/site/site.routes';
apiRouter.use('/sites', authMiddleware() as any, siteRoutes as any);

// 工时管理
import timesheetRoutes from './modules/ctms/timesheet/timesheet.routes';
apiRouter.use('/timesheets', authMiddleware() as any, timesheetRoutes as any);

// 收支管理
import financeRoutes from './modules/ctms/finance/finance.routes';
apiRouter.use('/finance', authMiddleware() as any, financeRoutes as any);

// 药物管理
import drugRoutes from './modules/ctms/drug/drug.routes';
apiRouter.use('/drugs', authMiddleware() as any, drugRoutes as any);

// 文档管理（TMF）
import documentRoutes from './modules/ctms/document/document.routes';
apiRouter.use('/documents', authMiddleware() as any, documentRoutes as any);

// CRF模版
import templateRoutes from './modules/edc/template/template.routes';
apiRouter.use('/edc/templates', authMiddleware() as any, templateRoutes as any);

// CRF表单管理
import formRoutes from './modules/edc/form/form.routes';
apiRouter.use('/edc/forms', authMiddleware() as any, formRoutes as any);

// 受试者管理
import subjectRoutes from './modules/edc/data-entry/subject.routes';
apiRouter.use('/edc/subjects', authMiddleware() as any, subjectRoutes as any);

// 数据质疑
import queryRoutes from './modules/edc/query/query.routes';
apiRouter.use('/edc/queries', authMiddleware() as any, queryRoutes as any);

// SDV 源数据核查
import sdvRoutes from './modules/edc/sdv/sdv.routes';
apiRouter.use('/edc/sdv', authMiddleware() as any, sdvRoutes as any);

// 知情同意管理
import consentRoutes from './modules/edc/consent/consent.routes';
apiRouter.use('/edc/consent', authMiddleware() as any, consentRoutes as any);

// 逻辑核查（Edit Check）
import editCheckRoutes from './modules/edc/edit-check/edit-check.routes';
apiRouter.use('/edc/edit-check', authMiddleware() as any, editCheckRoutes as any);

// AE/SAE 安全性管理
import aeRoutes from './modules/edc/ae/ae.routes';
apiRouter.use('/edc/ae', authMiddleware() as any, aeRoutes as any);

// 审批流程
import workflowRoutes from './modules/workflow/workflow.routes';
apiRouter.use('/workflow', authMiddleware() as any, workflowRoutes as any);

// 监察管理
import monitoringRoutes from './modules/ctms/monitoring/monitoring.routes';
apiRouter.use('/monitoring', authMiddleware() as any, monitoringRoutes as any);

// 随机化管理
import randomizationRoutes from './modules/edc/randomization/randomization.routes';
apiRouter.use('/edc/randomization', authMiddleware() as any, randomizationRoutes as any);

// 数据锁定
import lockRoutes from './modules/edc/lock/lock.routes';
apiRouter.use('/edc/locks', authMiddleware() as any, lockRoutes as any);

// 伦理审批管理
import ethicsRoutes from './modules/ctms/ethics/ethics.routes';
apiRouter.use('/ethics', authMiddleware() as any, ethicsRoutes as any);

// 合同管理
import contractRoutes from './modules/ctms/contract/contract.routes';
apiRouter.use('/contracts', authMiddleware() as any, contractRoutes as any);

// 供应商管理
import vendorRoutes from './modules/ctms/vendor/vendor.routes';
apiRouter.use('/vendors', authMiddleware() as any, vendorRoutes as any);

// 报告中心
import reportRoutes from './modules/report/report.routes';
apiRouter.use('/reports', authMiddleware() as any, reportRoutes as any);

// 数据导出
import exportRoutes from './modules/export/export.routes';
apiRouter.use('/export', authMiddleware() as any, exportRoutes as any);

// 组织机构管理
import organizationRoutes from './modules/organization/organization.routes';
apiRouter.use('/organizations', authMiddleware() as any, organizationRoutes as any);

// 电子签名
import signatureRoutes from './modules/signature/signature.routes';
apiRouter.use('/signatures', authMiddleware() as any, signatureRoutes as any);

// 数据同步
import syncRoutes from './modules/sync/sync.routes';
apiRouter.use('/sync', authMiddleware() as any, syncRoutes as any);

// 数据脱敏
import maskingRoutes from './modules/data-masking/masking.routes';
apiRouter.use('/data-masking', authMiddleware() as any, maskingRoutes as any);

// ABAC 策略引擎
import abacRoutes from './modules/abac/abac.routes';
apiRouter.use('/abac', authMiddleware() as any, abacRoutes as any);

// AI Agent 集成
import aiRoutes from './modules/ai/ai.routes';
apiRouter.use('/ai', authMiddleware() as any, aiRoutes as any);

// 审计日志
import auditRoutes from './modules/audit/audit.routes';
apiRouter.use('/audit', authMiddleware() as any, auditRoutes as any);

// 消息通知
import notificationRoutes from './modules/notification/notification.routes';
apiRouter.use('/notifications', authMiddleware() as any, notificationRoutes as any);

<<<<<<< HEAD
<<<<<<< HEAD
// 医生日历夹
import doctorFolderRoutes from './modules/doctor-patient-folder/routes/doctor-folder.routes';
apiRouter.use('/doctor-folder', authMiddleware() as any, doctorFolderRoutes as any);

=======
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
=======
>>>>>>> origin/main
app.use('/api', apiRouter);

// =========== 错误处理 ===========

// 404 处理
app.use('*', notFoundHandler as any);

// 全局错误处理器（必须放在最后）
app.use(errorHandler as any);

export default app;
