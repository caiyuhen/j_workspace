import React, { useState, useEffect } from 'react';
import { Card, Table, Button, Space, Spin, Alert } from 'antd';
import { DownloadOutlined, ExclamationCircleOutlined } from '@ant-design/icons';
import axios from 'axios';

const ExportHistoryPage = () => {
  const [exportHistory, setExportHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // 获取导出历史
  const fetchExportHistory = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get('/api/edc/export/history');
      setExportHistory(response.data.data);
    } catch (error) {
      console.error('获取导出历史失败:', error);
      setError('获取导出历史失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchExportHistory();
  }, []);

  // 表格列定义
  const columns = [
    {
      title: '导出ID',
      dataIndex: 'id',
      key: 'id',
      width: 200,
    },
    {
      title: '项目',
      dataIndex: 'projectId',
      key: 'projectId',
      width: 150,
    },
    {
      title: '格式',
      dataIndex: 'format',
      key: 'format',
      width: 100,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
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
      title: '数据量',
      dataIndex: 'rowCount',
      key: 'rowCount',
      width: 100,
    },
    {
      title: '创建时间',
      dataIndex: 'createdAt',
      key: 'createdAt',
      render: (text) => new Date(text).toLocaleString(),
      width: 200,
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (text, record) => (
        <Space>
          <Button 
            type="link" 
            icon={<DownloadOutlined />} 
            disabled={record.status !== 'completed'}
          >
            下载
          </Button>
          <Button 
            type="link" 
            icon={<ExclamationCircleOutlined />}
          >
            详情
          </Button>
        </Space>
      )
    }
  ];

  return (
    <div style={{ padding: 24 }}>
      <Card title="导出历史">
        {error && <Alert message={error} type="error" style={{ marginBottom: 16 }} />}
        <Table 
          dataSource={exportHistory} 
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

export default ExportHistoryPage;