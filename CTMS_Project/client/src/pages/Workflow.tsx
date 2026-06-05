import React, { useState, useEffect, useCallback } from 'react';
import {  Table, Modal, Form, Input, Select, Space, Button, Tabs, Descriptions, Badge, Card, Statistic, Row, Col, Drawer , App } from 'antd';
import { CheckOutlined, CloseOutlined, SendOutlined, EyeOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import PageHeader from '@/components/PageHeader';
import StatusTag from '@/components/StatusTag';
import { workflowApi } from '@/api/workflow';
import { projectApi } from '@/api/project';
import type { WorkflowDefinition, WorkflowInstance, WorkflowTask, ProcessTaskParams } from '@/types';

const { TextArea } = Input;

const workflowTypeOptions = [
  { value: 'project_approval', label: '项目审批' },
  { value: 'site_activation', label: '中心激活' },
  { value: 'budget_review', label: '预算审核' },
  { value: 'protocol_amendment', label: '方案修正' },
  { value: 'safety_report', label: '安全报告' },
  { value: 'data_lock', label: '数据锁定' },
  { value: 'contract_approval', label: '合同审批' },
  { value: 'other', label: '其他' },
];

const WorkflowPage: React.FC = () => {
  const { message } = App.useApp();
  const [activeTab, setActiveTab] = useState('instances');

  // 流程实例
  const [instances, setInstances] = useState<WorkflowInstance[]>([]);
  const [instLoading, setInstLoading] = useState(false);
  const [instPagination, setInstPagination] = useState({ page: 1, pageSize: 10, total: 0 });

  // 我的待办
  const [myTasks, setMyTasks] = useState<WorkflowTask[]>([]);
  const [taskLoading, setTaskLoading] = useState(false);
  const [taskPagination, setTaskPagination] = useState({ page: 1, pageSize: 10, total: 0 });

  // 流程定义
  const [definitions, setDefinitions] = useState<WorkflowDefinition[]>([]);
  const [defLoading, setDefLoading] = useState(false);

  // 发起审批弹窗
  const [startModalOpen, setStartModalOpen] = useState(false);
  const [startForm] = Form.useForm();
  const [startLoading, setStartLoading] = useState(false);

  // 审批处理弹窗
  const [processModalOpen, setProcessModalOpen] = useState(false);
  const [processForm] = Form.useForm();
  const [processLoading, setProcessLoading] = useState(false);
  const [currentTask, setCurrentTask] = useState<WorkflowTask | null>(null);

  // 详情抽屉
  const [detailOpen, setDetailOpen] = useState(false);
  const [selectedInstance, setSelectedInstance] = useState<WorkflowInstance | null>(null);

  // 统计
  const [stats, setStats] = useState<any>(null);

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

  const fetchInstances = useCallback(async (page = 1, pageSize = 10) => {
    setInstLoading(true);
    try {
      const res = await workflowApi.listInstances({ page, pageSize });
      setInstances(res?.list || []);
      setInstPagination({ page: res?.page || 1, pageSize: res?.pageSize || 10, total: res?.total || 0 });
    } catch {
      message.error('加载流程列表失败');
    } finally {
      setInstLoading(false);
    }
  }, []);

  const fetchMyTasks = useCallback(async (page = 1, pageSize = 10) => {
    setTaskLoading(true);
    try {
      const res = await workflowApi.getMyTasks({ page, pageSize });
      setMyTasks(res?.list || []);
      setTaskPagination({ page: res?.page || 1, pageSize: res?.pageSize || 10, total: res?.total || 0 });
    } catch {
      message.error('加载待办失败');
    } finally {
      setTaskLoading(false);
    }
  }, []);

  const fetchDefinitions = useCallback(async () => {
    setDefLoading(true);
    try {
      const res = await workflowApi.listDefinitions({ pageSize: 100 });
      setDefinitions(res?.list || []);
    } catch {
      message.error('加载流程定义失败');
    } finally {
      setDefLoading(false);
    }
  }, []);

  const fetchStats = useCallback(async () => {
    try {
      const res = await workflowApi.getStats();
      setStats(res?.list || [] || res);
    } catch {
      // ignore
    }
  }, []);

  useEffect(() => {
    fetchInstances();
    fetchMyTasks();
    fetchDefinitions();
    fetchStats();
    fetchProjects();
  }, [fetchInstances, fetchMyTasks, fetchDefinitions, fetchStats, fetchProjects]);

  const handleStartWorkflow = async () => {
    try {
      const values = await startForm.validateFields();
      setStartLoading(true);
      await workflowApi.startInstance(values);
      message.success('审批流程已发起');
      setStartModalOpen(false);
      startForm.resetFields();
      fetchInstances();
      fetchMyTasks();
    } catch (err: any) {
      if (err.errorFields) return;
      message.error('发起失败');
    } finally {
      setStartLoading(false);
    }
  };

  const openProcess = (task: WorkflowTask) => {
    setCurrentTask(task);
    processForm.resetFields();
    setProcessModalOpen(true);
  };

  const handleProcess = async (action: ProcessTaskParams['action']) => {
    try {
      const values = await processForm.validateFields();
      setProcessLoading(true);
      await workflowApi.processTask(currentTask!.id, {
        action,
        comment: values.comment
      });
      message.success(action === 'approve' ? '已审批通过' : action === 'reject' ? '已拒绝' : '操作成功');
      setProcessModalOpen(false);
      fetchMyTasks();
      fetchInstances();
      fetchStats();
    } catch (err: any) {
      if (err.errorFields) return;
      message.error('操作失败');
    } finally {
      setProcessLoading(false);
    }
  };

  const openDetail = async (instance: WorkflowInstance) => {
    setSelectedInstance(instance);
    setDetailOpen(true);
  };

  const instanceColumns = [
    { title: '流程类型', dataIndex: 'workflowType', key: 'workflowType', width: 120, render: (v: string) => workflowTypeOptions.find(o => o.value === v)?.label || v },
    { title: '项目 ID', dataIndex: 'projectId', key: 'projectId', ellipsis: true, width: 120 },
    { title: '当前阶段', dataIndex: 'currentStageName', key: 'currentStageName', ellipsis: true },
    { title: '状态', dataIndex: 'status', key: 'status', width: 100, render: (v: string) => <StatusTag status={v} category="workflow" /> },
    { title: '发起时间', dataIndex: 'createdAt', key: 'createdAt', width: 170, render: (v: string) => dayjs(v).format('YYYY-MM-DD HH:mm') },
    {
      title: '操作', key: 'actions', width: 100, fixed: 'right' as const,
      render: (_: any, record: WorkflowInstance) => (
        <Button type="link" size="small" icon={<EyeOutlined />} onClick={() => openDetail(record)}>详情</Button>
      ) },
  ];

  const taskColumns = [
    { title: '流程类型', key: 'workflowType', width: 120, render: (_: any, record: WorkflowTask) => workflowTypeOptions.find(o => o.value === record.instance?.workflowType)?.label || record.instance?.workflowType },
    { title: '当前阶段', dataIndex: 'stageName', key: 'stageName', ellipsis: true },
    { title: '状态', dataIndex: 'status', key: 'status', width: 100, render: (v: string) => <StatusTag status={v} category="workflow" /> },
    { title: '到达时间', dataIndex: 'createdAt', key: 'createdAt', width: 170, render: (v: string) => dayjs(v).format('YYYY-MM-DD HH:mm') },
    {
      title: '操作', key: 'actions', width: 160, fixed: 'right' as const,
      render: (_: any, record: WorkflowTask) => (
        <Space>
          <Button type="link" size="small" icon={<CheckOutlined />} style={{ color: '#52c41a' }} onClick={() => openProcess(record)}>通过</Button>
          <Button type="link" size="small" icon={<CloseOutlined />} style={{ color: '#ff4d4f' }} onClick={() => openProcess(record)}>拒绝</Button>
          <Button type="link" size="small" icon={<EyeOutlined />} onClick={() => openDetail(record.instance)}>详情</Button>
        </Space>
      ) },
  ];

  const tabItems = [
    {
      key: 'instances',
      label: (
        <span>流程列表 <Badge count={instPagination.total} showZero style={{ marginLeft: 4 }} /></span>
      ),
      children: (
        <Table
          rowKey="id"
          columns={instanceColumns}
          dataSource={instances}
          loading={instLoading}
          scroll={{ x: 800 }}
          pagination={{
            current: instPagination.page,
            pageSize: instPagination.pageSize,
            total: instPagination.total,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条`,
            onChange: (page, pageSize) => fetchInstances(page, pageSize) }}
        />
      ) },
    {
      key: 'my-tasks',
      label: (
        <span>我的待办 <Badge count={taskPagination.total} showZero style={{ marginLeft: 4, background: '#faad14' }} /></span>
      ),
      children: (
        <Table
          rowKey="id"
          columns={taskColumns}
          dataSource={myTasks}
          loading={taskLoading}
          scroll={{ x: 800 }}
          pagination={{
            current: taskPagination.page,
            pageSize: taskPagination.pageSize,
            total: taskPagination.total,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条`,
            onChange: (page, pageSize) => fetchMyTasks(page, pageSize) }}
        />
      ) },
    {
      key: 'definitions',
      label: '流程定义',
      children: (
        <Table
          rowKey="id"
          dataSource={definitions}
          loading={defLoading}
          pagination={false}
          columns={[
            { title: '流程编码', dataIndex: 'workflowCode', key: 'workflowCode', width: 160 },
            { title: '流程名称', dataIndex: 'workflowName', key: 'workflowName', ellipsis: true },
            { title: '流程类型', dataIndex: 'workflowType', key: 'workflowType', width: 120, render: (v: string) => workflowTypeOptions.find(o => o.value === v)?.label || v },
            { title: '阶段数', dataIndex: 'stages', key: 'stages', width: 80, render: (v: any[]) => v?.length || 0 },
            { title: '说明', dataIndex: 'description', key: 'description', ellipsis: true },
          ]}
        />
      ) },
  ];

  return (
    <div>
      <PageHeader
        title="工作流管理"
        subtitle="审批流程定义、发起和审批处理"
        extra={
          <Button type="primary" icon={<SendOutlined />} onClick={() => { startForm.resetFields(); setStartModalOpen(true); }}>
            发起审批
          </Button>
        }
      />

      {stats && (
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={6}><Card size="small"><Statistic title="进行中" value={stats.running || 0} styles={{ content: { color: '#1890ff' } }} /></Card></Col>
          <Col span={6}><Card size="small"><Statistic title="待我审批" value={stats.pending || 0} styles={{ content: { color: '#faad14' } }} /></Card></Col>
          <Col span={6}><Card size="small"><Statistic title="已通过" value={stats.approved || 0} styles={{ content: { color: '#52c41a' } }} /></Card></Col>
          <Col span={6}><Card size="small"><Statistic title="已拒绝" value={stats.rejected || 0} styles={{ content: { color: '#ff4d4f' } }} /></Card></Col>
        </Row>
      )}

      <Tabs activeKey={activeTab} onChange={setActiveTab} items={tabItems} />

      {/* 发起审批弹窗 */}
      <Modal
        title="发起审批"
        open={startModalOpen}
        onOk={handleStartWorkflow}
        onCancel={() => setStartModalOpen(false)}
        width={560}
        confirmLoading={startLoading}
        okText="提交"
        cancelText="取消"
      >
        <Form form={startForm} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item name="definitionId" label="选择流程" rules={[{ required: true, message: '请选择流程' }]}>
            <Select placeholder="请选择审批流程" options={definitions.map(d => ({ value: d.id, label: `${d.workflowName} (${d.workflowCode})` }))} />
          </Form.Item>
          <Form.Item name="projectId" label="关联项目">
            <Select placeholder="请选择项目" options={projects} loading={projectsLoading} showSearch optionFilterProp="label" allowClear />
          </Form.Item>
          <Form.Item name="initiatorComment" label="发起说明">
            <TextArea rows={3} placeholder="请填写审批说明" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 审批处理弹窗 */}
      <Modal
        title={`审批处理 - ${currentTask?.stageName || ''}`}
        open={processModalOpen}
        onCancel={() => setProcessModalOpen(false)}
        footer={null}
        width={480}
      >
        <Form form={processForm} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item name="comment" label="审批意见">
            <TextArea rows={3} placeholder="请填写审批意见" />
          </Form.Item>
          <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
            <Button onClick={() => setProcessModalOpen(false)}>取消</Button>
            <Button danger loading={processLoading} onClick={() => handleProcess('reject')}>拒绝</Button>
            <Button type="primary" loading={processLoading} onClick={() => handleProcess('approve')}>通过</Button>
          </Space>
        </Form>
      </Modal>

      {/* 流程详情抽屉 */}
      <Drawer
        title="流程详情"
        size="large"
        open={detailOpen}
        onClose={() => setDetailOpen(false)}
      >
        {selectedInstance && (
          <Descriptions bordered size="small" column={1}>
            <Descriptions.Item label="流程类型">{workflowTypeOptions.find(o => o.value === selectedInstance.workflowType)?.label || selectedInstance.workflowType}</Descriptions.Item>
            <Descriptions.Item label="状态"><StatusTag status={selectedInstance.status} category="workflow" /></Descriptions.Item>
            <Descriptions.Item label="当前阶段">{selectedInstance.currentStageName || '-'}</Descriptions.Item>
            <Descriptions.Item label="项目 ID">{selectedInstance.projectId || '-'}</Descriptions.Item>
            <Descriptions.Item label="发起时间">{dayjs(selectedInstance.createdAt).format('YYYY-MM-DD HH:mm')}</Descriptions.Item>
          </Descriptions>
        )}
      </Drawer>
    </div>
  );
};

export default WorkflowPage;
