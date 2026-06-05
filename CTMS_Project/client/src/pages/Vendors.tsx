import React, { useState, useEffect, useCallback } from 'react';
import { Table, Modal, Form, Input, Select, Space, Button, App, Popconfirm } from 'antd';
import { EditOutlined, DeleteOutlined } from '@ant-design/icons';
import PageHeader from '@/components/PageHeader';
import StatusTag from '@/components/StatusTag';
import { vendorApi } from '@/api/vendor';
import { settingsApi } from '@/api/settings';
import { projectApi } from '@/api/project';

const vendorTypeOptions = [
  { value: 'sponsor', label: '申办方' },
  { value: 'cro', label: 'CRO (合同研究组织)' },
  { value: 'vendor', label: '供应商' },
  { value: 'regulatory', label: '监管机构' },
  { value: 'other', label: '其他' },
];

const statusOptions = [
  { value: 'pending', label: '待审核' },
  { value: 'active', label: '活跃' },
  { value: 'inactive', label: '停用' },
  { value: 'terminated', label: '已终止' },
];

const VendorsPage: React.FC = () => {
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
  const [vendorOrgs, setVendorOrgs] = useState<{label: string, value: string, org: any}[]>([]);

  const fetchProjects = useCallback(async () => {
    try {
      const res = await projectApi.list({ page: 1, pageSize: 1000 });
      setProjects((res?.list || []).map((p: any) => ({
        label: p.projectName,
        value: p.id })));
    } catch {}
  }, []);

  const fetchVendorOrgs = useCallback(async () => {
    try {
      const res = await settingsApi.listOrganizations({ page: 1, pageSize: 1000 });
      const orgs = (res?.list || []).filter((o: any) => o.orgType !== 'site' && o.type !== 'site');
      setVendorOrgs(orgs.map((o: any) => ({
        label: o.orgName || o.name,
        value: o.orgName || o.name,
        org: o
      })));
    } catch {}
  }, []);

  const fetchData = useCallback(async (page = 1, pageSize = 10) => {
    setLoading(true);
    try {
      const res = await vendorApi.list({ page, pageSize, keyword });
      setData(res?.list || []);
      setPagination({ page: res?.page || 1, pageSize: res?.pageSize || 10, total: res?.total || 0 });
    } catch {
      message.error('加载供应商列表失败');
    } finally {
      setLoading(false);
    }
  }, [keyword]);

  useEffect(() => {
    fetchData();
    fetchProjects();
    fetchVendorOrgs();
  }, [fetchData, fetchProjects, fetchVendorOrgs]);

  const handleCreate = () => {
    setEditing(null);
    form.resetFields();
    // 自动生成供应商编码
    const randomSuffix = Math.floor(Math.random() * 1000).toString().padStart(3, '0');
    form.setFieldsValue({ vendorCode: `VEN-${randomSuffix}` });
    setModalOpen(true);
  };

  const handleEdit = (record: any) => {
    setEditing(record);
    form.setFieldsValue(record);
    setModalOpen(true);
  };

  const handleDelete = async (id: string) => {
    try {
      await vendorApi.delete(id);
      message.success('删除成功');
      fetchData(pagination.page, pagination.pageSize);
    } catch (err: any) {
      message.error(err.response?.data?.error?.message || '删除失败');
    }
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setSubmitLoading(true);

      if (editing) {
        await vendorApi.update(editing.id, values);
        message.success('更新成功');
      } else {
        await vendorApi.create(values);
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
    { title: '供应商编号', dataIndex: 'vendorCode', key: 'vendorCode' },
    { title: '供应商名称', dataIndex: 'vendorName', key: 'vendorName' },
    { title: '供应商类型', dataIndex: 'vendorType', key: 'vendorType',
      render: (v: string) => vendorTypeOptions.find(o => o.value === v)?.label || v
    },
    { title: '联系人', dataIndex: 'contactPerson', key: 'contactPerson' },
    { title: '联系电话', dataIndex: 'contactPhone', key: 'contactPhone' },
    { title: '状态', dataIndex: 'status', key: 'status',
      render: (v: string) => <StatusTag status={v} category="vendor" />
    },
    {
      title: '操作', key: 'actions', width: 150,
      render: (_: any, record: any) => (
        <Space>
          <Button type="link" size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)}>编辑</Button>
          <Popconfirm title="确定要删除该供应商吗？" onConfirm={() => handleDelete(record.id)}>
            <Button type="link" size="small" danger icon={<DeleteOutlined />}>删除</Button>
          </Popconfirm>
        </Space>
      )
    },
  ];

  return (
    <div>
      <PageHeader
        title="供应商管理"
        subtitle="管理CRO、中心实验室等供应商信息及绩效"
        showCreate
        onCreateClick={handleCreate}
        onSearch={setKeyword}
        searchPlaceholder="搜索供应商编号或名称"
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
        title={editing ? '编辑供应商' : '新建供应商'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        width={700}
        confirmLoading={submitLoading}
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Space style={{ width: '100%' }} size="large" align="start">
            <Form.Item name="projectId" label="所属项目" style={{ width: 300 }}>
              <Select placeholder="请选择项目" options={projects} showSearch optionFilterProp="label" allowClear />
            </Form.Item>
          </Space>
          
          <Space style={{ width: '100%' }} size="large" align="start">
            <Form.Item name="vendorCode" label="供应商编号" rules={[{ required: true }]} style={{ width: 300 }}>
              <Input 
                placeholder="请输入供应商编号" 
                suffix={
                  <a onClick={() => {
                    const randomSuffix = Math.floor(Math.random() * 1000).toString().padStart(3, '0');
                    form.setFieldsValue({ vendorCode: `VEN-${randomSuffix}` });
                  }}>自动生成</a>
                }
              />
            </Form.Item>
            <Form.Item name="vendorName" label="供应商名称" rules={[{ required: true }]} style={{ width: 300 }}>
              <Select 
                placeholder="请选择组织机构" 
                options={vendorOrgs}
                showSearch
                onChange={(_, option: any) => {
                  if (option && option.org) {
                    const type = option.org.orgType || option.org.type;
                    if (type && type !== 'site') {
                      form.setFieldsValue({ vendorType: type });
                    }
                  }
                }}
              />
            </Form.Item>
          </Space>
          
          <Space style={{ width: '100%' }} size="large" align="start">
            <Form.Item name="vendorType" label="供应商类型" rules={[{ required: true }]} style={{ width: 300 }}>
              <Select options={vendorTypeOptions} placeholder="请选择类型" />
            </Form.Item>
            {editing && (
              <Form.Item name="status" label="状态" style={{ width: 300 }}>
                <Select options={statusOptions} placeholder="请选择状态" />
              </Form.Item>
            )}
          </Space>

          <Space style={{ width: '100%' }} size="large" align="start">
            <Form.Item name="contactPerson" label="联系人" style={{ width: 200 }}>
              <Input placeholder="请输入联系人姓名" />
            </Form.Item>
            <Form.Item name="contactPhone" label="联系电话" style={{ width: 200 }}>
              <Input placeholder="请输入电话" />
            </Form.Item>
            <Form.Item name="contactEmail" label="电子邮箱" style={{ width: 200 }}>
              <Input placeholder="请输入邮箱" />
            </Form.Item>
          </Space>

          <Form.Item name="address" label="联系地址">
            <Input placeholder="请输入详细地址" />
          </Form.Item>

          <Form.Item name="description" label="备注">
            <Input.TextArea rows={3} placeholder="请输入备注" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default VendorsPage;
