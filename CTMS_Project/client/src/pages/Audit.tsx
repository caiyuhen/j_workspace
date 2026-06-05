import React, { useState, useEffect, useCallback } from 'react';
import {  Tag, Select, DatePicker, Space, Button, Drawer, Descriptions, Table, Typography , App } from 'antd';
import { EyeOutlined, SearchOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import type { Dayjs } from 'dayjs';
import PageHeader from '@/components/PageHeader';
import { auditApi } from '@/api/audit';
import type { AuditLog, AuditLogQuery } from '@/types';

const { Text } = Typography;


const { RangePicker } = DatePicker;

const actionColorMap: Record<string, string> = {
  CREATE: 'green',
  UPDATE: 'blue',
  DELETE: 'red',
  LOGIN: 'purple',
  LOGOUT: 'default',
  EXPORT: 'orange',
  SIGNATURE: 'cyan',
  RANDOMIZE: 'magenta',
  UNBLIND: 'volcano' };

const actionLabelMap: Record<string, string> = {
  CREATE: '创建',
  UPDATE: '更新',
  DELETE: '删除',
  LOGIN: '登录',
  LOGOUT: '登出',
  EXPORT: '导出',
  SIGNATURE: '签名',
  RANDOMIZE: '随机化',
  UNBLIND: '揭盲' };

const AuditPage: React.FC = () => {
  const { message } = App.useApp();
  const [data, setData] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({ page: 1, pageSize: 20, total: 0 });

  const [keyword, setKeyword] = useState('');
  const [actionFilter, setActionFilter] = useState<string | undefined>(undefined);
  const [tableNameFilter, setTableNameFilter] = useState<string | undefined>(undefined);
  const [dateRange, setDateRange] = useState<[Dayjs | null, Dayjs | null] | null>(null);

  // const [stats, setStats] = useState<AuditStats | null>(null);
  // const [statsLoading, setStatsLoading] = useState(false);

  const [detailOpen, setDetailOpen] = useState(false);
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null);

  const fetchData = useCallback(async (page = 1, pageSize = 20) => {
    setLoading(true);
    try {
      const params: AuditLogQuery = { page, pageSize, keyword };
      if (actionFilter) params.action = actionFilter;
      if (tableNameFilter) params.tableName = tableNameFilter;
      if (dateRange?.[0]) params.startDate = dateRange[0].format('YYYY-MM-DD');
      if (dateRange?.[1]) params.endDate = dateRange[1].format('YYYY-MM-DD');
      const res = await auditApi.query(params);
      setData(res?.list || []);
      setPagination({ page: res?.page || 1, pageSize: res?.pageSize || 10, total: res?.total || 0 });
    } catch { message.error('加载审计日志失败'); }
    finally { setLoading(false); }
  }, [keyword, actionFilter, tableNameFilter, dateRange]);

  const fetchStats = useCallback(async () => {
    // try { setStats(await auditApi.getStatistics()); }
    // catch { /* ignore */ }
  }, []);

  useEffect(() => { fetchData(); fetchStats(); }, [fetchData, fetchStats]);

  const handleViewDetail = async (record: AuditLog) => {
    setSelectedLog(record);
    setDetailOpen(true);
  };

  const columns = [
    { title: '时间', dataIndex: 'timestamp', width: 160, render: (v: string) => v ? dayjs(v).format('YYYY-MM-DD HH:mm:ss') : '-' },
    { title: '用户', dataIndex: 'userName', width: 100 },
    {
      title: '操作类型', dataIndex: 'action', width: 100,
      render: (v: string) => <Tag color={actionColorMap[v] || 'default'}>{actionLabelMap[v] || v}</Tag> },
    { title: '事件类型', dataIndex: 'eventType', width: 140, ellipsis: true },
    { title: '数据表', dataIndex: 'tableName', width: 130 },
    { title: '记录ID', dataIndex: 'recordId', width: 120, ellipsis: true },
    { title: 'IP地址', dataIndex: 'ipAddress', width: 130 },
    {
      title: '操作', width: 80,
      render: (_: any, record: AuditLog) => (
        <Button type="link" size="small" icon={<EyeOutlined />} onClick={() => handleViewDetail(record)}>详情</Button>
      ) },
  ];

  return (
    <>
      <PageHeader title="审计日志" searchPlaceholder="搜索用户/事件/记录ID" onSearch={(v) => setKeyword(v)}>
        <Space wrap>
          <Select
            placeholder="操作类型"
            allowClear
            style={{ width: 120 }}
            options={Object.entries(actionLabelMap).map(([v, l]) => ({ value: v, label: l }))}
            value={actionFilter}
            onChange={setActionFilter}
          />
          <Select
            placeholder="数据表"
            allowClear
            style={{ width: 140 }}
            options={[
              { value: 'User', label: 'User 用户' },
              { value: 'Project', label: 'Project 项目' },
              { value: 'Site', label: 'Site 中心' },
              { value: 'Subject', label: 'Subject 受试者' },
              { value: 'AdverseEvent', label: 'AE/SAE' },
              { value: 'Query', label: 'Query 质疑' },
              { value: 'WorkflowInstance', label: 'Workflow 工作流' },
              { value: 'Randomization', label: 'Randomization 随机化' },
              { value: 'SdvRecord', label: 'SDV 核查' },
              { value: 'Document', label: 'Document 文档' },
            ]}
            value={tableNameFilter}
            onChange={setTableNameFilter}
          />
          <RangePicker
            value={dateRange as any}
            onChange={(dates) => setDateRange(dates as [Dayjs | null, Dayjs | null] | null)}
          />
          <Button icon={<SearchOutlined />} onClick={() => fetchData(1, pagination.pageSize)}>查询</Button>
        </Space>
      </PageHeader>



      <Table
        rowKey="id"
        columns={columns}
        dataSource={data}
        loading={loading}
        pagination={{
          current: pagination.page, pageSize: pagination.pageSize, total: pagination.total,
          showSizeChanger: true, showTotal: (t) => `共 ${t} 条`,
          onChange: (p, ps) => fetchData(p, ps) }}
        scroll={{ x: 1100 }}
        size="small"
      />

      {/* 详情抽屉 */}
      <Drawer
        title="审计日志详情"
        open={detailOpen}
        onClose={() => setDetailOpen(false)}
        size="large"
      >
        {selectedLog && (
          <Descriptions column={1} bordered size="small">
            <Descriptions.Item label="日志ID">{selectedLog.id}</Descriptions.Item>
            <Descriptions.Item label="时间">{selectedLog.timestamp ? dayjs(selectedLog.timestamp).format('YYYY-MM-DD HH:mm:ss.SSS') : '-'}</Descriptions.Item>
            <Descriptions.Item label="用户">{selectedLog.userName} ({selectedLog.userId})</Descriptions.Item>
            <Descriptions.Item label="操作类型"><Tag color={actionColorMap[selectedLog.action]}>{actionLabelMap[selectedLog.action] || selectedLog.action}</Tag></Descriptions.Item>
            <Descriptions.Item label="事件类型">{selectedLog.eventType}</Descriptions.Item>
            <Descriptions.Item label="数据表">{selectedLog.tableName}</Descriptions.Item>
            <Descriptions.Item label="记录ID">{selectedLog.recordId}</Descriptions.Item>
            <Descriptions.Item label="IP地址">{selectedLog.ipAddress}</Descriptions.Item>
            <Descriptions.Item label="User-Agent"><Text style={{ fontSize: 12, wordBreak: 'break-all' }}>{selectedLog.userAgent || '-'}</Text></Descriptions.Item>
            {selectedLog.oldValue && (
              <Descriptions.Item label="变更前">
                <pre style={{ fontSize: 12, maxHeight: 200, overflow: 'auto', background: '#f5f5f5', padding: 8, borderRadius: 4 }}>
                  {JSON.stringify(selectedLog.oldValue, null, 2)}
                </pre>
              </Descriptions.Item>
            )}
            {selectedLog.newValue && (
              <Descriptions.Item label="变更后">
                <pre style={{ fontSize: 12, maxHeight: 200, overflow: 'auto', background: '#f5f5f5', padding: 8, borderRadius: 4 }}>
                  {JSON.stringify(selectedLog.newValue, null, 2)}
                </pre>
              </Descriptions.Item>
            )}
          </Descriptions>
        )}
      </Drawer>
    </>
  );
};

export default AuditPage;
