import React, { useState, useEffect } from 'react';
import { ArrowRight, RefreshCw, FileJson, Database, Server } from 'lucide-react';

export const DataComparison: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://127.0.0.1:8080/api/v1/pipeline/data-comparison');
      const json = await res.json();
      setData(json);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  if (loading && !data) {
    return (
      <div className="p-8 text-center bg-white rounded-xl border mt-8">
        <RefreshCw className="animate-spin w-6 h-6 mx-auto text-blue-500" />
        <div className="mt-2 text-slate-500">正在加载数据对比信息...</div>
      </div>
    );
  }

  if (!data || data.status !== 'success') {
    return (
      <div className="p-8 text-center bg-white rounded-xl border mt-8">
        <div className="text-slate-500">{data?.message || '无法加载对比数据'}</div>
      </div>
    );
  }

  return (
    <div className="mt-8 space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-bold text-slate-800">数据血缘追踪 (Patient ID: {data.patient_id})</h2>
        <button 
          onClick={fetchData} 
          disabled={loading}
          className="px-4 py-2 bg-blue-50 text-blue-600 rounded-lg flex items-center gap-2 hover:bg-blue-100 transition-colors"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          随机抽取示例患者
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Source */}
        <div className="bg-white rounded-xl border flex flex-col h-[600px] shadow-sm">
          <div className="p-4 flex items-center gap-2 border-b bg-slate-50 rounded-t-xl text-slate-700 font-semibold">
            <FileJson className="w-5 h-5 text-slate-500" />
            源数据 (解析入库)
          </div>
          <div className="flex-1 overflow-auto p-4 text-xs font-mono bg-[#1e1e1e] text-white">
            <pre>{JSON.stringify(data.raw_data, null, 2)}</pre>
          </div>
        </div>

        {/* Staging */}
        <div className="bg-white rounded-xl border flex flex-col h-[600px] shadow-sm relative">
          <div className="absolute -left-4 top-1/2 -translate-y-1/2 bg-white border rounded-full p-1 z-10 hidden lg:block shadow-sm">
            <ArrowRight className="w-5 h-5 text-slate-400" />
          </div>
          <div className="p-4 flex items-center gap-2 border-b bg-blue-50 rounded-t-xl text-blue-800 font-semibold">
            <Database className="w-5 h-5 text-blue-500" />
            导入数据 (SQLite Staging)
          </div>
          <div className="flex-1 overflow-auto p-4 text-xs font-mono bg-[#1e1e1e] text-white">
            <pre>{JSON.stringify(data.staging_data, null, 2)}</pre>
          </div>
        </div>

        {/* Cleaned */}
        <div className="bg-white rounded-xl border flex flex-col h-[600px] shadow-sm relative">
          <div className="absolute -left-4 top-1/2 -translate-y-1/2 bg-white border rounded-full p-1 z-10 hidden lg:block shadow-sm">
            <ArrowRight className="w-5 h-5 text-slate-400" />
          </div>
          <div className="p-4 flex items-center gap-2 border-b bg-emerald-50 rounded-t-xl text-emerald-800 font-semibold">
            <Server className="w-5 h-5 text-emerald-500" />
            清洗完数据 (MongoDB)
          </div>
          <div className="flex-1 overflow-auto p-4 text-xs font-mono bg-[#1e1e1e] text-white">
            <pre>{JSON.stringify(data.cleaned_data, null, 2)}</pre>
          </div>
        </div>
      </div>
    </div>
  );
};
