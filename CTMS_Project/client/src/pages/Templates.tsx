import React, { useState, useEffect, useCallback } from 'react';
import {  Table, Modal, Form, Input, Select, Space, Button, Tag, Popconfirm, Switch , App } from 'antd';
import { EditOutlined, DeleteOutlined, SendOutlined, CopyOutlined, StopOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import PageHeader from '@/components/PageHeader';
import StatusTag from '@/components/StatusTag';
import { templateApi } from '@/api/template';
import { projectApi } from '@/api/project';
import type { EdcTemplate, CreateTemplateParams } from '@/types';

const { TextArea } = Input;

const templateTypeOptions = [
  { value: 'crf', label: 'CRF 表单' },
  { value: 'ae_report', label: 'AE 报告' },
  { value: 'lab_result', label: '检验结果' },
  { value: 'visit_note', label: '访视记录' },
  { value: 'consent', label: '知情同意' },
  { value: 'other', label: '其他' },
];

const TemplatesPage: React.FC = () => {
  const { message } = App.useApp();
  const [data, setData] = useState<EdcTemplate[]>([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({ page: 1, pageSize: 10, total: 0 });
  const [keyword, setKeyword] = useState('');
  const [typeFilter, setTypeFilter] = useState<string | undefined>(undefined);
  const [statusFilter, setStatusFilter] = useState<string | undefined>(undefined);

  // 创建/编辑弹窗
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<EdcTemplate | null>(null);
  const [form] = Form.useForm();
  const [submitLoading, setSubmitLoading] = useState(false);

  // 克隆弹窗
  const [cloneModalOpen, setCloneModalOpen] = useState(false);
  const [cloneForm] = Form.useForm();
  const [cloneLoading, setCloneLoading] = useState(false);
  const [cloningId, setCloningId] = useState<string | null>(null);

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
      const res = await templateApi.list({ page, pageSize, keyword, templateType: typeFilter, status: statusFilter });
      setData(res?.list || []);
      setPagination({ page: res?.page || 1, pageSize: res?.pageSize || 10, total: res?.total || 0 });
    } catch {
      message.error('加载模板列表失败');
    } finally {
      setLoading(false);
    }
  }, [keyword, typeFilter, statusFilter]);

  useEffect(() => {
    fetchData();
    fetchProjects();
  }, [fetchData, fetchProjects]);

  const handleCreate = () => {
    setEditing(null);
    form.resetFields();
    setModalOpen(true);
  };

  const handleEdit = (record: EdcTemplate) => {
    setEditing(record);
    form.setFieldsValue(record);
    setModalOpen(true);
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setSubmitLoading(true);
      if (editing) {
        await templateApi.update(editing.id, values);
        message.success('模板更新成功');
      } else {
        await templateApi.create(values as CreateTemplateParams);
        message.success('模板创建成功');
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

  const handlePublish = async (id: string) => {
    try {
      await templateApi.publish(id);
      message.success('模板已发布');
      fetchData(pagination.page, pagination.pageSize);
    } catch {
      message.error('发布失败');
    }
  };

  const handleDeprecate = async (id: string) => {
    try {
      await templateApi.deprecate(id);
      message.success('模板已停用');
      fetchData(pagination.page, pagination.pageSize);
    } catch {
      message.error('停用失败');
    }
  };

  const handleDelete = async (id: string) => {
    try {
      // 先停用再删除
      await templateApi.deprecate(id);
      message.info('模板已停用（请通过后端管理删除）');
      fetchData(pagination.page, pagination.pageSize);
    } catch {
      message.error('操作失败');
    }
  };

  const openClone = (record: EdcTemplate) => {
    setCloningId(record.id);
    cloneForm.resetFields();
    cloneForm.setFieldsValue({
      newTemplateCode: `${record.templateCode}-copy`,
      newTemplateName: `${record.templateName} (副本)`,
      newVersion: record.version });
    setCloneModalOpen(true);
  };

  const handleClone = async () => {
    try {
      const values = await cloneForm.validateFields();
      setCloneLoading(true);
      await templateApi.clone(cloningId!, values);
      message.success('模板已克隆');
      setCloneModalOpen(false);
      fetchData(pagination.page, pagination.pageSize);
    } catch (err: any) {
      if (err.errorFields) return;
      message.error('克隆失败');
    } finally {
      setCloneLoading(false);
    }
  };

  const columns = [
    { title: '模板编号', dataIndex: 'templateCode', key: 'templateCode', width: 150 },
    { title: '模板名称', dataIndex: 'templateName', key: 'templateName', ellipsis: true },
    {
      title: '类型', dataIndex: 'templateType', key: 'templateType', width: 110,
      render: (v: string) => templateTypeOptions.find(o => o.value === v)?.label || v },
<<<<<<< HEAD
<<<<<<< HEAD
    { title: 'CDISC域', dataIndex: 'cdiscDomain', key: 'cdiscDomain', width: 100, render: (v: string) => v ? <Tag color="cyan">{v}</Tag> : '-' },
=======
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
=======
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
    { title: '版本', dataIndex: 'version', key: 'version', width: 80 },
    {
      title: '状态', dataIndex: 'status', key: 'status', width: 100,
      render: (v: string) => <StatusTag status={v} category="template" /> },
    { title: '共享', dataIndex: 'isShared', key: 'isShared', width: 70, render: (v: boolean) => v ? <Tag color="blue">是</Tag> : '-' },
    { title: '系统', dataIndex: 'isSystemTemplate', key: 'isSystemTemplate', width: 70, render: (v: boolean) => v ? <Tag color="purple">是</Tag> : '-' },
    { title: '更新时间', dataIndex: 'updatedAt', key: 'updatedAt', width: 170, render: (v: string) => dayjs(v).format('YYYY-MM-DD HH:mm') },
    {
      title: '操作', key: 'actions', width: 240, fixed: 'right' as const,
      render: (_: any, record: EdcTemplate) => (
        <Space size="small">
          <Button type="link" size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)}>编辑</Button>
          {record.status === 'draft' && (
            <Button type="link" size="small" icon={<SendOutlined />} style={{ color: '#52c41a' }} onClick={() => handlePublish(record.id)}>发布</Button>
          )}
          {record.status === 'published' && (
            <Button type="link" size="small" icon={<StopOutlined />} onClick={() => handleDeprecate(record.id)}>停用</Button>
          )}
          <Button type="link" size="small" icon={<CopyOutlined />} onClick={() => openClone(record)}>克隆</Button>
          {record.status === 'draft' && (
            <Popconfirm title="确定删除？" onConfirm={() => handleDelete(record.id)}>
              <Button type="link" size="small" danger icon={<DeleteOutlined />}>删除</Button>
            </Popconfirm>
          )}
        </Space>
      ) },
  ];

  return (
    <div>
      <PageHeader
        title="CRF 模板库"
        subtitle="自定义 CRF 表单模板的设计与管理"
        showCreate
        onCreateClick={handleCreate}
        onSearch={setKeyword}
        searchPlaceholder="搜索模板编号或名称"
      >
        <Select placeholder="模板类型" allowClear style={{ width: 120 }} onChange={setTypeFilter} options={templateTypeOptions} value={typeFilter} />
        <Select placeholder="状态" allowClear style={{ width: 110 }} onChange={setStatusFilter} options={[
          { value: 'draft', label: '草稿' },
          { value: 'published', label: '已发布' },
          { value: 'deprecated', label: '已停用' },
        ]} value={statusFilter} />
      </PageHeader>

      <Table
        rowKey="id"
        columns={columns}
        dataSource={data}
        loading={loading}
        scroll={{ x: 1300 }}
        pagination={{
          current: pagination.page,
          pageSize: pagination.pageSize,
          total: pagination.total,
          showSizeChanger: true,
          showTotal: (total) => `共 ${total} 条`,
          onChange: (page, pageSize) => fetchData(page, pageSize) }}
      />

      {/* 创建/编辑模板 */}
      <Modal
        title={editing ? '编辑模板' : '新建模板'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        width={640}
        confirmLoading={submitLoading}
        okText="保存"
        cancelText="取消"
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Space style={{ width: '100%' }} size="large">
            <Form.Item name="templateCode" label="模板编号" rules={[{ required: true }]}>
              <Input placeholder="如 CRF-DM-001" style={{ width: 250 }} />
            </Form.Item>
            <Form.Item name="templateName" label="模板名称" rules={[{ required: true }]}>
              <Input placeholder="模板名称" style={{ width: 320 }} />
            </Form.Item>
          </Space>
          <Space style={{ width: '100%' }} size="large">
            <Form.Item name="templateType" label="模板类型" rules={[{ required: true }]}>
              <Select style={{ width: 200 }} options={templateTypeOptions} />
            </Form.Item>
            <Form.Item name="version" label="版本" rules={[{ required: true }]}>
              <Input placeholder="如 1.0" style={{ width: 200 }} />
            </Form.Item>
          </Space>
<<<<<<< HEAD
<<<<<<< HEAD
          <Form.Item name="cdiscDomain" label="CDISC/CDASH域">
            <Select placeholder="请选择CDISC域" allowClear>
              <Select.Option value="DM">Demographics (DM)</Select.Option>
              <Select.Option value="AE">Adverse Events (AE)</Select.Option>
              <Select.Option value="VS">Vital Signs (VS)</Select.Option>
              <Select.Option value="LB">Laboratory (LB)</Select.Option>
              <Select.Option value="CM">Concomitant Medications (CM)</Select.Option>
              <Select.Option value="DS">Disposition (DS)</Select.Option>
              <Select.Option value="IE">Inclusion/Exclusion (IE)</Select.Option>
            </Select>
          </Form.Item>
=======
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
=======
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
          <Form.Item name="projectId" label="适用项目">
            <Select placeholder="请选择项目" options={projects} loading={projectsLoading} showSearch optionFilterProp="label" allowClear />
          </Form.Item>
          <Form.Item name="description" label="模板描述">
            <TextArea rows={2} placeholder="模板用途说明" />
          </Form.Item>
          <Space style={{ width: '100%' }} size="large">
            <Form.Item name="isShared" label="共享" valuePropName="checked">
              <Switch checkedChildren="是" unCheckedChildren="否" />
            </Form.Item>
            <Form.Item name="isSystemTemplate" label="系统模板" valuePropName="checked">
              <Switch checkedChildren="是" unCheckedChildren="否" />
            </Form.Item>
          </Space>
          {editing && (
            <Form.Item name="status" label="状态">
              <Select options={[
                { value: 'draft', label: '草稿' },
                { value: 'published', label: '已发布' },
                { value: 'deprecated', label: '已停用' },
                { value: 'archived', label: '已归档' },
              ]} />
            </Form.Item>
          )}
          <Form.Item name="templateData" label="模板数据 (JSON)">
            <TextArea rows={4} placeholder='{"fields": [...], "layout": "..."}' />
          </Form.Item>
        </Form>
      </Modal>

      {/* 克隆弹窗 */}
      <Modal
        title="克隆模板"
        open={cloneModalOpen}
        onOk={handleClone}
        onCancel={() => setCloneModalOpen(false)}
        confirmLoading={cloneLoading}
        okText="克隆"
        cancelText="取消"
      >
        <Form form={cloneForm} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item name="newTemplateCode" label="新模板编号" rules={[{ required: true }]}>
            <Input placeholder="新模板编号" />
          </Form.Item>
          <Form.Item name="newTemplateName" label="新模板名称" rules={[{ required: true }]}>
            <Input placeholder="新模板名称" />
          </Form.Item>
          <Form.Item name="newVersion" label="版本">
            <Input placeholder="如 2.0" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default TemplatesPage;
