import React, { useState, useEffect, useCallback } from 'react';
import { Table, Modal, Form, Input, Select, Space, Button, DatePicker, App } from 'antd';
import { EditOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import PageHeader from '@/components/PageHeader';
import StatusTag from '@/components/StatusTag';
import { ethicsApi } from '@/api/ethics';
import { projectApi } from '@/api/project';
import { siteApi } from '@/api/site';

const approvalTypeOptions = [
  { value: 'initial', label: '初始审查' },
  { value: 'amendment', label: '修正案审查' },
  { value: 'follow_up', label: '跟踪审查' },
  { value: 'annual_review', label: '年度审查' },
  { value: 'safety_report', label: '安全性报告' },
];

const approvalStatusOptions = [
  { value: 'pending', label: '待提交' },
  { value: 'under_review', label: '审查中' },
  { value: 'approved', label: '已批准' },
  { value: 'conditionally_approved', label: '附条件批准' },
  { value: 'rejected', label: '未批准' },
  { value: 'withdrawn', label: '已撤回' },
];

const EthicsPage: React.FC = () => {
  const { message } = App.useApp();
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({ page: 1, pageSize: 10, total: 0 });
  const [keyword, setKeyword] = useState('');

  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<any | null>(null);
  const [form] = Form.useForm();
  const [submitLoading, setSubmitLoading] = useState(false);

  const [projects, setProjects] = useState<{label: string, value: string}[]>([]);
  const [sites, setSites] = useState<{label: string, value: string}[]>([]);

  const fetchProjects = useCallback(async () => {
    try {
      const res = await projectApi.list({ page: 1, pageSize: 1000 });
      setProjects((res?.list || []).map((p: any) => ({ label: p.projectName, value: p.id })));
    } catch {}
  }, []);

  const fetchSites = useCallback(async () => {
    try {
      const res = await siteApi.list({ page: 1, pageSize: 1000 });
      setSites((res?.list || []).map((s: any) => ({ label: s.siteName, value: s.id })));
    } catch {}
  }, []);

  const fetchData = useCallback(async (page = 1, pageSize = 10) => {
    setLoading(true);
    try {
      const res = await ethicsApi.list({ page, pageSize, keyword });
      setData(res?.list || []);
      setPagination({ page: res?.page || 1, pageSize: res?.pageSize || 10, total: res?.total || 0 });
    } catch {
      message.error('加载伦理列表失败');
    } finally {
      setLoading(false);
    }
  }, [keyword]);

  useEffect(() => {
    fetchData();
    fetchProjects();
    fetchSites();
  }, [fetchData, fetchProjects, fetchSites]);

  const handleCreate = () => {
    setEditing(null);
    form.resetFields();
    setModalOpen(true);
  };

  const handleEdit = (record: any) => {
    setEditing(record);
    form.setFieldsValue({
      ...record,
      submissionDate: record.submissionDate ? dayjs(record.submissionDate) : null,
      approvalDate: record.approvalDate ? dayjs(record.approvalDate) : null,
      expiryDate: record.expiryDate ? dayjs(record.expiryDate) : null,
    });
    setModalOpen(true);
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setSubmitLoading(true);
      
      const payload = {
        ...values,
        submissionDate: values.submissionDate ? values.submissionDate.format('YYYY-MM-DD') : undefined,
        approvalDate: values.approvalDate ? values.approvalDate.format('YYYY-MM-DD') : undefined,
        expiryDate: values.expiryDate ? values.expiryDate.format('YYYY-MM-DD') : undefined,
      };

      if (editing) {
        await ethicsApi.update(editing.id, payload);
        message.success('更新成功');
      } else {
        await ethicsApi.create(payload);
        message.success('创建成功');
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

  const columns = [
    { title: '伦理委员会', dataIndex: 'ethicsCommittee', key: 'ethicsCommittee' },
    { title: '审查类型', dataIndex: 'approvalType', key: 'approvalType',
      render: (v: string) => approvalTypeOptions.find(o => o.value === v)?.label || v
    },
    { title: '批件号', dataIndex: 'approvalNumber', key: 'approvalNumber' },
    { title: '状态', dataIndex: 'approvalStatus', key: 'approvalStatus',
      render: (v: string) => <StatusTag status={v} category="ethics" />
    },
    { title: '递交日期', dataIndex: 'submissionDate', key: 'submissionDate',
      render: (v: string) => v ? dayjs(v).format('YYYY-MM-DD') : '-'
    },
    { title: '批准日期', dataIndex: 'approvalDate', key: 'approvalDate',
      render: (v: string) => v ? dayjs(v).format('YYYY-MM-DD') : '-'
    },
    { title: '过期日期', dataIndex: 'expiryDate', key: 'expiryDate',
      render: (v: string) => v ? dayjs(v).format('YYYY-MM-DD') : '-'
    },
    {
      title: '操作', key: 'actions', width: 120,
      render: (_: any, record: any) => (
        <Space>
          <Button type="link" size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)}>编辑</Button>
        </Space>
      )
    },
  ];

  return (
    <div>
      <PageHeader
        title="伦理审批管理"
        subtitle="管理伦理委员会审批进度、批件及相关文档"
        showCreate
        onCreateClick={handleCreate}
        onSearch={setKeyword}
        searchPlaceholder="搜索伦理委员会或批件号"
      />

      <Table
        rowKey="id"
        columns={columns}
        dataSource={data}
        loading={loading}
        pagination={{
          current: pagination.page,
          pageSize: pagination.pageSize,
          total: pagination.total,
          showSizeChanger: true,
          onChange: (page, pageSize) => fetchData(page, pageSize)
        }}
      />

      <Modal
        title={editing ? '编辑伦理审批' : '新建伦理审批'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        width={700}
        confirmLoading={submitLoading}
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Space style={{ width: '100%' }} size="large" align="start">
            <Form.Item name="projectId" label="关联项目" rules={[{ required: true }]} style={{ width: 300 }}>
              <Select options={projects} placeholder="请选择项目" showSearch optionFilterProp="label" />
            </Form.Item>
            <Form.Item name="siteId" label="关联中心" style={{ width: 300 }}>
              <Select options={sites} placeholder="请选择中心 (可选)" allowClear showSearch optionFilterProp="label" />
            </Form.Item>
          </Space>
          <Space style={{ width: '100%' }} size="large" align="start">
            <Form.Item name="ethicsCommittee" label="伦理委员会名称" rules={[{ required: true }]} style={{ width: 300 }}>
              <Input placeholder="请输入伦理委员会名称" />
            </Form.Item>
            <Form.Item name="approvalType" label="审查类型" rules={[{ required: true }]} style={{ width: 300 }}>
              <Select options={approvalTypeOptions} placeholder="请选择审查类型" />
            </Form.Item>
          </Space>
          <Space style={{ width: '100%' }} size="large" align="start">
            <Form.Item name="approvalNumber" label="批件号" style={{ width: 300 }}>
              <Input placeholder="请输入批件号" />
            </Form.Item>
            <Form.Item name="approvalStatus" label="状态" style={{ width: 300 }}>
              <Select options={approvalStatusOptions} placeholder="请选择状态" />
            </Form.Item>
          </Space>
          <Space style={{ width: '100%' }} size="large" align="start">
            <Form.Item name="submissionDate" label="递交日期" style={{ width: 200 }}>
              <DatePicker style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="approvalDate" label="批准日期" style={{ width: 200 }}>
              <DatePicker style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="expiryDate" label="过期日期" style={{ width: 200 }}>
              <DatePicker style={{ width: '100%' }} />
            </Form.Item>
          </Space>
          <Form.Item name="notes" label="备注">
            <Input.TextArea rows={3} placeholder="请输入备注" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default EthicsPage;
