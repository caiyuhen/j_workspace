import { Router } from 'express';
import { EtlProcess, ExportConfig } from './etl-process';
import { ExportFormat, ExportRequest } from './export.types';
import { ConsistencyValidator } from './consistency-validator';
import { CDISCSdtmConverter } from './cdisc-sdtm-converter';
import { authMiddleware } from '../../../shared/middleware/auth';
import prisma from '../../../config/database';

const router = Router();
const etlProcess = new EtlProcess();
const validator = new ConsistencyValidator();
const converter = new CDISCSdtmConverter();

router.use(authMiddleware());

// 获取导出配置
router.get('/config', async (req, res) => {
  try {
    res.json({ 
      success: true, 
      data: { 
        version: '1.0.0',
        supportedFormats: ['SDTM', 'ECRF', 'ADAM'],
        maxFileSize: '100MB'
      } 
    });
  } catch (error) {
    res.status(500).json({ 
      success: false, 
      message: '获取配置失败',
      error: (error as Error).message 
    });
  }
});

// 执行SDTM导出
router.post('/form/:formId/to-sdtm', async (req, res) => {
  try {
    const { formId } = req.params;
    
    // 参数验证
    if (!formId) {
      return res.status(400).json({ 
        success: false, 
        message: '表单ID不能为空' 
      });
    }
    
    // 执行导出
    const result = await etlProcess.executeSdtmExport({
      projectId: req.body.projectId || 'default',
      userId: req.user?.userId,
      filters: {
        formIds: [formId]
      }
    });
    
    res.json({ success: true, data: result });
  } catch (error) {
    console.error('导出失败:', error);
    res.status(500).json({ 
      success: false, 
      message: '导出失败', 
      error: (error as Error).message 
    });
  }
});

// 执行ECRF导出
router.post('/form/:formId/to-ecrf', async (req, res) => {
  try {
    const { formId } = req.params;
    
    // 参数验证
    if (!formId) {
      return res.status(400).json({ 
        success: false, 
        message: '表单ID不能为空' 
      });
    }
    
    // 构造导出请求
    const exportRequest: ExportRequest = {
      format: ExportFormat.ECRF,
      projectId: req.body.projectId || 'default',
      userId: req.user?.userId,
      fileName: req.body.fileName || `ecrf_${formId}.json`,
      filters: {
        formIds: [formId]
      }
    };
    
    // 执行导出
    const result = await etlProcess.executeEcrfExport(exportRequest);
    
    res.json({ success: true, data: result });
  } catch (error) {
    console.error('ECRF导出失败:', error);
    res.status(500).json({ 
      success: false, 
      message: 'ECRF导出失败', 
      error: (error as Error).message 
    });
  }
});

// 执行ADaM导出
router.post('/form/:formId/to-adam', async (req, res) => {
  try {
    const { formId } = req.params;
    
    // 参数验证
    if (!formId) {
      return res.status(400).json({ 
        success: false, 
        message: '表单ID不能为空' 
      });
    }
    
    // 构造导出请求
    const exportRequest: ExportRequest = {
      format: ExportFormat.ADAM,
      projectId: req.body.projectId || 'default',
      userId: req.user?.userId,
      fileName: req.body.fileName || `adam_${formId}.json`,
      filters: {
        formIds: [formId]
      }
    };
    
    // 执行导出
    const result = await etlProcess.executeAdamExport(exportRequest);
    
    res.json({ success: true, data: result });
  } catch (error) {
    console.error('ADaM导出失败:', error);
    res.status(500).json({ 
      success: false, 
      message: 'ADaM导出失败', 
      error: (error as Error).message 
    });
  }
});

// 验证表单合规性
router.get('/validate-form/:formId', async (req, res) => {
  try {
    const { formId } = req.params;
    
    // 参数验证
    if (!formId) {
      return res.status(400).json({ 
        success: false, 
        message: '表单ID不能为空' 
      });
    }
    
    const result = await validator.validateFormCompliance(formId);
    res.json({ success: true, data: result });
  } catch (error) {
    console.error('验证失败:', error);
    res.status(500).json({ 
      success: false, 
      message: '验证失败', 
      error: (error as Error).message 
    });
  }
});

// 执行完整的 SDTM 导出（支持生成 XPT 压缩包）
router.post('/sdtm', async (req, res) => {
  try {
    const { projectId, domains, format } = req.body;
    
    // 参数验证
    if (!projectId) {
      return res.status(400).json({ 
        success: false, 
        message: '项目ID不能为空' 
      });
    }
    
    const exportConfig: ExportConfig = {
      projectId,
      userId: req.user?.userId,
      format,
      filters: {
        domains
      }
    };
    
    const result = await etlProcess.executeSdtmExport(exportConfig);

    // 如果指定了 xpt 格式并且生成了文件
    if (format === 'xpt' && result.fileBuffer) {
      res.setHeader('Content-Type', 'application/zip');
      res.setHeader('Content-Disposition', `attachment; filename=${result.fileName}`);
      return res.send(result.fileBuffer);
    }

    res.json({ success: true, data: result });
  } catch (error) {
    console.error('SDTM导出失败:', error);
    res.status(500).json({ 
      success: false, 
      message: 'SDTM导出失败', 
      error: (error as Error).message 
    });
  }
});

// 批量导出
router.post('/batch-to-sdtm', async (req, res) => {
  try {
    const { projectId, filters } = req.body;
    
    // 参数验证
    if (!projectId) {
      return res.status(400).json({ 
        success: false, 
        message: '项目ID不能为空' 
      });
    }
    
    const exportConfig: ExportConfig = {
      projectId,
      userId: req.user?.userId,
      filters: filters || {}
    };
    
    const result = await etlProcess.executeSdtmExport(exportConfig);
    res.json({ success: true, data: result });
  } catch (error) {
    console.error('批量导出失败:', error);
    res.status(500).json({ 
      success: false, 
      message: '批量导出失败', 
      error: (error as Error).message 
    });
  }
});

// 获取导出历史
router.get('/history', async (req, res) => {
  try {
    const { projectId, page = 1, limit = 10 } = req.query;
    
    const exports = await prisma.sdtmExport.findMany({
      where: projectId ? { projectId: projectId as string } : {},
      orderBy: { createdAt: 'desc' },
      skip: (Number(page) - 1) * Number(limit),
      take: Number(limit)
    });
    
    res.json({ success: true, data: exports });
  } catch (error) {
    console.error('获取导出历史失败:', error);
    res.status(500).json({ 
      success: false, 
      message: '获取导出历史失败', 
      error: (error as Error).message 
    });
  }
});

export default router;
