import React from 'react';
import { Table, Button, Modal, Form, Input, Select, DatePicker, Space } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';

const TrialList: React.FC = () => {
  const [modalVisible, setModalVisible] = React.useState(false);
  const [form] = Form.useForm();

  const columns = [
    {
      title: '试验编号',
      dataIndex: 'protocolId',
      key: 'protocolId',
    },
    {
      title: '试验名称 (中文)',
      dataIndex: 'trialNameCn',
      key: 'trialNameCn',
    },
    {
      title: '试验名称 (英文)',
      dataIndex: 'trialNameEn',
      key: 'trialNameEn',
    },
    {
      title: '分期',
      dataIndex: 'phase',
      key: 'phase',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
    },
    {
      title: '开始日期',
      dataIndex: 'startDate',
      key: 'startDate',
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: any) => (
        <Space>
          <Button icon={<EditOutlined />} size="small">编辑</Button>
          <Button icon={<DeleteOutlined />} danger size="small">删除</Button>
        </Space>
      ),
    },
  ];

  const trials = [
    {
      key: '1',
      protocolId: 'BGB-101',
      trialNameEn: 'Study BGB-101 in Breast Cancer',
      trialNameCn: 'BGB-101 乳腺癌临床试验',
      phase: 'III',
      status: '进行中',
      startDate: '2024-01-15',
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <h2>试验管理</h2>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalVisible(true)}>
          新建试验
        </Button>
      </div>

      <Table columns={columns} dataSource={trials} />

      <Modal
        title="新建试验"
        open={modalVisible}
        onOk={() => {
          form.validateFields().then((values) => {
            console.log(values);
            setModalVisible(false);
            form.resetFields();
          });
        }}
        onCancel={() => setModalVisible(false)}
        width={800}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="protocolId"
            label="试验编号"
            rules={[{ required: true, message: '请输入试验编号' }]}
          >
            <Input placeholder="例如：BGB-101" />
          </Form.Item>

          <Form.Item
            name="trialNameEn"
            label="试验名称 (英文)"
            rules={[{ required: true, message: '请输入试验名称' }]}
          >
            <Input placeholder="Enter trial name in English" />
          </Form.Item>

          <Form.Item
            name="trialNameCn"
            label="试验名称 (中文)"
          >
            <Input placeholder="试验名称 (中文)" />
          </Form.Item>

          <Form.Item
            name="phase"
            label="试验分期"
            rules={[{ required: true, message: '请选择试验分期' }]}
          >
            <Select>
              <Select.Option value="I">I 期</Select.Option>
              <Select.Option value="II">II 期</Select.Option>
              <Select.Option value="III">III 期</Select.Option>
              <Select.Option value="IV">IV 期</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="designType"
            label="试验设计"
          >
            <Select mode="multiple">
              <Select.Option value="randomized">随机</Select.Option>
              <Select.Option value="double-blind">双盲</Select.Option>
              <Select.Option value="open-label">开放标签</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="indicationArea"
            label="适应症领域"
          >
            <Input placeholder="例如：乳腺癌、糖尿病等" />
          </Form.Item>

          <Form.Item
            name="startDate"
            label="计划开始日期"
          >
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            name="endDate"
            label="计划结束日期"
          >
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            name="sponsorName"
            label="赞助方"
          >
            <Input placeholder="赞助方名称" />
          </Form.Item>

          <Form.Item
            name="croName"
            label="CRO"
          >
            <Input placeholder="CRO 名称" />
          </Form.Item>

          <Form.Item
            name="enrollmentTarget"
            label="目标入组数"
          >
            <Input type="number" placeholder="例如：120" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default TrialList;
