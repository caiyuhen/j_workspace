import React, { useState, useEffect } from 'react';
import { Card, Button, Modal, Form, Input, Select, Space, Typography, Row, Col } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;

const FormDesignerPage = () => {
  const [templates, setTemplates] = useState([]);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [form] = Form.useForm();

  // 模拟表单模板数据
  useEffect(() => {
    // 这里应该调用API获取模板列表
    setTemplates([
      {
        id: '1',
        templateName: '高血压随访表',
        templateType: 'crf',
        fields: ['血压', '心率', '症状描述']
      },
      {
        id: '2',
        templateName: '糖尿病随访表',
        templateType: 'crf',
        fields: ['血糖', '胰岛素用量', '并发症']
      }
    ]);
  }, []);

  const handleCreateTemplate = async (values) => {
    // 调用API创建模板
    console.log('创建模板:', values);
    setIsModalVisible(false);
    form.resetFields();
  };

  return (
    <div style={{ padding: 24 }}>
      <Card 
        title="表单模板管理" 
        extra={
          <Button 
            type="primary" 
            icon={<PlusOutlined />} 
            onClick={() => setIsModalVisible(true)}
          >
            新建模板
          </Button>
        }
      >
        <Row gutter={[16, 16]}>
          {templates.map(item => (
            <Col key={item.id} xs={24} sm={12} md={8} lg={8} xl={6}>
              <Card title={item.templateName}>
                <p><Text type="secondary">类型:</Text> {item.templateType}</p>
                <p><Text type="secondary">字段:</Text> {item.fields.join(', ')}</p>
                <div style={{ marginTop: 16 }}>
                  <Button icon={<EditOutlined />} style={{ marginRight: 8 }}>编辑</Button>
                  <Button icon={<DeleteOutlined />} type="primary" danger>删除</Button>
                </div>
              </Card>
            </Col>
          ))}
        </Row>
      </Card>

      {/* 创建模板模态框 */}
      <Modal
        title="创建表单模板"
        open={isModalVisible}
        onCancel={() => setIsModalVisible(false)}
        footer={null}
      >
        <Form form={form} layout="vertical" onFinish={handleCreateTemplate}>
          <Form.Item 
            name="templateName" 
            label="模板名称"
            rules={[{ required: true, message: '请输入模板名称' }]}
          >
            <Input />
          </Form.Item>
          
          <Form.Item 
            name="templateType" 
            label="模板类型"
            rules={[{ required: true, message: '请选择模板类型' }]}
          >
            <Select>
              <Option value="crf">CRF表单</Option>
              <Option value="informed_consent">知情同意书</Option>
              <Option value="screening">筛选表</Option>
              <Option value="visit">访视表</Option>
              <Option value="other">其他</Option>
            </Select>
          </Form.Item>
          
          <Form.Item 
            name="description" 
            label="描述"
          >
            <Input.TextArea />
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

export default FormDesignerPage;