import React, { useState, useEffect, useCallback } from 'react';
import {  Table, Modal, Form, Input, Select, Space, Button, Drawer, Descriptions , App } from 'antd';
import { EyeOutlined, SendOutlined, CloseCircleOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import PageHeader from '@/components/PageHeader';
import StatusTag from '@/components/StatusTag';
import { queryApi } from '@/api/query';
import { projectApi } from '@/api/project';
import { settingsApi } from '@/api/settings';
import type { DataQuery, CreateQueryParams } from '@/types';

const { TextArea } = Input;

const queryTypeOptions = [
  { value: 'data_discrepancy', label: '数据差异' },
  { value: 'missing_data', label: '数据缺失' },
  { value: 'protocol_deviation', label: '方案偏离' },
  { value: 'query clarification', label: '查询澄清' },
  { value: 'other', label: '其他' },
];

const priorityOptions = [
  { value: 'low', label: '低' },
  { value: 'medium', label: '中' },
  { value: 'high', label: '高' },
  { value: 'critical', label: '紧急' },
];

const QueriesPage: React.FC = () => {
  const { message } = App.useApp();
  const [data, setData] = useState<DataQuery[]>([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({ page: 1, pageSize: 10, total: 0 });
  const [keyword, setKeyword] = useState('');
  const [priorityFilter, setPriorityFilter] = useState<string | undefined>(undefined);
  const [statusFilter, setStatusFilter] = useState<string | undefined>(undefined);

  // 创建质疑弹窗
  const [modalOpen, setModalOpen] = useState(false);
  const [form] = Form.useForm();
  const [submitLoading, setSubmitLoading] = useState(false);

  // 详情抽屉
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [selectedQuery, setSelectedQuery] = useState<DataQuery | null>(null);

  // 回复弹窗
  const [replyOpen, setReplyOpen] = useState(false);
  const [replyForm] = Form.useForm();
  const [replyLoading, setReplyLoading] = useState(false);

  const [projects, setProjects] = useState<{label: string, value: string}[]>([]);
  const [projectsLoading, setProjectsLoading] = useState(false);
  const [users, setUsers] = useState<{label: string, value: string}[]>([]);
  const [usersLoading, setUsersLoading] = useState(false);

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

  const fetchUsers = useCallback(async () => {
    setUsersLoading(true);
    try {
      const res = await settingsApi.listUsers({ page: 1, pageSize: 1000 });
      setUsers((res?.list || []).map((u: any) => ({
        label: u.displayName || u.username,
        value: u.id })));
    } catch {
      // ignore
    } finally {
      setUsersLoading(false);
    }
  }, []);

  const fetchData = useCallback(async (page = 1, pageSize = 10) => {
    setLoading(true);
    try {
      const res = await queryApi.list({ page, pageSize, keyword, priority: priorityFilter, status: statusFilter });
      setData(res?.list || []);
      setPagination({ page: res?.page || 1, pageSize: res?.pageSize || 10, total: res?.total || 0 });
    } catch {
      message.error('加载质疑列表失败');
    } finally {
      setLoading(false);
    }
  }, [keyword, priorityFilter, statusFilter]);

  useEffect(() => {
    fetchData();
    fetchProjects();
    fetchUsers();
  }, [fetchData, fetchProjects, fetchUsers]);

  const handleCreate = () => {
    form.resetFields();
    setModalOpen(true);
  };

  const handleCreateSubmit = async () => {
    try {
      const values = await form.validateFields();
      setSubmitLoading(true);
      await queryApi.create(values as CreateQueryParams);
      message.success('质疑已创建');
      setModalOpen(false);
      fetchData(pagination.page, pagination.pageSize);
    } catch (err: any) {
      if (err.errorFields) return;
      message.error(err.response?.data?.error?.message || '创建失败');
    } finally {
      setSubmitLoading(false);
    }
  };

  const openDetail = async (record: DataQuery) => {
    try {
      const res = await queryApi.getById(record.id);
      setSelectedQuery((res as any)?.data || res);
      setDrawerOpen(true);
    } catch {
      message.error('获取详情失败');
    }
  };

  const handleReply = async () => {
    try {
      const values = await replyForm.validateFields();
      setReplyLoading(true);
      await queryApi.reply(selectedQuery!.id, values);
      message.success('回复成功');
      setReplyOpen(false);
      replyForm.resetFields();
      // 重新获取详情
      const updated = await queryApi.getById(selectedQuery!.id);
      setSelectedQuery((updated as any)?.data || updated);
      fetchData(pagination.page, pagination.pageSize);
    } catch (err: any) {
      if (err.errorFields) return;
      message.error('回复失败');
    } finally {
      setReplyLoading(false);
    }
  };

  const handleClose = async (id: string) => {
    try {
      await queryApi.reply(id, { content: '质疑已关闭', action: 'close' });
      message.success('质疑已关闭');
      setDrawerOpen(false);
      fetchData(pagination.page, pagination.pageSize);
    } catch {
      message.error('操作失败');
    }
  };

  const columns = [
    { title: '标题', dataIndex: 'title', key: 'title', ellipsis: true },
    {
      title: '类型', dataIndex: 'queryType', key: 'queryType', width: 110,
      render: (v: string) => queryTypeOptions.find(o => o.value === v)?.label || v },
    {
      title: '优先级', dataIndex: 'priority', key: 'priority', width: 90,
      render: (v: string) => <StatusTag status={v} category="queryPriority" /> },
    {
      title: '状态', dataIndex: 'status', key: 'status', width: 100,
      render: (v: string) => <StatusTag status={v} category="queryStatus" /> },
    { title: '创建时间', dataIndex: 'createdAt', key: 'createdAt', width: 170, render: (v: string) => v ? dayjs(v).format('YYYY-MM-DD HH:mm') : '-' },
    {
      title: '操作', key: 'actions', width: 120, fixed: 'right' as const,
      render: (_: any, record: DataQuery) => (
        <Space>
          <Button type="link" size="small" icon={<EyeOutlined />} onClick={() => openDetail(record)}>详情</Button>
          {record.status === 'open' && (
            <Button type="link" size="small" icon={<CloseCircleOutlined />} onClick={() => handleClose(record.id)}>关闭</Button>
          )}
        </Space>
      ) },
  ];

  return (
    <div>
      <PageHeader
        title="质疑管理"
        subtitle="数据质疑的创建、回复和关闭"
        showCreate
        onCreateClick={handleCreate}
        onSearch={setKeyword}
        searchPlaceholder="搜索质疑标题"
      >
        <Select placeholder="优先级" allowClear style={{ width: 110 }} onChange={setPriorityFilter} options={priorityOptions} value={priorityFilter} />
        <Select placeholder="状态" allowClear style={{ width: 110 }} onChange={setStatusFilter} options={[
          { value: 'open', label: '待回复' },
          { value: 'replied', label: '已回复' },
          { value: 'closed', label: '已关闭' },
        ]} value={statusFilter} />
      </PageHeader>

      <Table
        rowKey="id"
        columns={columns}
        dataSource={data}
        loading={loading}
        scroll={{ x: 900 }}
        pagination={{
          current: pagination.page,
          pageSize: pagination.pageSize,
          total: pagination.total,
          showSizeChanger: true,
          showTotal: (total) => `共 ${total} 条`,
          onChange: (page, pageSize) => fetchData(page, pageSize) }}
      />

      {/* 创建质疑 */}
      <Modal
        title="创建数据质疑"
        open={modalOpen}
        onOk={handleCreateSubmit}
        onCancel={() => setModalOpen(false)}
        width={640}
        confirmLoading={submitLoading}
        okText="提交"
        cancelText="取消"
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item name="projectId" label="所属项目" rules={[{ required: true, message: '请选择项目' }]}>
            <Select placeholder="请选择项目" options={projects} loading={projectsLoading} showSearch optionFilterProp="label" />
          </Form.Item>
          <Form.Item name="title" label="质疑标题" rules={[{ required: true, message: '请输入标题' }]}>
            <Input placeholder="简要描述质疑内容" />
          </Form.Item>
          <Form.Item name="description" label="详细描述" rules={[{ required: true, message: '请输入描述' }]}>
            <TextArea rows={4} placeholder="详细描述数据问题" />
          </Form.Item>
          <Space style={{ width: '100%' }} size="large">
            <Form.Item name="queryType" label="质疑类型" rules={[{ required: true }]}>
              <Select placeholder="请选择" style={{ width: 200 }} options={queryTypeOptions} />
            </Form.Item>
            <Form.Item name="priority" label="优先级">
              <Select placeholder="请选择" style={{ width: 200 }} options={priorityOptions} />
            </Form.Item>
          </Space>
          <Space style={{ width: '100%' }} size="large">
            <Form.Item name="subjectId" label="受试者 ID">
              <Input placeholder="可选" style={{ width: 280 }} />
            </Form.Item>
            <Form.Item name="assignedTo" label="指派给">
              <Select placeholder="请选择人员" options={users} loading={usersLoading} showSearch optionFilterProp="label" allowClear style={{ width: 280 }} />
            </Form.Item>
          </Space>
        </Form>
      </Modal>

      {/* 质疑详情抽屉 */}
      <Drawer
        title={`质疑详情 - ${selectedQuery?.title || ''}`}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        size="large"
        extra={
          selectedQuery?.status === 'open' && (
            <Space>
              <Button icon={<SendOutlined />} onClick={() => { replyForm.resetFields(); setReplyOpen(true); }}>回复</Button>
              <Button danger onClick={() => handleClose(selectedQuery!.id)}>关闭质疑</Button>
            </Space>
          )
        }
      >
        {selectedQuery && (
          <Descriptions bordered size="small" column={1}>
            <Descriptions.Item label="标题">{selectedQuery.title}</Descriptions.Item>
            <Descriptions.Item label="类型">{queryTypeOptions.find(o => o.value === selectedQuery.queryType)?.label}</Descriptions.Item>
            <Descriptions.Item label="优先级"><StatusTag status={selectedQuery.priority} category="queryPriority" /></Descriptions.Item>
            <Descriptions.Item label="状态"><StatusTag status={selectedQuery.status} category="queryStatus" /></Descriptions.Item>
            <Descriptions.Item label="描述">{selectedQuery.description}</Descriptions.Item>
            <Descriptions.Item label="创建时间">{dayjs(selectedQuery.createdAt).format('YYYY-MM-DD HH:mm')}</Descriptions.Item>
            <Descriptions.Item label="更新时间">{dayjs(selectedQuery.updatedAt).format('YYYY-MM-DD HH:mm')}</Descriptions.Item>
          </Descriptions>
        )}
      </Drawer>

      {/* 回复弹窗 */}
      <Modal
        title="回复质疑"
        open={replyOpen}
        onOk={handleReply}
        onCancel={() => setReplyOpen(false)}
        confirmLoading={replyLoading}
        okText="发送回复"
        cancelText="取消"
      >
        <Form form={replyForm} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item name="content" label="回复内容" rules={[{ required: true, message: '请输入回复内容' }]}>
            <TextArea rows={4} placeholder="请输入回复内容" />
          </Form.Item>
          <Form.Item name="action" label="操作">
            <Select placeholder="请选择操作" options={[
              { value: 'reply', label: '仅回复' },
              { value: 'close', label: '回复并关闭' },
              { value: 'escalate', label: '回复并升级' },
            ]} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default QueriesPage;
