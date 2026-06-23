import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { UploadCloud, FileType, CheckCircle2 } from "lucide-react"
import { toast } from "sonner"

interface UploadFormProps {
  onUploadSuccess: () => void;
}

const UploadForm: React.FC<UploadFormProps> = ({ onUploadSuccess }) => {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      toast.error('请先选择一个文件。');
      return;
    }

    setLoading(true);

    const formData = new FormData();
    formData.append('file', file);

    // Determine endpoint based on file extension
    const isDicom = file.name.toLowerCase().endsWith('.dcm');
    const endpoint = isDicom 
      ? 'http://127.0.0.1:8080/api/v1/dicom/upload' 
      : 'http://127.0.0.1:8080/api/v1/ingestion/upload';

    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || '上传失败');
      }

      const data = await response.json();
      toast.success(`文件已加入处理队列`, {
        description: data.message || `文件 ${data.filename} 正在后台解析，请稍后刷新历史批次列表查看结果。`,
      });
      
      setFile(null);
      const fileInput = document.getElementById('file-upload') as HTMLInputElement;
      if (fileInput) fileInput.value = '';

      onUploadSuccess();
    } catch (err: any) {
      toast.error('上传失败', {
        description: err.message || '上传过程中发生未知错误。',
      });
    } finally {
      setLoading(false);
    }
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
                onChange={handleFileChange} 
                className="cursor-pointer"
              />
            </div>
          </div>
          <Button onClick={handleUpload} disabled={loading || !file} className="w-full sm:w-auto">
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
