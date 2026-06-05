const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const winston = require('winston');
const expressWinston = require('express-winston');
require('dotenv').config();

// 创建日志记录器
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  transports: [
    new winston.transports.File({ filename: 'error.log', level: 'error' }),
    new winston.transports.File({ filename: 'combined.log' })
  ]
});

// 添加控制台日志
if (process.env.NODE_ENV !== 'production') {
  logger.add(new winston.transports.Console({
    format: winston.format.simple()
  }));
}

const app = express();
const PORT = process.env.PORT || 3000;

// 安全中间件
app.use(helmet());
app.use(cors());

// 速率限制
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15分钟
  max: 1000 // 限制每个IP 1000个请求
});
app.use(limiter);

// 请求日志
app.use(expressWinston.logger({
  transports: [
    new winston.transports.Console()
  ],
  format: winston.format.combine(
    winston.format.colorize(),
    winston.format.json()
  ),
  meta: true,
  msg: "HTTP {{req.method}} {{req.url}} {{res.statusCode}} {{res.responseTime}}ms",
  expressFormat: true,
  colorize: true,
  ignoredRoutes: ['/health']
}));

// 解析JSON请求体
app.use(express.json());

// 健康检查端点
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'OK', service: 'api-gateway' });
});

// 首页重定向到文档
app.get('/', (req, res) => {
  res.redirect('/docs');
});

// API文档端点
app.get('/docs', (req, res) => {
  res.json({
    message: 'Clinical Trial Management System API Gateway',
    version: '1.0.0',
    documentation: 'https://github.com/your-project/api-docs',
    endpoints: {
      auth: '/api/auth/*',
      ctms: '/api/ctms/*',
      edc: '/api/edc/*',
      iwrs: '/api/iwrs/*',
      patientFolder: '/api/patient-folder/*'
    }
  });
});

// API路由代理中间件
const createProxyMiddleware = (target, path) => {
  return (req, res, next) => {
    // 这里是代理逻辑示例
    // 在实际部署中应该使用如NGINX这样的代理服务器
    req.url = req.path.replace('/api/', '/') || '/';
    logger.info(`Proxying request to ${target}${req.url}`);
    next();
  };
};

// 应用代理中间件到各个模块
// 注意：这里只是框架示意，实际生产环境应该使用专业的API网关
app.use('/api/auth', createProxyMiddleware('http://localhost:3001', '/api/auth'));
app.use('/api/ctms', createProxyMiddleware('http://localhost:3002', '/api/ctms'));
app.use('/api/edc', createProxyMiddleware('http://localhost:3003', '/api/edc'));
app.use('/api/iwrs', createProxyMiddleware('http://localhost:3004', '/api/iwrs'));
app.use('/api/patient-folder', createProxyMiddleware('http://localhost:3005', '/api/patient-folder'));

// 错误处理中间件
app.use((err, req, res, next) => {
  logger.error(err);
  res.status(500).json({
    success: false,
    message: 'Internal server error'
  });
});

// 404处理
app.use((req, res) => {
  res.status(404).json({
    success: false,
    message: 'API endpoint not found'
  });
});

app.listen(PORT, () => {
  logger.info(`API网关运行在端口 ${PORT}`);
});

module.exports = app;