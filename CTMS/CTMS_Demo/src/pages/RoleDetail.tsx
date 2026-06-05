
import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, Button, Typography, Descriptions, Tag, Collapse } from 'antd';
import { ROLES, STAGES } from '../constants';
import { MATRIX_DATA } from '../data';
import { ArrowLeftOutlined } from '@ant-design/icons';

const { Title, Paragraph, Text } = Typography;

const RoleDetail: React.FC = () => {
  const { roleId } = useParams<{ roleId: string }>();
  const navigate = useNavigate();
  const role = ROLES.find(r => r.key === roleId);

  if (!role) {
    return <div>角色不存在</div>;
  }

  // Get tasks for this role across all stages
  const roleData = MATRIX_DATA.filter(d => d.roleId === roleId);

  // Group by stage for display order
  const stageGroups = STAGES.map(stage => {
    const data = roleData.find(d => d.stageId === stage.key);
    return {
      stage,
      data
    };
  }).filter(group => group.data); // Only show stages where this role has tasks

  const collapseItems = stageGroups.map(({ stage, data }) => ({
    key: stage.key,
    label: stage.label,
    children: (
      <>
        <Descriptions column={1} bordered size="small">
          <Descriptions.Item label="GCP 关键关注点">
            <Tag color="blue">{data?.keyFocus || '暂无'}</Tag>
          </Descriptions.Item>
        </Descriptions>
        
        <div style={{ marginTop: 16, border: '1px solid #d9d9d9', borderRadius: 8 }}>
          <div style={{ padding: '12px 24px', borderBottom: '1px solid #d9d9d9', background: '#fafafa' }}>
            具体任务清单
          </div>
          <div>
            {!(data?.tasks?.length) ? (
              <div style={{ padding: '12px 24px', color: 'rgba(0,0,0,0.45)' }}>暂无数据</div>
            ) : (
              (data?.tasks || []).map((item, index) => (
                <div key={index} style={{ padding: '12px 24px', borderBottom: index < (data?.tasks || []).length - 1 ? '1px solid #f0f0f0' : 'none' }}>
                  <div style={{ width: '100%' }}>
                    <Title level={5} style={{ marginTop: 0 }}>{item.title}</Title>
                    <Paragraph style={{ marginBottom: 8 }}>{item.description}</Paragraph>
                    
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                      {item.ctmsSupport && (
                        <div style={{ background: '#e6f7ff', padding: '8px 12px', borderRadius: 4, borderLeft: '4px solid #1890ff' }}>
                          <Text strong style={{ color: '#0050b3' }}>CTMS 功能支撑: </Text>
                          <Text>{item.ctmsSupport}</Text>
                        </div>
                      )}
                      
                      {item.gcpReference && (
                        <div style={{ background: '#f6ffed', padding: '8px 12px', borderRadius: 4, borderLeft: '4px solid #52c41a' }}>
                          <Text strong style={{ color: '#389e0d' }}>GCP 合规要点: </Text>
                          <Text>{item.gcpReference}</Text>
                        </div>
                      )}
                    </div>

                    {item.requiredDocs && item.requiredDocs.length > 0 && (
                      <div style={{ marginTop: 12 }}>
                        <Text type="secondary" style={{ marginRight: 8 }}>必备文档:</Text>
                        {item.requiredDocs.map(doc => <Tag key={doc} color="orange">{doc}</Tag>)}
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </>
    )
  }));

  return (
    <div>
      <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(-1)} style={{ marginBottom: 16 }}>返回</Button>
      <Card title={<Title level={3}>{role.label}</Title>} style={{ marginBottom: 24 }}>
        <Paragraph>{role.description}</Paragraph>
      </Card>

      <Title level={4}>各阶段工作内容与合规要点</Title>
      
      {stageGroups.length === 0 ? (
        <Paragraph>暂无详细任务数据</Paragraph>
      ) : (
        <Collapse 
          defaultActiveKey={stageGroups.map(g => g.stage.key)}
          items={collapseItems}
        />
      )}
    </div>
  );
};

export default RoleDetail;
