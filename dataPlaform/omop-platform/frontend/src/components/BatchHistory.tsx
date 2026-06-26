import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { History, FileText, CheckCircle2, AlertCircle, Loader2, Trash2, BarChart2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { toast } from 'sonner'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import type { Batch } from '@/types'

interface BatchHistoryProps {
  batches: Batch[];
  loading: boolean;
  error: string | null;
  onRefresh?: () => void;
  autoOpenBatchId?: string | null;
  onAutoOpenDone?: () => void;
  onOpenProfiling?: (batch: Batch) => void;
}

const BatchHistory: React.FC<BatchHistoryProps> = ({ batches = [], loading, error, onRefresh, autoOpenBatchId, onAutoOpenDone, onOpenProfiling }) => {
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

  // Handle auto open profiling data
  useEffect(() => {
    if (autoOpenBatchId && batches) {
      const targetBatch = batches.find(b => b.id === autoOpenBatchId);
      if (targetBatch) {
        if (targetBatch.status === 'completed' && targetBatch.profiling_data) {
          if (onOpenProfiling) onOpenProfiling(targetBatch);
          if (onAutoOpenDone) onAutoOpenDone();
        } else if (targetBatch.status === 'failed') {
          toast.error(`文件 ${targetBatch.filename} 处理失败`);
          if (onAutoOpenDone) onAutoOpenDone();
        }
      }
    }
  }, [autoOpenBatchId, batches, onAutoOpenDone, onOpenProfiling]);

  const handleClearData = async () => {
    setClearing(true);
    try {
      const res = await fetch('http://127.0.0.1:8080/api/v1/ingestion/clear', {
        method: 'POST',
      });
      if (!res.ok) throw new Error('清除数据失败');
      setShowConfirm(false);
      toast.success('历史数据与影像文件已全部清空');
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
          {batches && batches.length > 0 && batches[0].profiling_data && batches[0].profiling_data.length > 0 && (() => {
            const latest = batches[0];
            const errorRate = latest.total_rows > 0 ? (latest.error_rows / latest.total_rows * 100).toFixed(1) : '0.0';
            const hasError = latest.error_rows > 0;
            // 假设存在 null_rate，进行高空值统计
            const highNullCols = latest.profiling_data.filter((c: any) => c.null_rate > 0.5).length;
            const hasNullAnomalies = highNullCols > 0;
            const isAnomalous = hasError || hasNullAnomalies;
            
            return (
              <Button 
                variant="outline" 
                onClick={() => onOpenProfiling && onOpenProfiling(latest)}
                className={`flex items-center gap-3 h-10 px-3 border shadow-sm transition-all ${isAnomalous ? 'border-orange-200 bg-orange-50/50 hover:bg-orange-100' : 'border-emerald-200 bg-emerald-50/50 hover:bg-emerald-100'}`}
              >
                {/* Mini Inline Chart */}
                <div className="flex items-end gap-[2px] h-5 w-5 pb-0.5" title="异常概览">
                  <div className={`w-1.5 rounded-t-[1px] ${isAnomalous ? 'bg-orange-300' : 'bg-emerald-300'} h-[50%]`}></div>
                  <div className={`w-1.5 rounded-t-[1px] ${isAnomalous ? 'bg-orange-400' : 'bg-emerald-400'} h-[80%]`}></div>
                  <div className={`w-1.5 rounded-t-[1px] ${hasError ? 'bg-red-500 animate-pulse' : hasNullAnomalies ? 'bg-orange-500' : 'bg-emerald-500'} h-[100%]`}></div>
                </div>
                <div className="flex flex-col items-start text-left justify-center">
                  <span className={`text-xs font-bold leading-none mb-1 ${isAnomalous ? 'text-orange-700' : 'text-emerald-700'}`}>
                    异常分析图表
                  </span>
                  <span className={`text-[10px] leading-none font-medium ${isAnomalous ? 'text-orange-600' : 'text-emerald-600'}`}>
                    {hasError ? `行异常率 ${errorRate}%` : hasNullAnomalies ? `${highNullCols}个字段高空值` : '数据质量优良'}
                  </span>
                </div>
              </Button>
            );
          })()}
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
                  <TableHead className="text-center">操作</TableHead>
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
                    <TableCell className="text-center">
                      <Button 
                        variant="ghost" 
                        size="sm" 
                        disabled={batch.status !== 'completed'}
                        onClick={() => onOpenProfiling && onOpenProfiling(batch)}
                        className="h-8 flex items-center gap-1 text-blue-600 hover:text-blue-700 hover:bg-blue-50"
                      >
                        <BarChart2 className="w-4 h-4" />
                        数据分布探查
                      </Button>
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
