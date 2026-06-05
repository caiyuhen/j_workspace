
import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, Button, Typography, Steps, Descriptions, Tag, Row, Col } from 'antd';
import { STAGES, ROLES } from '../constants';
import { MATRIX_DATA } from '../data';
import { ArrowLeftOutlined } from '@ant-design/icons';

const { Title, Paragraph, Text } = Typography;

const StageDetail: React.FC = () => {
  const { stageId } = useParams<{ stageId: string }>();
  const navigate = useNavigate();
  const stage = STAGES.find(s => s.key === stageId);
  const stageIndex = STAGES.findIndex(s => s.key === stageId);

  if (!stage) {
    return <div>阶段不存在</div>;
  }

  // Get tasks for this stage across all roles
  const stageData = MATRIX_DATA.filter(d => d.stageId === stageId);

  // Group by role
  const roleGroups = ROLES.map(role => {
    const data = stageData.find(d => d.roleId === role.key);
    return {
      role,
      data
    };
  }).filter(group => group.data);

  return (
    <div>
      <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(-1)} style={{ marginBottom: 16 }}>返回</Button>
      <Steps 
        current={stageIndex} 
        onChange={(current) => navigate(`/stage/${STAGES[current].key}`)}
        style={{ marginBottom: 24, cursor: 'pointer' }}
        items={STAGES.map(s => ({ key: s.key, title: s.label }))}
      />

      <Card title={<Title level={3}>{stage.label}</Title>} style={{ marginBottom: 24 }}>
        <Paragraph>{stage.description}</Paragraph>
      </Card>

      <Title level={4}>各角色协作与分工</Title>

      {roleGroups.length === 0 ? (
        <Paragraph>暂无详细任务数据</Paragraph>
      ) : (
        <Row gutter={[16, 16]}>
          {roleGroups.map(({ role, data }) => (
            <Col span={24} key={role.key}>
              <Card title={role.label} bordered>
                 <Descriptions column={1} bordered size="small" style={{marginBottom: 16}}>
                    <Descriptions.Item label="GCP 关键职责">
                      <Tag color="green">{data?.keyFocus || '暂无'}</Tag>
                    </Descriptions.Item>
                 </Descriptions>
                 
                 <div style={{ border: '1px solid #d9d9d9', borderRadius: 8 }}>
                   <div style={{ padding: '8px 16px', borderBottom: '1px solid #d9d9d9', background: '#fafafa', fontWeight: 500 }}>
                     执行任务
                   </div>
                   <div>
                     {!(data?.tasks?.length) ? (
                        <div style={{ padding: '8px 16px', color: 'rgba(0,0,0,0.45)' }}>暂无数据</div>
                     ) : (
                        (data?.tasks || []).map((item, index) => (
                           <div key={index} style={{ padding: '8px 16px', borderBottom: index < (data?.tasks || []).length - 1 ? '1px solid #f0f0f0' : 'none' }}>
                              <div style={{ width: '100%' }}>
                                <Title level={5} style={{ marginTop: 0 }}>{item.title}</Title>
                                <Paragraph style={{ marginBottom: 8 }}>{item.description}</Paragraph>
                                
                                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                                  {item.ctmsSupport && (
                                    <div style={{ background: '#e6f7ff', padding: '4px 8px', borderRadius: 4, fontSize: '12px' }}>
                                      <Text strong style={{ color: '#0050b3' }}>CTMS: </Text>
                                      <Text>{item.ctmsSupport}</Text>
                                    </div>
                                  )}
                                  
                                  {item.gcpReference && (
                                    <div style={{ background: '#f6ffed', padding: '4px 8px', borderRadius: 4, fontSize: '12px' }}>
                                      <Text strong style={{ color: '#389e0d' }}>GCP: </Text>
                                      <Text>{item.gcpReference}</Text>
                                    </div>
                                  )}
                                </div>

                                 {item.requiredDocs && item.requiredDocs.length > 0 && (
                                  <div style={{ marginTop: 8 }}>
                                    {item.requiredDocs.map(doc => <Tag key={doc} color="orange" style={{fontSize: '10px'}}>{doc}</Tag>)}
                                  </div>
                                )}
                              </div>
                           </div>
                        ))
                     )}
                   </div>
                 </div>
              </Card>
            </Col>
          ))}
        </Row>
      )}
    </div>
  );
};

export default StageDetail;
