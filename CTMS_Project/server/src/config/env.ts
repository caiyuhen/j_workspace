import dotenv from 'dotenv';
import path from 'path';

dotenv.config({ path: path.join(__dirname, '../../.env') });

interface Config {
  nodeEnv: string;
  port: number;
  host: string;
  databaseUrl: string;
  jwtSecret: string;
  jwtAccessExpiresIn: string;
  jwtRefreshExpiresIn: string;
  corsOrigin: string;
  logLevel: string;
  llmBaseUrl: string;
  llmEndpoint: string;
  compliance21CFR: boolean;
  complianceALCOA: boolean;
}

function requiredEnv(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(`Missing required environment variable: ${name}`);
  }
  return value;
}

export const config: Config = {
  nodeEnv: process.env.NODE_ENV || 'development',
  port: parseInt(process.env.PORT || '3000', 10),
  host: process.env.HOST || 'localhost',
  databaseUrl: requiredEnv('DATABASE_URL'),
  jwtSecret: requiredEnv('JWT_SECRET'),
  jwtAccessExpiresIn: process.env.JWT_ACCESS_EXPIRES_IN || '15m',
  jwtRefreshExpiresIn: process.env.JWT_REFRESH_EXPIRES_IN || '7d',
  corsOrigin: process.env.CORS_ORIGIN || 'http://localhost:5173',
  logLevel: process.env.LOG_LEVEL || 'info',
  llmBaseUrl: process.env.LLM_BASE_URL || 'http://192.168.0.126:8802/write/',
  llmEndpoint: process.env.LLM_ENDPOINT || '/chat',
  compliance21CFR: process.env.COMPLIANCE_21CFR_PART11_ENABLED === 'true',
  complianceALCOA: process.env.COMPLIANCE_ALCOA_PLUS_ENABLED === 'true',
};

export default config;
