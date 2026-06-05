import React, { useState, useEffect, useCallback } from 'react';
import {  Table, Modal, Form, Input, Select, Space, Button, DatePicker, Tabs, Tag, Row, Col, Card, Statistic , App } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined, DollarOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import PageHeader from '@/components/PageHeader';
import StatusTag from '@/components/StatusTag';
import { financeApi } from '@/api/finance';
import { projectApi } from '@/api/project';
import type { Income, CreateIncomeParams, Expense, CreateExpenseParams, FinanceSummary } from '@/types';

const incomeTypeOptions = [
  { value: 'contract', label: '合同款' },
  { value: 'milestone', label: '里程碑款' },
  { value: 'amendment', label: '合同变更' },
  { value: 'other', label: '其他' },
];

const expenseCategoryOptions = [
  { value: 'personnel', label: '人力成本' },
  { value: 'travel', label: '差旅费用' },
  { value: 'equipment', label: '设备采购' },
  { value: 'supply', label: '物资供应' },
  { value: 'subcontract', label: '外包服务' },
  { value: 'miscellaneous', label: '其他费用' },
];

const incomeStatusMap: Record<string, { color: string; label: string }> = {
  expected: { color: 'default', label: '预期' },
  invoiced: { color: 'processing', label: '已开票' },
  received: { color: 'success', label: '已到账' },
  overdue: { color: 'error', label: '逾期' } };

const expenseStatusMap: Record<string, { color: string; label: string }> = {
  pending: { color: 'default', label: '待审批' },
  approved: { color: 'processing', label: '已审批' },
  rejected: { color: 'error', label: '已拒绝' },
  paid: { color: 'success', label: '已支付' } };

