import React, { useState, useEffect } from 'react';
import { Card, Table, Button, Space, Spin, Alert } from 'antd';
import { DownloadOutlined } from '@ant-design/icons';
import axios from 'axios';

const ReportsPage = () => {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // 获取报告列表
  const fetchReports = async () => {
    setLoading(true);
    setError(null);
    try {
      // 这里应该调用实际API
      const response = await axios.get('/api/edc/export/reports');
      setReports(response.data.data);
    } catch (error) {
      console.error('获取报告失败:', error);
      setError('获取报告失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  // 表格列定义
  const columns = [
    {
      title: '报告名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
    },
    {
      title: '生成时间',
      dataIndex: 'generatedAt',
      key: 'generatedAt',
      render: (text) => new Date(text).toLocaleString(),
    },
    {
      title: '大小',
      dataIndex: 'size',
      key: 'size',
    },
    {
      title: '操作',
      key: 'action',
      render: (text, record) => (
        <Space>
          <Button 
            type="link" 
            icon={<DownloadOutlined />}
            disabled={record.status !== 'completed'}
          >
            下载
          </Button>
        </Space>
      )
    }
  ];

  return (
    <div style={{ padding: 24 }}>
      <Card title="导出报告中心">
        {error && <Alert message={error} type="error" style={{ marginBottom: 16 }} />}
        <Table 
          dataSource={reports} 
          columns={columns} 
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true
          }}
        />
      </Card>
    </div>
  );
};

export default ReportsPage;