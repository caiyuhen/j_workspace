const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
require('dotenv').config();

const ctmsRoutes = require('./routes/ctmsRoutes');
const { authenticateToken } = require('./middleware/authMiddleware');

const app = express();
const PORT = process.env.PORT || 3002;

// 安全中间件
app.use(helmet());
app.use(cors());

// 速率限制
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15分钟
  max: 100 // 限制每个IP 100个请求
});
app.use(limiter);

// 解析JSON请求体
app.use(express.json());

// 健康检查端点
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'OK', service: 'ctms-service' });
});

// CTMS相关路由
app.use('/api/ctms', authenticateToken, ctmsRoutes);

app.listen(PORT, () => {
  console.log(`CTMS服务运行在端口 ${PORT}`);
});

module.exports = app;