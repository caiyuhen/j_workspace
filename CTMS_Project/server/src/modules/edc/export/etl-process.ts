import prisma from '../../../config/database';
import { CrfForm } from './form.types';
import { SdtmData, SdtmDataset } from './sdtm.types';
import { CDISCSdtmConverter } from './cdisc-sdtm-converter';
import { ConsistencyValidator } from './consistency-validator';
import { ExportFormat, ExportRequest, AuditLogEntry } from './export.types';
import { AdamExporter } from './adam-exporter';

/**
 * 导出配置
 */
export interface ExportConfig {
  projectId: string;
  userId?: string;
  filters?: {
    startDate?: Date;
    endDate?: Date;
    domains?: string[];
    formIds?: string[];
  };
  mappingRules?: any;
  targetConfig?: any;
}

/**
 * 导出结果
 */
export interface ExportResult {
  exportId: string;
  status: 'completed' | 'failed';
  rowCount: number;
  timestamp: Date;
  originalData?: any;
  transformedData?: SdtmData;
  loadInfo?: any;
  fileBuffer?: Buffer;
  fileName?: string;
}

/**
 * ETL处理流程
 * 处理从CRF到SDTM/ECRF的完整流程
 */
export class EtlProcess {
  private converter: CDISCSdtmConverter;
  private validator: ConsistencyValidator;
  private adamExporter: AdamExporter;
  private auditLogs: AuditLogEntry[] = [];
  
  constructor() {
    this.converter = new CDISCSdtmConverter();
    this.validator = new ConsistencyValidator();
    this.adamExporter = new AdamExporter();
  }
  
  /**
   * 添加审计日志记录
   * @param userId 操作用户ID
   * @param action 操作行为
   * @param details 操作详情
   * @param status 操作结果
   */
  private async addAuditLog(projectId: string, userId: string | undefined, action: string, details: string, status: 'success' | 'failed') {
    const actualUserId = userId || '00000000-0000-0000-0000-000000000000'; // fallback
    this.auditLogs.push({
      timestamp: new Date(),
      userId: actualUserId,
      action,
      details,
      status
    });

    try {
      await prisma.auditLog.create({
        data: {
          systemCode: 'EDC',
          projectId: projectId,
          userId: actualUserId,
          eventType: 'EXPORT',
          action: action,
          newValues: { details, status }
        }
      });
    } catch (error) {
      console.error('保存审计日志失败:', error);
    }
  }
  
  /**
   * 执行完整的从CRF到SDTM数据转换ETL流程
   * @param exportConfig 导出配置
   * @returns 导出结果
   */
  async executeSdtmExport(exportConfig: ExportConfig): Promise<ExportResult> {
    try {
      // 1. 提取阶段：从CRF表单中提取数据
      const extractedData = await this.extractCrfData(exportConfig);
      
      // 2. 验证阶段：验证数据一致性
      const validationResult = await this.validateData(extractedData);
      
      // 3. 转换阶段：将数据转换为SDTM结构
      const transformedData = await this.transformToSdtm(extractedData);
      
      // 4. 加载阶段：将SDTM数据加载到目标位置
      const loadResult = await this.loadSdtmData(transformedData, exportConfig);
      
      let fileBuffer: Buffer | undefined;
      let fileName: string | undefined;

      if (exportConfig.format === 'xpt') {
        fileBuffer = await this.xptWriter.writeToZip(transformedData);
        fileName = `sdtm_export_${Date.now()}.zip`;
      }

      await this.addAuditLog(exportConfig.projectId, exportConfig.userId, 'SDTM_EXPORT', `导出表单数: ${extractedData.forms.length}`, 'success');
      
      return {
        exportId: this.generateExportId(),
        status: 'completed',
        rowCount: this.calculateRowCount(transformedData),
        timestamp: new Date(),
        originalData: extractedData,
        transformedData,
        loadInfo: loadResult,
        fileBuffer,
        fileName
      };
    } catch (error: any) {
      console.error('ETL导出过程失败:', error);
      await this.addAuditLog(exportConfig.projectId, exportConfig.userId, 'SDTM_EXPORT', `导出失败: ${error.message}`, 'failed');
      return {
        exportId: this.generateExportId(),
        status: 'failed',
        rowCount: 0,
        timestamp: new Date(),
        originalData: null,
        transformedData: undefined,
        loadInfo: null
      };
    }
  }
  
