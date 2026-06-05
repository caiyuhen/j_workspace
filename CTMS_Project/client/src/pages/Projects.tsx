import React, { useState, useEffect, useCallback } from 'react';
import { Table, Modal, Form, Input, Select, InputNumber, DatePicker, Space, Button, Popconfirm, Tag, Timeline, App } from 'antd';
import { EditOutlined, DeleteOutlined, PlusOutlined, UnorderedListOutlined, MinusCircleOutlined, EnvironmentOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import PageHeader from '@/components/PageHeader';
import StatusTag from '@/components/StatusTag';
import ConfirmModal from '@/components/ConfirmModal';
import { projectApi } from '@/api/project';
import { settingsApi } from '@/api/settings';
import type { Project, CreateProjectParams, Milestone } from '@/types';

const { TextArea } = Input;

const studyTypeOptions = [
  { value: 'interventional', label: '干预性研究' },
  { value: 'observational', label: '观察性研究' },
  { value: 'post_marketing', label: '上市后研究' },
];

const phaseOptions = [
  { value: 'phase_i', label: 'I 期' },
  { value: 'phase_ii', label: 'II 期' },
  { value: 'phase_iii', label: 'III 期' },
  { value: 'phase_iv', label: 'IV 期' },
  { value: 'ind_enabling', label: 'IND 支持' },
  { value: 'other', label: '其他' },
];

const blindTypeOptions = [
  { value: 'open', label: '开放' },
  { value: 'single_blind', label: '单盲' },
  { value: 'double_blind', label: '双盲' },
  { value: 'triple_blind', label: '三盲' },
];

const statusOptions = [
  { value: 'planning', label: '计划中' },
  { value: 'recruiting', label: '招募中' },
  { value: 'active', label: '进行中' },
  { value: 'paused', label: '暂停' },
  { value: 'completed', label: '已完成' },
  { value: 'terminated', label: '终止' },
];

const ProjectsPage: React.FC = () => {
  const { message } = App.useApp();
  const [data, setData] = useState<Project[]>([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({ page: 1, pageSize: 10, total: 0 });
  const [keyword, setKeyword] = useState('');
  const [statusFilter, setStatusFilter] = useState<string | undefined>(undefined);

  // 弹窗状态
  const [modalOpen, setModalOpen] = useState(false);
  const [editingProject, setEditingProject] = useState<Project | null>(null);
  const [form] = Form.useForm();
  const [submitLoading, setSubmitLoading] = useState(false);

  // 里程碑弹窗
  const [milestoneOpen, setMilestoneOpen] = useState(false);
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [milestones, setMilestones] = useState<Milestone[]>([]);
  const [milestoneForm] = Form.useForm();
  const [milestoneLoading, setMilestoneLoading] = useState(false);

  // 删除确认
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  // 机构字典
  const [siteOrgs, setSiteOrgs] = useState<{label: string, value: string, org: any}[]>([]);

  const fetchSiteOrgs = useCallback(async () => {
    try {
      const res = await settingsApi.listOrganizations({ page: 1, pageSize: 1000 });
      const orgs = (res?.list || []).filter((o: any) => o.orgType === 'site' || o.type === 'site');
      setSiteOrgs(orgs.map((o: any) => ({
        label: o.orgName || o.name,
        value: o.orgName || o.name,
        org: o
      })));
    } catch {
      // ignore
    }
  }, []);

  const fetchData = useCallback(async (page = 1, pageSize = 10) => {
    setLoading(true);
    try {
      const res = await projectApi.list({ page, pageSize, keyword, status: statusFilter });
      setData(res?.list || []);
      setPagination({ page: res?.page || 1, pageSize: res?.pageSize || 10, total: res?.total || 0 });
    } catch (err: any) {
      message.error('加载项目列表失败');
    } finally {
      setLoading(false);
    }
  }, [keyword, statusFilter]);

  useEffect(() => {
    fetchData();
    fetchSiteOrgs();
  }, [fetchData, fetchSiteOrgs]);

  const handleSearch = (value: string) => {
    setKeyword(value);
  };

  const handleCreate = () => {
    setEditingProject(null);
    form.resetFields();
    // Auto-generate project code
    const randomSuffix = Math.floor(Math.random() * 1000).toString().padStart(3, '0');
    form.setFieldsValue({ projectCode: `PRJ-${dayjs().format('YYYY')}-${randomSuffix}` });
    setModalOpen(true);
  };

  const handleEdit = async (record: Project) => {
    setEditingProject(record);
    form.setFieldsValue({
      ...record,
      startDate: record.startDate ? dayjs(record.startDate) : undefined,
      endDate: record.endDate ? dayjs(record.endDate) : undefined });
    setModalOpen(true);
    // 加载项目完整信息以获取中心
    try {
      const res = await projectApi.getById(record.id);
      setEditingProject(res);
    } catch {
      // 忽略
    }
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setSubmitLoading(true);
      const params: CreateProjectParams = {
        ...values,
        startDate: values.startDate?.toISOString(),
        endDate: values.endDate?.toISOString() };
      if (editingProject) {
        await projectApi.update(editingProject.id, params);
        message.success('项目更新成功');
      } else {
        await projectApi.create(params);
        message.success('项目创建成功');
      }
      setModalOpen(false);
      fetchData(1, pagination.pageSize);
    } catch (err: any) {
      if (err.errorFields) return;
      message.error(err.response?.data?.error?.message || '操作失败');
    } finally {
      setSubmitLoading(false);
    }
  };

  const handleDeleteConfirm = () => {
    setDeleteLoading(true);
    projectApi.delete(deleteId!)
      .then(() => {
        message.success('项目已删除');
        setDeleteOpen(false);
        fetchData(pagination.page, pagination.pageSize);
      })
      .catch(() => message.error('删除失败'))
      .finally(() => setDeleteLoading(false));
  };

  // 里程碑
  const openMilestones = async (projectId: string) => {
    setSelectedProjectId(projectId);
    setMilestoneOpen(true);
    setMilestoneLoading(true);
    try {
      const res = await projectApi.getMilestones(projectId);
      setMilestones((res as any)?.data || (Array.isArray(res) ? res : []));
    } catch {
      message.error('加载里程碑失败');
    } finally {
      setMilestoneLoading(false);
    }
  };

  const handleAddMilestone = async () => {
    try {
      const values = await milestoneForm.validateFields();
      await projectApi.createMilestone(selectedProjectId!, {
        ...values,
        plannedDate: values.plannedDate.toISOString() });
      message.success('里程碑已添加');
      milestoneForm.resetFields();
      openMilestones(selectedProjectId!);
    } catch (err: any) {
      if (err.errorFields) return;
      message.error('添加失败');
    }
  };

  const columns = [
    { title: '项目编号', dataIndex: 'projectCode', key: 'projectCode', width: 140 },
    { title: '项目名称', dataIndex: 'projectName', key: 'projectName', ellipsis: true },
    {
      title: '研究类型', dataIndex: 'studyType', key: 'studyType', width: 120,
      render: (v: string) => studyTypeOptions.find(o => o.value === v)?.label || v },
    {
      title: '阶段', dataIndex: 'phase', key: 'phase', width: 80,
      render: (v: string) => phaseOptions.find(o => o.value === v)?.label || v },
    { title: '计划样本量', dataIndex: 'sampleSize', key: 'sampleSize', width: 100 },
    {
      title: '总预算', dataIndex: 'totalBudget', key: 'totalBudget', width: 120,
      render: (v: number) => v ? `¥${v.toLocaleString()}` : '-' },
    {
      title: '状态', dataIndex: 'status', key: 'status', width: 100,
      render: (v: string) => <StatusTag status={v} category="project" /> },
    { title: '创建时间', dataIndex: 'createdAt', key: 'createdAt', width: 170, render: (v: string) => v ? dayjs(v).format('YYYY-MM-DD HH:mm') : '-' },
    {
      title: '操作', key: 'actions', width: 200, fixed: 'right' as const,
      render: (_: any, record: Project) => (
        <Space>
          <Button type="link" size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)}>编辑</Button>
          <Button type="link" size="small" icon={<UnorderedListOutlined />} onClick={() => openMilestones(record.id)}>里程碑</Button>
          <Popconfirm title="确定删除该项目？" onConfirm={() => { setDeleteId(record.id); setDeleteOpen(true); }} okText="删除" cancelText="取消" okButtonProps={{ danger: true }}>
            <Button type="link" size="small" danger icon={<DeleteOutlined />}>删除</Button>
          </Popconfirm>
        </Space>
      ) },
  ];

  const milestoneTypeLabels: Record<string, string> = {
    project_start: '项目启动', site_init: '中心启动', first_patient: '首例入组',
    last_patient: '末例入组', db_lock: '数据库锁定', study_close: '研究关闭', other: '其他' };

  return (
    <div>
      <PageHeader
        title="项目管理"
        subtitle="临床试验项目的创建、编辑、监控和全生命周期管理"
        showCreate
        onCreateClick={handleCreate}
        onSearch={handleSearch}
        searchPlaceholder="搜索项目编号或名称"
      >
        <Select
          placeholder="项目状态"
          allowClear
          style={{ width: 130 }}
          onChange={setStatusFilter}
          options={statusOptions}
          value={statusFilter}
        />
      </PageHeader>

      <Table
        rowKey="id"
        columns={columns}
        dataSource={data}
        loading={loading}
        scroll={{ x: 1200 }}
        pagination={{
          current: pagination.page,
          pageSize: pagination.pageSize,
          total: pagination.total,
          showSizeChanger: true,
          showTotal: (total) => `共 ${total} 条`,
          onChange: (page, pageSize) => fetchData(page, pageSize) }}
      />

      {/* 新建/编辑项目弹窗 */}
      <Modal
        title={editingProject ? '编辑项目' : '新建项目'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        width={720}
        confirmLoading={submitLoading}
        okText="保存"
        cancelText="取消"
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Space style={{ width: '100%' }} size="large" align="start">
            <Form.Item name="projectCode" label="项目编号" rules={[{ required: true, message: '请输入项目编号' }]}>
              <Input 
                placeholder="如 PRJ-2026-001" 
                style={{ width: 180 }} 
                disabled
                suffix={
                  !editingProject && <a onClick={() => {
                    const randomSuffix = Math.floor(Math.random() * 1000).toString().padStart(3, '0');
                    form.setFieldsValue({ projectCode: `PRJ-${dayjs().format('YYYY')}-${randomSuffix}` });
                  }}>自动生成</a>
                }
              />
            </Form.Item>
            <Form.Item name="projectName" label="项目名称" rules={[{ required: true, message: '请输入项目名称' }]}>
              <Input placeholder="项目全称" style={{ width: 380 }} />
            </Form.Item>
          </Space>
          <Space style={{ width: '100%' }} size="large">
            <Form.Item name="studyType" label="研究类型">
              <Select placeholder="请选择" style={{ width: 220 }} options={studyTypeOptions} />
            </Form.Item>
            <Form.Item name="phase" label="研究阶段">
              <Select placeholder="请选择" style={{ width: 220 }} options={phaseOptions} />
            </Form.Item>
            <Form.Item name="blindType" label="盲法">
              <Select placeholder="请选择" style={{ width: 140 }} options={blindTypeOptions} />
            </Form.Item>
          </Space>
          <Space style={{ width: '100%' }} size="large">
            <Form.Item name="sampleSize" label="计划样本量">
              <InputNumber placeholder="例数" min={1} style={{ width: 140 }} />
            </Form.Item>
            <Form.Item name="totalBudget" label="总预算 (¥)">
              <InputNumber placeholder="金额" min={0} step={10000} style={{ width: 140 }} />
            </Form.Item>
          </Space>
          <Space style={{ width: '100%' }} size="large">
            <Form.Item name="startDate" label="计划开始日期">
              <DatePicker style={{ width: 140 }} />
            </Form.Item>
            <Form.Item name="endDate" label="计划结束日期">
              <DatePicker style={{ width: 140 }} />
            </Form.Item>
            {editingProject && (
              <Form.Item name="status" label="项目状态">
                <Select placeholder="请选择" style={{ width: 140 }} options={statusOptions} />
              </Form.Item>
            )}
          </Space>
          <Form.Item name="therapeuticArea" label="治疗领域">
            <Input placeholder="如 肿瘤学、心血管" />
          </Form.Item>
          <Form.Item name="description" label="项目描述">
            <TextArea rows={3} placeholder="项目简介" />
          </Form.Item>

          <div style={{ marginTop: 24 }}>
            {editingProject && editingProject.sites && editingProject.sites.length > 0 && (
              <div style={{ marginBottom: 16 }}>
                <div style={{ marginBottom: 8, fontWeight: 500 }}>已有研究中心</div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                  {editingProject.sites.map((s: any) => (
                    <Tag key={s.id} color="blue">{s.siteCode} - {s.siteName}</Tag>
                  ))}
                </div>
              </div>
            )}
            <div style={{ marginBottom: 8, fontWeight: 500 }}>
              {editingProject ? '新增研究中心（可选）' : '初始研究中心（可选）'}
            </div>
            <Form.List name="sites">
              {(fields, { add, remove }) => (
                <>
                  {fields.map(({ key, name, ...restField }) => (
                    <Space key={key} style={{ display: 'flex', marginBottom: 8 }} align="baseline">
                      <Form.Item
                        {...restField}
                        name={[name, 'siteCode']}
                        rules={[{ required: true, message: '请输入中心编号' }]}
                      >
                        <Input placeholder="中心编号" style={{ width: 140 }} disabled />
                      </Form.Item>
                      <Form.Item
                        {...restField}
                        name={[name, 'siteName']}
                        rules={[{ required: true, message: '请输入中心名称' }]}
                      >
                        <Select 
                          placeholder="中心名称" 
                          style={{ width: 180 }}
                          options={siteOrgs}
                          showSearch
                          onChange={(_, option: any) => {
                            if (option && option.org) {
                              const code = option.org.orgCode || option.org.code;
                              if (code) {
                                const sites = form.getFieldValue('sites') || [];
                                sites[name] = { ...sites[name], siteCode: code };
                                form.setFieldsValue({ sites });
                              }
                            }
                          }}
                        />
                      </Form.Item>
                      <Form.Item
                        {...restField}
                        name={[name, 'plannedSampleSize']}
                      >
                        <InputNumber placeholder="计划样本量" min={1} style={{ width: 120 }} />
                      </Form.Item>
                      <MinusCircleOutlined onClick={() => remove(name)} style={{ color: '#ff4d4f', marginLeft: 8 }} />
                    </Space>
                  ))}
                  <Form.Item>
                    <Button type="dashed" onClick={() => {
                      const randomSuffix = Math.floor(Math.random() * 1000).toString().padStart(3, '0');
                      add({ siteCode: `SITE-${dayjs().format('YYYY')}-${randomSuffix}` });
                    }} block icon={<PlusOutlined />}>
                      添加研究中心
                    </Button>
                  </Form.Item>
                </>
              )}
            </Form.List>
          </div>
        </Form>
      </Modal>

      {/* 里程碑弹窗 */}
      <Modal
        title="项目里程碑"
        open={milestoneOpen}
        onCancel={() => setMilestoneOpen(false)}
        footer={null}
        width={640}
      >
        <Form form={milestoneForm} layout="inline" style={{ marginBottom: 16 }}>
          <Form.Item name="milestoneName" rules={[{ required: true, message: '名称' }]}>
            <Input placeholder="里程碑名称" style={{ width: 160 }} />
          </Form.Item>
          <Form.Item name="milestoneType" rules={[{ required: true, message: '类型' }]}>
            <Select placeholder="类型" style={{ width: 130 }} options={Object.entries(milestoneTypeLabels).map(([k, v]) => ({ value: k, label: v }))} />
          </Form.Item>
          <Form.Item name="plannedDate" rules={[{ required: true, message: '日期' }]}>
            <DatePicker placeholder="计划日期" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" icon={<PlusOutlined />} onClick={handleAddMilestone}>添加</Button>
          </Form.Item>
        </Form>
        <Timeline
          items={milestones.map((m) => ({
            color: m.status === 'completed' ? 'green' : m.status === 'overdue' ? 'red' : 'blue',
            children: (
              <div>
                <div><strong>{m.milestoneName}</strong> <Tag>{milestoneTypeLabels[m.milestoneType] || m.milestoneType}</Tag></div>
                <div style={{ color: '#999', fontSize: 12 }}>
                  计划: {dayjs(m.plannedDate).format('YYYY-MM-DD')}
                  {m.actualDate && ` | 实际: ${dayjs(m.actualDate).format('YYYY-MM-DD')}`}
                  {m.status && <span style={{ marginLeft: 8 }}><StatusTag status={m.status} category="site" /></span>}
                </div>
              </div>
            ) }))}
        />
        {milestoneLoading && <div style={{ textAlign: 'center', color: '#999' }}>加载中...</div>}
        {milestones.length === 0 && !milestoneLoading && <div style={{ textAlign: 'center', color: '#999', padding: 24 }}>暂无里程碑</div>}
      </Modal>

      {/* 删除确认 */}
      <ConfirmModal
        open={deleteOpen}
        content="此操作将永久删除该项目及其所有关联数据，确定继续？"
        onOk={handleDeleteConfirm}
        onCancel={() => setDeleteOpen(false)}
        okText="确认删除"
        loading={deleteLoading}
      />
    </div>
  );
};

export default ProjectsPage;
