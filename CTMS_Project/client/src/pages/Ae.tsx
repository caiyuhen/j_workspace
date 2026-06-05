import React, { useState, useEffect, useCallback } from 'react';
import {  Table, Modal, Form, Input, Select, Space, Button, Drawer, Descriptions, Tag, DatePicker , App } from 'antd';
import { EditOutlined, EyeOutlined, FileTextOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import PageHeader from '@/components/PageHeader';
import StatusTag from '@/components/StatusTag';
import { aeApi } from '@/api/ae';
import { projectApi } from '@/api/project';
import type { AdverseEvent, CreateAEParams, SaeReport, CreateSaeReportParams } from '@/types';

const { TextArea } = Input;

const severityOptions = [
  { value: 'mild', label: '轻度' },
  { value: 'moderate', label: '中度' },
  { value: 'severe', label: '重度' },
];

const seriousnessOptions = [
  { value: 'non_serious', label: '非严重' },
  { value: 'serious', label: '严重' },
];

const causalityOptions = [
  { value: 'not_related', label: '不相关' },
  { value: 'unlikely', label: '不太可能' },
  { value: 'possible', label: '可能' },
  { value: 'probable', label: '很可能' },
  { value: 'definite', label: '肯定' },
];

const outcomeOptions = [
  { value: 'resolved', label: '已恢复' },
  { value: 'resolving', label: '恢复中' },
  { value: 'not_resolved', label: '未恢复' },
  { value: 'fatal', label: '致死' },
  { value: 'unknown', label: '未知' },
];

const reportTypeOptions = [
  { value: 'initial', label: '初次报告' },
  { value: 'follow_up', label: '随访报告' },
  { value: 'final', label: '总结报告' },
  { value: 'death', label: '死亡报告' },
  { value: 'expedited', label: '加急报告' },
  { value: 'annual', label: '年度报告' },
];

const AePage: React.FC = () => {
  const { message } = App.useApp();
  const [data, setData] = useState<AdverseEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({ page: 1, pageSize: 10, total: 0 });
  const [keyword, setKeyword] = useState('');
  const [typeFilter, setTypeFilter] = useState<string | undefined>(undefined);

  // 创建/编辑弹窗
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<AdverseEvent | null>(null);
  const [form] = Form.useForm();
  const [submitLoading, setSubmitLoading] = useState(false);

  // 详情抽屉
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [selectedAe, setSelectedAe] = useState<AdverseEvent | null>(null);
  const [reports, setReports] = useState<SaeReport[]>([]);
  const [reportsLoading, setReportsLoading] = useState(false);

  // SAE 报告弹窗
  const [reportModalOpen, setReportModalOpen] = useState(false);
  const [reportForm] = Form.useForm();
  const [reportSubmitLoading, setReportSubmitLoading] = useState(false);

  const [projects, setProjects] = useState<{label: string, value: string}[]>([]);
  const [projectsLoading, setProjectsLoading] = useState(false);

  const fetchProjects = useCallback(async () => {
    setProjectsLoading(true);
    try {
      const res = await projectApi.list({ page: 1, pageSize: 1000 });
      setProjects((res?.list || []).map((p: any) => ({
        label: p.projectName,
        value: p.id })));
    } catch {
      // ignore
    } finally {
      setProjectsLoading(false);
    }
  }, []);

  const fetchData = useCallback(async (page = 1, pageSize = 10) => {
    setLoading(true);
    try {
      const res = await aeApi.list({ page, pageSize, keyword, eventType: typeFilter });
      setData(res?.list || []);
      setPagination({ page: res?.page || 1, pageSize: res?.pageSize || 10, total: res?.total || 0 });
    } catch {
      message.error('加载 AE 列表失败');
    } finally {
      setLoading(false);
    }
  }, [keyword, typeFilter]);

  useEffect(() => {
    fetchData();
    fetchProjects();
  }, [fetchData, fetchProjects]);



  const handleCreate = () => {
    setEditing(null);
    form.resetFields();
    setModalOpen(true);
  };
  
  const handleEdit = (record: AdverseEvent) => {
    setEditing(record);
    form.setFieldsValue({
      ...record,
      onsetDate: record.onsetDate ? dayjs(record.onsetDate) : undefined,
      endDate: record.endDate ? dayjs(record.endDate) : undefined });
    setModalOpen(true);
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setSubmitLoading(true);
      const params = {
        ...values,
        onsetDate: values.onsetDate?.toISOString(),
        endDate: values.endDate?.toISOString() };
      if (editing) {
        await aeApi.update(editing.id, params);
        message.success('AE 更新成功');
      } else {
        await aeApi.create(params as CreateAEParams);
        message.success('AE 创建成功');
      }
      setModalOpen(false);
      fetchData(pagination.page, pagination.pageSize);
    } catch (err: any) {
      if (err.errorFields) {
        message.warning('请检查表单填写是否正确');
        return;
      }
      message.error(err.response?.data?.error?.message || '操作失败');
    } finally {
      setSubmitLoading(false);
    }
  };

  const openDetail = async (record: AdverseEvent) => {
    setSelectedAe(record);
    setDrawerOpen(true);
    setReportsLoading(true);
    try {
      const res = await aeApi.getReports(record.id);
      setReports((res as any)?.data || (Array.isArray(res) ? res : []));
    } catch {
      setReports([]);
    } finally {
      setReportsLoading(false);
    }
  };

  const handleCloseAe = async (id: string) => {
    try {
      await aeApi.close(id);
      message.success('AE 已关闭');
      setDrawerOpen(false);
      fetchData(pagination.page, pagination.pageSize);
    } catch {
      message.error('操作失败');
    }
  };

  const handleCreateReport = async () => {
    try {
      const values = await reportForm.validateFields();
      setReportSubmitLoading(true);
      await aeApi.createReport(selectedAe!.id, {
        ...values,
        reportDate: values.reportDate.toISOString() } as CreateSaeReportParams);
      message.success('SAE 报告已创建');
      setReportModalOpen(false);
      reportForm.resetFields();
      openDetail(selectedAe!);
    } catch (err: any) {
      if (err.errorFields) {
        message.warning('请检查表单填写是否正确');
        return;
      }
      message.error('创建失败');
    } finally {
      setReportSubmitLoading(false);
    }
  };

  const columns = [
    {
      title: '事件类型', dataIndex: 'eventType', key: 'eventType', width: 90,
      render: (v: string) => <Tag color={v === 'sae' ? 'red' : 'orange'}>{v === 'sae' ? 'SAE' : 'AE'}</Tag> },
    { title: '不良事件术语', dataIndex: 'termPreferred', key: 'termPreferred', ellipsis: true },
    {
      title: '严重程度', dataIndex: 'severity', key: 'severity', width: 90,
      render: (v: string) => <StatusTag status={v} category="severity" /> },
    {
      title: '严重性', dataIndex: 'seriousness', key: 'seriousness', width: 90,
      render: (v: string) => <StatusTag status={v} category="seriousness" /> },
    { title: '发生日期', dataIndex: 'onsetDate', key: 'onsetDate', width: 110, render: (v: string) => dayjs(v).format('YYYY-MM-DD') },
    {
      title: '结局', dataIndex: 'outcome', key: 'outcome', width: 100,
      render: (v: string) => v ? outcomeOptions.find(o => o.value === v)?.label || v : '-' },
    {
      title: '状态', dataIndex: 'status', key: 'status', width: 90,
      render: (v: string) => <StatusTag status={v} category="workflow" /> },
    {
      title: '操作', key: 'actions', width: 140, fixed: 'right' as const,
      render: (_: any, record: AdverseEvent) => (
        <Space>
          <Button type="link" size="small" icon={<EyeOutlined />} onClick={() => openDetail(record)}>详情</Button>
          <Button type="link" size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)}>编辑</Button>
        </Space>
      ) },
  ];

  return (
    <div>
      <PageHeader
        title="AE/SAE 安全性报告"
        subtitle="不良事件和严重不良事件的报告与管理"
        onSearch={setKeyword}
        searchPlaceholder="搜索不良事件术语"
      >
        <Space>
          <Select placeholder="事件类型" allowClear style={{ width: 120 }} onChange={setTypeFilter} options={[
            { value: 'ae', label: 'AE' },
            { value: 'sae', label: 'SAE' },
          ]} value={typeFilter} />
          <Button type="primary" onClick={handleCreate}>添加报告</Button>
        </Space>
      </PageHeader>

      <Table
        rowKey="id"
        columns={columns}
        dataSource={data}
        loading={loading}
        scroll={{ x: 1000 }}
        pagination={{
          current: pagination.page,
          pageSize: pagination.pageSize,
          total: pagination.total,
          showSizeChanger: true,
          showTotal: (total) => `共 ${total} 条`,
          onChange: (page, pageSize) => fetchData(page, pageSize) }}
      />

      {/* 创建/编辑 AE */}
      <Modal
        title={editing ? '编辑不良事件' : '报告不良事件'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        width={720}
        confirmLoading={submitLoading}
        okText="保存"
        cancelText="取消"
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Space style={{ width: '100%' }} size="large">
            <Form.Item name="projectId" label="项目 ID" rules={[{ required: true, message: '请选择项目' }]}>
              <Select placeholder="请选择项目" options={projects} loading={projectsLoading} showSearch optionFilterProp="label" style={{ width: 200 }} />
            </Form.Item>
            <Form.Item name="subjectId" label="受试者 ID" rules={[{ required: true }]}>
              <Input placeholder="受试者 UUID" style={{ width: 200 }} />
            </Form.Item>
            {!editing && (
              <Form.Item name="eventType" label="事件类型" rules={[{ required: true }]}>
                <Select style={{ width: 120 }} options={[
                  { value: 'ae', label: 'AE' },
                  { value: 'sae', label: 'SAE' },
                ]} />
              </Form.Item>
            )}
          </Space>
          <Form.Item name="termPreferred" label="不良事件术语 (PT)" rules={[{ required: true }]}>
            <Input placeholder="MedDRA 首选术语" />
          </Form.Item>
          <Space style={{ width: '100%' }} size="large">
            <Form.Item name="termCode" label="MedDRA 编码">
              <Input placeholder="编码" style={{ width: 200 }} />
            </Form.Item>
            <Form.Item name="meddraCode" label="MedDRA Code">
              <Input placeholder="MedDRA Code" style={{ width: 200 }} />
            </Form.Item>
          </Space>
          <Space style={{ width: '100%' }} size="large">
            <Form.Item name="onsetDate" label="发生日期" rules={[{ required: true }]}>
              <DatePicker style={{ width: 200 }} />
            </Form.Item>
            <Form.Item name="endDate" label="结束日期">
              <DatePicker style={{ width: 200 }} />
            </Form.Item>
            <Form.Item name="isOngoing" label="是否持续" valuePropName="checked">
              <Select style={{ width: 120 }} options={[{ value: true, label: '是' }, { value: false, label: '否' }]} />
            </Form.Item>
          </Space>
          <Space style={{ width: '100%' }} size="large">
            <Form.Item name="severity" label="严重程度" rules={[{ required: true }]}>
              <Select style={{ width: 200 }} options={severityOptions} />
            </Form.Item>
            <Form.Item name="seriousness" label="严重性" rules={[{ required: true }]}>
              <Select style={{ width: 200 }} options={seriousnessOptions} />
            </Form.Item>
            <Form.Item name="causality" label="因果判断">
              <Select style={{ width: 200 }} options={causalityOptions} placeholder="请选择" />
            </Form.Item>
            <Form.Item name="outcome" label="结局">
              <Select style={{ width: 200 }} options={outcomeOptions} placeholder="请选择" />
            </Form.Item>
          </Space>
          <Form.Item name="description" label="事件描述" rules={[{ required: true }]}>
            <TextArea rows={3} placeholder="详细描述不良事件" />
          </Form.Item>
        </Form>
      </Modal>

      {/* AE 详情抽屉 */}
      <Drawer
        title={`不良事件详情 - ${selectedAe?.termPreferred || ''}`}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        size="large"
        extra={
          <Space>
            {selectedAe?.eventType === 'sae' && (
              <Button type="primary" icon={<FileTextOutlined />} onClick={() => { reportForm.resetFields(); setReportModalOpen(true); }}>
                新建 SAE 报告
              </Button>
            )}
            {selectedAe?.status === 'open' && (
              <Button danger onClick={() => handleCloseAe(selectedAe!.id)}>关闭 AE</Button>
            )}
          </Space>
        }
      >
        {selectedAe && (
          <>
            <Descriptions bordered size="small" column={2}>
              <Descriptions.Item label="事件类型">
                <Tag color={selectedAe.eventType === 'sae' ? 'red' : 'orange'}>{selectedAe.eventType === 'sae' ? 'SAE' : 'AE'}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="不良事件术语">{selectedAe.termPreferred}</Descriptions.Item>
              <Descriptions.Item label="MedDRA 编码">{selectedAe.termCode || '-'}</Descriptions.Item>
              <Descriptions.Item label="严重程度"><StatusTag status={selectedAe.severity} category="severity" /></Descriptions.Item>
              <Descriptions.Item label="严重性"><StatusTag status={selectedAe.seriousness} category="seriousness" /></Descriptions.Item>
              <Descriptions.Item label="因果判断">{causalityOptions.find(o => o.value === selectedAe.causality)?.label || '-'}</Descriptions.Item>
              <Descriptions.Item label="发生日期">{dayjs(selectedAe.onsetDate).format('YYYY-MM-DD')}</Descriptions.Item>
              <Descriptions.Item label="结束日期">{selectedAe.endDate ? dayjs(selectedAe.endDate).format('YYYY-MM-DD') : '持续中'}</Descriptions.Item>
              <Descriptions.Item label="结局">{selectedAe.outcome ? outcomeOptions.find(o => o.value === selectedAe.outcome)?.label : '-'}</Descriptions.Item>
              <Descriptions.Item label="状态"><StatusTag status={selectedAe.status} category="workflow" /></Descriptions.Item>
              <Descriptions.Item label="事件描述" span={2}>{selectedAe.description}</Descriptions.Item>
            </Descriptions>

            {selectedAe.eventType === 'sae' && (
              <>
                <div style={{ marginTop: 24, marginBottom: 12, fontWeight: 600 }}>SAE 报告记录</div>
                <Table
                  rowKey="id"
                  dataSource={reports}
                  loading={reportsLoading}
                  pagination={false}
                  size="small"
                  columns={[
                    { title: '报告类型', dataIndex: 'reportType', key: 'reportType', render: (v: string) => reportTypeOptions.find(o => o.value === v)?.label || v },
                    { title: '报告日期', dataIndex: 'reportDate', key: 'reportDate', render: (v: string) => dayjs(v).format('YYYY-MM-DD') },
                    { title: '审阅状态', dataIndex: 'reviewStatus', key: 'reviewStatus', render: (v: string) => v ? <Tag>{v}</Tag> : '-' },
                    { title: '提交状态', dataIndex: 'submissionStatus', key: 'submissionStatus', render: (v: string) => v ? <Tag color="blue">{v}</Tag> : '-' },
                  ]}
                />
                {reports.length === 0 && !reportsLoading && (
                  <div style={{ textAlign: 'center', color: '#999', padding: 16 }}>暂无 SAE 报告</div>
                )}
              </>
            )}
          </>
        )}

        {/* 新建 SAE 报告弹窗 */}
        <Modal
          title="新建 SAE 报告"
          open={reportModalOpen}
          onOk={handleCreateReport}
          onCancel={() => setReportModalOpen(false)}
          confirmLoading={reportSubmitLoading}
          okText="创建报告"
          cancelText="取消"
        >
          <Form form={reportForm} layout="vertical" style={{ marginTop: 16 }}>
            <Form.Item name="reportType" label="报告类型" rules={[{ required: true }]}>
              <Select options={reportTypeOptions} />
            </Form.Item>
            <Form.Item name="reportDate" label="报告日期" rules={[{ required: true }]}>
              <DatePicker style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="regulatoryBody" label="监管机构">
              <Input placeholder="如 NMPA、FDA" />
            </Form.Item>
            <Form.Item name="reportVersion" label="报告版本">
              <Input placeholder="如 1.0" />
            </Form.Item>
          </Form>
        </Modal>
      </Drawer>
    </div>
  );
};

export default AePage;