  /**
   * 执行ADaM导出流程
   * @param exportRequest 请求对象
   * @returns 导出结果
   */
  async executeAdamExport(exportRequest: ExportRequest): Promise<any> {
    const { format, projectId } = exportRequest;
    
    // 验证格式
    if (format !== ExportFormat.ADAM) {
      throw new Error('不支持的导出格式，ADaM导出仅限于ExportFormat.ADAM');
    }
    
    try {
      // 调用内部ADaM导出器
      const result = await this.adamExporter.export(exportRequest);
      
      await this.addAuditLog(projectId, exportRequest.userId, 'ADAM_EXPORT', `导出触发`, 'success');
      
      return {
        ...result,
        auditLogs: this.auditLogs
      };
    } catch (error: any) {
      console.error('ADaM导出过程失败:', error);
      await this.addAuditLog(projectId, exportRequest.userId, 'ADAM_EXPORT', `导出失败: ${error.message}`, 'failed');
      return {
        exportId: this.generateExportId(),
        format,
        status: 'failed',
        timestamp: new Date(),
        error: error.message,
        auditLogs: this.auditLogs
      };
    }
  }

  /**
   * 执行ECRF导出流程
   */
  async executeEcrfExport(exportRequest: ExportRequest): Promise<any> {
    try {
      const extractedData = await this.extractCrfData({
        projectId: exportRequest.projectId,
        userId: exportRequest.userId,
        filters: exportRequest.filters
      });
      const transformedData = this.transformToEcrf(extractedData);
      const loadResult = this.loadEcrfData(transformedData, exportRequest.fileName || 'ecrf.json');

      await this.addAuditLog(exportRequest.projectId, exportRequest.userId, 'ECRF_EXPORT', `导出表单数: ${extractedData.forms.length}`, 'success');

      return {
        exportId: this.generateExportId(),
        status: 'completed',
        timestamp: new Date(),
        data: transformedData,
        loadInfo: loadResult
      };
    } catch (error: any) {
      console.error('ECRF导出失败:', error);
      await this.addAuditLog(exportRequest.projectId, exportRequest.userId, 'ECRF_EXPORT', `导出失败: ${error.message}`, 'failed');
      return {
        exportId: this.generateExportId(),
        status: 'failed',
        timestamp: new Date(),
        error: error.message
      };
    }
  }

  /**
   * 将CRF数据转换为ECRF格式（模拟实现）
   * @param extractedData 提取的数据
   * @returns 转换后的ECRF数据
   */
  private transformToEcrf(extractedData: any): any {
    // 模拟转换过程
    return {
      metadata: extractedData.metadata,
      forms: extractedData.forms.map((form: any) => ({
        id: form.id,
        name: form.name,
        version: form.version,
        fields: form.fields.map((field: any) => ({
          id: field.id,
          code: field.fieldCode,
          name: field.fieldName,
          type: field.fieldType,
          cdashVariable: field.cdashVariable,
          sdtmVariable: field.sdtmVariable,
          options: field.options // 原始选项结构保持
        }))
      }))
    };
  }
  
  /**
   * 加载ECRF数据（模拟实现）
   * @param data 转换后的ECRF数据
   * @param fileName 文件名
   * @returns 加载结果
   */
  private loadEcrfData(data: any, fileName: string): any {
    // 模拟保存过程
    return {
      fileName: fileName,
      fileSize: JSON.stringify(data).length,
      exportDate: new Date()
    };
  }
  
