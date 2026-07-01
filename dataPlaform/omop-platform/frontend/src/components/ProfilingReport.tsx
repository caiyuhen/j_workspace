import React, { useMemo, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog"
import { ScrollArea } from "@/components/ui/scroll-area"
import { ArrowLeft, BarChart2, FileText, AlertCircle, Database, Hash, Type, AlertTriangle, Bug } from "lucide-react"
import type { Batch } from '@/types'

interface ProfilingReportProps {
  batch?: Batch | null;
  onBack: () => void;
}

export const ProfilingReport: React.FC<ProfilingReportProps> = ({ batch, onBack }) => {
  const [showErrorModal, setShowErrorModal] = useState(false);
  const [errorDetails, setErrorDetails] = useState<any[]>([]);
  const [loadingErrors, setLoadingErrors] = useState(false);

  const fetchErrorDetails = async () => {
    if (!batch?.id) return;
    setLoadingErrors(true);
    setShowErrorModal(true);
    try {
      const res = await fetch(`http://127.0.0.1:8433/api/v1/ingestion/batches/${batch.id}/errors`);
      const data = await res.json();
      setErrorDetails(data.items || []);
    } catch (err) {
      console.error("Failed to fetch error details", err);
    } finally {
      setLoadingErrors(false);
    }
  };
  if (!batch) {
    return (
      <div className="space-y-4">
        <Button variant="ghost" onClick={onBack} className="flex items-center gap-2 mb-4">
          <ArrowLeft className="w-4 h-4" /> 返回工作台
        </Button>
        <Card className="border-slate-200">
          <CardContent className="p-10 flex flex-col items-center justify-center min-h-[400px] text-slate-500 gap-4">
            <AlertCircle className="w-12 h-12 text-slate-300" />
            <p>请先在数据接入工作台选择一个已完成解析的批次查看探查报告。</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const { filename, profiling_data, total_rows, error_rows } = batch;

  const summary = useMemo(() => {
    if (!profiling_data || !Array.isArray(profiling_data)) return null;
    
    const totalFields = profiling_data.length;
    const numericFields = profiling_data.filter((d: any) => d.type === 'numeric').length;
    const stringFields = profiling_data.filter((d: any) => d.type === 'string').length;
    const highNullFields = profiling_data.filter((d: any) => d.null_rate > 0.2); // >20% null rate is considered high
    const averageNullRate = profiling_data.reduce((acc: number, d: any) => acc + d.null_rate, 0) / totalFields;
    const errorRate = total_rows > 0 ? (error_rows / total_rows) * 100 : 0;

    return {
      totalFields,
      numericFields,
      stringFields,
      highNullFields,
      averageNullRate,
      totalRows: total_rows,
      errorRows: error_rows,
      errorRate
    };
  }, [profiling_data, total_rows, error_rows]);

  const displayedData = profiling_data || [];

    if (displayedData.length === 0) {
      // Look for dicom URL in the first few records if available, though typically we just get batch info here.
      // Wait, profiling_data usually holds metadata directly for dicom batches.
      let dicomUrl = null;
      try {
        if (batch.profiling_data && batch.profiling_data.length > 0) {
          // If value_as_string was parsed or raw JSON is here
          const meta = typeof batch.profiling_data[0] === 'string' ? JSON.parse(batch.profiling_data[0]) : batch.profiling_data[0];
          if (meta && meta._dicom_url) {
            dicomUrl = meta._dicom_url;
          }
        }
      } catch (e) {
        console.error("Failed to extract DICOM URL", e);
      }

      return (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
          <div className="flex items-center justify-between">
            <Button variant="ghost" onClick={onBack} className="flex items-center gap-2 text-slate-600 hover:text-slate-900">
              <ArrowLeft className="w-4 h-4" /> 返回列表
            </Button>
            <div className="flex items-center gap-2 text-sm text-slate-500 bg-white px-3 py-1.5 rounded-full border shadow-sm">
              <FileText className="w-4 h-4" />
              <span>当前分析文件: <strong>{filename}</strong></span>
            </div>
          </div>
          <Card className="border-none shadow-md overflow-hidden min-h-[400px] flex flex-col items-center justify-center text-slate-500 p-6">
            <BarChart2 className="w-16 h-16 text-slate-200 mb-4" />
            <p className="text-lg">该批次（如 DICOM 影像文件）暂无结构化探查数据。</p>
            <p className="text-sm mt-2 opacity-80 mb-6 text-center max-w-lg">影像文件的元数据已提取至 StagingObservation 区，影像本体已归档脱敏存储至 MinIO。</p>
            
            {dicomUrl ? (
              <div className="flex flex-col items-center gap-4 border border-blue-100 bg-blue-50/50 p-6 rounded-xl">
                <p className="text-sm font-medium text-blue-800">影像已脱敏并安全归档</p>
                <Button onClick={() => window.open(dicomUrl, '_blank')} className="bg-blue-600 hover:bg-blue-700 h-10 px-6 shadow-sm">
                  <FileText className="w-4 h-4 mr-2" />
                  在线查看 / 下载 DICOM 原片
                </Button>
                <p className="text-xs text-blue-500 max-w-xs text-center">系统通过 MinIO 对象存储生成了带有签名的安全临时访问链接。</p>
              </div>
            ) : (
              <Button variant="outline" disabled className="opacity-50">
                暂未获取到影像直链
              </Button>
            )}
          </Card>
        </div>
      );
    }

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex items-center justify-between">
        <Button variant="ghost" onClick={onBack} className="flex items-center gap-2 text-slate-600 hover:text-slate-900">
          <ArrowLeft className="w-4 h-4" /> 返回列表
        </Button>
        <div className="flex items-center gap-2 text-sm text-slate-500 bg-white px-3 py-1.5 rounded-full border shadow-sm">
          <FileText className="w-4 h-4" />
          <span>当前分析文件: <strong>{filename}</strong></span>
        </div>
      </div>

      <Card className="border-none shadow-md overflow-hidden">
        <div className="bg-gradient-to-r from-blue-600 to-indigo-700 p-6 text-white flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold flex items-center gap-3">
              <BarChart2 className="w-6 h-6 text-blue-200" />
              数据质量与分布全景探查
            </h2>
            <p className="text-blue-100 mt-2 opacity-90 max-w-2xl">
              基于 Pandas 自动推断数据类型，识别高空值字段，并提取各列中出现频率最高的 Top 10 真实数据分布。
            </p>
          </div>
        </div>
        
        {/* 统一分析概览区域 */}
        {summary && (
          <div className="bg-white border-b border-slate-100 p-6">
            <h3 className="text-lg font-semibold text-slate-800 mb-4 flex items-center gap-2">
              <Database className="w-5 h-5 text-blue-600" />
              全局数据洞察
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div className="bg-slate-50 p-4 rounded-xl border border-slate-100 flex items-start gap-4">
                <div className="bg-slate-200 p-2 rounded-lg">
                  <Database className="w-5 h-5 text-slate-700" />
                </div>
                <div>
                  <p className="text-sm text-slate-500 font-medium">总数据行数</p>
                  <p className="text-2xl font-bold text-slate-800">{summary.totalRows.toLocaleString()}</p>
                </div>
              </div>

              <div 
                className={`p-4 rounded-xl border flex items-start gap-4 ${summary.errorRows > 0 ? 'bg-red-50 border-red-100 cursor-pointer hover:bg-red-100 transition-colors' : 'bg-green-50 border-green-100'}`}
                onClick={summary.errorRows > 0 ? fetchErrorDetails : undefined}
                title={summary.errorRows > 0 ? "点击查看具体的异常数据列表" : ""}
              >
                <div className={`${summary.errorRows > 0 ? 'bg-red-100' : 'bg-green-100'} p-2 rounded-lg`}>
                  <Bug className={`w-5 h-5 ${summary.errorRows > 0 ? 'text-red-600' : 'text-green-600'}`} />
                </div>
                <div>
                  <p className={`text-sm font-medium ${summary.errorRows > 0 ? 'text-red-700' : 'text-green-700'}`}>解析异常行数</p>
                  <p className={`text-2xl font-bold flex items-baseline gap-1 ${summary.errorRows > 0 ? 'text-red-800' : 'text-green-800'}`}>
                    {summary.errorRows.toLocaleString()} 
                    {summary.errorRows > 0 && <span className="text-sm font-normal text-red-600">({summary.errorRate.toFixed(1)}%)</span>}
                  </p>
                </div>
              </div>

              <div className="bg-slate-50 p-4 rounded-xl border border-slate-100 flex items-start gap-4">
                <div className="bg-blue-100 p-2 rounded-lg">
                  <FileText className="w-5 h-5 text-blue-700" />
                </div>
                <div>
                  <p className="text-sm text-slate-500 font-medium">总字段数</p>
                  <p className="text-2xl font-bold text-slate-800">{summary.totalFields}</p>
                </div>
              </div>
              
              <div className="bg-slate-50 p-4 rounded-xl border border-slate-100 flex items-start gap-4">
                <div className="bg-indigo-100 p-2 rounded-lg">
                  <Hash className="w-5 h-5 text-indigo-700" />
                </div>
                <div>
                  <p className="text-sm text-slate-500 font-medium">数值型字段</p>
                  <p className="text-2xl font-bold text-slate-800">{summary.numericFields}</p>
                </div>
              </div>
              
              <div className={`p-4 rounded-xl border flex items-start gap-4 ${summary.highNullFields.length > 0 ? 'bg-orange-50 border-orange-100' : 'bg-green-50 border-green-100'}`}>
                <div className={`${summary.highNullFields.length > 0 ? 'bg-orange-100' : 'bg-green-100'} p-2 rounded-lg`}>
                  <AlertTriangle className={`w-5 h-5 ${summary.highNullFields.length > 0 ? 'text-orange-600' : 'text-green-600'}`} />
                </div>
                <div>
                  <p className={`text-sm font-medium ${summary.highNullFields.length > 0 ? 'text-orange-700' : 'text-green-700'}`}>高空值警告 (&gt;20%)</p>
                  <p className={`text-2xl font-bold ${summary.highNullFields.length > 0 ? 'text-orange-800' : 'text-green-800'}`}>
                    {summary.highNullFields.length} <span className="text-sm font-normal">个字段</span>
                  </p>
                </div>
              </div>
            </div>
            
            {summary.highNullFields.length > 0 && (
              <div className="mt-4 bg-orange-50/50 border border-orange-100 rounded-lg p-3 text-sm text-orange-800 flex items-center gap-2 flex-wrap">
                <span className="font-semibold">需注意的字段:</span>
                {summary.highNullFields.map((f: any, i: number) => (
                  <Badge key={i} variant="outline" className="bg-white border-orange-200 text-orange-700 hover:bg-orange-50">
                    {f.name} ({(f.null_rate * 100).toFixed(1)}%)
                  </Badge>
                ))}
              </div>
            )}
          </div>
        )}

        <div className="p-6 bg-slate-50">
          {displayedData.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-slate-500">
              <div className="bg-green-100 p-4 rounded-full mb-4">
                <AlertCircle className="w-10 h-10 text-green-600" />
              </div>
              <h3 className="text-xl font-semibold text-slate-700 mb-2">太棒了！没有发现异常</h3>
              <p>当前数据集中没有包含空值或异常的字段。</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
              {displayedData.map((col: any, idx: number) => (
                <Card key={idx} className="border-slate-200 shadow-sm hover:shadow-md transition-shadow bg-white">
                  <CardHeader className="pb-3 border-b border-slate-100">
                    <div className="flex justify-between items-center">
                      <CardTitle className="text-lg font-bold text-slate-800 truncate pr-2" title={col.name}>
                        {col.name}
                      </CardTitle>
                      <Badge variant={col.type === 'numeric' ? 'default' : 'secondary'} className={col.type === 'numeric' ? 'bg-indigo-100 text-indigo-700 hover:bg-indigo-200 border-indigo-200' : ''}>
                        {col.type}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="pt-4">
                    <div className="mb-6">
                      <div className="flex justify-between text-sm mb-1.5">
                        <span className="text-slate-500 font-medium">空值率 (Null Rate)</span>
                        <span className={`font-bold ${col.null_rate > 0.5 ? 'text-red-500' : 'text-slate-700'}`}>
                          {(col.null_rate * 100).toFixed(1)}%
                        </span>
                      </div>
                      <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden shadow-inner">
                        <div 
                          className={`h-full transition-all duration-1000 ease-out ${col.null_rate > 0.5 ? 'bg-red-500' : 'bg-slate-400'}`}
                          style={{ width: `${col.null_rate * 100}%` }}
                        ></div>
                      </div>
                    </div>
                    
                    <div>
                      <p className="text-sm font-semibold text-slate-500 mb-3 flex items-center justify-between">
                        <span>Top 10 值分布</span>
                      </p>
                      <div className="space-y-3">
                        {col.distribution?.map((d: any, dIdx: number) => {
                          const maxCount = col.distribution[0]?.count || 1;
                          const pct = (d.count / maxCount) * 100;
                          return (
                            <div key={dIdx} className="text-sm flex items-center gap-3 group">
                              <div className="w-5/12 truncate text-slate-700 font-medium group-hover:text-blue-700 transition-colors" title={d.value}>
                                {d.value === 'nan' || !d.value ? '(空)' : d.value}
                              </div>
                              <div className="flex-1 bg-blue-50 h-6 rounded overflow-hidden shadow-inner">
                                <div className="bg-blue-500 h-full transition-all duration-700 ease-out group-hover:bg-blue-600" style={{ width: `${pct}%` }}></div>
                              </div>
                              <div className="w-16 text-right text-slate-800 font-bold">{d.count.toLocaleString()}</div>
                            </div>
                          );
                        })}
                        {(!col.distribution || col.distribution.length === 0) && (
                          <div className="py-4 text-center text-slate-400 text-sm border-2 border-dashed border-slate-100 rounded-lg">
                            暂无有效分布数据
                          </div>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </Card>

      <Dialog open={showErrorModal} onOpenChange={setShowErrorModal}>
        <DialogContent className="max-w-4xl max-h-[80vh] flex flex-col">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-red-600">
              <AlertTriangle className="w-5 h-5" />
              解析异常数据详情 ({summary?.errorRows.toLocaleString()} 行)
            </DialogTitle>
            <DialogDescription>
              以下是由于列数错位或格式损坏导致解析失败的数据行。
            </DialogDescription>
          </DialogHeader>
          
          <ScrollArea className="flex-1 mt-4 border rounded-md">
            {loadingErrors ? (
              <div className="p-8 text-center text-slate-500 animate-pulse">正在加载异常数据...</div>
            ) : errorDetails.length > 0 ? (
              <div className="p-4 space-y-4">
                {errorDetails.map((err, i) => (
                  <div key={i} className="bg-slate-50 border border-slate-200 rounded-lg p-3">
                    <div className="flex items-center gap-3 mb-2">
                      <Badge variant="destructive">第 {err.line_number} 行</Badge>
                      <span className="text-sm font-medium text-red-600">{err.error_message}</span>
                    </div>
                    <div className="bg-slate-900 text-slate-300 font-mono text-xs p-3 rounded overflow-x-auto whitespace-nowrap">
                      {err.raw_data}
                    </div>
                  </div>
                ))}
                {summary?.errorRows && summary.errorRows > 100 && (
                  <div className="text-center text-sm text-slate-500 pt-2">
                    仅显示前 100 条异常数据...
                  </div>
                )}
              </div>
            ) : (
              <div className="p-8 text-center text-slate-500">未能加载到具体的异常数据。</div>
            )}
          </ScrollArea>
        </DialogContent>
      </Dialog>
    </div>
  );
};
