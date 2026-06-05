/**
 * CRF字段定义
 */
export interface CrfFormField {
  id: string;
  fieldCode: string;
  fieldName: string;
  fieldType: string;
  cdiscDomain?: string;
  cdashDataset?: string;
  cdashVariable?: string;
  cdashDataType?: string;
  sdtmVariable?: string;
  codeListOid?: string;
  options?: { label: string; value: string }[];
}

/**
 * CRF表单定义
 */
export interface CrfForm {
  id: string;
  formCode: string;
  formName: string;
  cdiscDomain?: string;
  sdtmDatasetName?: string;
  fields: CrfFormField[];
}