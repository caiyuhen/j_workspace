import React, { useState, useEffect, useCallback } from 'react';
import {  Table, Modal, Form, Input, Space, Button, Drawer, Descriptions, Tag, Alert , App } from 'antd';
import { EyeOutlined, ExclamationCircleOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import PageHeader from '@/components/PageHeader';
import { randomizationApi } from '@/api/randomization';
import type { RandomizationRecord, CreateRandomizationParams } from '@/types';

const statusMap: Record<string, { color: string; label: string }> = {
  randomized: { color: 'success', label: '已随机' },
  unblinded: { color: 'warning', label: '已揭盲' },
  cancelled: { color: 'error', label: '已取消' } };

const RandomizationPage: React.FC = () => {
  const { message } = App.useApp();
  const [data, setData] = useState<RandomizationRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({ page: 1, pageSize: 10, total: 0 });
  const [keyword, setKeyword] = useState('');

  const [modalOpen, setModalOpen] = useState(false);
  const [form] = Form.useForm();
  const [submitLoading, setSubmitLoading] = useState(false);

  const [unblindModalOpen, setUnblindModalOpen] = useState(false);
  const [unblindSubjectId, setUnblindSubjectId] = useState<string | null>(null);
  const [unblindForm] = Form.useForm();
  const [unblindLoading, setUnblindLoading] = useState(false);

  const [detailOpen, setDetailOpen] = useState(false);
  const [selectedRecord, setSelectedRecord] = useState<RandomizationRecord | null>(null);

  const fetchData = useCallback(async (page = 1, pageSize = 10) => {
    setLoading(true);
    try {
      const res = await randomizationApi.list({ page, pageSize, keyword });
      setData(res?.list || []);
      setPagination({ page: res?.page || 1, pageSize: res?.pageSize || 10, total: res?.total || 0 });
    } catch {
      message.error('加载随机化记录失败');
    } finally {
      setLoading(false);
    }
  }, [keyword]);

  useEffect(() => { fetchData(); }, [fetchData]);



  const handleOpenCreate = () => {
    form.resetFields();
    setModalOpen(true);
  };
  
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setSubmitLoading(true);
      await randomizationApi.createRecord(values as CreateRandomizationParams);
      message.success('随机化成功');
      setModalOpen(false);
      fetchData(pagination.page, pagination.pageSize);
    } catch {
      /* validation */
    } finally {
      setSubmitLoading(false);
    }
  };

  const handleUnblind = (record: RandomizationRecord) => {
    if (record.isUnblinded) {
      message.warning('该受试者已被揭盲');
      return;
    }
    setUnblindSubjectId(record.subjectId);
    unblindForm.resetFields();
    setUnblindModalOpen(true);
  };

  const handleUnblindSubmit = async () => {
    try {
      const values = await unblindForm.validateFields();
      setUnblindLoading(true);
      await randomizationApi.emergencyUnblind(unblindSubjectId!, values.reason);
      message.success('紧急揭盲成功');
      setUnblindModalOpen(false);
      fetchData(pagination.page, pagination.pageSize);
    } catch {
      /* validation */
    } finally {
      setUnblindLoading(false);
    }
  };

  const handleViewDetail = (record: RandomizationRecord) => {
    setSelectedRecord(record);
    setDetailOpen(true);
  };


  const columns = [
    { title: '随机号', dataIndex: 'randomizationNumber', width: 120 },
    { title: '受试者', dataIndex: ['subject', 'subjectCode'], width: 120, render: (v: string, r: RandomizationRecord) => v || r.subjectId },
    { title: '中心', dataIndex: ['site', 'name'], width: 140, ellipsis: true, render: (v: string) => v || '-' },
    { title: '分层', dataIndex: 'stratum', width: 100 },
    {
      title: '分配臂', dataIndex: 'treatmentArm', width: 120,
      render: (v: string, r: RandomizationRecord) => r.isUnblinded ? v : '****（盲态）' },
    { title: '随机化人', dataIndex: ['randomizedBy', 'displayName'], width: 100 },
    { title: '随机化日期', dataIndex: 'randomizationDate', width: 120, render: (v: string) => v ? dayjs(v).format('YYYY-MM-DD') : '-' },
    {
      title: '状态', dataIndex: 'status', width: 100,
      render: (v: string) => {
        const cfg = statusMap[v] || { color: 'default', label: v };
        return <Tag color={cfg.color}>{cfg.label}</Tag>;
      } },
    {
      title: '操作', width: 200,
      render: (_: any, record: RandomizationRecord) => (
        <Space size="small">
          <Button type="link" size="small" icon={<EyeOutlined />} onClick={() => handleViewDetail(record)}>详情</Button>
          {!record.isUnblinded && (
            <Button type="link" size="small" danger icon={<ExclamationCircleOutlined />} onClick={() => handleUnblind(record)}>紧急揭盲</Button>
          )}
        </Space>
      ) },
  ];

  return (
    <>
      <PageHeader
        title="随机化管理"
        searchPlaceholder="搜索受试者/随机号"
        onSearch={(v) => setKeyword(v)}
      >
        <Space>
          <Button type="primary" onClick={handleOpenCreate}>随机化</Button>
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
        scroll={{ x: 1200 }}
      />

      {/* 随机化弹窗 */}
      <Modal
        title="随机化分配"
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        confirmLoading={submitLoading}
        width={500}
      >
        <Alert message="随机化操作不可逆，请确认信息正确后再提交" type="warning" showIcon style={{ marginBottom: 16 }} />
        <Form form={form} layout="vertical">
          <Form.Item name="projectId" label="项目 ID" rules={[{ required: true }]}>
            <Input placeholder="请输入项目 ID" />
          </Form.Item>
          <Form.Item name="subjectId" label="受试者 ID" rules={[{ required: true }]}>
            <Input placeholder="请输入受试者 ID" />
          </Form.Item>
          <Form.Item name="siteId" label="中心 ID" rules={[{ required: true }]}>
            <Input placeholder="请输入中心 ID" />
          </Form.Item>
          <Form.Item name="stratum" label="分层因素">
            <Input placeholder="可选" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 紧急揭盲弹窗 */}
      <Modal
        title="紧急揭盲"
        open={unblindModalOpen}
        onOk={handleUnblindSubmit}
        onCancel={() => setUnblindModalOpen(false)}
        confirmLoading={unblindLoading}
        width={500}
      >
        <Alert message="紧急揭盲为严肃操作，必须记录充分的揭盲理由，操作将被完整审计追踪" type="error" showIcon style={{ marginBottom: 16 }} />
        <Form form={unblindForm} layout="vertical">
          <Form.Item name="reason" label="揭盲理由" rules={[{ required: true, message: '请输入揭盲理由' }]}>
            <Input.TextArea rows={4} placeholder="请详细说明紧急揭盲的原因" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 详情抽屉 */}
      <Drawer
        title={selectedRecord ? `随机化详情 - ${selectedRecord.randomizationNumber}` : '详情'}
        open={detailOpen}
        onClose={() => setDetailOpen(false)}
        size="large"
      >
        {selectedRecord && (
          <Descriptions column={1} bordered size="small">
            <Descriptions.Item label="随机号">{selectedRecord.randomizationNumber}</Descriptions.Item>
            <Descriptions.Item label="受试者">{selectedRecord.subject?.subjectCode || selectedRecord.subjectId}</Descriptions.Item>
            <Descriptions.Item label="中心">{selectedRecord.site?.name || selectedRecord.siteId}</Descriptions.Item>
            <Descriptions.Item label="分层">{selectedRecord.stratum || '-'}</Descriptions.Item>
            <Descriptions.Item label="分配臂">
              {selectedRecord.isUnblinded ? (
                <Tag color="warning">{selectedRecord.treatmentArm}</Tag>
              ) : (
                <Tag>****（盲态）</Tag>
              )}
            </Descriptions.Item>
            <Descriptions.Item label="随机化人">{selectedRecord.randomizedBy?.displayName || '-'}</Descriptions.Item>
            <Descriptions.Item label="随机化日期">{selectedRecord.randomizationDate ? dayjs(selectedRecord.randomizationDate).format('YYYY-MM-DD HH:mm') : '-'}</Descriptions.Item>
            <Descriptions.Item label="状态"><Tag color={statusMap[selectedRecord.status]?.color}>{statusMap[selectedRecord.status]?.label}</Tag></Descriptions.Item>
            {selectedRecord.isUnblinded && (
              <>
                <Descriptions.Item label="揭盲时间">{selectedRecord.unblindedAt ? dayjs(selectedRecord.unblindedAt).format('YYYY-MM-DD HH:mm') : '-'}</Descriptions.Item>
                <Descriptions.Item label="揭盲理由">{selectedRecord.unblindReason || '-'}</Descriptions.Item>
              </>
            )}
          </Descriptions>
        )}
      </Drawer>
    </>
  );
};

export default RandomizationPage;
