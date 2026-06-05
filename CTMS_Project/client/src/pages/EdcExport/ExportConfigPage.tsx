import React, { useState, useEffect } from 'react';
import { Card, Form, Input, Select, DatePicker, Button, Space, Alert, Upload, Table, Row, Col, Spin } from 'antd';
import { UploadOutlined, DownloadOutlined, ExclamationCircleOutlined } from '@ant-design/icons';
import axios from 'axios';

const ExportConfigPage = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [exportConfig, setExportConfig] = useState({
    projectId: '',
    startDate: null,
    endDate: null,
    domains: [],
    formIds: [],
    format: 'SDTM'
  });
  const [exportHistory, setExportHistory] = useState([]);
  const [isFormValid, setIsFormValid] = useState(false);

  // 模拟获取项目列表
  const projects = [
    { id: 'project1', name: '乳腺癌临床试验项目' },
    { id: 'project2', name: '心血管疾病研究项目' },
    { id: 'project3', name: '糖尿病治疗项目' }
  ];

  // 模拟获取表单列表
  const forms = [
    { id: 'form1', name: '人口统计学表单' },
    { id: 'form2', name: '不良事件报告表单' },
    { id: 'form3', name: '随访记录表单' }
  ];

  // 模拟获取CDISC域列表
  const domains = [
    { id: 'DM', name: 'Demographics (DM)' },
    { id: 'AE', name: 'Adverse Events (AE)' },
    { id: 'VS', name: 'Vital Signs (VS)' },
    { id: 'LB', name: 'Laboratory (LB)' },
    { id: 'CM', name: 'Concomitant Medications (CM)' },
    { id: 'DS', name: 'Disposition (DS)' },
    { id: 'IE', name: 'Inclusion/Exclusion (IE)' }
  ];

  // 获取导出历史
  const fetchExportHistory = async () => {
    try {
      // 这里应该调用实际API
      const response = await axios.get('/api/edc/export/history');
      setExportHistory(response.data.data);
    } catch (error) {
      console.error('获取导出历史失败:', error);
    }
  };

  useEffect(() => {
    fetchExportHistory();
  }, []);

  // 处理表单变更
  const handleFormChange = (changedValues, allValues) => {
    setExportConfig(allValues);
    // 简单的表单验证
    setIsFormValid(!!allValues.projectId);
  };

  // 处理提交导出
  const handleExportSubmit = async (values) => {
    setLoading(true);
    try {
      if (values.format === 'XPT' || values.format === 'xpt') {
        // 请求下载
        const response = await axios.post('/api/edc/export/sdtm', {
          projectId: values.projectId,
          domains: values.domains,
          format: 'xpt'
        }, { responseType: 'blob' });
        
        // 创建下载链接
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        const contentDisposition = response.headers['content-disposition'];
        let fileName = 'sdtm_export.zip';
        if (contentDisposition) {
          const fileNameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
          if (fileNameMatch && fileNameMatch.length === 2)
            fileName = fileNameMatch[1];
        }
        link.setAttribute('download', fileName);
        document.body.appendChild(link);
        link.click();
        link.remove();
        
      } else {
        // 调用实际导出API
        await axios.post('/api/edc/export/batch-to-sdtm', {
          projectId: values.projectId,
          filters: {
            startDate: values.startDate,
            endDate: values.endDate,
            domains: values.domains,
            formIds: values.formIds
          }
        });
      }
      
      // 重新获取历史记录
      fetchExportHistory();
      // 显示成功消息或重置表单
      alert('导出任务已提交/完成');
    } catch (error) {
      console.error('导出失败:', error);
      alert('导出失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  // 表单字段定义
  const formItems = [
    {
      name: 'projectId',
      label: '项目',
      required: true,
      rules: [{ required: true, message: '请选择项目' }],
      component: (
        <Select placeholder="请选择项目">
          {projects.map(project => (
            <Select.Option key={project.id} value={project.id}>{project.name}</Select.Option>
          ))}
        </Select>
      )
    },
    {
      name: 'startDate',
      label: '开始日期',
      component: <DatePicker style={{ width: '100%' }} />
    },
    {
      name: 'endDate',
      label: '结束日期',
      component: <DatePicker style={{ width: '100%' }} />
    },
    {
      name: 'domains',
      label: 'CDISC域',
      component: (
        <Select mode="multiple" placeholder="请选择CDISC域">
          {domains.map(domain => (
            <Select.Option key={domain.id} value={domain.id}>{domain.name}</Select.Option>
          ))}
        </Select>
      )
    },
    {
      name: 'formIds',
      label: '表单',
      component: (
        <Select mode="multiple" placeholder="请选择表单">
          {forms.map(form => (
            <Option key={form.id} value={form.id}>{form.name}</Option>
          ))}
        </Select>
      )
    },
    {
      name: 'format',
      label: '导出格式',
      initialValue: 'SDTM',
      component: (
        <Select>
          <Select.Option value="SDTM">SDTM (JSON)</Select.Option>
          <Select.Option value="xpt">SDTM (XPT/ZIP)</Select.Option>
          <Select.Option value="ECRF">ECRF</Select.Option>
          <Select.Option value="ADAM">ADaM</Select.Option>
        </Select>
      )
    }
  ];

  // 导出历史表格列定义
  const historyColumns = [
    {
      title: '导出ID',
      dataIndex: 'id',
      key: 'id',
    },
    {
      title: '项目',
      dataIndex: 'projectId',
      key: 'projectId',
    },
    {
      title: '格式',
      dataIndex: 'format',
      key: 'format',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (text) => {
        if (text === 'completed') {
          return <span style={{ color: 'green' }}>已完成</span>;
        } else if (text === 'failed') {
          return <span style={{ color: 'red' }}>失败</span>;
        }
        return <span>处理中</span>;
      }
    },
    {
      title: '导出时间',
      dataIndex: 'createdAt',
      key: 'createdAt',
      render: (text) => new Date(text).toLocaleDateString()
    },
    {
      title: '操作',
      key: 'action',
      render: (text, record) => (
        <Space>
          <Button type="link" icon={<DownloadOutlined />}>下载</Button>
          <Button type="link" icon={<ExclamationCircleOutlined />}>详情</Button>
        </Space>
      )
    }
  ];

  return (
    <div style={{ padding: 24 }}>
      <Card title="CDISC/SDTM 导出配置" style={{ marginBottom: 24 }}>
        <Form 
          form={form} 
          layout="vertical" 
          onValuesChange={handleFormChange}
          onFinish={handleExportSubmit}
        >
          <Row gutter={16}>
            {formItems.map((item, index) => (
              <Col span={8} key={index}>
                <Form.Item
                  name={item.name}
                  label={item.label}
                  rules={item.rules}
                  initialValue={item.initialValue}
                >
                  {item.component}
                </Form.Item>
              </Col>
            ))}
          </Row>
          
          <Form.Item>
            <Space>
              <Button 
                type="primary" 
                htmlType="submit" 
                loading={loading}
                disabled={!isFormValid}
              >
                提交导出任务
              </Button>
              <Button onClick={() => form.resetFields()}>重置</Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>

      <Card title="导出历史记录">
        <Table 
          dataSource={exportHistory} 
          columns={historyColumns} 
          rowKey="id"
          loading={loading}
          pagination={false}
        />
      </Card>
    </div>
  );
};

export default ExportConfigPage;