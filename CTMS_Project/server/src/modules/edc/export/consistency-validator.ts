import prisma from '../../../config/database';
import { CrfFormField, CrfForm } from './form.types';

/**
 * 验证错误定义
 */
export interface ValidationError {
  field: string;
  message: string;
}

/**
 * 验证结果
 */
export interface ValidationResult {
  isValid: boolean;
  errors: ValidationError[];
}

/**
 * 字段合规性结果
 */
export interface FieldComplianceResult {
  fieldId: string;
  fieldName: string;
  compliance: ValidationResult;
}

/**
 * 表单合规性结果
 */
export interface FormComplianceResult {
  isValid: boolean;
  totalFields: number;
  totalErrors: number;
  fieldResults: FieldComplianceResult[];
}

/**
 * 字段一致性检查器
 * 用于验证CRF字段是否符合CDISC标准
 */
export class ConsistencyValidator {
  
  /**
   * 验证CRF字段是否符合CDISC标准
   * @param fieldId CRF字段ID
   * @returns 验证结果
   */
  async validateCrfField(fieldId: string): Promise<ValidationResult> {
    const errors: ValidationError[] = [];
    
    // 从数据库获取字段详情
    const field = await prisma.crfFormField.findUnique({
      where: { id: fieldId },
      select: {
        id: true,
        fieldCode: true,
        fieldName: true,
        fieldType: true,
        cdiscDomain: true,
        cdashVariable: true,
        cdashDataType: true,
        codeListOid: true,
        options: true
      }
    });
    
    if (!field) {
      return {
        isValid: false,
        errors: [{
          field: 'fieldId',
          message: `字段不存在: ${fieldId}`
        }]
      };
    }
    
    // 1. 必填字段验证
    if (!field.cdiscDomain && field.fieldType !== 'hidden') {
      errors.push({
        field: 'cdiscDomain',
        message: '字段必须指定CDISC域标识符'
      });
    }
    
    // 2. 数据类型一致性
    if (field.fieldType === 'number' && !field.cdashDataType?.includes('NUM')) {
      errors.push({
        field: 'cdashDataType',
        message: '数值字段应指定NUM数据类型'
      });
    }
    
    // 3. 代码表完整性检查
    if (field.codeListOid) {
      const codeList = await prisma.cdiscCodeList.findUnique({
        where: { codeListOid: field.codeListOid }
      });
      
      if (!codeList) {
        errors.push({
          field: 'codeListOid',
          message: `指定的CDISC代码表不存在: ${field.codeListOid}`
        });
      }
    }
    
    // 4. 格式一致性检查
    if (field.cdashVariable && field.cdashVariable.length > 40) {
      errors.push({
        field: 'cdashVariable',
        message: 'CDASH变量名长度不应超过40字符'
      });
    }
    
    return {
      isValid: errors.length === 0,
      errors
    };
  }
  
  /**
   * 验证整个表单符合CDISC标准
   * @param formId CRF表单ID
   * @returns 表单合规性结果
   */
  async validateFormCompliance(formId: string): Promise<FormComplianceResult> {
    const results: FieldComplianceResult[] = [];
    let totalErrors = 0;
    
    // 从数据库获取表单和所有字段
    const form = await prisma.crfForm.findUnique({
      where: { id: formId },
      include: {
        fields: {
          select: {
            id: true,
            fieldName: true
          }
        }
      }
    });
    
    if (!form) {
      throw new Error(`CRF表单不存在: ${formId}`);
    }
    
    // 逐字段验证
    for (const field of form.fields) {
      const result = await this.validateCrfField(field.id);
      results.push({
        fieldId: field.id,
        fieldName: field.fieldName,
        compliance: result
      });
      totalErrors += result.errors.length;
    }
    
    return {
      isValid: totalErrors === 0,
      totalFields: form.fields.length,
      totalErrors,
      fieldResults: results
    };
  }
}