/**
 * SDTM变量定义
 */
export interface SdtmVariable {
  name: string;           // SDTM变量名
  domain: string;         // CDISC域
  dataset: string;        // CDASH数据集
  dataType: string;       // 数据类型
  label: string;          // 变量标签
  format: string;         // 数据格式
  allowedValues?: {      // 允许的值
    value: string;
    label: string;
  }[];
}

/**
 * SDTM数据集
 */
export interface SdtmDataset {
  datasetName: string;    // 数据集名称
  domain: string;         // CDISC域
  variables: SdtmVariable[]; // 变量列表
  records: any[];         // 数据记录
}

/**
 * SDTM数据结构
 */
export interface SdtmData {
  datasets: SdtmDataset[]; // 数据集列表
}