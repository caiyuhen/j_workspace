import React, { useState, useEffect, useCallback } from 'react';
import {  Table, Modal, Form, Input, InputNumber, Select, Space, Button, DatePicker, Tag , App } from 'antd';
import { PlusOutlined, SendOutlined, CheckOutlined, CloseOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import PageHeader from '@/components/PageHeader';
import StatusTag from '@/components/StatusTag';
import { timesheetApi } from '@/api/timesheet';
import { projectApi } from '@/api/project';
import { settingsApi } from '@/api/settings';
import type { Timesheet, CreateTimesheetParams } from '@/types';

const workTypeOptions = [
  { value: 'monitoring', label: '监查' },
  { value: 'site_management', label: '中心管理' },
  { value: 'project_management', label: '项目管理' },
  { value: 'data_review', label: '数据审核' },
  { value: 'training', label: '培训' },
  { value: 'meeting', label: '会议' },
  { value: 'travel', label: '差旅' },
  { value: 'other', label: '其他' },
];

const TimesheetPage: React.FC = () => {
  const { message } = App.useApp();
  const [data, setData] = useState<Timesheet[]>([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({ page: 1, pageSize: 10, total: 0 });
  const [statusFilter, setStatusFilter] = useState<string | undefined>(undefined);

  // 创建弹窗
  const [modalOpen, setModalOpen] = useState(false);
  const [form] = Form.useForm();
  const [submitLoading, setSubmitLoading] = useState(false);

  // 审批弹窗
  const [approveModalOpen, setApproveModalOpen] = useState(false);
  const [approveForm] = Form.useForm();
  const [approveLoading, setApproveLoading] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  // 详情抽屉
  const [detailOpen, setDetailOpen] = useState(false);
  const [selectedTimesheet, setSelectedTimesheet] = useState<Timesheet | null>(null);

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
      const res = await timesheetApi.list({ page, pageSize, status: statusFilter });
      setData(res?.list || []);
      setPagination({ page: res?.page || 1, pageSize: res?.pageSize || 10, total: res?.total || 0 });
    } catch {
      message.error('加载工时列表失败');
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    fetchData();
    fetchProjects();
    fetchUsers();
  }, [fetchData, fetchProjects, fetchUsers]);

  const handleCreate = () => {
    form.resetFields();
    // 默认添加一条空记录
    form.setFieldsValue({
      entries: [{ workDate: dayjs(), hours: 0, workType: 'monitoring', isBillable: true }] });
    setModalOpen(true);
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setSubmitLoading(true);
      const params: CreateTimesheetParams = {
        ...values,
        weekStartDate: values.weekStartDate.toISOString(),
        entries: (values.entries || []).map((e: any) => ({
          ...e,
          workDate: e.workDate.toISOString() })) };
      await timesheetApi.create(params);
      message.success('工时已保存');
      setModalOpen(false);
      fetchData(pagination.page, pagination.pageSize);
    } catch (err: any) {
      if (err.errorFields) return;
      message.error(err.response?.data?.error?.message || '保存失败');
    } finally {
      setSubmitLoading(false);
    }
  };

  const handleSubmitTimesheet = async (id: string) => {
    try {
      await timesheetApi.submit(id);
      message.success('工时已提交');
      fetchData(pagination.page, pagination.pageSize);
    } catch {
      message.error('提交失败');
    }
  };

  const openApprove = (id: string) => {
    setSelectedId(id);
    approveForm.resetFields();
    setApproveModalOpen(true);
  };

  const handleApprove = async (action: 'approve' | 'reject') => {
    try {
      const values = await approveForm.validateFields();
      setApproveLoading(true);
      await timesheetApi.approve(selectedId!, { action, comment: values.comment });
      message.success(action === 'approve' ? '已批准' : '已拒绝');
      setApproveModalOpen(false);
      fetchData(pagination.page, pagination.pageSize);
    } catch (err: any) {
      if (err.errorFields) return;
      message.error('操作失败');
    } finally {
      setApproveLoading(false);
    }
  };

  const openDetail = (record: Timesheet) => {
    setSelectedTimesheet(record);
    setDetailOpen(true);
  };

  const columns = [
    { title: '用户 ID', dataIndex: 'userId', key: 'userId', width: 120, ellipsis: true },
    { title: '周起始日', dataIndex: 'weekStartDate', key: 'weekStartDate', width: 120, render: (v: string) => dayjs(v).format('YYYY-MM-DD') },
    {
      title: '总工时', key: 'totalHours', width: 90,
      render: (_: any, record: Timesheet) => {
        const total = (record.entries || []).reduce((sum: number, e: any) => sum + (e.hours || 0), 0);
        return <span>{total}h</span>;
      } },
    {
      title: '状态', dataIndex: 'status', key: 'status', width: 100,
      render: (v: string) => <StatusTag status={v} category="timesheet" /> },
    { title: '创建时间', dataIndex: 'createdAt', key: 'createdAt', width: 170, render: (v: string) => dayjs(v).format('YYYY-MM-DD HH:mm') },
    {
      title: '操作', key: 'actions', width: 200, fixed: 'right' as const,
      render: (_: any, record: Timesheet) => (
        <Space>
          <Button type="link" size="small" onClick={() => openDetail(record)}>详情</Button>
          {record.status === 'draft' && (
            <Button type="link" size="small" icon={<SendOutlined />} onClick={() => handleSubmitTimesheet(record.id)}>提交</Button>
          )}
          {record.status === 'submitted' && (
            <>
              <Button type="link" size="small" icon={<CheckOutlined />} style={{ color: '#52c41a' }} onClick={() => openApprove(record.id)}>批准</Button>
              <Button type="link" size="small" icon={<CloseOutlined />} style={{ color: '#ff4d4f' }} onClick={() => openApprove(record.id)}>拒绝</Button>
            </>
          )}
        </Space>
      ) },
  ];

  return (
    <div>
      <PageHeader
        title="工时管理"
        subtitle="项目成员工时记录和统计"
        showCreate
        onCreateClick={handleCreate}
      >
        <Select placeholder="状态" allowClear style={{ width: 120 }} onChange={setStatusFilter} options={[
          { value: 'draft', label: '草稿' },
          { value: 'submitted', label: '已提交' },
          { value: 'approved', label: '已批准' },
          { value: 'rejected', label: '已拒绝' },
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

      {/* 创建工时 */}
      <Modal
        title="填写工时"
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        width={800}
        confirmLoading={submitLoading}
        okText="保存"
        cancelText="取消"
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Space style={{ width: '100%' }} size="large">
            <Form.Item name="userId" label="人员" rules={[{ required: true, message: '请选择人员' }]}>
              <Select placeholder="请选择人员" options={users} loading={usersLoading} showSearch optionFilterProp="label" style={{ width: 280 }} />
            </Form.Item>
            <Form.Item name="projectId" label="关联项目">
              <Select placeholder="请选择项目" options={projects} loading={projectsLoading} showSearch optionFilterProp="label" allowClear style={{ width: 280 }} />
            </Form.Item>
            <Form.Item name="weekStartDate" label="周起始日" rules={[{ required: true }]}>
              <DatePicker style={{ width: 140 }} />
            </Form.Item>
          </Space>
          <Form.List name="entries">
            {(fields, { add, remove }) => (
              <>
                {fields.map(({ key, name, ...restField }) => (
                  <Space key={key} style={{ display: 'flex', marginBottom: 8, width: '100%' }} size="small" align="start">
                    <Form.Item {...restField} name={[name, 'workDate']} rules={[{ required: true, message: '日期' }]}>
                      <DatePicker placeholder="日期" />
                    </Form.Item>
                    <Form.Item {...restField} name={[name, 'hours']} rules={[{ required: true, message: '工时' }, { validator: async (_, value) => { if (value === 0 || value === 0.0) throw new Error('工时不能为0'); } }]}>
                      <InputNumber placeholder="工时" min={0.5} max={24} step={0.5} style={{ width: 80 }} />
                    </Form.Item>
                    <Form.Item {...restField} name={[name, 'workType']} rules={[{ required: true, message: '类型' }]}>
                      <Select placeholder="类型" style={{ width: 120 }} options={workTypeOptions} />
                    </Form.Item>
                    <Form.Item {...restField} name={[name, 'description']}>
                      <Input placeholder="说明" style={{ width: 140 }} />
                    </Form.Item>
                    <Form.Item {...restField} name={[name, 'isBillable']}>
                      <Select placeholder="计费" style={{ width: 80 }} options={[{ value: true, label: '是' }, { value: false, label: '否' }]} />
                    </Form.Item>
                    <Button type="link" danger onClick={() => remove(name)} style={{ marginTop: 4 }}>删除</Button>
                  </Space>
                ))}
                <Button type="dashed" onClick={() => add()} block icon={<PlusOutlined />}>添加工作日</Button>
              </>
            )}
          </Form.List>
        </Form>
      </Modal>

      {/* 审批弹窗 */}
      <Modal
        title="审批工时"
        open={approveModalOpen}
        onCancel={() => setApproveModalOpen(false)}
        footer={null}
        width={420}
      >
        <Form form={approveForm} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item name="comment" label="审批意见">
            <Input.TextArea rows={3} placeholder="请填写审批意见" />
          </Form.Item>
          <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
            <Button onClick={() => setApproveModalOpen(false)}>取消</Button>
            <Button danger loading={approveLoading} onClick={() => handleApprove('reject')}>拒绝</Button>
            <Button type="primary" loading={approveLoading} onClick={() => handleApprove('approve')}>批准</Button>
          </Space>
        </Form>
      </Modal>

      {/* 详情抽屉 */}
      <Modal
        title="工时详情"
        open={detailOpen}
        onCancel={() => setDetailOpen(false)}
        footer={null}
        width={640}
      >
        {selectedTimesheet && (
          <Table
            rowKey={(_, i) => i?.toString() || ''}
            dataSource={selectedTimesheet.entries || []}
            pagination={false}
            size="small"
            columns={[
              { title: '日期', dataIndex: 'workDate', render: (v: string) => dayjs(v).format('YYYY-MM-DD') },
              { title: '工时(h)', dataIndex: 'hours' },
              { title: '工作类型', dataIndex: 'workType', render: (v: string) => workTypeOptions.find(o => o.value === v)?.label || v },
              { title: '说明', dataIndex: 'description' },
              { title: '计费', dataIndex: 'isBillable', render: (v: boolean) => v ? <Tag color="green">是</Tag> : <Tag>否</Tag> },
            ]}
          />
        )}
      </Modal>
    </div>
  );
};

export default TimesheetPage;