const FinancePage: React.FC = () => {
  const { message } = App.useApp();
  const [activeTab, setActiveTab] = useState('income');
  const [projectId] = useState<string | undefined>(undefined);
  const [keyword, setKeyword] = useState('');

  // 收入
  const [incomeData, setIncomeData] = useState<Income[]>([]);
  const [incomeLoading, setIncomeLoading] = useState(false);
  const [incomePagination, setIncomePagination] = useState({ page: 1, pageSize: 10, total: 0 });

  // 支出
  const [expenseData, setExpenseData] = useState<Expense[]>([]);
  const [expenseLoading, setExpenseLoading] = useState(false);
  const [expensePagination, setExpensePagination] = useState({ page: 1, pageSize: 10, total: 0 });

  // 汇总
  const [summary, setSummary] = useState<FinanceSummary | null>(null);

  // 弹窗
  const [modalOpen, setModalOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<Income | Expense | null>(null);
  const [form] = Form.useForm();
  const [submitLoading, setSubmitLoading] = useState(false);

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

  const fetchIncome = useCallback(async (page = 1, pageSize = 10) => {
    setIncomeLoading(true);
    try {
      const res = await financeApi.listIncome({ page, pageSize, keyword, projectId });
      setIncomeData(res?.list || []);
      setIncomePagination({ page: res?.page || 1, pageSize: res?.pageSize || 10, total: res?.total || 0 });
    } catch { message.error('加载收入列表失败'); }
    finally { setIncomeLoading(false); }
  }, [keyword, projectId]);

  const fetchExpense = useCallback(async (page = 1, pageSize = 10) => {
    setExpenseLoading(true);
    try {
      const res = await financeApi.listExpense({ page, pageSize, keyword, projectId });
      setExpenseData(res?.list || []);
      setExpensePagination({ page: res?.page || 1, pageSize: res?.pageSize || 10, total: res?.total || 0 });
    } catch { message.error('加载支出列表失败'); }
    finally { setExpenseLoading(false); }
  }, [keyword, projectId]);

  const fetchSummary = useCallback(async () => {
    if (!projectId) return;
    try { setSummary(await financeApi.getSummary(projectId)); }
    catch { /* ignore */ }
  }, [projectId]);

  useEffect(() => { fetchIncome(); fetchExpense(); fetchProjects(); }, [fetchIncome, fetchExpense, fetchProjects]);
  useEffect(() => { fetchSummary(); }, [fetchSummary]);

  const handleCreateIncome = () => {
    form.resetFields();
    setModalOpen(true);
  };

  const handleCreateExpense = () => {
    form.resetFields();
    setModalOpen(true);
  };

  const handleEditIncome = (record: Income) => {
    setEditingItem(record);
    form.setFieldsValue({ ...record, expectedDate: dayjs(record.expectedDate) });
    setModalOpen(true);
  };

  const handleEditExpense = (record: Expense) => {
    setEditingItem(record);
    form.setFieldsValue({ ...record, expenseDate: dayjs(record.expenseDate) });
    setModalOpen(true);
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setSubmitLoading(true);
      if (activeTab === 'income') {
        const params: CreateIncomeParams = { ...values, amount: Number(values.amount), expectedDate: values.expectedDate?.format('YYYY-MM-DD') };
        if (editingItem) {
          await financeApi.updateIncome(editingItem.id, params);
          message.success('更新收入记录成功');
        } else {
          await financeApi.createIncome(params);
          message.success('创建收入记录成功');
        }
        fetchIncome(incomePagination.page, incomePagination.pageSize);
      } else {
        const params: CreateExpenseParams = { ...values, amount: Number(values.amount), expenseDate: values.expenseDate?.format('YYYY-MM-DD') };
        if (editingItem) {
          await financeApi.updateExpense(editingItem.id, params);
          message.success('更新支出记录成功');
        } else {
          await financeApi.createExpense(params);
          message.success('创建支出记录成功');
        }
        fetchExpense(expensePagination.page, expensePagination.pageSize);
      }
      setModalOpen(false);
      fetchSummary();
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

  const handleDeleteIncome = (record: Income) => {
    Modal.confirm({ title: '确认删除', content: `确定删除收入记录「${record.invoiceNumber || record.description}」吗？`,
      onOk: async () => { await financeApi.removeIncome(record.id); message.success('已删除'); fetchIncome(incomePagination.page, incomePagination.pageSize); fetchSummary(); }
    });
  };

  const handleDeleteExpense = (record: Expense) => {
    Modal.confirm({ title: '确认删除', content: `确定删除支出记录「${record.invoiceNumber || record.description}」吗？`,
      onOk: async () => { await financeApi.removeExpense(record.id); message.success('已删除'); fetchExpense(expensePagination.page, expensePagination.pageSize); fetchSummary(); }
    });
  };

  const incomeColumns = [
    { title: '收入类型', dataIndex: 'incomeType', width: 100, render: (v: string) => incomeTypeOptions.find(o => o.value === v)?.label },
    { title: '金额 (¥)', dataIndex: 'amount', width: 120, render: (v: number) => `¥ ${v.toLocaleString()}` },
    { title: '发票号', dataIndex: 'invoiceNumber', width: 140, ellipsis: true },
    { title: '预期日期', dataIndex: 'expectedDate', width: 110, render: (v: string) => v ? dayjs(v).format('YYYY-MM-DD') : '-' },
    { title: '到账日期', dataIndex: 'receivedDate', width: 110, render: (v: string) => v ? dayjs(v).format('YYYY-MM-DD') : '-' },
    { title: '描述', dataIndex: 'description', ellipsis: true },
    {
      title: '状态', dataIndex: 'status', width: 80,
      render: (v: string) => <StatusTag status={v} category="finance" /> },
    {
      title: '操作', width: 140,
      render: (_: any, record: Income) => (
        <Space size="small">
          <Button type="link" size="small" icon={<EditOutlined />} onClick={() => handleEditIncome(record)}>编辑</Button>
          <Button type="link" size="small" danger icon={<DeleteOutlined />} onClick={() => handleDeleteIncome(record)}>删除</Button>
        </Space>
      ) },
  ];

  const expenseColumns = [
    { title: '费用分类', dataIndex: 'category', width: 100, render: (v: string) => expenseCategoryOptions.find(o => o.value === v)?.label },
    { title: '金额 (¥)', dataIndex: 'amount', width: 120, render: (v: number) => `¥ ${v.toLocaleString()}` },
    { title: '发票号', dataIndex: 'invoiceNumber', width: 140, ellipsis: true },
    { title: '供应商', dataIndex: 'vendor', width: 120, ellipsis: true },
    { title: '费用日期', dataIndex: 'expenseDate', width: 110, render: (v: string) => v ? dayjs(v).format('YYYY-MM-DD') : '-' },
    { title: '描述', dataIndex: 'description', ellipsis: true },
    {
      title: '状态', dataIndex: 'status', width: 80,
      render: (v: string) => <StatusTag status={v} category="finance" /> },
    {
      title: '操作', width: 140,
      render: (_: any, record: Expense) => (
        <Space size="small">
          <Button type="link" size="small" icon={<EditOutlined />} onClick={() => handleEditExpense(record)}>编辑</Button>
          <Button type="link" size="small" danger icon={<DeleteOutlined />} onClick={() => handleDeleteExpense(record)}>删除</Button>
        </Space>
      ) },
  ];

  return (
    <>
      <PageHeader
        title="财务管理"
        searchPlaceholder="搜索收支记录"
        onSearch={(v) => setKeyword(v)}
      >
        <Space>
          <Button type="primary" onClick={activeTab === 'income' ? handleCreateIncome : handleCreateExpense}>
            {activeTab === 'income' ? '新增收入' : '新增支出'}
          </Button>
        </Space>
      </PageHeader>

      {summary && (
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={8}>
            <Card size="small">
              <Statistic title="总收入" value={summary.totalIncome} prefix={<ArrowUpOutlined />} styles={{ content: { color: '#3f8600' } }}
                formatter={(v) => `¥ ${Number(v).toLocaleString()}`} />
            </Card>
          </Col>
          <Col span={8}>
            <Card size="small">
              <Statistic title="总支出" value={summary.totalExpense} prefix={<ArrowDownOutlined />} styles={{ content: { color: '#cf1322' } }}
                formatter={(v) => `¥ ${Number(v).toLocaleString()}`} />
            </Card>
          </Col>
          <Col span={8}>
            <Card size="small">
              <Statistic title="结余" value={summary.balance} prefix={<DollarOutlined />} styles={{ content: { color: summary.balance >= 0 ? '#3f8600' : '#cf1322' } }}
                formatter={(v) => `¥ ${Number(v).toLocaleString()}`} />
            </Card>
          </Col>
        </Row>
      )}

      <Tabs activeKey={activeTab} onChange={setActiveTab} items={[
        {
          key: 'income', label: <span><ArrowUpOutlined /> 收入管理</span>, children: (
            <Table rowKey="id" columns={incomeColumns} dataSource={incomeData} loading={incomeLoading}
              pagination={{
                current: incomePagination.page, pageSize: incomePagination.pageSize, total: incomePagination.total,
                showSizeChanger: true, showTotal: (t) => `共 ${t} 条`,
                onChange: (p, ps) => fetchIncome(p, ps) }}
              scroll={{ x: 1100 }} />
          ) },
        {
          key: 'expense', label: <span><ArrowDownOutlined /> 支出管理</span>, children: (
            <Table rowKey="id" columns={expenseColumns} dataSource={expenseData} loading={expenseLoading}
              pagination={{
                current: expensePagination.page, pageSize: expensePagination.pageSize, total: expensePagination.total,
                showSizeChanger: true, showTotal: (t) => `共 ${t} 条`,
                onChange: (p, ps) => fetchExpense(p, ps) }}
              scroll={{ x: 1100 }} />
          ) },
      ]} />

      {/* 创建/编辑弹窗 */}
      <Modal
        title={editingItem ? '编辑' : (activeTab === 'income' ? '新增收入' : '新增支出')}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        confirmLoading={submitLoading}
        width={560}
      >
        {activeTab === 'income' ? (
          <Form form={form} layout="vertical">
            <Form.Item name="incomeType" label="收入类型" rules={[{ required: true }]}>
              <Select options={incomeTypeOptions} />
            </Form.Item>
            <Form.Item name="amount" label="金额 (¥)" rules={[{ required: true }]}>
              <Input type="number" prefix="¥" />
            </Form.Item>
            <Form.Item name="expectedDate" label="预期日期" rules={[{ required: true }]}>
              <DatePicker style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="invoiceNumber" label="发票号">
              <Input placeholder="可选" />
            </Form.Item>
            <Form.Item name="projectId" label="关联项目">
              <Select placeholder="请选择项目" options={projects} loading={projectsLoading} showSearch optionFilterProp="label" allowClear />
            </Form.Item>
            <Form.Item name="description" label="描述" rules={[{ required: true }]}>
              <Input.TextArea rows={2} />
            </Form.Item>
          </Form>
        ) : (
          <Form form={form} layout="vertical">
            <Form.Item name="category" label="费用分类" rules={[{ required: true }]}>
              <Select options={expenseCategoryOptions} />
            </Form.Item>
            <Form.Item name="amount" label="金额 (¥)" rules={[{ required: true }]}>
              <Input type="number" prefix="¥" />
            </Form.Item>
            <Form.Item name="expenseDate" label="费用日期" rules={[{ required: true }]}>
              <DatePicker style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="invoiceNumber" label="发票号">
              <Input placeholder="可选" />
            </Form.Item>
            <Form.Item name="vendor" label="供应商">
              <Input placeholder="可选" />
            </Form.Item>
            <Form.Item name="projectId" label="关联项目">
              <Select placeholder="请选择项目" options={projects} loading={projectsLoading} showSearch optionFilterProp="label" allowClear />
            </Form.Item>
            <Form.Item name="description" label="描述" rules={[{ required: true }]}>
              <Input.TextArea rows={2} />
            </Form.Item>
          </Form>
        )}
      </Modal>
    </>
  );
};

export default FinancePage;


