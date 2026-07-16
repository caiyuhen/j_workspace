import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { UploadCloud, FileType, CheckCircle2 } from "lucide-react"
import { toast } from "sonner"

interface UploadFormProps {
  onUploadSuccess: (batchId?: string) => void;
}

const UploadForm: React.FC<UploadFormProps> = ({ onUploadSuccess }) => {
  const [files, setFiles] = useState<File[]>([]);
  const [loading, setLoading] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFiles(Array.from(e.target.files));
    } else {
      setFiles([]);
    }
  };

  const handleUpload = async () => {
    if (files.length === 0) {
      toast.error('请先选择至少一个文件。');
      return;
    }

    setLoading(true);
    let successCount = 0;
    let lastBatchId: string | undefined = undefined;

    for (const file of files) {
      const formData = new FormData();
      formData.append('file', file);

      // Determine endpoint based on file extension
      const isDicom = file.name.toLowerCase().endsWith('.dcm');
      const endpoint = isDicom 
        ? 'http://127.0.0.1:8433/api/v1/dicom/upload' 
        : 'http://127.0.0.1:8433/api/v1/ingestion/upload';

      try {
        const response = await fetch(endpoint, {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) {
          const errData = await response.json();
          throw new Error(errData.detail || `文件 ${file.name} 上传失败`);
        }

        const data = await response.json();
        successCount++;
        lastBatchId = data.batch_id;
      } catch (err: any) {
        toast.error(`文件 ${file.name} 上传失败`, {
          description: err.message || '上传过程中发生未知错误。',
        });
      }
    }

    if (successCount > 0) {
      toast.success(`成功加入 ${successCount} 个文件到处理队列`, {
        description: `文件正在后台解析，完成后将自动展示数据探查报告。`,
      });
      setFiles([]);
      const fileInput = document.getElementById('file-upload') as HTMLInputElement;
      if (fileInput) fileInput.value = '';

      onUploadSuccess(lastBatchId);
    }

    setLoading(false);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <UploadCloud className="w-5 h-5 text-blue-600" />
          多模态数据上传
        </CardTitle>
        <CardDescription>上传导出的 CSV 医疗结构化数据 或 DICOM 影像数据，触发双流脱敏与 Staging 解析链路。</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col sm:flex-row gap-4 items-end">
          <div className="grid w-full max-w-sm items-center gap-1.5">
            <Label htmlFor="file-upload">选择 CSV / DICOM 文件</Label>
            <div className="flex gap-2 items-center">
              <Input 
                id="file-upload" 
                type="file" 
                accept=".csv,.dcm" 
                multiple
                onChange={handleFileChange} 
                className="cursor-pointer"
              />
            </div>
          </div>
          <Button onClick={handleUpload} disabled={loading || files.length === 0} className="w-full sm:w-auto">
            {loading ? (
              <span className="flex items-center gap-2">
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                正在解析与处理...
              </span>
            ) : (
              <span className="flex items-center gap-2">
                <UploadCloud className="w-4 h-4" />
                上传并自动处理
              </span>
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

export default UploadForm;
