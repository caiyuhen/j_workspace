import React, { useState, useEffect } from 'react';
import { Card, Button, Modal, Form, Input, Select, DatePicker, Space, Tag, Row, Col } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined } from '@ant-design/icons';

const { Option } = Select;

const PatientListPage = () => {
  const [patients, setPatients] = useState([]);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [form] = Form.useForm();

  // 模拟患者数据
  useEffect(() => {
    // 这里应该调用API获取患者列表
    setPatients([
      {
        id: '1',
        patientName: '张三',
        gender: 'male',
        dateOfBirth: '1980-01-01',
        diagnosis: '高血压',
        patientTags: ['高血压', '慢性病']
      },
      {
        id: '2',
        patientName: '李四',
        gender: 'female',
        dateOfBirth: '1990-05-15',
        diagnosis: '糖尿病',
        patientTags: ['糖尿病', '慢性病']
      }
    ]);
  }, []);

  const handleCreatePatient = async (values) => {
    // 调用API创建患者
    console.log('创建患者:', values);
    setIsModalVisible(false);
    form.resetFields();
  };

  const handleDeletePatient = (id) => {
    // 调用API删除患者
    console.log('删除患者:', id);
  };

  return (
    <div style={{ padding: 24 }}>
      <Card 
        title="患者档案" 
        extra={
          <Button 
            type="primary" 
            icon={<PlusOutlined />} 
            onClick={() => setIsModalVisible(true)}
          >
            新增患者
          </Button>
        }
      >
        <Row gutter={[16, 16]}>
          {patients.map(item => (
            <Col key={item.id} xs={24} sm={12} md={8} lg={8} xl={6}>
              <Card title={item.patientName} actions={[
                <EyeOutlined key="view" />,
                <EditOutlined key="edit" />,
                <DeleteOutlined key="delete" onClick={() => handleDeletePatient(item.id)} />
              ]}>
                <p>性别: {item.gender === 'male' ? '男' : '女'}</p>
                <p>出生日期: {item.dateOfBirth}</p>
                <p>诊断: {item.diagnosis}</p>
                <div>
                  {item.patientTags.map((tag, index) => (
                    <Tag key={index}>{tag}</Tag>
                  ))}
                </div>
              </Card>
            </Col>
          ))}
        </Row>
      </Card>

      {/* 创建患者模态框 */}
      <Modal
        title="创建患者"
        open={isModalVisible}
        onCancel={() => setIsModalVisible(false)}
        footer={null}
      >
        <Form form={form} layout="vertical" onFinish={handleCreatePatient}>
          <Form.Item 
            name="patientName" 
            label="患者姓名"
            rules={[{ required: true, message: '请输入患者姓名' }]}
          >
            <Input />
          </Form.Item>
          
          <Form.Item 
            name="gender" 
            label="性别"
            rules={[{ required: true, message: '请选择性别' }]}
          >
            <Select>
              <Option value="male">男</Option>
              <Option value="female">女</Option>
              <Option value="other">其他</Option>
            </Select>
          </Form.Item>
          
          <Form.Item 
            name="dateOfBirth" 
            label="出生日期"
          >
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          
          <Form.Item 
            name="diagnosis" 
            label="诊断"
          >
            <Input />
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

export default PatientListPage;