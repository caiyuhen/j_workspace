import React from 'react';
import { Typography } from 'antd';

const { Title, Paragraph } = Typography;

// 占位页面组件工厂
function createPlaceholderPage(title: string, description: string) {
  const Page: React.FC = () => (
    <div style={{ padding: 24 }}>
      <Title level={4}>{title}</Title>
      <Paragraph type="secondary">{description}</Paragraph>
      <div
        style={{
          padding: 48,
          textAlign: 'center',
          background: '#fafafa',
          borderRadius: 8,
          marginTop: 16,
        }}
      >
        <Typography.Text type="secondary" style={{ fontSize: 16 }}>
          模块开发中，敬请期待...
        </Typography.Text>
      </div>
    </div>
  );
  Page.displayName = title;
  return Page;
}

export default createPlaceholderPage;
