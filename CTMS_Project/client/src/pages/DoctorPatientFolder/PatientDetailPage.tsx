import React, { useState, useEffect } from 'react';
import { Card, Table, Button, Modal, Form, Input, DatePicker, Space, Tag, Tabs, Select } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined, FileSearchOutlined } from '@ant-design/icons';

const { TabPane } = Tabs;

const PatientDetailPage = ({ match }) => {
  const [patient, setPatient] = useState(null);
  const [followUps, setFollowUps] = useState([]);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [form] = Form.useForm();

  // 模拟患者数据
  useEffect(() => {
    // 这里应该调用API获取患者详情
    setPatient({
      id: '1',
      patientName: '张三',
      gender: 'male',
      dateOfBirth: '1980-01-01',
      contactInfo: '13800138000',
      diagnosis: '高血压',
      treatmentHistory: ['2023年服用降压药', '2024年体检正常']
    });

    // 模拟随访数据
    setFollowUps([
      {
        id: '1',
        visitDate: '2024-01-15',
        visitType: '常规随访',
        formTemplateName: '高血压随访表'
      },
      {
        id: '2',
        visitDate: '2024-02-15',
        visitType: '专项检查',
        formTemplateName: '高血压专项检查'
      }
    ]);
  }, []);

  const handleCreateFollowUp = async (values) => {
    // 调用API创建随访记录
    console.log('创建随访:', values);
    setIsModalVisible(false);
    form.resetFields();
  };

  return (
    <div style={{ padding: 24 }}>
      {patient && (
        <>
          <Card title={patient.patientName} extra={
            <Button icon={<FileSearchOutlined />}>导出数据</Button>
          }>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <div>
                <p><strong>性别:</strong> {patient.gender === 'male' ? '男' : '女'}</p>
                <p><strong>出生日期:</strong> {patient.dateOfBirth}</p>
                <p><strong>联系方式:</strong> {patient.contactInfo}</p>
                <p><strong>诊断:</strong> {patient.diagnosis}</p>
              </div>
              <div>
                <h4>治疗历史</h4>
                {patient.treatmentHistory.map((history, index) => (
                  <p key={index}>{history}</p>
                ))}
              </div>
            </div>
          </Card>

          <Card 
            title="随访记录" 
            extra={
              <Button 
                type="primary" 
                icon={<PlusOutlined />} 
                onClick={() => setIsModalVisible(true)}
              >
                添加随访
              </Button>
            }
            style={{ marginTop: 24 }}
          >
            <Tabs defaultActiveKey="1">
              <TabPane tab="历史记录" key="1">
                <Table
                  dataSource={followUps}
                  rowKey="id"
                  pagination={false}
                  columns={[
                    {
                      title: '随访日期',
                      dataIndex: 'visitDate',
                      key: 'visitDate',
                    },
                    {
                      title: '随访类型',
                      dataIndex: 'visitType',
                      key: 'visitType',
                    },
                    {
                      title: '模板',
                      dataIndex: 'formTemplateName',
                      key: 'formTemplateName',
                    },
                    {
                      title: '操作',
                      key: 'action',
                      render: (_, record) => (
                        <Space size="middle">
                          <Button icon={<EyeOutlined />} size="small">查看</Button>
                          <Button icon={<EditOutlined />} size="small">编辑</Button>
                        </Space>
                      ),
                    },
                  ]}
                />
              </TabPane>
              <TabPane tab="数据统计" key="2">
                {/* 数据统计内容 */}
                <p>这里显示统计分析结果</p>
              </TabPane>
            </Tabs>
          </Card>
        </>
      )}

      {/* 创建随访模态框 */}
      <Modal
        title="创建随访"
        open={isModalVisible}
        onCancel={() => setIsModalVisible(false)}
        footer={null}
      >
        <Form form={form} layout="vertical" onFinish={handleCreateFollowUp}>
          <Form.Item 
            name="visitDate" 
            label="随访日期"
            rules={[{ required: true, message: '请选择随访日期' }]}
          >
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          
          <Form.Item 
            name="visitType" 
            label="随访类型"
            rules={[{ required: true, message: '请输入随访类型' }]}
          >
            <Input />
          </Form.Item>
          
          <Form.Item 
            name="formTemplateId" 
            label="引用模板"
          >
            <Select placeholder="选择表单模板">
              <Option value="template1">高血压随访表</Option>
              <Option value="template2">糖尿病随访表</Option>
              <Option value="template3">专项检查</Option>
            </Select>
          </Form.Item>
          
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">创建</Button>
              <Button onClick={() => setIsModalVisible(false)}>取消</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default PatientDetailPage;