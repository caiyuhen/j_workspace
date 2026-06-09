import React, { useState, useEffect, useCallback } from 'react';
<<<<<<< HEAD
<<<<<<< HEAD
import {  Table, Modal, Form, Input, Select, Space, Button, Drawer, Descriptions, Tag, DatePicker, Row, Col, App, Upload } from 'antd';
import { EditOutlined, EyeOutlined, DeleteOutlined, CheckCircleOutlined, ClockCircleOutlined, UploadOutlined } from '@ant-design/icons';
=======
import {  Table, Modal, Form, Input, Select, Space, Button, Drawer, Descriptions, Tag, DatePicker, Row, Col , App } from 'antd';
import { EditOutlined, EyeOutlined, DeleteOutlined, CheckCircleOutlined, ClockCircleOutlined } from '@ant-design/icons';
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
=======
import {  Table, Modal, Form, Input, Select, Space, Button, Drawer, Descriptions, Tag, DatePicker, Row, Col , App } from 'antd';
import { EditOutlined, EyeOutlined, DeleteOutlined, CheckCircleOutlined, ClockCircleOutlined } from '@ant-design/icons';
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
import dayjs from 'dayjs';
import PageHeader from '@/components/PageHeader';
import StatusTag from '@/components/StatusTag';
import { documentApi } from '@/api/document';
import { projectApi } from '@/api/project';
import type { Document, CreateDocumentParams, DocumentVersion } from '@/types';

<<<<<<< HEAD
<<<<<<< HEAD
const categoryOptions = [
  { value: 'section_00_general', label: '通用管理' },
  { value: 'section_01_icf', label: '知情同意' },
  { value: 'section_02_regulatory', label: '法规事务' },
  { value: 'section_03_irb_iec', label: '伦理审查' },
  { value: 'section_04_investigator', label: '研究者' },
  { value: 'section_05_pharmacy', label: '试验药物' },
  { value: 'section_06_lab', label: '实验室' },
  { value: 'section_07_safety', label: '安全性' },
  { value: 'section_08_statistics', label: '数据与统计' },
  { value: 'section_09_financial', label: '财务' },
  { value: 'section_10_site', label: '中心管理' },
  { value: 'section_11_misc', label: '其他' },
];

