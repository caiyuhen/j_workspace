import React, { useMemo, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { Batch } from '@/types';

interface BatchAnalyticsPanelProps {
  batches?: Batch[];
  onExport?: () => void;
  onSelectBatch?: (batch: Batch) => void;
}

const BatchAnalyticsPanel: React.FC<BatchAnalyticsPanelProps> = ({
  batches = [],
  onExport,
  onSelectBatch,
}) => {
  const [batchKeyword, setBatchKeyword] = useState('');
  const [startTime, setStartTime] = useState('');
  const [endTime, setEndTime] = useState('');

  const filteredBatches = useMemo(() => {
    return batches.filter((batch) => {
      const matchesKeyword =
        !batchKeyword ||
        batch.id.toLowerCase().includes(batchKeyword.toLowerCase()) ||
        batch.filename.toLowerCase().includes(batchKeyword.toLowerCase());
      const batchTime = new Date(batch.created_at).getTime();
      const matchesStart = !startTime || batchTime >= new Date(startTime).getTime();
      const matchesEnd = !endTime || batchTime <= new Date(endTime).getTime();
      return matchesKeyword && matchesStart && matchesEnd;
    });
  }, [batches, batchKeyword, startTime, endTime]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>批次分析</CardTitle>
        <CardDescription>按批次号、时间范围和批次类型查看增量处理结果。</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <Input
            placeholder="批次号"
            value={batchKeyword}
            onChange={(event) => setBatchKeyword(event.target.value)}
          />
          <Input
            placeholder="开始时间"
            type="datetime-local"
            value={startTime}
            onChange={(event) => setStartTime(event.target.value)}
          />
          <Input
            placeholder="结束时间"
            type="datetime-local"
            value={endTime}
            onChange={(event) => setEndTime(event.target.value)}
          />
          <Button onClick={onExport}>导出当前筛选</Button>
        </div>

        <div className="space-y-3">
          {filteredBatches.length === 0 ? (
            <div className="rounded-lg border border-dashed p-6 text-sm text-slate-500">
              暂无匹配的批次分析结果。
            </div>
          ) : (
            filteredBatches.map((batch) => (
              <div key={batch.id} className="rounded-lg border bg-slate-50 p-4">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="font-semibold text-slate-900">{batch.filename}</div>
                    <div className="mt-1 text-sm text-slate-500">
                      {batch.batch_type === 'incremental' ? '增量批次' : batch.batch_type === 'replay' ? '补处理批次' : '全量批次'}
                    </div>
                    <div className="mt-1 text-xs text-slate-400">{batch.id}</div>
                  </div>
                  <Button variant="outline" onClick={() => onSelectBatch?.(batch)}>
                    查看详情
                  </Button>
                </div>
                <div className="mt-3 flex flex-wrap gap-4 text-sm text-slate-700">
                  <span>新增 {batch.inserted_rows ?? 0}</span>
                  <span>更新 {batch.updated_rows ?? 0}</span>
                  <span>删除 {batch.deleted_rows ?? 0}</span>
                  <span>未变化 {batch.unchanged_rows ?? 0}</span>
                </div>
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default BatchAnalyticsPanel;
