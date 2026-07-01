import React, { useState, useEffect } from 'react';
import { BrainCircuit, AlertTriangle, RefreshCw, Activity, Pill, FileText } from 'lucide-react';

interface NLPStatItem {
  name: string;
  count: number;
}

interface NLPStatsResponse {
  status: string;
  message?: string;
  data?: {
    conditions: NLPStatItem[];
    drugs: NLPStatItem[];
    observations: NLPStatItem[];
  };
}

export const NLPAnalysis: React.FC = () => {
  const [stats, setStats] = useState<NLPStatsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('http://127.0.0.1:8433/api/v1/pipeline/nlp-stats');
      if (!response.ok) {
        throw new Error('获取NLP分析数据失败');
      }
      const data = await response.json();
      setStats(data);
    } catch (err: any) {
      setError(err.message || '网络错误');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  if (loading) {
    return (
      <div className="bg-white p-6 rounded-xl border flex items-center justify-center min-h-[300px] text-slate-500">
        <RefreshCw className="w-6 h-6 animate-spin mr-3 text-purple-500" />
        <p>正在深度分析自然语言提取实体...</p>
      </div>
    );
  }

  if (error || (stats && stats.status === 'error')) {
    return (
      <div className="bg-white p-6 rounded-xl border flex items-center justify-center min-h-[300px] text-red-500">
        <AlertTriangle className="w-6 h-6 mr-3" />
        <p>{error || stats?.message}</p>
      </div>
    );
  }

  if (!stats || stats.status === 'empty' || !stats.data) {
    return (
      <div className="bg-white p-6 rounded-xl border flex items-center justify-center min-h-[300px] text-slate-500">
        <BrainCircuit className="w-8 h-8 mr-3 text-slate-300" />
        <p>{stats?.message || "暂无 NLP 分析数据"}</p>
      </div>
    );
  }

  const renderDistribution = (title: string, items: NLPStatItem[], icon: React.ReactNode, colorClass: string, bgClass: string) => {
    const maxCount = items.length > 0 ? Math.max(...items.map(i => i.count)) : 0;

    return (
      <div className="bg-white p-6 rounded-xl border shadow-sm">
        <div className="flex items-center gap-3 mb-6">
          <div className={`p-3 rounded-lg ${bgClass}`}>
            {icon}
          </div>
          <h3 className="text-lg font-semibold text-slate-800">{title}</h3>
        </div>
        
        {items.length === 0 ? (
          <p className="text-sm text-slate-400 italic">暂无相关实体</p>
        ) : (
          <div className="space-y-4">
            {items.map((item, idx) => (
              <div key={idx} className="relative">
                <div className="flex justify-between text-sm mb-1">
                  <span className="font-medium text-slate-700 truncate pr-4" title={item.name}>{item.name}</span>
                  <span className="text-slate-500">{item.count} 次</span>
                </div>
                <div className="w-full bg-slate-100 rounded-full h-2">
                  <div 
                    className={`${colorClass} h-2 rounded-full transition-all duration-1000`} 
                    style={{ width: `${maxCount > 0 ? (item.count / maxCount) * 100 : 0}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="mt-8 space-y-6">
      <div className="flex items-center gap-3 mb-2">
        <BrainCircuit className="w-7 h-7 text-purple-600" />
        <h2 className="text-xl font-bold text-slate-800">NLP 深度语义提取分析</h2>
        <span className="px-3 py-1 bg-purple-100 text-purple-700 text-xs font-medium rounded-full ml-2">
          Hugging Face Transformers
        </span>
      </div>
      <p className="text-slate-500 text-sm mb-6">
        基于深度学习 NER 模型从非结构化文本（如主诉、现病史、影像报告）中自动抽取的实体分布。
      </p>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {renderDistribution(
          "疾病与症状 (Top 10)", 
          stats.data.conditions, 
          <Activity className="w-6 h-6 text-rose-500" />, 
          "bg-rose-500", 
          "bg-rose-50"
        )}
        {renderDistribution(
          "提取药品 (Top 10)", 
          stats.data.drugs, 
          <Pill className="w-6 h-6 text-blue-500" />, 
          "bg-blue-500", 
          "bg-blue-50"
        )}
        {renderDistribution(
          "独立文本观察 (Top 10)", 
          stats.data.observations, 
          <FileText className="w-6 h-6 text-amber-500" />, 
          "bg-amber-500", 
          "bg-amber-50"
        )}
      </div>
    </div>
  );
};
