import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { History, FileText, CheckCircle2, AlertCircle, Loader2, Trash2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { toast } from 'sonner'

export interface Batch {
  id: string;
  filename: string;
  total_rows: number;
  error_rows: number;
  status: string;
  created_at: string;
}

interface BatchHistoryProps {
  batches: Batch[];
  loading: boolean;
  error: string | null;
  onRefresh?: () => void;
}

const BatchHistory: React.FC<BatchHistoryProps> = ({ batches = [], loading, error, onRefresh }) => {
  const [clearing, setClearing] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  // Setup polling for processing batches
  useEffect(() => {
    const hasProcessing = (batches || []).some(b => b.status === 'processing');
    let interval: NodeJS.Timeout;
    
    if (hasProcessing && onRefresh) {
      interval = setInterval(() => {
        onRefresh();
      }, 3000); // Poll every 3 seconds if any batch is still processing
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [batches, onRefresh]);

  const handleClearData = async () => {
    setClearing(true);
    try {
      const res = await fetch('http://127.0.0.1:8080/api/v1/ingestion/clear', {
        method: 'POST',
      });
      if (!res.ok) throw new Error('清除数据失败');
      setShowConfirm(false);
      toast.success('历史数据已全部清空');
      if (onRefresh) onRefresh();
    } catch (err) {
      console.error(err);
      toast.error('清除数据失败，请查看控制台');
    } finally {
      setClearing(false);
    }
  };

  if (loading && (!batches || batches.length === 0)) {
    // Only show loading if we are explicitly told it's loading and there is NO data.
    return (
      <Card>
        <CardContent className="p-10 flex justify-center items-center min-h-[400px]">
          <div className="flex flex-col items-center text-slate-500 gap-2">
            <div className="w-8 h-8 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin" />
            <p>正在加载历史记录...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="border-red-200 bg-red-50">
        <CardContent className="p-6 text-red-600 flex items-center gap-2">
          <AlertCircle className="w-5 h-5" />
          {error}
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle className="flex items-center gap-2">
            <History className="w-5 h-5 text-blue-600" />
            接入历史批次
          </CardTitle>
          <CardDescription>最近的数据接入批次记录以及其处理状态。</CardDescription>
        </div>
        <div className="flex gap-2">
          {showConfirm ? (
            <>
              <Button variant="outline" size="sm" onClick={() => setShowConfirm(false)}>
                取消
              </Button>
              <Button 
                variant="destructive" 
                size="sm" 
                onClick={handleClearData} 
                disabled={clearing}
                className="flex items-center gap-2"
              >
                {clearing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
                确认清空
              </Button>
            </>
          ) : (
            <Button 
              variant="destructive" 
              size="sm" 
              onClick={() => setShowConfirm(true)} 
              disabled={clearing || !batches || batches.length === 0}
              className="flex items-center gap-2"
            >
              <Trash2 className="w-4 h-4" />
              清空所有数据
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {!batches || batches.length === 0 ? (
          <div className="text-center py-10 text-slate-500 flex flex-col items-center gap-2">
            <FileText className="w-10 h-10 text-slate-300" />
            <p>暂无接入批次，请上传文件以开始。</p>
          </div>
        ) : (
          <ScrollArea className="h-[400px] w-full rounded-md border">
            <Table>
              <TableHeader className="sticky top-0 bg-slate-100 z-10 shadow-sm">
                <TableRow>
                  <TableHead className="w-[200px]">文件名</TableHead>
                  <TableHead className="text-right">总行数</TableHead>
                  <TableHead className="text-right">异常行数</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead className="text-right">创建时间</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {batches.map((batch) => (
                  <TableRow key={batch.id}>
                    <TableCell className="font-medium flex items-center gap-2">
                      <FileText className="w-4 h-4 text-slate-400" />
                      {batch.filename}
                    </TableCell>
                    <TableCell className="text-right">{batch.total_rows.toLocaleString()}</TableCell>
                    <TableCell className={`text-right ${batch.error_rows > 0 ? 'text-red-600 font-medium' : 'text-slate-500'}`}>
                      {batch.error_rows.toLocaleString()}
                      {batch.total_rows > 0 && batch.error_rows > 0 && (
                        <span className="text-xs ml-1 opacity-70">
                          ({((batch.error_rows / batch.total_rows) * 100).toFixed(1)}%)
                        </span>
                      )}
                    </TableCell>
                    <TableCell>
                      {batch.status === 'completed' ? (
                        <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200 gap-1">
                          <CheckCircle2 className="w-3 h-3" /> 已完成
                        </Badge>
                      ) : batch.status === 'processing' ? (
                        <Badge className="bg-blue-500 flex items-center gap-1 w-fit">
                          <Loader2 className="w-3 h-3 animate-spin" /> 执行中
                        </Badge>
                      ) : batch.status === 'failed' ? (
                        <Badge variant="destructive" className="flex items-center gap-1 w-fit">
                          <AlertCircle className="w-3 h-3" /> 失败
                        </Badge>
                      ) : (
                        <Badge variant="secondary">{batch.status}</Badge>
                      )}
                    </TableCell>
                    <TableCell className="text-right text-slate-500 text-sm">
                      {new Date(batch.created_at).toLocaleString('zh-CN', {
                        month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
                      })}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </ScrollArea>
        )}
      </CardContent>
    </Card>
  );
};

export default BatchHistory;
