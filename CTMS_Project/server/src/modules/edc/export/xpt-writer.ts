import AdmZip from 'adm-zip';
import { SdtmData } from './sdtm.types';

export class XptWriter {
  /**
   * 将SDTM数据写入模拟的XPT格式并打包为ZIP
   * 由于XPT是二进制格式，这里我们以CSV或JSON文本作为示例模拟生成文件
   */
  async writeToZip(sdtmData: SdtmData): Promise<Buffer> {
    const zip = new AdmZip();

    for (const dataset of sdtmData.datasets) {
      // 在实际的SAS XPT中，这里会调用相应的XPT二进制写入库
      // 为了演示，我们将每个domain的数据生成为带有 ".xpt" 后缀的JSON字符串
      
      const fileName = `${dataset.datasetName.toLowerCase()}.xpt`;
      const fileContent = JSON.stringify({
        header: {
          studyid: 'CTMS_TRIAL',
          domain: dataset.domain,
          variables: dataset.variables.map(v => v.name)
        },
        records: dataset.records
      }, null, 2);

      zip.addFile(fileName, Buffer.from(fileContent, 'utf-8'));
    }

    return zip.toBuffer();
  }
}
