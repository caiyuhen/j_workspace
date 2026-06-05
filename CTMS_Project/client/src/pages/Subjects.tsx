import React, { useState, useEffect, useCallback } from 'react';
import {  Table, Modal, Form, Input, Select, Space, Button, Drawer, Descriptions, DatePicker , App } from 'antd';
import { EditOutlined, EyeOutlined, CalendarOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import PageHeader from '@/components/PageHeader';
import StatusTag from '@/components/StatusTag';
import { subjectApi } from '@/api/subject';
import { projectApi } from '@/api/project';
import type { Subject, CreateSubjectParams, Visit, CreateVisitParams } from '@/types';

const enrollmentOptions = [
  { value: 'screening', label: '筛选中' },
  { value: 'enrolled', label: '已入组' },
  { value: 'randomized', label: '已随机' },
  { value: 'ongoing', label: '进行中' },
  { value: 'completed', label: '已完成' },
  { value: 'discontinued', label: '退出' },
  { value: 'withdrawn', label: '撤回' },
];

const SubjectsPage: React.FC = () => {
  const { message } = App.useApp();
  const [data, setData] = useState<Subject[]>([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({ page: 1, pageSize: 10, total: 0 });
  const [keyword, setKeyword] = useState('');
  const [statusFilter, setStatusFilter] = useState<string | undefined>(undefined);

  // 新建/编辑弹窗
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Subject | null>(null);
  const [form] = Form.useForm();
  const [submitLoading, setSubmitLoading] = useState(false);

  // 详情抽屉
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [selectedSubject, setSelectedSubject] = useState<Subject | null>(null);
  const [visits, setVisits] = useState<Visit[]>([]);
  const [visitsLoading, setVisitsLoading] = useState(false);

  // 新建访视
  const [visitForm] = Form.useForm();
  const [visitModalOpen, setVisitModalOpen] = useState(false);

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
      const res = await subjectApi.list({ page, pageSize, keyword, status: statusFilter });
      setData(res?.list || []);
      setPagination({ page: res?.page || 1, pageSize: res?.pageSize || 10, total: res?.total || 0 });
    } catch {
      message.error('加载受试者列表失败');
    } finally {
      setLoading(false);
    }
  }, [keyword, statusFilter]);

  useEffect(() => {
    fetchData();
    fetchProjects();
  }, [fetchData, fetchProjects]);

  const handleCreate = () => {
    setEditing(null);
    form.resetFields();
    setModalOpen(true);
  };

  const handleEdit = (record: Subject) => {
    setEditing(record);
    form.setFieldsValue(record);
    setModalOpen(true);
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setSubmitLoading(true);
      if (editing) {
        await subjectApi.update(editing.id, values);
        message.success('受试者信息已更新');
      } else {
        await subjectApi.create(values as CreateSubjectParams);
        message.success('受试者创建成功');
      }
      setModalOpen(false);
      fetchData(pagination.page, pagination.pageSize);
    } catch (err: any) {
      if (err.errorFields) return;
      message.error(err.response?.data?.error?.message || '操作失败');
    } finally {
      setSubmitLoading(false);
    }
  };

  const openDetail = async (record: Subject) => {
    setSelectedSubject(record);
    setDrawerOpen(true);
    setVisitsLoading(true);
    try {
      const res = await subjectApi.getVisits(record.id);
      setVisits((res as any)?.data || (Array.isArray(res) ? res : []));
    } catch {
      message.error('加载访视失败');
    } finally {
      setVisitsLoading(false);
    }
  };

  const handleAddVisit = async () => {
    try {
      const values = await visitForm.validateFields();
      await subjectApi.createVisit(selectedSubject!.id, {
        ...values,
        plannedDate: values.plannedDate.toISOString() } as CreateVisitParams);
      message.success('访视已添加');
      setVisitModalOpen(false);
      visitForm.resetFields();
      openDetail(selectedSubject!);
    } catch (err: any) {
      if (err.errorFields) return;
      message.error('添加失败');
    }
  };

  const columns = [
    { title: '受试者编号', dataIndex: 'subjectCode', key: 'subjectCode', width: 160 },
    { title: '筛选号', dataIndex: 'screeningNumber', key: 'screeningNumber', width: 130 },
    { title: '随机号', dataIndex: 'randomizationNumber', key: 'randomizationNumber', width: 130 },
    {
      title: '入组状态', dataIndex: 'enrollmentStatus', key: 'enrollmentStatus', width: 120,
      render: (v: string) => <StatusTag status={v} category="enrollment" /> },
    { title: '创建时间', dataIndex: 'createdAt', key: 'createdAt', width: 170, render: (v: string) => v ? dayjs(v).format('YYYY-MM-DD HH:mm') : '-' },
    {
      title: '操作', key: 'actions', width: 160, fixed: 'right' as const,
      render: (_: any, record: Subject) => (
        <Space>
          <Button type="link" size="small" icon={<EyeOutlined />} onClick={() => openDetail(record)}>详情</Button>
          <Button type="link" size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)}>编辑</Button>
        </Space>
      ) },
  ];

  return (
    <div>
      <PageHeader
        title="受试者管理"
        subtitle="受试者入组、随机化和知情同意管理"
        showCreate
        onCreateClick={handleCreate}
        onSearch={setKeyword}
        searchPlaceholder="搜索受试者编号"
      >
        <Select
          placeholder="入组状态"
          allowClear
          style={{ width: 130 }}
          onChange={setStatusFilter}
          options={enrollmentOptions}
          value={statusFilter}
        />
      </PageHeader>

      <Table
        rowKey="id"
        columns={columns}
        dataSource={data}
        loading={loading}
        scroll={{ x: 800 }}
        pagination={{
          current: pagination.page,
          pageSize: pagination.pageSize,
          total: pagination.total,
          showSizeChanger: true,
          showTotal: (total) => `共 ${total} 条`,
          onChange: (page, pageSize) => fetchData(page, pageSize) }}
      />

      {/* 新建/编辑受试者 */}
      <Modal
        title={editing ? '编辑受试者' : '新建受试者'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        width={560}
        confirmLoading={submitLoading}
        okText="保存"
        cancelText="取消"
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item name="projectId" label="项目 ID" rules={[{ required: true, message: '请选择项目' }]}>
            <Select placeholder="请选择项目" options={projects} loading={projectsLoading} showSearch optionFilterProp="label" />
          </Form.Item>
          <Space style={{ width: '100%' }} size="large">
            <Form.Item name="subjectCode" label="受试者编号" rules={[{ required: true, message: '请输入编号' }]}>
              <Input placeholder="如 SUBJ-001" style={{ width: 220 }} />
            </Form.Item>
            <Form.Item name="screeningNumber" label="筛选号">
              <Input placeholder="筛选号" style={{ width: 220 }} />
            </Form.Item>
          </Space>
          <Space style={{ width: '100%' }} size="large">
            <Form.Item name="siteId" label="中心 ID">
              <Input placeholder="中心 UUID" style={{ width: 220 }} />
            </Form.Item>
            <Form.Item name="enrollmentStatus" label="入组状态">
              <Select placeholder="请选择" style={{ width: 220 }} options={enrollmentOptions} />
            </Form.Item>
          </Space>
          {editing && (
            <>
              <Form.Item name="randomizationNumber" label="随机号">
                <Input placeholder="随机号" />
              </Form.Item>
              <Form.Item name="discontinuationReason" label="退出原因">
                <Input.TextArea rows={2} placeholder="退出或撤回原因" />
              </Form.Item>
            </>
          )}
        </Form>
      </Modal>

      {/* 受试者详情抽屉 */}
      <Drawer
        title={`受试者详情 - ${selectedSubject?.subjectCode || ''}`}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        size="large"
      >
        {selectedSubject && (
          <>
            <Descriptions bordered size="small" column={2}>
              <Descriptions.Item label="受试者编号">{selectedSubject.subjectCode}</Descriptions.Item>
              <Descriptions.Item label="筛选号">{selectedSubject.screeningNumber || '-'}</Descriptions.Item>
              <Descriptions.Item label="随机号">{selectedSubject.randomizationNumber || '-'}</Descriptions.Item>
              <Descriptions.Item label="入组状态">
                <StatusTag status={selectedSubject.enrollmentStatus} category="enrollment" />
              </Descriptions.Item>
              <Descriptions.Item label="创建时间">{dayjs(selectedSubject.createdAt).format('YYYY-MM-DD HH:mm')}</Descriptions.Item>
              <Descriptions.Item label="更新时间">{dayjs(selectedSubject.updatedAt).format('YYYY-MM-DD HH:mm')}</Descriptions.Item>
              {selectedSubject.discontinuationReason && (
                <Descriptions.Item label="退出原因" span={2}>{selectedSubject.discontinuationReason}</Descriptions.Item>
              )}
            </Descriptions>

            <div style={{ marginTop: 24, marginBottom: 12, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontWeight: 600 }}>访视记录</span>
              <Button type="primary" size="small" icon={<CalendarOutlined />} onClick={() => { visitForm.resetFields(); setVisitModalOpen(true); }}>
                新增访视
              </Button>
            </div>
            <Table
              rowKey="id"
              dataSource={visits}
              loading={visitsLoading}
              pagination={false}
              size="small"
              columns={[
                { title: '访视编码', dataIndex: 'visitCode', key: 'visitCode', width: 100 },
                { title: '访视名称', dataIndex: 'visitName', key: 'visitName' },
                { title: '计划日期', dataIndex: 'plannedDate', key: 'plannedDate', width: 120, render: (v: string) => dayjs(v).format('YYYY-MM-DD') },
                { title: '实际日期', dataIndex: 'actualDate', key: 'actualDate', width: 120, render: (v: string) => v ? dayjs(v).format('YYYY-MM-DD') : '-' },
              ]}
            />
            {visits.length === 0 && !visitsLoading && (
              <div style={{ textAlign: 'center', color: '#999', padding: 24 }}>暂无访视记录</div>
            )}
          </>
        )}

        {/* 新增访视弹窗 */}
        <Modal
          title="新增访视"
          open={visitModalOpen}
          onOk={handleAddVisit}
          onCancel={() => setVisitModalOpen(false)}
          okText="添加"
          cancelText="取消"
        >
          <Form form={visitForm} layout="vertical" style={{ marginTop: 16 }}>
            <Form.Item name="visitCode" label="访视编码" rules={[{ required: true }]}>
              <Input placeholder="如 V01" />
            </Form.Item>
            <Form.Item name="visitName" label="访视名称" rules={[{ required: true }]}>
              <Input placeholder="如 筛选访视" />
            </Form.Item>
            <Form.Item name="plannedDate" label="计划日期" rules={[{ required: true }]}>
              <DatePicker style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="siteId" label="中心 ID">
              <Input placeholder="中心 UUID（可选）" />
            </Form.Item>
          </Form>
        </Modal>
      </Drawer>
    </div>
  );
};

export default SubjectsPage;
