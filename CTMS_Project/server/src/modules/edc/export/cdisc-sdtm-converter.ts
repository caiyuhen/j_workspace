import prisma from '../../../config/database';
import { CrfFormField, CrfForm } from './form.types';
import { SdtmVariable, SdtmDataset } from './sdtm.types';

/**
 * CRF到SDTM转换器
 * 负责根据CRF表单定义，将数据转换为符合CDISC SDTM标准的数据集
 */
export class CDISCSdtmConverter {
  /**
   * 将CRF表单转换为SDTM数据集
   * @param formId CRF表单ID
   * @returns 转换后的SDTM数据集
   */
  async convertFormToSdtm(formId: string): Promise<SdtmDataset> {
    // 1. 从数据库获取CRF表单及其字段
    const form = await prisma.crfForm.findUnique({
      where: { id: formId },
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

    if (!form) {
      throw new Error(`CRF表单 ${formId} 未找到`);
    }

    const sdtmVariables: SdtmVariable[] = [];
    
    // 2. 遍历CRF字段，进行CDISC到SDTM的字段映射
    for (const field of form.fields) {
      const crfField: CrfFormField = {
        id: field.id,
        fieldCode: field.fieldCode,
        fieldName: field.fieldName,
        fieldType: field.fieldType,
        cdiscDomain: field.cdiscDomain || undefined,
        cdashDataset: field.cdashDataset || undefined,
        cdashVariable: field.cdashVariable || undefined,
        cdashDataType: field.cdashDataType || undefined,
        sdtmVariable: field.sdtmVariable || undefined,
        codeListOid: field.codeListOid || undefined,
        options: field.options as any
      };
      const sdtmVariable = this.mapCdiscToSdtm(crfField);
      if (sdtmVariable) {
        sdtmVariables.push(sdtmVariable);
      }
    }

    // 3. 构造SDTM数据集
    const dataset: SdtmDataset = {
      datasetName: form.cdiscDomain || 'UNKNOWN',
      domain: form.cdiscDomain || 'UNKNOWN',
      variables: sdtmVariables,
      records: []
    };

    return dataset;
  }

  /**
   * 将单个CRF字段映射为SDTM变量
   * @param field CRF字段对象
   * @returns 映射后的SDTM变量，如果无法映射则返回null
   */
  private mapCdiscToSdtm(field: CrfFormField): SdtmVariable | null {
    // 根据领域和字段名进行映射逻辑
    // 此处为简化示例，实际逻辑依据CDISC标准和项目规则细化
    
    if (!field.cdiscDomain || !field.cdashVariable || !field.fieldName) {
      return null;
    }

    const sdtmVariable: SdtmVariable = {
      name: field.cdashVariable,
      domain: field.cdiscDomain,
      dataset: field.cdiscDomain,
      label: field.fieldName,
      dataType: field.cdashDataType || 'string',
      format: '',
    };

    return sdtmVariable;
  }

  /**
   * 验证CRF表单结构是否满足SDTM导出要求
   * @param formId CRF表单ID
   * @returns 验证结果
   */
  async validateCrfStructure(formId: string): Promise<{ isValid: boolean; errors: string[] }> {
    // 实现结构验证逻辑，例如检查必需字段、域定义等
    
    const form = await prisma.crfForm.findUnique({
      where: { id: formId },
      select: {
        id: true,
        formName: true,
        cdiscDomain: true,
        fields: {
          select: {
            id: true,
            fieldCode: true,
            fieldName: true,
            cdiscDomain: true,
            cdashVariable: true
          }
        }
      }
    });

    if (!form) {
      return { isValid: false, errors: [`表单 ${formId} 不存在`] };
    }

    if (!form.cdiscDomain) {
      return { isValid: false, errors: [`表单 ${formId} 缺少CDISC域定义`] };
    }

    const errors: string[] = [];

    // 验证领域字段
    for (const field of form.fields) {
      if (!field.fieldCode) {
        errors.push(`字段 ${field.id} 缺少FieldCode`);
      }
      if (!field.cdashVariable) {
        errors.push(`字段 ${field.id} 缺少CDASH变量名`);
      }
      // 可以添加更多的CDISC标准检查规则
    }

    return { isValid: errors.length === 0, errors };
  }

  /**
   * 根据SDTM数据集生成记录
   * @param dataset SDTM数据集
   * @returns 生成的记录列表
   */
  generateSdtmRecords(dataset: SdtmDataset): any[] {
    // 实现将SDTM变量列表转换为实际记录的逻辑
    // 这部分逻辑通常会根据实际CRF数据生成一个完整的行列表
    return dataset.variables.map(variable => ({
      domain: dataset.domain,
      variableName: variable.name,
      label: variable.label
    }));
  }
}