const documentTypeOptions = [
  { value: 'protocol', label: 'Protocol 方案' },
  { value: 'icf', label: 'ICF 知情同意书' },
  { value: 'regulatory_submission', label: '法规递交' },
  { value: 'irb_approval', label: '伦理批件' },
  { value: 'cv', label: '简历' },
  { value: 'license', label: '执照/资质' },
  { value: 'report', label: '报告' },
  { value: 'correspondence', label: '通信记录' },
  { value: 'lab_certificate', label: '实验室认证' },
  { value: 'safety_report', label: '安全性报告' },
  { value: 'training_record', label: '培训记录' },
  { value: 'financial', label: '财务文档' },
=======
=======
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
const documentTypeOptions = [
  { value: 'TMF', label: 'TMF 试验主文档' },
  { value: 'ISF', label: 'ISF 研究者文件夹' },
  { value: 'ICF', label: 'ICF 知情同意书' },
  { value: 'CSR', label: 'CSR 临床研究报告' },
  { value: 'Protocol', label: 'Protocol 方案' },
  { value: 'Other', label: '其他' },
];



const categoryOptions = [
  { value: 'protocol', label: '方案' },
  { value: 'icf', label: '知情同意' },
  { value: 'regulatory', label: ' regulatory 法规' },
  { value: 'safety', label: '安全性' },
  { value: 'data_management', label: '数据管理' },
  { value: 'monitoring', label: '监察' },
  { value: 'pharmacy', label: '试验药物' },
  { value: 'finance', label: '财务' },
<<<<<<< HEAD
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
=======
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
  { value: 'other', label: '其他' },
];

const DocumentsPage: React.FC = () => {
  const { message } = App.useApp();
  const [data, setData] = useState<Document[]>([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({ page: 1, pageSize: 10, total: 0 });
  const [keyword, setKeyword] = useState('');
  const [typeFilter, setTypeFilter] = useState<string | undefined>(undefined);
  const [statusFilter, setStatusFilter] = useState<string | undefined>(undefined);

  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Document | null>(null);
  const [form] = Form.useForm();
  const [submitLoading, setSubmitLoading] = useState(false);

  const [detailOpen, setDetailOpen] = useState(false);
  const [selectedDoc, setSelectedDoc] = useState<Document | null>(null);
  const [versions, setVersions] = useState<DocumentVersion[]>([]);
  const [versionsLoading, setVersionsLoading] = useState(false);
  const [projects, setProjects] = useState<{label: string, value: string}[]>([]);

  const fetchProjects = useCallback(async () => {
    try {
      const res = await projectApi.list({ page: 1, pageSize: 1000 });
      setProjects((res?.list || []).map((p: any) => ({ label: p.projectName, value: p.id })));
    } catch {}
  }, []);

  const fetchData = useCallback(async (page = 1, pageSize = 10) => {
    setLoading(true);
    try {
      const res = await documentApi.list({ page, pageSize, keyword, documentType: typeFilter, status: statusFilter });
      setData(res?.list || []);
      setPagination({ page: res?.page || 1, pageSize: res?.pageSize || 10, total: res?.total || 0 });
    } catch {
      message.error('加载文档列表失败');
    } finally {
      setLoading(false);
    }
  }, [keyword, typeFilter, statusFilter]);

  useEffect(() => { fetchData(); fetchProjects(); }, [fetchData, fetchProjects]);

  const handleCreate = () => {
    setEditing(null);
    form.resetFields();
    setModalOpen(true);
  };

<<<<<<< HEAD
<<<<<<< HEAD
  const handleEdit = (record: any) => {
    setEditing(record);
    form.setFieldsValue({
      ...record,
      documentNumber: record.documentCode,
      title: record.documentName,
      category: record.tmfSection,
      effectiveDate: record.expectedDate ? dayjs(record.expectedDate) : undefined,
      expiryDate: record.expiryDate ? dayjs(record.expiryDate) : undefined });
    setModalOpen(true);
    setDetailOpen(false); // 编辑时关闭详情抽屉
=======
=======
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
  const handleEdit = (record: Document) => {
    setEditing(record);
    form.setFieldsValue({
      ...record,
      effectiveDate: record.effectiveDate ? dayjs(record.effectiveDate) : undefined,
      expiryDate: record.expiryDate ? dayjs(record.expiryDate) : undefined });
    setModalOpen(true);
<<<<<<< HEAD
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
=======
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setSubmitLoading(true);
<<<<<<< HEAD
<<<<<<< HEAD
      const params: any = {
        projectId: values.projectId,
        tmfSection: values.category || 'section_00_general',
        documentCode: values.documentNumber,
        documentName: values.title,
        documentType: values.documentType || 'other',
        description: values.description,
        isRequired: values.isRequired
      };

      if (values.effectiveDate) {
        params.expectedDate = values.effectiveDate.toISOString();
      }
      if (values.expiryDate) {
        params.expiryDate = values.expiryDate.toISOString();
      }
      
      let docId = '';
      if (editing) {
        await documentApi.update(editing.id, params);
        docId = editing.id;
      } else {
        const newDoc = await documentApi.create(params);
        docId = newDoc.id;
      }

      // 处理文件上传
      const fileList = values.file;
      if (fileList && fileList.length > 0 && fileList[0].originFileObj) {
        const file = fileList[0].originFileObj as File;
        try {
          await documentApi.uploadVersion(docId, {
            fileUrl: URL.createObjectURL(file), // 模拟上传后的URL
            fileSize: file.size,
            mimeType: file.type,
            changeLog: '初始版本上传'
          });
        } catch (uploadErr: any) {
          // 如果是新建文档且文件上传失败，可以选择不做回滚，但需提示用户
          throw new Error(uploadErr.response?.data?.error?.message || '文件上传失败');
        }
      }

      message.success(editing ? '更新文档成功' : '创建文档成功');
=======
=======
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
      const params: CreateDocumentParams = {
        ...values,
        effectiveDate: values.effectiveDate?.format('YYYY-MM-DD'),
        expiryDate: values.expiryDate?.format('YYYY-MM-DD') };
      if (editing) {
        await documentApi.update(editing.id, params);
        message.success('更新文档成功');
      } else {
        await documentApi.create(params);
        message.success('创建文档成功');
      }
<<<<<<< HEAD
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
=======
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
      setModalOpen(false);
      fetchData(pagination.page, pagination.pageSize);
    } catch (err: any) {
      if (err.errorFields) {
        message.warning('请检查表单填写是否正确');
        return;
      }
<<<<<<< HEAD
<<<<<<< HEAD
      message.error(err.message || err.response?.data?.error?.message || '操作失败');
=======
      message.error(err.response?.data?.error?.message || '操作失败');
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
=======
      message.error(err.response?.data?.error?.message || '操作失败');
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
    } finally {
      setSubmitLoading(false);
    }
  };

<<<<<<< HEAD
<<<<<<< HEAD
  const handleDelete = (record: any) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除文档「${record.documentName}」吗？`,
=======
=======
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
  const handleDelete = (record: Document) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除文档「${record.title}」吗？`,
<<<<<<< HEAD
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
=======
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
      onOk: async () => {
        await documentApi.remove(record.id);
        message.success('删除成功');
        fetchData(pagination.page, pagination.pageSize);
      } });
  };

<<<<<<< HEAD
<<<<<<< HEAD
  const handleViewDetail = async (record: any) => {
=======
  const handleViewDetail = async (record: Document) => {
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
=======
  const handleViewDetail = async (record: Document) => {
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
    setSelectedDoc(record);
    setDetailOpen(true);
    setVersionsLoading(true);
    try {
      const v = await documentApi.getVersions(record.id);
      setVersions(v);
    } catch {
      message.error('加载版本历史失败');
    } finally {
      setVersionsLoading(false);
    }
  };

<<<<<<< HEAD
<<<<<<< HEAD
  const handleApprove = (record: any, status: string) => {
    Modal.confirm({
      title: status === 'approved' ? '批准文档' : '拒绝文档',
      content: `确定要${status === 'approved' ? '批准' : '拒绝'}文档「${record.documentName}」吗？`,
=======
=======
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
  const handleApprove = (record: Document, status: string) => {
    Modal.confirm({
      title: status === 'approved' ? '批准文档' : '拒绝文档',
      content: `确定要${status === 'approved' ? '批准' : '拒绝'}文档「${record.title}」吗？`,
<<<<<<< HEAD
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
=======
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
      onOk: async () => {
        await documentApi.updateStatus(record.id, { status });
        message.success(`文档已${status === 'approved' ? '批准' : '拒绝'}`);
        fetchData(pagination.page, pagination.pageSize);
      } });
  };

  const columns = [
<<<<<<< HEAD
<<<<<<< HEAD
    { title: '文档编号', dataIndex: 'documentCode', width: 130 },
    { title: '标题', dataIndex: 'documentName', width: 220, ellipsis: true },
=======
    { title: '文档编号', dataIndex: 'documentNumber', width: 130 },
    { title: '标题', dataIndex: 'title', width: 220, ellipsis: true },
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
=======
    { title: '文档编号', dataIndex: 'documentNumber', width: 130 },
    { title: '标题', dataIndex: 'title', width: 220, ellipsis: true },
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
    {
      title: '类型',
      dataIndex: 'documentType',
      width: 130,
      render: (v: string) => documentTypeOptions.find(o => o.value === v)?.label || v },
<<<<<<< HEAD
<<<<<<< HEAD
    { title: '分类', dataIndex: 'tmfSection', width: 100, render: (v: string) => categoryOptions.find(o => o.value === v)?.label || v },
    { title: '版本', dataIndex: 'version', width: 60, align: 'center' as const },
    {
      title: '完成状态',
      dataIndex: 'isRequired',
      width: 90,
      render: (v: boolean, record: any) => record.fileUrl
        ? <Tag color="success" icon={<CheckCircleOutlined />}>已上传</Tag>
        : <Tag color="warning" icon={<ClockCircleOutlined />}>未上传</Tag> },
=======
=======
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
    { title: '分类', dataIndex: 'category', width: 100, render: (v: string) => categoryOptions.find(o => o.value === v)?.label || v },
    { title: '版本', dataIndex: 'version', width: 60, align: 'center' as const },
    {
      title: '完成状态',
      dataIndex: 'isCompleted',
      width: 90,
      render: (v: boolean) => v
        ? <Tag color="success" icon={<CheckCircleOutlined />}>已完成</Tag>
        : <Tag color="warning" icon={<ClockCircleOutlined />}>未完成</Tag> },
<<<<<<< HEAD
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
=======
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
    {
      title: '文档状态',
      dataIndex: 'status',
      width: 90,
      render: (v: string) => <StatusTag status={v} category="document" /> },
<<<<<<< HEAD
<<<<<<< HEAD
    { title: '上传人', dataIndex: ['uploadedBy'], width: 100 },
=======
    { title: '作者', dataIndex: ['author', 'displayName'], width: 100 },
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
=======
    { title: '作者', dataIndex: ['author', 'displayName'], width: 100 },
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
    {
      title: '更新时间',
      dataIndex: 'updatedAt',
      width: 120,
      render: (v: string) => v ? dayjs(v).format('YYYY-MM-DD HH:mm') : '-' },
    {
      title: '操作',
      width: 220,
<<<<<<< HEAD
<<<<<<< HEAD
      render: (_: any, record: any) => (
=======
      render: (_: any, record: Document) => (
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
=======
      render: (_: any, record: Document) => (
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
        <Space size="small">
          <Button type="link" size="small" icon={<EyeOutlined />} onClick={() => handleViewDetail(record)}>查看</Button>
          <Button type="link" size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)}>编辑</Button>
          {record.status === 'pending_review' && (
            <>
              <Button type="link" size="small" style={{ color: '#52c41a' }} onClick={() => handleApprove(record, 'approved')}>批准</Button>
              <Button type="link" size="small" danger onClick={() => handleApprove(record, 'rejected')}>拒绝</Button>
            </>
          )}
          <Button type="link" size="small" danger icon={<DeleteOutlined />} onClick={() => handleDelete(record)}>删除</Button>
        </Space>
      ) },
  ];

  return (
    <>
      <PageHeader
        title="文档管理"
        searchPlaceholder="搜索文档"
        onSearch={(v) => setKeyword(v)}
      >
        <Space>
          <Select placeholder="文档类型" allowClear style={{ width: 150 }} options={documentTypeOptions} value={typeFilter} onChange={setTypeFilter} />
          <Select placeholder="文档状态" allowClear style={{ width: 130 }} options={[{value: 'draft', label: '草稿'}, {value: 'under_review', label: '审核中'}, {value: 'approved', label: '已批准'}, {value: 'rejected', label: '已拒绝'}, {value: 'archived', label: '已归档'}]} value={statusFilter} onChange={setStatusFilter} />
          <Button type="primary" onClick={handleCreate}>创建文档</Button>
        </Space>
      </PageHeader>

      {/* 统计卡片 */}


      <Table
        rowKey="id"
        columns={columns}
        dataSource={data}
        loading={loading}
        pagination={{
          current: pagination.page, pageSize: pagination.pageSize, total: pagination.total,
          showSizeChanger: true, showTotal: (t) => `共 ${t} 条`,
          onChange: (p, ps) => fetchData(p, ps) }}
        scroll={{ x: 1500 }}
      />

      {/* 创建/编辑弹窗 */}
      <Modal
        title={editing ? '编辑文档' : '创建文档'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        confirmLoading={submitLoading}
        width={640}
      >
<<<<<<< HEAD
<<<<<<< HEAD
        <Form form={form} layout="vertical" initialValues={{ documentType: 'other', isRequired: false }}>
          <Form.Item name="projectId" label="关联项目" rules={[{ required: true, message: '请选择关联项目' }]}>
            <Select options={projects} placeholder="请选择项目" showSearch optionFilterProp="label" disabled={!!editing} />
=======
        <Form form={form} layout="vertical" initialValues={{ documentType: 'TMF', isRequired: false }}>
          <Form.Item name="projectId" label="关联项目" rules={[{ required: true, message: '请选择关联项目' }]}>
            <Select options={projects} placeholder="请选择项目" showSearch optionFilterProp="label" />
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
=======
        <Form form={form} layout="vertical" initialValues={{ documentType: 'TMF', isRequired: false }}>
          <Form.Item name="projectId" label="关联项目" rules={[{ required: true, message: '请选择关联项目' }]}>
            <Select options={projects} placeholder="请选择项目" showSearch optionFilterProp="label" />
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="documentNumber" label="文档编号" rules={[{ required: true }]}>
                <Input 
                  placeholder="如: TMF-001" 
<<<<<<< HEAD
<<<<<<< HEAD
                  disabled={!!editing}
                  suffix={
                    !editing && <a onClick={() => {
=======
                  suffix={
                    <a onClick={() => {
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
=======
                  suffix={
                    <a onClick={() => {
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
                      const randomSuffix = Math.floor(Math.random() * 1000).toString().padStart(3, '0');
                      form.setFieldsValue({ documentNumber: `TMF-${randomSuffix}` });
                    }}>自动生成</a>
                  }
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="documentType" label="文档类型" rules={[{ required: true }]}>
                <Select options={documentTypeOptions} />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="title" label="文档标题" rules={[{ required: true }]}>
            <Input placeholder="请输入文档标题" />
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="category" label="分类" rules={[{ required: true }]}>
                <Select options={categoryOptions} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="subCategory" label="子分类">
                <Input placeholder="可选" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="effectiveDate" label="生效日期">
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="expiryDate" label="过期日期">
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={3} placeholder="文档描述" />
          </Form.Item>
          <Form.Item name="isRequired" label="必填文档">
            <Select options={[{ value: true, label: '是' }, { value: false, label: '否' }]} />
          </Form.Item>
<<<<<<< HEAD
<<<<<<< HEAD
          <Form.Item 
            name="file" 
            label="上传附件 (可选)" 
            valuePropName="fileList" 
            getValueFromEvent={e => Array.isArray(e) ? e : e?.fileList}
          >
            <Upload beforeUpload={() => false} maxCount={1}>
              <Button icon={<UploadOutlined />}>选择文件</Button>
            </Upload>
          </Form.Item>
=======
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
=======
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
        </Form>
      </Modal>

      {/* 详情抽屉 */}
      <Drawer
<<<<<<< HEAD
<<<<<<< HEAD
        title={
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span>{selectedDoc ? `${selectedDoc.documentCode} - ${selectedDoc.documentName}` : '文档详情'}</span>
            {selectedDoc && (
              <Button type="primary" icon={<EditOutlined />} onClick={() => handleEdit(selectedDoc)}>
                编辑文档
              </Button>
            )}
          </div>
        }
=======
        title={selectedDoc ? `${selectedDoc.documentNumber} - ${selectedDoc.title}` : '文档详情'}
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
=======
        title={selectedDoc ? `${selectedDoc.documentNumber} - ${selectedDoc.title}` : '文档详情'}
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
        open={detailOpen}
        onClose={() => setDetailOpen(false)}
        size="large"
      >
        {selectedDoc && (
          <>
            <Descriptions column={2} bordered size="small" style={{ marginBottom: 16 }}>
<<<<<<< HEAD
<<<<<<< HEAD
              <Descriptions.Item label="文档编号">{selectedDoc.documentCode}</Descriptions.Item>
              <Descriptions.Item label="类型">{documentTypeOptions.find(o => o.value === selectedDoc.documentType)?.label}</Descriptions.Item>
              <Descriptions.Item label="版本">V{selectedDoc.version}</Descriptions.Item>
              <Descriptions.Item label="状态"><StatusTag status={selectedDoc.status} category="document" /></Descriptions.Item>
              <Descriptions.Item label="上传人">{selectedDoc.uploadedBy || '-'}</Descriptions.Item>
              <Descriptions.Item label="完成状态">
                {selectedDoc.fileUrl
                  ? <Tag color="success">已上传</Tag>
                  : <Tag color="warning">未上传</Tag>}
              </Descriptions.Item>
              <Descriptions.Item label="生效日期">{selectedDoc.expectedDate ? dayjs(selectedDoc.expectedDate).format('YYYY-MM-DD') : '-'}</Descriptions.Item>
=======
=======
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
              <Descriptions.Item label="文档编号">{selectedDoc.documentNumber}</Descriptions.Item>
              <Descriptions.Item label="类型">{documentTypeOptions.find(o => o.value === selectedDoc.documentType)?.label}</Descriptions.Item>
              <Descriptions.Item label="版本">V{selectedDoc.version}</Descriptions.Item>
              <Descriptions.Item label="状态"><StatusTag status={selectedDoc.status} category="document" /></Descriptions.Item>
              <Descriptions.Item label="作者">{selectedDoc.author?.displayName || '-'}</Descriptions.Item>
              <Descriptions.Item label="完成状态">
                {selectedDoc.isCompleted
                  ? <Tag color="success">已完成</Tag>
                  : <Tag color="warning">未完成</Tag>}
              </Descriptions.Item>
              <Descriptions.Item label="生效日期">{selectedDoc.effectiveDate ? dayjs(selectedDoc.effectiveDate).format('YYYY-MM-DD') : '-'}</Descriptions.Item>
<<<<<<< HEAD
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
=======
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
              <Descriptions.Item label="过期日期">{selectedDoc.expiryDate ? dayjs(selectedDoc.expiryDate).format('YYYY-MM-DD') : '-'}</Descriptions.Item>
              <Descriptions.Item label="描述" span={2}>{selectedDoc.description || '-'}</Descriptions.Item>
            </Descriptions>

            <h4 style={{ marginTop: 16, marginBottom: 8 }}>版本历史</h4>
<<<<<<< HEAD
<<<<<<< HEAD
            <div style={{ marginBottom: 16 }}>
              <Upload 
                beforeUpload={async (file) => {
                  try {
                    await documentApi.uploadVersion(selectedDoc.id, {
                      fileUrl: URL.createObjectURL(file), // 模拟上传URL
                      fileSize: file.size,
                      mimeType: file.type,
                      changeLog: '上传新版本'
                    });
                    message.success('新版本上传成功');
                    // 重新加载版本历史
                    setVersionsLoading(true);
                    const v = await documentApi.getVersions(selectedDoc.id);
                    setVersions(v);
                    setVersionsLoading(false);
                  } catch (err: any) {
                    message.error(err.response?.data?.error?.message || '上传失败');
                  }
                  return false;
                }}
                showUploadList={false}
              >
                <Button type="primary" icon={<UploadOutlined />}>上传新版本</Button>
              </Upload>
            </div>
            <Table rowKey="id" size="small" dataSource={versions} loading={versionsLoading} pagination={false}
              columns={[
                { title: '版本', dataIndex: 'version', width: 60 },
                { title: '文件名', dataIndex: 'changeLog', ellipsis: true },
                { title: '大小', dataIndex: 'fileSize', width: 80, render: (v: number) => v ? `${(v / 1024).toFixed(1)} KB` : '-' },
                { title: '上传人', dataIndex: 'uploadedBy', width: 100 },
                { title: '上传时间', dataIndex: 'uploadedAt', width: 140, render: (v: string) => v ? dayjs(v).format('YYYY-MM-DD HH:mm') : '-' },
=======
=======
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
            <Table rowKey="id" size="small" dataSource={versions} loading={versionsLoading} pagination={false}
              columns={[
                { title: '版本', dataIndex: 'version', width: 60 },
                { title: '文件名', dataIndex: 'fileName', ellipsis: true },
                { title: '大小', dataIndex: 'fileSize', width: 80, render: (v: number) => v ? `${(v / 1024).toFixed(1)} KB` : '-' },
                { title: '上传人', dataIndex: ['uploadedBy', 'displayName'], width: 100 },
                { title: '上传时间', dataIndex: 'createdAt', width: 140, render: (v: string) => v ? dayjs(v).format('YYYY-MM-DD HH:mm') : '-' },
                { title: '状态', dataIndex: 'status', width: 80, render: (v: string) => <StatusTag status={v} category="document" /> },
<<<<<<< HEAD
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
=======
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
              ]}
            />
          </>
        )}
      </Drawer>
    </>
  );
};

export default DocumentsPage;
