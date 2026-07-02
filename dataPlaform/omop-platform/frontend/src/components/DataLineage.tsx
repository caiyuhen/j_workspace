import React, { useState } from 'react';
import { Network, Search, ArrowRight, Activity, Beaker, Pill, RefreshCw, Dices, Database, Cpu, LayoutTemplate } from 'lucide-react';
import { Card } from '@/components/ui/card';

interface LineageData {
  patient_id: string;
  stage1: {
    source_file: string;
    raw_data: Record<string, any>;
  };
  stage2: {
    stg_person: Record<string, any>;
    stg_condition_occurrence: string[];
    stg_measurement: string[];
    stg_drug_exposure: string[];
  };
  stage3: Record<string, any>;
}

export const DataLineage: React.FC = () => {
  const [patientId, setPatientId] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<LineageData | null>(null);

  const fetchLineage = async (pid: string) => {
    if (!pid) return;
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`http://127.0.0.1:8433/api/v1/pipeline/lineage/${pid}`);
      if (!response.ok) {
        if (response.status === 404) throw new Error('未找到该患者的数据血缘记录');
        throw new Error('获取数据血缘失败');
      }
      const result = await response.json();
      setData(result.data);
    } catch (err: any) {
      setError(err.message);
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchLineage(patientId);
  };

  const handleRandomSample = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('http://127.0.0.1:8433/api/v1/pipeline/lineage/random');
      if (!response.ok) throw new Error('随机抽取失败');
      const result = await response.json();
      setPatientId(result.data.patient_id);
      setData(result.data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="p-3 bg-indigo-100 rounded-lg">
          <Network className="w-6 h-6 text-indigo-600" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-slate-800">数据血缘与全链路追踪</h2>
          <p className="text-sm text-slate-500">追踪患者数据从原始上传 CSV 到 OMOP CDM 标准化落盘的转换过程，验证 NLP 和规则引擎的提取准确性。</p>
        </div>
      </div>

      <Card className="p-6">
        <form onSubmit={handleSearch} className="flex gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
            <input
              type="text"
              value={patientId}
              onChange={(e) => setPatientId(e.target.value)}
              placeholder="输入 Patient ID 进行血缘追踪..."
              className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all"
            />
          </div>
          <button
            type="submit"
            disabled={loading || !patientId}
            className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50 font-medium"
          >
            追踪
          </button>
          <button
            type="button"
            onClick={handleRandomSample}
            disabled={loading}
            className="px-6 py-2 bg-white border border-indigo-200 text-indigo-600 rounded-lg hover:bg-indigo-50 transition-colors disabled:opacity-50 flex items-center gap-2 font-medium"
          >
            <Dices className="w-4 h-4" />
            随机抽取
          </button>
        </form>

        {error && (
          <div className="mt-4 p-4 bg-red-50 text-red-600 rounded-lg border border-red-100">
            {error}
          </div>
        )}
      </Card>

      {loading && (
        <div className="flex items-center justify-center p-12 text-slate-500">
          <RefreshCw className="w-8 h-8 animate-spin mr-3 text-indigo-500" />
          <span>正在构建数据血缘图谱...</span>
        </div>
      )}

      {data && !loading && (
        <div className="overflow-x-auto pb-4">
          <div className="grid grid-cols-3 gap-6 min-w-[900px]">

          {/* Stage 1: 源数据 (Source) */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold flex items-center gap-2 text-slate-700">
              <span className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center text-slate-600 font-bold text-sm">1</span>
              源数据
            </h3>
            <Card className="p-0 bg-slate-900 overflow-hidden h-[800px] flex flex-col">
              <div className="bg-slate-800 px-4 py-2 text-slate-400 text-xs font-mono border-b border-slate-700 flex justify-between shrink-0">
                <span>{data.stage1.source_file}</span>
                <span>Raw</span>
              </div>
              <div className="p-4 overflow-auto text-xs font-mono text-slate-300 flex-1">
                <pre>
                  {JSON.stringify(data.stage1.raw_data, null, 2)}
                </pre>
              </div>
            </Card>
          </div>

          {/* Stage 2: Staging */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold flex items-center gap-2 text-blue-700">
              <span className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-bold text-sm">2</span>
              Staging
            </h3>
            <Card className="p-0 bg-slate-900 overflow-hidden h-[800px] flex flex-col">
              <div className="bg-slate-800 px-4 py-2 text-slate-400 text-xs font-mono border-b border-slate-700 flex justify-between shrink-0">
                <span>staging_tables.json</span>
                <span>Relational</span>
              </div>
              <div className="p-4 overflow-auto text-xs font-mono text-blue-400 flex-1">
                <pre>
                  {JSON.stringify(data.stage2, null, 2)}
                </pre>
              </div>
            </Card>
          </div>

          {/* Stage 3: 清洗后的数据 (进入Mongo的数据) */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold flex items-center gap-2 text-emerald-700">
              <span className="w-8 h-8 rounded-full bg-emerald-100 flex items-center justify-center text-emerald-600 font-bold text-sm">3</span>
              清洗后的数据 (MongoDB)
            </h3>
            <Card className="p-0 bg-slate-900 overflow-hidden h-[800px] flex flex-col">
              <div className="bg-slate-800 px-4 py-2 text-slate-400 text-xs font-mono border-b border-slate-700 flex justify-between shrink-0">
                <span>{data.patient_id}.json</span>
                <span>OMOP Nested</span>
              </div>
              <div className="p-4 overflow-auto text-xs font-mono text-emerald-400 flex-1">
                <pre>
                  {JSON.stringify(data.stage3, null, 2)}
                </pre>
              </div>
            </Card>
          </div>

        </div>
      </div>
      )}
    </div>
  );
};