import React, { useState } from 'react';
import { Card, Form, Input, Button, Space, Table, Alert } from 'antd';
import axios from 'axios';

const ValidationPage = () => {
  const [form] = Form.useForm();
  const [validationResult, setValidationResult] = useState(null);
  const [loading, setLoading] = useState(false);

  // 处理表单提交
  const handleSubmit = async (values) => {
    setLoading(true);
    try {
      // 调用验证API
      const response = await axios.get(`/api/edc/export/validate-form/${values.formId}`);
      setValidationResult(response.data.data);
    } catch (error) {
      console.error('验证失败:', error);
      alert('验证失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  // 表格列定义
  const columns = [
    {
      title: '字段名',
      dataIndex: 'fieldName',
      key: 'fieldName',
    },
    {
      title: '合规状态',
      dataIndex: 'compliance.isValid',
      key: 'isValid',
      render: (isValid) => {
        if (isValid) {
          return <span style={{ color: 'green' }}>合规</span>;
        }
        return <span style={{ color: 'red' }}>不合规</span>;
      }
    },
    {
      title: '错误信息',
      dataIndex: 'compliance.errors',
      key: 'errors',
      render: (errors) => (
        <div>
          {errors && errors.length > 0 ? (
            errors.map((error, index) => <div key={index}>{error.message}</div>)
          ) : '无'}
        </div>
      )
    }
  ];

  return (
    <div style={{ padding: 24 }}>
      <Card title="CDISC合规性验证" style={{ marginBottom: 24 }}>
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item
            name="formId"
            label="表单ID"
            rules={[{ required: true, message: '请输入表单ID' }]}
          >
            <Input placeholder="请输入CRF表单ID" />
          </Form.Item>
          
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={loading}>
                执行验证
              </Button>
              <Button onClick={() => form.resetFields()}>重置</Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>

      {validationResult && (
        <Card title="验证结果">
          <Alert
            message={
              validationResult.isValid 
                ? "所有字段合规，符合CDISC标准" 
                : `发现 ${validationResult.totalErrors} 个不合规字段`
            }
            type={validationResult.isValid ? "success" : "error"}
            showIcon
            style={{ marginBottom: 16 }}
          />
          
          <Table 
            dataSource={validationResult.fieldResults} 
            columns={columns} 
            rowKey="fieldId"
            pagination={false}
          />
        </Card>
      )}
    </div>
  );
};

export default ValidationPage;