  /**
   * 数据提取：从CRF表单中提取结构化数据
   * @param exportConfig 导出配置
   * @returns 提取的数据
   */
  private async extractCrfData(exportConfig: ExportConfig): Promise<any> {
    // 权限校验：确保用户有权访问该项目
    if (exportConfig.userId) {
      const userRole = await prisma.userRole.findFirst({
        where: {
          userId: exportConfig.userId,
          projectId: exportConfig.projectId
        }
      });
      if (!userRole) {
        const user = await prisma.user.findUnique({ 
          where: { id: exportConfig.userId },
          include: { userRoles: { include: { role: true } } }
        });
        const isSystemAdmin = user?.userRoles.some(ur => ur.role?.isSystemRole);
        if (!isSystemAdmin) {
          throw new Error('权限不足：无法访问该项目的数据');
        }
      }
    }

    const whereClause: any = {
      projectId: exportConfig.projectId,
      status: 'published'
    };
    
    // 应用过滤条件
    if (exportConfig.filters?.startDate) {
      whereClause.createdAt = { gte: exportConfig.filters.startDate };
    }
    
    if (exportConfig.filters?.endDate) {
      whereClause.createdAt = { lte: exportConfig.filters.endDate };
    }
    
    if (exportConfig.filters?.domains && exportConfig.filters.domains.length > 0) {
      whereClause.cdiscDomain = { in: exportConfig.filters.domains };
    }
    
    if (exportConfig.filters?.formIds && exportConfig.filters.formIds.length > 0) {
      whereClause.id = { in: exportConfig.filters.formIds };
    }
    
    // 从数据库查询表单
    const forms = await prisma.crfForm.findMany({
      where: whereClause,
      include: {
        fields: { 
          orderBy: { sortOrder: 'asc' },
          select: {
            id: true,
            fieldCode: true,
            fieldName: true,
            fieldType: true,
            cdiscDomain: true,
            cdashDataset: true,
            cdashVariable: true,
            cdashDataType: true,
            sdtmVariable: true,
            codeListOid: true,
            options: true
          }
        }
      }
    });
    
    return {
      forms,
      metadata: {
        project: exportConfig.projectId,
        exportDate: new Date(),
        filters: exportConfig.filters
      }
    };
  }
  
  /**
   * 数据验证：验证数据符合CDISC标准
   * @param extractedData 提取的数据
   * @returns 验证结果
   */
  private async validateData(extractedData: any): Promise<any> {
    const validationResults: any[] = [];
    let isValid = true;
    let totalErrors = 0;
    
    // 对每个表单进行验证
    for (const form of extractedData.forms) {
      try {
        const result = await this.validator.validateFormCompliance(form.id);
        validationResults.push({
          formId: form.id,
          validationResult: result
        });
        totalErrors += result.totalErrors;
        if (!result.isValid) {
          isValid = false;
        }
      } catch (error) {
        console.error(`验证表单 ${form.id} 时出错:`, error);
      }
    }
    
    return {
      isValid,
      totalErrors,
      validationDetails: validationResults
    };
  }
  
  /**
   * 转换处理：执行CDISC到SDTM的转换
   * @param extractedData 提取的数据
   * @returns 转换后的SDTM数据
   */
  private async transformToSdtm(extractedData: any): Promise<SdtmData> {
    const sdtmDatasets: SdtmDataset[] = [];
    
    // 逐个表单进行转换
    for (const form of extractedData.forms) {
      try {
        const dataset = await this.converter.convertFormToSdtm(form.id);
        sdtmDatasets.push(dataset);
      } catch (error) {
        console.error(`转换表单 ${form.id} 时出错:`, error);
      }
    }
    
    // 合并数据集
    const finalSdtmData = this.mergeSdtmDatasets(sdtmDatasets);
    return finalSdtmData;
  }
  
  /**
   * 合并多个SDTM数据集
   * @param datasets SDTM数据集列表
   * @returns 合并后的数据
   */
  private mergeSdtmDatasets(datasets: SdtmDataset[]): SdtmData {
    return {
      datasets
    };
  }
  
  /**
   * 加载准备：生成标准SDTM导出文件
   * @param sdtmData SDTM数据
   * @param exportConfig 导出配置
   * @returns 加载结果
   */
  private async loadSdtmData(sdtmData: SdtmData, exportConfig: ExportConfig): Promise<any> {
    // 实际实现中需要将数据保存到文件系统或数据库
    // 这里模拟保存过程
    
    // 将SDTM数据保存到系统
    const savedExport = await prisma.sdtmExport.create({
      data: {
        projectId: exportConfig.projectId,
        exportConfig: JSON.stringify(exportConfig),
        data: JSON.stringify(sdtmData),
        status: 'completed'
      }
    });
    
    return {
      exportId: savedExport.id,
      filePath: `/exports/sdtm_${savedExport.id}.csv`,
      fileSize: JSON.stringify(sdtmData).length,
      exportDate: new Date()
    };
  }
  
  /**
   * 计算数据行数
   * @param sdtmData SDTM数据
   * @returns 数据行数
   */
  private calculateRowCount(sdtmData: SdtmData): number {
    // 实际实现中需要计算所有记录的总数
    // 这里简化为采用数据集数量
    return sdtmData.datasets.length;
  }
  
  /**
   * 生成导出ID
   * @returns 导出ID
   */
  private generateExportId(): string {
    return `export_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
}