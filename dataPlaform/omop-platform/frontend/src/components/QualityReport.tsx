import React, { useState, useEffect } from 'react';
import { Activity, Database, CheckCircle, AlertTriangle, FileText, Pill, Stethoscope, RefreshCw } from 'lucide-react';

interface QualityMetrics {
  total_conditions: number;
  total_measurements: number;
  total_drugs: number;
  total_observations: number;
  standardized_conditions: number;
  standardized_measurements: number;
  standardized_drugs: number;
}

interface QualityReportResponse {
  status: string;
  message?: string;
  total_patients: number;
  metrics: QualityMetrics;
}

export const QualityReport: React.FC = () => {
  const [report, setReport] = useState<QualityReportResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchReport = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('http://127.0.0.1:8080/api/v1/pipeline/quality-report');
      if (!response.ok) {
        throw new Error('获取报告失败');
      }
      const data = await response.json();
      setReport(data);
    } catch (err: any) {
      setError(err.message || '网络错误');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReport();
  }, []);

  if (loading) {
    return (
      <div className="bg-white p-8 rounded-xl border flex flex-col items-center justify-center min-h-[400px] text-slate-500">
        <RefreshCw className="w-8 h-8 animate-spin mb-4 text-blue-500" />
        <p>正在生成质量评估报告，请稍候...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white p-8 rounded-xl border flex flex-col items-center justify-center min-h-[400px] text-red-500">
        <AlertTriangle className="w-8 h-8 mb-4" />
        <p>{error}</p>
        <button onClick={fetchReport} className="mt-4 px-4 py-2 bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200">
          重试
        </button>
      </div>
    );
  }

  if (!report || report.status === 'empty' || report.total_patients === 0) {
    return (
      <div className="bg-white p-8 rounded-xl border flex flex-col items-center justify-center min-h-[400px] text-slate-500">
        <Database className="w-12 h-12 mb-4 text-slate-300" />
        <p className="text-lg font-medium text-slate-700">暂无数据</p>
        <p className="mt-2">MongoDB 中目前没有已清洗的数据，请先执行数据管线。</p>
        <button onClick={fetchReport} className="mt-6 px-4 py-2 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 flex items-center gap-2">
          <RefreshCw className="w-4 h-4" />
          刷新状态
        </button>
      </div>
    );
  }

  const m = report.metrics;

  const calculateRate = (standardized: number, total: number) => {
    if (total === 0) return 0;
    return Math.round((standardized / total) * 100);
  };

  const cards = [
    {
      title: '诊断记录 (Condition)',
      icon: <Stethoscope className="w-6 h-6 text-indigo-500" />,
      bg: 'bg-indigo-50',
      total: m.total_conditions,
      standardized: m.standardized_conditions,
    },
    {
      title: '生化检验 (Measurement)',
      icon: <Activity className="w-6 h-6 text-emerald-500" />,
      bg: 'bg-emerald-50',
      total: m.total_measurements,
      standardized: m.standardized_measurements,
    },
    {
      title: '药品处方 (Drug Exposure)',
      icon: <Pill className="w-6 h-6 text-rose-500" />,
      bg: 'bg-rose-50',
      total: m.total_drugs,
      standardized: m.standardized_drugs,
    },
    {
      title: '临床观察与NLP (Observation)',
      icon: <FileText className="w-6 h-6 text-amber-500" />,
      bg: 'bg-amber-50',
      total: m.total_observations,
      // Observation might not be fully standardized in MVP, show total
      standardized: m.total_observations, 
      hideRate: true
    }
  ];

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-xl border flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-800 flex items-center gap-2">
            <CheckCircle className="w-6 h-6 text-green-500" />
            数据清洗与对齐质量报告
          </h2>
          <p className="text-slate-500 mt-1">
            {report.status === 'fallback' 
              ? '当前为沙盒离线模式，显示缓存/模拟的评估结果。' 
              : '基于目标 MongoDB 数据库中的结构化 JSON 文档生成。'}
          </p>
        </div>
        <div className="text-right">
          <p className="text-sm text-slate-500 mb-1">已清洗患者总数</p>
          <p className="text-3xl font-black text-blue-600">{report.total_patients.toLocaleString()}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {cards.map((card, idx) => {
          const rate = calculateRate(card.standardized, card.total);
          return (
            <div key={idx} className="bg-white p-6 rounded-xl border flex flex-col">
              <div className="flex items-center gap-3 mb-4">
                <div className={`p-3 rounded-lg ${card.bg}`}>
                  {card.icon}
                </div>
                <h3 className="font-semibold text-slate-700">{card.title}</h3>
              </div>
              
              <div className="mt-auto space-y-4">
                <div>
                  <p className="text-sm text-slate-500">解析入库总条数</p>
                  <p className="text-2xl font-bold text-slate-800">{card.total.toLocaleString()}</p>
                </div>
                
                {!card.hideRate && (
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-slate-500">术语对齐率</span>
                      <span className="font-medium text-slate-700">{rate}%</span>
                    </div>
                    <div className="w-full bg-slate-100 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full ${rate >= 90 ? 'bg-green-500' : rate >= 50 ? 'bg-yellow-500' : 'bg-red-500'}`}
                        style={{ width: `${rate}%` }}
                      ></div>
                    </div>
                    <p className="text-xs text-slate-400 mt-2">
                      成功映射: {card.standardized.toLocaleString()} 条
                    </p>
                  </div>
                )}
                {card.hideRate && (
                  <div>
                     <p className="text-sm text-slate-500 mt-6">包含主诉、现病史等非结构化特征</p>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
