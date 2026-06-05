import React, { useState, useEffect, useCallback } from 'react';
import {  Table, Modal, Form, Input, Select, Space, Button, Drawer, Descriptions, Tag, DatePicker, Tabs , App } from 'antd';
import { EditOutlined, EyeOutlined, DeleteOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import PageHeader from '@/components/PageHeader';
import StatusTag from '@/components/StatusTag';
import { monitoringApi } from '@/api/monitoring';
import { projectApi } from '@/api/project';
import type { MonitoringPlan, MonitoringVisit, CreateMonitoringPlanParams, CreateMonitoringVisitParams } from '@/types';

const visitTypeOptions = [
  { value: 'SIV', label: 'SIV 中心启动' },
  { value: 'SMV', label: 'SMV 监查访问' },
  { value: 'COV', label: 'COV 关键评估' },
  { value: 'PMV', label: 'PMV 项目监查' },
  { value: 'CLOSEOUT', label: 'CLOSEOUT 中心关闭' },
];

const planStatusMap: Record<string, { color: string; label: string }> = {
  planned: { color: 'default', label: '已计划' },
  in_progress: { color: 'processing', label: '进行中' },
  completed: { color: 'success', label: '已完成' },
  cancelled: { color: 'error', label: '已取消' } };

const MonitoringPage: React.FC = () => {
  const { message } = App.useApp();
  const [data, setData] = useState<MonitoringPlan[]>([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({ page: 1, pageSize: 10, total: 0 });
  const [keyword, setKeyword] = useState('');
  const [typeFilter, setTypeFilter] = useState<string | undefined>(undefined);
  const [activeTab, setActiveTab] = useState('plans');

  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<MonitoringPlan | null>(null);
  const [form] = Form.useForm();
  const [submitLoading, setSubmitLoading] = useState(false);
  const [projects, setProjects] = useState<{label: string, value: string}[]>([]);

  const [drawerOpen, setDrawerOpen] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState<MonitoringPlan | null>(null);
  const [visits, setVisits] = useState<MonitoringVisit[]>([]);
  const [visitsLoading, setVisitsLoading] = useState(false);

  const [visitModalOpen, setVisitModalOpen] = useState(false);
  const [visitForm] = Form.useForm();
  const [visitSubmitLoading, setVisitSubmitLoading] = useState(false);

  // ===== 计划管理 =====
  const fetchPlans = useCallback(async (page = 1, pageSize = 10) => {
    setLoading(true);
    try {
      const res = await monitoringApi.listPlans({ page, pageSize, keyword, visitType: typeFilter });
      setData(res?.list || []);
      setPagination({ page: res?.page || 1, pageSize: res?.pageSize || 10, total: res?.total || 0 });
    } catch {
      message.error('加载监察计划列表失败');
    } finally {
      setLoading(false);
    }
  }, [keyword, typeFilter]);

  const fetchProjects = useCallback(async () => {
    try {
      const res = await projectApi.list({ page: 1, pageSize: 1000 });
      setProjects((res?.list || []).map((p: any) => ({ label: p.projectName, value: p.id })));
    } catch {}
  }, []);

  const [allPlans, setAllPlans] = useState<{label: string, value: string}[]>([]);
  const [allPlansLoading, setAllPlansLoading] = useState(false);

  const fetchAllPlans = useCallback(async () => {
    setAllPlansLoading(true);
    try {
      const res = await monitoringApi.listPlans({ page: 1, pageSize: 1000 });
      setAllPlans((res?.list || []).map((p: any) => ({ label: p.planName, value: p.id })));
    } catch {
      // ignore
    } finally {
      setAllPlansLoading(false);
    }
  }, []);

  useEffect(() => { fetchPlans(); fetchProjects(); fetchAllPlans(); }, [fetchPlans, fetchProjects, fetchAllPlans]);

  const handleCreate = () => {
    if (activeTab === 'plans') {
      setEditing(null);
      form.resetFields();
      setModalOpen(true);
    } else {
      if (!selectedPlan) {
        message.warning('请先在计划列表中选择一个计划查看详情，或在此选择所属计划。');
        // 可选：也可以在这里加载计划列表供选择
      }
      visitForm.resetFields();
      if (selectedPlan) {
        visitForm.setFieldsValue({ planId: selectedPlan.id, visitType: selectedPlan.visitType });
      }
      setVisitModalOpen(true);
    }
  };

  const handleEdit = (record: MonitoringPlan) => {
    setEditing(record);
    form.setFieldsValue({
      ...record,
      scheduledDate: record.scheduledDate ? dayjs(record.scheduledDate) : undefined });
    setModalOpen(true);
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setSubmitLoading(true);
      const params: CreateMonitoringPlanParams = {
        ...values,
        scheduledDate: values.scheduledDate?.format('YYYY-MM-DD') };
      if (editing) {
        await monitoringApi.updatePlan(editing.id, params);
        message.success('更新监察计划成功');
      } else {
        await monitoringApi.createPlan(params);
        message.success('创建监察计划成功');
      }
      setModalOpen(false);
      fetchPlans(pagination.page, pagination.pageSize);
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

  const handleVisitSubmit = async () => {
    try {
      const values = await visitForm.validateFields();
      setVisitSubmitLoading(true);
      const params: CreateMonitoringVisitParams = {
        ...values,
        visitDate: values.visitDate?.format('YYYY-MM-DD')
      };
      await monitoringApi.createVisit(params);
      message.success('创建访视记录成功');
      setVisitModalOpen(false);
      if (selectedPlan && selectedPlan.id === values.planId) {
        handleViewDetail(selectedPlan); // 刷新访视列表
      }
    } catch (err: any) {
      if (err.errorFields) {
        message.warning('请检查表单填写是否正确');
        return;
      }
      message.error(err.response?.data?.error?.message || '创建失败');
    } finally {
      setVisitSubmitLoading(false);
    }
  };

  const handleDelete = (record: MonitoringPlan) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除监察计划「${record.planName}」吗？`,
      onOk: async () => {
        await monitoringApi.deletePlan(record.id);
        message.success('删除成功');
        fetchPlans(pagination.page, pagination.pageSize);
      } });
  };

  const handleViewDetail = async (record: MonitoringPlan) => {
    setSelectedPlan(record);
    setDrawerOpen(true);
    setVisitsLoading(true);
    try {
      const res = await monitoringApi.listVisits({ planId: record.id, page: 1, pageSize: 100 });
      setVisits(res?.list || []);
    } catch {
      message.error('加载访视记录失败');
    } finally {
      setVisitsLoading(false);
    }
  };

  // ===== 计划列定义 =====
  const planColumns = [
    { title: '计划名称', dataIndex: 'planName', width: 200, ellipsis: true },
    {
      title: '访视类型',
      dataIndex: 'visitType',
      width: 140,
      render: (v: string) => visitTypeOptions.find(o => o.value === v)?.label || v },
    { title: '项目', dataIndex: ['project', 'name'], width: 160, ellipsis: true },
    { title: '中心', dataIndex: ['site', 'name'], width: 140, ellipsis: true },
    { title: 'CRA', dataIndex: ['cra', 'displayName'], width: 100 },
    {
      title: '计划日期',
      dataIndex: 'scheduledDate',
      width: 120,
      render: (v: string) => v ? dayjs(v).format('YYYY-MM-DD') : '-' },
    {
      title: '状态',
      dataIndex: 'status',
      width: 100,
      render: (v: string) => {
        const cfg = planStatusMap[v] || { color: 'default', label: v };
        return <Tag color={cfg.color}>{cfg.label}</Tag>;
      } },
    {
      title: '操作',
      width: 160,
      render: (_: any, record: MonitoringPlan) => (
        <Space size="small">
          <Button type="link" size="small" icon={<EyeOutlined />} onClick={() => handleViewDetail(record)}>查看</Button>
          <Button type="link" size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)}>编辑</Button>
          <Button type="link" size="small" danger icon={<DeleteOutlined />} onClick={() => handleDelete(record)}>删除</Button>
        </Space>
      ) },
  ];

  // ===== 访视列定义 =====
  const visitColumns = [
    { title: '访视日期', dataIndex: 'visitDate', width: 120, render: (v: string) => v ? dayjs(v).format('YYYY-MM-DD') : '-' },
    { title: '访视类型', dataIndex: 'visitType', width: 140 },
    {
      title: '状态',
      dataIndex: 'status',
      width: 100,
      render: (v: string) => <StatusTag status={v} /> },
    { title: '摘要', dataIndex: 'summary', ellipsis: true },
    {
      title: '下次访视',
      dataIndex: 'nextVisitDate',
      width: 120,
      render: (v: string) => v ? dayjs(v).format('YYYY-MM-DD') : '-' },
  ];

  return (
    <>
      <PageHeader
        title="监察管理"
        searchPlaceholder="搜索计划名称"
        onSearch={(v) => { setKeyword(v); }}
      >
        <Space>
          <Select
            placeholder="访视类型"
            allowClear
            style={{ width: 160 }}
            options={visitTypeOptions}
            value={typeFilter}
            onChange={setTypeFilter}
          />
          <Button type="primary" onClick={handleCreate}>
            {activeTab === 'plans' ? '创建监察计划' : '创建访视记录'}
          </Button>
        </Space>
      </PageHeader>

      <Tabs activeKey={activeTab} onChange={setActiveTab} items={[
        { key: 'plans', label: '监察计划', children: (
          <Table
            rowKey="id"
            columns={planColumns}
            dataSource={data}
            loading={loading}
            pagination={{
              current: pagination.page,
              pageSize: pagination.pageSize,
              total: pagination.total,
              showSizeChanger: true,
              showTotal: (t) => `共 ${t} 条`,
              onChange: (p, ps) => fetchPlans(p, ps) }}
            scroll={{ x: 1200 }}
          />
        )},
        { key: 'visits', label: '访视记录', children: (
          <Table
            rowKey="id"
            columns={visitColumns}
            dataSource={visits}
            loading={visitsLoading}
            pagination={false}
            scroll={{ x: 900 }}
            locale={{ emptyText: '请先选择一个监察计划查看访视记录' }}
          />
        )},
      ]} />

      {/* 创建/编辑计划弹窗 */}
      <Modal
        title={editing ? '编辑监察计划' : '创建监察计划'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        confirmLoading={submitLoading}
        width={600}
      >
        <Form form={form} layout="vertical" initialValues={{ status: 'planned' }}>
          <Form.Item name="projectId" label="关联项目" rules={[{ required: true, message: '请选择关联项目' }]}>
            <Select options={projects} placeholder="请选择项目" showSearch optionFilterProp="label" />
          </Form.Item>
          <Form.Item name="planName" label="计划名称" rules={[{ required: true, message: '请输入计划名称' }]}>
            <Input placeholder="请输入监察计划名称" />
          </Form.Item>
          <Form.Item name="visitType" label="访视类型" rules={[{ required: true, message: '请选择访视类型' }]}>
            <Select options={visitTypeOptions} placeholder="请选择" />
          </Form.Item>
          <Form.Item name="scheduledDate" label="计划日期" rules={[{ required: true, message: '请选择计划日期' }]}>
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="scope" label="监查范围">
            <Input.TextArea rows={3} placeholder="描述本次监查的范围" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 创建访视记录弹窗 */}
      <Modal
        title="创建访视记录"
        open={visitModalOpen}
        onOk={handleVisitSubmit}
        onCancel={() => setVisitModalOpen(false)}
        confirmLoading={visitSubmitLoading}
        width={600}
      >
        <Form form={visitForm} layout="vertical">
          <Form.Item name="planId" label="关联监察计划" rules={[{ required: true, message: '请选择关联的监察计划' }]}>
            <Select options={allPlans} loading={allPlansLoading} placeholder="请选择计划" showSearch optionFilterProp="label" />
          </Form.Item>
          <Form.Item name="visitType" label="访视类型" rules={[{ required: true, message: '请选择访视类型' }]}>
            <Select options={visitTypeOptions} placeholder="请选择" />
          </Form.Item>
          <Form.Item name="visitDate" label="访视日期" rules={[{ required: true, message: '请选择访视日期' }]}>
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="summary" label="摘要">
            <Input.TextArea rows={3} placeholder="简要描述本次访视内容" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 详情抽屉 */}
      <Drawer
        title={selectedPlan?.planName}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        size="large"
      >
        {selectedPlan && (
          <Descriptions column={2} bordered size="small">
            <Descriptions.Item label="计划名称" span={2}>{selectedPlan.planName}</Descriptions.Item>
            <Descriptions.Item label="访视类型">{visitTypeOptions.find(o => o.value === selectedPlan.visitType)?.label}</Descriptions.Item>
            <Descriptions.Item label="状态">
              <Tag color={planStatusMap[selectedPlan.status]?.color}>{planStatusMap[selectedPlan.status]?.label}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="项目">{selectedPlan.project?.name || '-'}</Descriptions.Item>
            <Descriptions.Item label="中心">{selectedPlan.site?.name || '-'}</Descriptions.Item>
            <Descriptions.Item label="CRA">{selectedPlan.cra?.displayName || '-'}</Descriptions.Item>
            <Descriptions.Item label="计划日期">{selectedPlan.scheduledDate ? dayjs(selectedPlan.scheduledDate).format('YYYY-MM-DD') : '-'}</Descriptions.Item>
            <Descriptions.Item label="实际日期">{selectedPlan.actualDate ? dayjs(selectedPlan.actualDate).format('YYYY-MM-DD') : '-'}</Descriptions.Item>
            <Descriptions.Item label="范围" span={2}>{selectedPlan.scope || '-'}</Descriptions.Item>
            <Descriptions.Item label="发现" span={2}>{selectedPlan.findings || '-'}</Descriptions.Item>
            <Descriptions.Item label="备注" span={2}>{selectedPlan.remarks || '-'}</Descriptions.Item>
          </Descriptions>
        )}
      </Drawer>
    </>
  );
};

export default MonitoringPage;
