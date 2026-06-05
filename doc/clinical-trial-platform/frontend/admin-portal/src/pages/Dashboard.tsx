import React from 'react';
import { Card, Statistic, Row, Col, Table, Typography } from 'antd';
import {
  UserOutlined,
  FileTextOutlined,
  CheckCircleOutlined,
  WarningOutlined,
} from '@ant-design/icons';

const { Title } = Typography;

const Dashboard: React.FC = () => {
  const trialColumns = [
    {
      title: '试验编号',
      dataIndex: 'protocolId',
      key: 'protocolId',
    },
    {
      title: '试验名称',
      dataIndex: 'trialName',
      key: 'trialName',
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
      title: '入组数/目标',
      dataIndex: 'enrollment',
      key: 'enrollment',
    },
  ];

  const trials = [
    {
      key: '1',
      protocolId: 'BGB-101',
      trialName: 'BGB-101 乳腺癌研究',
      phase: 'III',
      status: 'Active',
      enrollment: '45/120',
    },
    {
      key: '2',
      protocolId: 'BGB-102',
      trialName: 'BGB-102 糖尿病研究',
      phase: 'II',
      status: 'Recruiting',
      enrollment: '12/50',
    },
  ];

  return (
    <div>
      <Title level={2}>仪表盘</Title>
      
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="进行中的试验"
              value={12}
              prefix={<FileTextOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="研究中心"
              value={45}
              prefix={<UserOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="已完成病例"
              value={1523}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="待处理疑问"
              value={23}
              prefix={<WarningOutlined />}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
      </Row>

      <Card title="最近试验" style={{ marginTop: 24 }}>
        <Table columns={trialColumns} dataSource={trials} />
      </Card>
    </div>
  );
};

export default Dashboard;
