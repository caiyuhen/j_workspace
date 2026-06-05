import React from 'react';
import { Typography, Space, Input, Button } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import type { ReactNode } from 'react';

const { Title, Text } = Typography;

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  extra?: ReactNode;
  showCreate?: boolean;
  onCreateClick?: () => void;
  createText?: string;
  showSearch?: boolean;
  onSearch?: (value: string) => void;
  searchPlaceholder?: string;
  children?: ReactNode;
}

const PageHeader: React.FC<PageHeaderProps> = ({
  title,
  subtitle,
  extra,
  showCreate = false,
  onCreateClick,
  createText = '新建',
  showSearch = true,
  onSearch,
  searchPlaceholder = '搜索...',
  children,
}) => (
  <div style={{ marginBottom: 16 }}>
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
      <div>
        <Title level={4} style={{ margin: 0 }}>{title}</Title>
        {subtitle && <Text type="secondary" style={{ fontSize: 13 }}>{subtitle}</Text>}
      </div>
      <Space>
        {children}
        {showSearch && onSearch && (
          <Input.Search
            placeholder={searchPlaceholder}
            allowClear
            onSearch={onSearch}
            style={{ width: 240 }}
          />
        )}
        {showCreate && (
          <Button type="primary" icon={<PlusOutlined />} onClick={onCreateClick}>
            {createText}
          </Button>
        )}
        {extra}
      </Space>
    </div>
  </div>
);

export default PageHeader;
