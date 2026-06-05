import express, { Application, Request, Response, NextFunction } from 'express';
import cors from 'cors';
import helmet from 'helmet';
import rateLimit from 'express-rate-limit';
import dotenv from 'dotenv';
import { logger } from './utils/logger';
import { config } from './config';

// Import routes
import authRoutes from './routes/auth.routes';
import userRoutes from './routes/user.routes';
import roleRoutes from './routes/role.routes';

// Load environment variables
dotenv.config();

const app: Application = express();
const PORT = process.env.PORT || 3000;

// ===== Security Middleware =====

// CORS configuration
const corsOptions = {
  origin: process.env.CORS_ORIGINS
    ? process.env.CORS_ORIGINS.split(',').map((origin) => origin.trim())
    : '*',
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization'],
};
app.use(cors(corsOptions));

// Helmet for security headers
app.use(helmet());

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: parseInt(process.env.RATE_LIMIT_MAX || '100', 10), // 100 requests per windowMs
  message: {
    success: false,
    message: 'Too many requests from this IP, please try again later.',
  },
  standardHeaders: true,
  legacyHeaders: false,
});
app.use('/api/', limiter);

// ===== Body Parser Middleware =====

app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// ===== Request Logging Middleware =====

app.use((req: Request, res: Response, next: NextFunction) => {
  const start = Date.now();
  const logData = {
    method: req.method,
    url: req.url,
    ip: req.ip,
    userAgent: req.get('user-agent'),
  };

  res.on('finish', () => {
    const duration = Date.now() - start;
    logData.status = res.statusCode;
    logData.duration = `${duration}ms`;
    
    if (req.method === 'POST' || req.method === 'PUT' || req.method === 'PATCH') {
      logger.info('Request completed', logData);
    } else {
      logger.http('Request completed', logData);
    }
  });

  next();
});

// ===== Health Check =====

app.get('/health', (req: Request, res: Response) => {
  res.json({
    success: true,
    service: 'auth-service',
    version: '1.0.0',
    timestamp: new Date().toISOString(),
    status: 'healthy',
  });
});

app.get('/ready', async (req: Request, res: Response) => {
  try {
    // Check database connectivity
    // This would be implemented with actual DB check
    res.json({
      success: true,
      status: 'ready',
    });
  } catch (error) {
    res.status(503).json({
      success: false,
      status: 'not ready',
      error: error instanceof Error ? error.message : 'Unknown error',
    });
  }
});

// ===== API Routes =====

app.use('/api/v1/auth', authRoutes);
app.use('/api/v1/users', userRoutes);
app.use('/api/v1/roles', roleRoutes);

// ===== 404 Handler =====

app.use((req: Request, res: Response) => {
  res.status(404).json({
    success: false,
    message: 'Route not found',
    path: req.path,
  });
});

// ===== Error Handler =====

app.use((err: Error, req: Request, res: Response, next: NextFunction) => {
  logger.error('Unhandled error', {
    error: err.message,
    stack: err.stack,
    url: req.url,
    method: req.method,
  });

  res.status(500).json({
    success: false,
    message: process.env.NODE_ENV === 'production'
      ? 'Internal server error'
      : err.message,
  });
});

// ===== Start Server =====

const startServer = async () => {
  try {
    // Initialize database connection
    // This would be handled by Prisma
    logger.info('Initializing Auth Service...');

    // Wait for database to be ready (if needed)
    // await waitForDatabase();

    app.listen(PORT, () => {
      logger.info(`Auth Service is running on port ${PORT}`);
      logger.info(`Environment: ${process.env.NODE_ENV || 'development'}`);
      logger.info(`Health check: http://localhost:${PORT}/health`);
      logger.info(`Ready check: http://localhost:${PORT}/ready`);
      logger.info(`API Docs: http://localhost:${PORT}/api/v1`);
    });
  } catch (error) {
    logger.error('Failed to start server', {
      error: error instanceof Error ? error.message : 'Unknown error',
    });
    process.exit(1);
  }
};

// Handle unhandled promise rejections
process.on('unhandledRejection', (reason, promise) => {
  logger.error('Unhandled Rejection', {
    reason: reason instanceof Error ? reason.message : reason,
  });
});

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
  logger.error('Uncaught Exception', {
    error: error instanceof Error ? error.message : error,
  });
  process.exit(1);
});

// Graceful shutdown
const gracefulShutdown = (signal: string) => {
  logger.info(`${signal} received. Starting graceful shutdown...`);
  
  // Close server, disconnect database, etc.
  // server.close(() => {
  //   logger.info('HTTP server closed');
  //   prisma.$disconnect().then(() => {
  //     logger.info('Database connection closed');
  //     process.exit(0);
  //   });
  // });

  // Force shutdown after 10 seconds
  setTimeout(() => {
    logger.error('Forced shutdown after timeout');
    process.exit(1);
  }, 10000);
};

process.on('SIGTERM', () => gracefulShutdown('SIGTERM'));
process.on('SIGINT', () => gracefulShutdown('SIGINT'));

// Start the server
startServer();

export default app;
