import React, { useState, useEffect, useCallback } from 'react';
import {  Table, Modal, Form, Input, Select, Space, Button, Drawer, Descriptions, Tag, Progress , App } from 'antd';
import { CheckCircleOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import PageHeader from '@/components/PageHeader';
import { sdvApi } from '@/api/sdv';
import type { SdvRecord, CreateSdvParams, SdvItem } from '@/types';

const sdvStatusMap: Record<string, { color: string; label: string }> = {
  pending: { color: 'default', label: '待核查' },
  in_progress: { color: 'processing', label: '核查中' },
  completed: { color: 'success', label: '已完成' },
  failed: { color: 'error', label: '有差异' } };

const itemStatusMap: Record<string, { color: string; label: string }> = {
  pending: { color: 'default', label: '待核' },
  verified: { color: 'success', label: '一致' },
  discrepancy: { color: 'error', label: '差异' } };

const SdvPage: React.FC = () => {
  const { message } = App.useApp();
  const [data, setData] = useState<SdvRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({ page: 1, pageSize: 10, total: 0 });
  const [keyword, setKeyword] = useState('');
  const [statusFilter, setStatusFilter] = useState<string | undefined>(undefined);

  const [modalOpen, setModalOpen] = useState(false);
  const [form] = Form.useForm();
  const [submitLoading, setSubmitLoading] = useState(false);

  const [detailOpen, setDetailOpen] = useState(false);
  const [selectedRecord, setSelectedRecord] = useState<SdvRecord | null>(null);
  const [items, setItems] = useState<SdvItem[]>([]);
  const [itemsLoading, setItemsLoading] = useState(false);
  const [completeLoading, setCompleteLoading] = useState(false);

  const fetchData = useCallback(async (page = 1, pageSize = 10) => {
    setLoading(true);
    try {
      const res = await sdvApi.list({ page, pageSize, keyword, status: statusFilter });
      setData(res?.list || []);
      setPagination({ page: res?.page || 1, pageSize: res?.pageSize || 10, total: res?.total || 0 });
    } catch {
      message.error('加载SDV记录失败');
    } finally {
      setLoading(false);
    }
  }, [keyword, statusFilter]);

  const fetchStats = useCallback(async () => {
    // try { setStats(await sdvApi.getStatistics()); }
    // catch { /* error */ }
  }, []);

  useEffect(() => { fetchData(); fetchStats(); }, [fetchData, fetchStats]);

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setSubmitLoading(true);
      await sdvApi.create(values as CreateSdvParams);
      message.success('创建 SDV 记录成功');
      setModalOpen(false);
      fetchData(pagination.page, pagination.pageSize);
    } catch {
      /* validation */
    } finally {
      setSubmitLoading(false);
    }
  };

  const handleDetail = (record: SdvRecord) => {
    setSelectedRecord(record);
    setItemsLoading(true);
    sdvApi.getById(record.id).then(res => {
      setSelectedRecord(res as unknown as SdvRecord);
      setItems((res as any)?.items || []);
    }).catch(() => {
      message.error('加载核查详情失败');
      setItems([]);
    }).finally(() => {
      setItemsLoading(false);
    });
    setDetailOpen(true);
  };

  const handleItemUpdate = async (itemId: string, status: 'verified' | 'discrepancy', notes?: string) => {
    if (!selectedRecord) return;
    try {
      await sdvApi.updateItem(selectedRecord.id, itemId, { status, notes });
      message.success('更新核查项成功');
      // Refresh items
      const detail = await sdvApi.getById(selectedRecord.id);
      setItems((detail as any).items || []);
    } catch {
      message.error('更新失败');
    }
  };

  const handleComplete = async () => {
    if (!selectedRecord) return;
    setCompleteLoading(true);
    try {
      await sdvApi.complete(selectedRecord.id);
      message.success('SDV 核查已完成');
      setDetailOpen(false);
      fetchData(pagination.page, pagination.pageSize);
      fetchStats();
    } catch {
      message.error('完成核查失败');
    } finally {
      setCompleteLoading(false);
    }
  };

  const updateItemStatus = async (recordId: string, itemId: string, status: 'verified' | 'discrepancy') => {
    try {
      await sdvApi.updateItem(recordId, itemId, { status, notes: '' });
      message.success('核查状态已更新');
      fetchData(pagination.page, pagination.pageSize);
    } catch { message.error('更新失败'); }
  };

  const columns = [
    { title: '受试者', dataIndex: 'subjectId', width: 120 },
    { title: '访视', dataIndex: 'visitName', width: 120 },
    { title: '表单', dataIndex: 'formName', width: 120, ellipsis: true },
    { title: 'CRA', dataIndex: ['cra', 'displayName'], width: 100 },
    {
      title: '进度',
      width: 180,
      render: (_: any, record: SdvRecord) => {
        const total = record.totalItems || 0;
        const verified = record.verifiedItems || 0;
        return (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Progress percent={total > 0 ? Math.round((verified / total) * 100) : 0} size="small" style={{ flex: 1 }} />
            <span style={{ fontSize: 12, color: '#999' }}>{verified}/{total}</span>
          </div>
        );
      } },
    {
      title: '状态', dataIndex: 'status', width: 100,
      render: (v: string) => {
        const cfg = sdvStatusMap[v] || { color: 'default', label: v };
        return <Tag color={cfg.color}>{cfg.label}</Tag>;
      } },
    { title: '完成时间', dataIndex: 'completedAt', width: 140, render: (v: string) => v ? dayjs(v).format('YYYY-MM-DD HH:mm') : '-' },
    {
      title: '操作', width: 180,
      render: (_: any, record: SdvRecord) => (
        <Space size="small">
          <Button type="link" size="small" onClick={() => handleDetail(record)}>详情</Button>
          {record.status === 'in_progress' && (
              <Button type="link" size="small" onClick={() => updateItemStatus(record.id, record.id, 'discrepancy')}>标记差异</Button>
            )}
        </Space>
      ) },
  ];

  return (
    <>
      <PageHeader
        title="源数据核查 (SDV)"
        searchPlaceholder="搜索受试者/访视"
        onSearch={(v) => setKeyword(v)}
      >
        <Select
          placeholder="核查状态"
          allowClear
          style={{ width: 130 }}
          options={Object.entries(sdvStatusMap).map(([v, c]) => ({ value: v, label: c.label }))}
          value={statusFilter}
          onChange={setStatusFilter}
        />
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
      />

      {/* 创建弹窗 */}
      <Modal
        title="创建 SDV 核查记录"
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        confirmLoading={submitLoading}
        width={500}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="projectId" label="项目 ID" rules={[{ required: true }]}>
            <Input placeholder="请输入项目 ID" />
          </Form.Item>
          <Form.Item name="siteId" label="中心 ID" rules={[{ required: true }]}>
            <Input placeholder="请输入中心 ID" />
          </Form.Item>
          <Form.Item name="subjectId" label="受试者 ID" rules={[{ required: true }]}>
            <Input placeholder="请输入受试者 ID" />
          </Form.Item>
          <Form.Item name="visitName" label="访视名称" rules={[{ required: true }]}>
            <Input placeholder="请输入访视名称" />
          </Form.Item>
          <Form.Item name="formName" label="表单名称">
            <Input placeholder="可选" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 详情抽屉 */}
      <Drawer
        title={selectedRecord ? `SDV 核查 - ${selectedRecord.visitName}` : 'SDV 详情'}
        open={detailOpen}
        onClose={() => setDetailOpen(false)}
        size="large"
        extra={
          selectedRecord?.status === 'in_progress' ? (
            <Button type="primary" icon={<CheckCircleOutlined />} loading={completeLoading} onClick={handleComplete}>
              完成核查
            </Button>
          ) : null
        }
      >
        {selectedRecord && (
          <>
            <Descriptions column={2} bordered size="small" style={{ marginBottom: 16 }}>
              <Descriptions.Item label="受试者">{selectedRecord.subjectId}</Descriptions.Item>
              <Descriptions.Item label="访视">{selectedRecord.visitName}</Descriptions.Item>
              <Descriptions.Item label="CRA">{selectedRecord.cra?.displayName || '-'}</Descriptions.Item>
              <Descriptions.Item label="状态"><Tag color={sdvStatusMap[selectedRecord.status]?.color}>{sdvStatusMap[selectedRecord.status]?.label}</Tag></Descriptions.Item>
              <Descriptions.Item label="核查项总数">{selectedRecord.totalItems}</Descriptions.Item>
              <Descriptions.Item label="已核实">{selectedRecord.verifiedItems}</Descriptions.Item>
              <Descriptions.Item label="发现" span={2}>{selectedRecord.findings || '-'}</Descriptions.Item>
            </Descriptions>

            <h4 style={{ marginBottom: 8 }}>核查项明细</h4>
            <Table
              loading={itemsLoading}
              dataSource={items}
              size="small"
              rowKey="id"
              pagination={false}
              columns={[
                {
                  title: '核查项',
                  key: 'info',
                  render: (_, item) => (
                    <div>
                      <Space style={{ marginBottom: 4 }}>
                        <strong>{item.fieldName}</strong>
                        <Tag color={itemStatusMap[item.status]?.color}>{itemStatusMap[item.status]?.label}</Tag>
                      </Space>
                      <div>
                        <span style={{ marginRight: 16 }}>CRF值: <code>{JSON.stringify(item.crfValue)}</code></span>
                        <span>源数据值: <code>{JSON.stringify(item.sourceValue)}</code></span>
                      </div>
                      {item.notes && <div style={{ color: '#faad14', marginTop: 4 }}>备注: {item.notes}</div>}
                    </div>
                  )
                },
                {
                  title: '操作',
                  key: 'action',
                  width: 150,
                  render: (_, item) => (
                    <Space>
                      <Button type="link" size="small" style={{ color: '#52c41a', padding: 0 }}
                        disabled={item.status === 'verified'}
                        onClick={() => handleItemUpdate(item.id, 'verified')}>
                        一致
                      </Button>
                      <Button type="link" size="small" danger style={{ padding: 0 }}
                        disabled={item.status === 'discrepancy'}
                        onClick={() => handleItemUpdate(item.id, 'discrepancy')}>
                        差异
                      </Button>
                    </Space>
                  )
                }
              ]}
            />
          </>
        )}
      </Drawer>
    </>
  );
};

export default SdvPage;
