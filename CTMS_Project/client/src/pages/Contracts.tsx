import React, { useState, useEffect, useCallback } from 'react';
import { Table, Modal, Form, Input, Select, Space, Button, DatePicker, InputNumber, App, Popconfirm } from 'antd';
import { EditOutlined, DeleteOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import PageHeader from '@/components/PageHeader';
import StatusTag from '@/components/StatusTag';
import { contractApi } from '@/api/contract';
import { projectApi } from '@/api/project';
import { vendorApi } from '@/api/vendor';

const contractTypeOptions = [
  { value: 'master', label: '主合同' },
  { value: 'amendment', label: '补充协议' },
  { value: 'sow', label: '工作说明书 (SOW)' },
  { value: 'nda', label: '保密协议 (NDA)' },
  { value: 'other', label: '其他' },
];

const signStatusOptions = [
  { value: 'draft', label: '草稿' },
  { value: 'pending_sign', label: '待签署' },
  { value: 'signed', label: '已签署' },
  { value: 'expired', label: '已过期' },
  { value: 'terminated', label: '已终止' },
];

const ContractPage: React.FC = () => {
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
  const [vendors, setVendors] = useState<{label: string, value: string}[]>([]);

  const fetchProjects = useCallback(async () => {
    try {
      const res = await projectApi.list({ page: 1, pageSize: 1000 });
      setProjects((res?.list || []).map((p: any) => ({ label: p.projectName, value: p.id })));
    } catch {}
  }, []);

  const fetchVendors = useCallback(async () => {
    try {
      const res = await vendorApi.list({ page: 1, pageSize: 1000 });
      setVendors((res?.list || []).map((v: any) => ({ label: v.vendorName, value: v.id })));
    } catch {}
  }, []);

  const fetchData = useCallback(async (page = 1, pageSize = 10) => {
    setLoading(true);
    try {
      const res = await contractApi.list({ page, pageSize, keyword });
      setData(res?.list || []);
      setPagination({ page: res?.page || 1, pageSize: res?.pageSize || 10, total: res?.total || 0 });
    } catch {
      message.error('加载合同列表失败');
    } finally {
      setLoading(false);
    }
  }, [keyword]);

  useEffect(() => {
    fetchData();
    fetchProjects();
    fetchVendors();
  }, [fetchData, fetchProjects, fetchVendors]);

  const handleCreate = () => {
    setEditing(null);
    form.resetFields();
    // 自动生成合同编码
    const randomSuffix = Math.floor(Math.random() * 10000).toString().padStart(4, '0');
    form.setFieldsValue({ contractCode: `CON-${dayjs().format('YYYYMMDD')}-${randomSuffix}`, currency: 'CNY', version: '1.0' });
    setModalOpen(true);
  };

  const handleEdit = (record: any) => {
    setEditing(record);
    form.setFieldsValue({
      ...record,
      startDate: record.startDate ? dayjs(record.startDate) : null,
      endDate: record.endDate ? dayjs(record.endDate) : null,
    });
    setModalOpen(true);
  };

  const handleDelete = async (id: string) => {
    try {
      await contractApi.delete(id);
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
      
      const payload = {
        ...values,
        startDate: values.startDate ? values.startDate.format('YYYY-MM-DD') : undefined,
        endDate: values.endDate ? values.endDate.format('YYYY-MM-DD') : undefined,
      };

      if (editing) {
        await contractApi.update(editing.id, payload);
        message.success('更新成功');
      } else {
        await contractApi.create(payload);
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
    { title: '合同编码', dataIndex: 'contractCode', key: 'contractCode' },
    { title: '合同名称', dataIndex: 'contractName', key: 'contractName' },
    { title: '合同类型', dataIndex: 'contractType', key: 'contractType',
      render: (v: string) => contractTypeOptions.find(o => o.value === v)?.label || v
    },
    { title: '金额', dataIndex: 'amount', key: 'amount',
      render: (v: number, r: any) => v ? `${v.toLocaleString()} ${r.currency}` : '-'
    },
    { title: '签署状态', dataIndex: 'signStatus', key: 'signStatus',
      render: (v: string) => <StatusTag status={v} category="contract" />
    },
    { title: '生效日期', dataIndex: 'startDate', key: 'startDate',
      render: (v: string) => v ? dayjs(v).format('YYYY-MM-DD') : '-'
    },
    { title: '到期日期', dataIndex: 'endDate', key: 'endDate',
      render: (v: string) => v ? dayjs(v).format('YYYY-MM-DD') : '-'
    },
    {
      title: '操作', key: 'actions', width: 150,
      render: (_: any, record: any) => (
        <Space>
          <Button type="link" size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)}>编辑</Button>
          <Popconfirm title="确定要删除该合同吗？" onConfirm={() => handleDelete(record.id)}>
            <Button type="link" size="small" danger icon={<DeleteOutlined />}>删除</Button>
          </Popconfirm>
        </Space>
      )
    },
  ];

  return (
    <div>
      <PageHeader
        title="合同管理"
        subtitle="管理中心合同、第三方服务合同及付款里程碑"
        showCreate
        onCreateClick={handleCreate}
        onSearch={setKeyword}
        searchPlaceholder="搜索合同编号或名称"
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
        title={editing ? '编辑合同' : '新建合同'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        width={750}
        confirmLoading={submitLoading}
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Space style={{ width: '100%' }} size="large" align="start">
            <Form.Item name="contractCode" label="合同编码" rules={[{ required: true }]} style={{ width: 320 }}>
              <Input placeholder="请输入合同编码" />
            </Form.Item>
            <Form.Item name="contractName" label="合同名称" rules={[{ required: true }]} style={{ width: 320 }}>
              <Input placeholder="请输入合同名称" />
            </Form.Item>
          </Space>
          
          <Space style={{ width: '100%' }} size="large" align="start">
            <Form.Item name="contractType" label="合同类型" rules={[{ required: true }]} style={{ width: 320 }}>
              <Select options={contractTypeOptions} placeholder="请选择合同类型" />
            </Form.Item>
            {editing && (
              <Form.Item name="signStatus" label="签署状态" style={{ width: 320 }}>
                <Select options={signStatusOptions} placeholder="请选择状态" />
              </Form.Item>
            )}
          </Space>

          <Space style={{ width: '100%' }} size="large" align="start">
            <Form.Item name="projectId" label="关联项目" style={{ width: 320 }}>
              <Select options={projects} placeholder="请选择关联项目 (可选)" allowClear showSearch optionFilterProp="label" />
            </Form.Item>
            <Form.Item name="vendorId" label="关联供应商" style={{ width: 320 }}>
              <Select options={vendors} placeholder="请选择供应商 (可选)" allowClear showSearch optionFilterProp="label" />
            </Form.Item>
          </Space>

          <Space style={{ width: '100%' }} size="large" align="start">
            <Form.Item name="amount" label="合同金额" style={{ width: 200 }}>
              <InputNumber style={{ width: '100%' }} min={0} placeholder="请输入金额" />
            </Form.Item>
            <Form.Item name="currency" label="币种" style={{ width: 100 }}>
              <Select options={[{ value: 'CNY', label: 'CNY' }, { value: 'USD', label: 'USD' }]} />
            </Form.Item>
            <Form.Item name="startDate" label="生效日期" style={{ width: 150 }}>
              <DatePicker style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="endDate" label="到期日期" style={{ width: 150 }}>
              <DatePicker style={{ width: '100%' }} />
            </Form.Item>
          </Space>

          <Form.Item name="description" label="备注描述">
            <Input.TextArea rows={3} placeholder="请输入其他备注" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default ContractPage;
