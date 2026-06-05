import React from 'react';
import { Button, Card, Typography } from 'antd';
import { FileSearchOutlined } from '@ant-design/icons';

const ReportsPage = () => {
  return (
    <Card>
      <Typography.Title level={3} style={{ textAlign: 'center' }}>
        <FileSearchOutlined style={{ marginRight: 12 }} />
        数据统计与报告
      </Typography.Title>
      <div style={{ textAlign: 'center', marginTop: 48 }}>
        <Button type="primary" size="large" style={{ marginRight: 16 }}>
          导出患者数据
        </Button>
        <Button type="primary" size="large" style={{ marginRight: 16 }}>
          生成随访报告
        </Button>
        <Button type="primary" size="large">
          查看统计数据
        </Button>
      </div>
      <div style={{ marginTop: 48 }}>
        <h3>分析功能</h3>
        <ul>
          <li>患者随访频率分析</li>
          <li>疾病类型分布</li>
          <li>治疗效果趋势</li>
          <li>药物使用统计</li>
        </ul>
      </div>
    </Card>
  );
};

export default ReportsPage;