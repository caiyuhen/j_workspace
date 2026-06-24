import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Play, Server, Database, CheckCircle2, XCircle, Activity, Loader2, Square } from 'lucide-react';
import { toast } from 'sonner';

interface PipelineStatus {
  status: 'idle' | 'running' | 'success' | 'failed' | 'cancelled';
  last_run: string | null;
  metrics: {
    total: number;
    passed: number;
    failed: number;
  };
  connections: {
    sqlite: boolean;
    postgres: boolean;
    mongodb: boolean;
  };
  logs: string[];
}

export function PipelineMonitor() {
  const [pipelineData, setPipelineData] = useState<PipelineStatus>({
    status: 'idle',
    last_run: null,
    metrics: { total: 0, passed: 0, failed: 0 },
    connections: { sqlite: false, postgres: false, mongodb: false },
    logs: []
  });

  const fetchStatus = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8080/api/v1/pipeline/status');
      if (res.ok) {
        const data = await res.json();
        setPipelineData(data);
      }
    } catch (error) {
      console.error("Failed to fetch pipeline status", error);
    }
  };

  useEffect(() => {
    // Initial fetch
    fetchStatus();
    // Poll every 2 seconds unconditionally to avoid stale closure issues
    const interval = setInterval(() => {
      fetchStatus();
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  const handleRunPipeline = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8080/api/v1/pipeline/run', { method: 'POST' });
      if (res.ok) {
        toast.success('已触发清洗与标准化管线');
        setPipelineData(prev => ({ ...prev, status: 'running', logs: ['[System] 发送管线执行指令...'] }));
        fetchStatus();
      } else {
        toast.error('管线正在运行中，无法重复触发');
      }
    } catch (error) {
      toast.error('网络错误');
    }
  };

  const handleStopPipeline = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8080/api/v1/pipeline/stop', { method: 'POST' });
      if (res.ok) {
        toast.warning('已发送停止指令');
        fetchStatus();
      } else {
        toast.error('无法停止当前管线');
      }
    } catch (error) {
      toast.error('网络错误');
    }
  };

  const getStatusBadge = () => {
    switch (pipelineData.status) {
      case 'running': return <Badge className="bg-blue-500 flex items-center gap-1"><Loader2 className="w-3 h-3 animate-spin" /> 执行中</Badge>;
      case 'success': return <Badge className="bg-green-500">已完成</Badge>;
      case 'failed': return <Badge className="bg-red-500">执行失败</Badge>;
      case 'cancelled': return <Badge className="bg-orange-500">已终止</Badge>;
      default: return <Badge variant="secondary">待命</Badge>;
    }
  };

  const ConnectionStatus = ({ name, isConnected }: { name: string, isConnected: boolean }) => (
    <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg border border-slate-100">
      <div className="flex items-center gap-2">
        <Server className="w-4 h-4 text-slate-500" />
        <span className="text-sm font-medium text-slate-700">{name}</span>
      </div>
      {isConnected ? (
        <CheckCircle2 className="w-5 h-5 text-green-500" />
      ) : (
        <XCircle className="w-5 h-5 text-red-400" />
      )}
    </div>
  );

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-900">数据清洗与归一化管线</h2>
          <p className="text-slate-500 mt-1">Staging -&gt; 术语标准化 (PG) -&gt; 目标物理隔离 (MongoDB)</p>
        </div>
        <div className="flex gap-3">
          {pipelineData.status === 'running' ? (
            <Button 
              onClick={handleStopPipeline}
              variant="destructive"
              className="gap-2"
            >
              <Square className="w-4 h-4 fill-current" />
              停止管线
            </Button>
          ) : (
            <Button 
              onClick={handleRunPipeline}
              className="bg-indigo-600 hover:bg-indigo-700 gap-2"
            >
              <Play className="w-4 h-4" />
              执行数据管线
            </Button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Node Status Card */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <Activity className="w-4 h-4 text-blue-500" /> 
              节点连通性监控
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <ConnectionStatus name="本地 Staging 提取 (SQLite)" isConnected={pipelineData.connections.sqlite} />
            <ConnectionStatus name="术语字典对接 (PostgreSQL)" isConnected={pipelineData.connections.postgres} />
            <ConnectionStatus name="目标隔离库写入 (MongoDB)" isConnected={pipelineData.connections.mongodb} />
          </CardContent>
        </Card>

        {/* Metrics Card */}
        <Card className="md:col-span-2">
          <CardHeader className="pb-3 flex flex-row items-center justify-between">
            <CardTitle className="text-base flex items-center gap-2">
              <Database className="w-4 h-4 text-emerald-500" /> 
              处理指标与状态
            </CardTitle>
            {getStatusBadge()}
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-4 text-center mt-2">
              <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
                <div className="text-sm text-slate-500 mb-1">提取总行数</div>
                <div className="text-3xl font-bold text-slate-800">{pipelineData.metrics.total}</div>
              </div>
              <div className="bg-emerald-50 p-4 rounded-xl border border-emerald-100">
                <div className="text-sm text-emerald-600 mb-1">
                  术语对齐 ({pipelineData.metrics.total > 0 ? ((pipelineData.metrics.passed / pipelineData.metrics.total) * 100).toFixed(1) : '0.0'}%)
                </div>
                <div className="text-3xl font-bold text-emerald-600">{pipelineData.metrics.passed}</div>
              </div>
              <div className="bg-red-50 p-4 rounded-xl border border-red-100 flex flex-col justify-between">
                <div>
                  <div className="text-sm text-red-600 mb-1">校验拦截</div>
                  <div className="text-3xl font-bold text-red-600">{pipelineData.metrics.failed}</div>
                </div>
                {pipelineData.metrics.failed > 0 && (
                  <Button 
                    variant="outline" 
                    size="sm" 
                    className="mt-2 text-xs border-red-200 text-red-600 hover:bg-red-100 h-7"
                    onClick={() => window.open('http://127.0.0.1:8080/api/v1/pipeline/errors/download', '_blank')}
                  >
                    下载异常报告
                  </Button>
                )}
              </div>
            </div>
            {pipelineData.last_run && (
              <p className="text-xs text-slate-400 mt-4 text-right">
                上次运行时间: {new Date(pipelineData.last_run).toLocaleString()}
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Logs Console */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <Activity className="w-4 h-4 text-slate-500" /> 
            实时执行日志
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="bg-slate-900 rounded-lg p-4 h-64 overflow-y-auto font-mono text-xs text-slate-300">
            {pipelineData.logs.length === 0 ? (
              <div className="text-slate-600 text-center mt-24">暂无执行日志，请点击上方按钮触发管线</div>
            ) : (
              pipelineData.logs.map((log, idx) => {
                let color = "text-slate-300";
                if (log.includes("[ERROR]") || log.includes("❌")) color = "text-red-400";
                if (log.includes("[WARNING]")) color = "text-yellow-400";
                if (log.includes("✅")) color = "text-emerald-400";
                
                return (
                  <div key={idx} className={`mb-1 ${color}`}>
                    {log}
                  </div>
                );
              })
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
