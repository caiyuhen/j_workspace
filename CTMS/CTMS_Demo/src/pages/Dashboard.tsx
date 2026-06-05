
import React from 'react';
import { Card, Row, Col, Typography, Timeline, Divider } from 'antd';
import type { TimelineItemProps } from 'antd';
import { ROLES, STAGES } from '../constants';
import { useNavigate } from 'react-router-dom';
import { SafetyCertificateOutlined, FileSearchOutlined, AlertOutlined, SolutionOutlined } from '@ant-design/icons';

const { Title, Paragraph, Text } = Typography;

const Dashboard: React.FC = () => {
  const navigate = useNavigate();

  const timelineItems: TimelineItemProps[] = [
    {
      title: 'Step 1',
      color: 'blue',
      icon: <SolutionOutlined />,
      content: (
        <>
          <Text strong>研究者 (Site)</Text>
          <br/>
          报告 AE/SAE/SUSAR (通过 CTMS 药物警戒模块提交)
        </>
      )
    },
    {
      title: 'Step 2',
      color: 'green',
      icon: <FileSearchOutlined />,
      content: (
        <>
           <Text strong>CRA</Text>
           <br/>
           确认 AE/SAE 信息完整性 (关联受试者源数据 SDV)
        </>
      )
    },
    {
      title: 'Step 3',
      color: 'red',
      icon: <AlertOutlined />,
      content: (
        <>
           <Text strong>PV (药物警戒)</Text>
           <br/>
           评估因果关系，提交 SUSAR 报告至 IRB/监管机构 (24小时内)
        </>
      )
    },
    {
      title: 'Step 4',
      color: 'orange',
      content: (
        <>
           <Text strong>PM (项目经理)</Text>
           <br/>
           通过仪表盘监控 SAE 发生率，评估项目风险
        </>
      )
    },
    {
      title: 'Step 5',
      color: 'purple',
      icon: <SafetyCertificateOutlined />,
      content: (
        <>
           <Text strong>QA (质量保证)</Text>
           <br/>
           审计报告及时性与合规性 (CAPA 跟踪)
        </>
      )
    }
  ];

  return (
    <div>
      <div style={{ textAlign: 'center', marginBottom: 40 }}>
        <Title level={2}>CTMS 临床试验管理系统</Title>
        <Paragraph>
          基于 GCP 规范，围绕“按角色分工、按流程管控”的核心设计
        </Paragraph>
      </div>

      <Title level={3}>8大核心角色</Title>
      <Row gutter={[16, 16]}>
        {ROLES.map(role => (
          <Col xs={24} sm={12} md={8} lg={6} key={role.key}>
            <Card 
              title={role.label} 
              hoverable 
              onClick={() => navigate(`/role/${role.key}`)}
              style={{ height: '100%' }}
            >
              <Paragraph ellipsis={{ rows: 2 }}>{role.description}</Paragraph>
            </Card>
          </Col>
        ))}
      </Row>

      <Divider />

      <Title level={3}>核心协作流程演示：AE/SAE/SUSAR 报告</Title>
      <Card style={{ background: '#fafafa' }}>
        <Timeline 
          mode="start"
          items={timelineItems}
        />
      </Card>

      <Divider />

      <Title level={3} style={{ marginTop: 40 }}>6个关键阶段</Title>
      <Row gutter={[16, 16]}>
        {STAGES.map(stage => (
          <Col xs={24} sm={12} md={8} key={stage.key}>
            <Card 
              title={stage.label} 
              hoverable
              onClick={() => navigate(`/stage/${stage.key}`)}
            >
              <Paragraph ellipsis={{ rows: 2 }}>{stage.description}</Paragraph>
            </Card>
          </Col>
        ))}
      </Row>
    </div>
  );
};

export default Dashboard;
