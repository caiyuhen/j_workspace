import React, { useState, useEffect } from 'react';
import { Typography, Card, Row, Col, Statistic, Table, Tag, Spin } from 'antd';
import {
  ProjectOutlined,
  BankOutlined,
  UserOutlined,
  SafetyOutlined,
  FileTextOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import dayjs from 'dayjs';
import { useAuthStore } from '@/stores/auth';
import { projectApi } from '@/api/project';
import { siteApi } from '@/api/site';
import { subjectApi } from '@/api/subject';
import { queryApi } from '@/api/query';
import { aeApi } from '@/api/ae';
import { workflowApi } from '@/api/workflow';
import type { WorkflowTask, DataQuery, AdverseEvent } from '@/types';

const { Title, Text } = Typography;

interface DashboardStats {
  projects: number;
  sites: number;
  subjects: number;
  aeCount: number;
  openQueries: number;
  pendingTasks: number;
}

const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const [stats, setStats] = useState<DashboardStats>({
    projects: 0, sites: 0, subjects: 0, aeCount: 0, openQueries: 0, pendingTasks: 0,
  });
  const [loading, setLoading] = useState(true);
  const [recentTasks, setRecentTasks] = useState<WorkflowTask[]>([]);
  const [recentQueries, setRecentQueries] = useState<DataQuery[]>([]);
  const [recentAes, setRecentAes] = useState<AdverseEvent[]>([]);

  useEffect(() => {
    const loadDashboard = async () => {
      setLoading(true);
      try {
        // 并行加载所有数据
        const [projectRes, siteRes, subjectRes, queryRes, aeRes, taskRes] = await Promise.allSettled([
          projectApi.list({ page: 1, pageSize: 1 }),
          siteApi.list({ page: 1, pageSize: 1 }),
          subjectApi.list({ page: 1, pageSize: 1 }),
          queryApi.list({ page: 1, pageSize: 5, status: 'open' }),
          aeApi.list({ page: 1, pageSize: 5 }),
          workflowApi.getMyTasks({ page: 1, pageSize: 5, status: 'pending' }),
        ]);

        const projects = projectRes.status === 'fulfilled' ? projectRes.value : null;
        const sites = siteRes.status === 'fulfilled' ? siteRes.value : null;
        const subjects = subjectRes.status === 'fulfilled' ? subjectRes.value : null;
        const queries = queryRes.status === 'fulfilled' ? queryRes.value : null;
        const aes = aeRes.status === 'fulfilled' ? aeRes.value : null;
        const tasks = taskRes.status === 'fulfilled' ? taskRes.value : null;

        setStats({
          projects: projects?.total || 0,
          sites: sites?.total || 0,
          subjects: subjects?.total || 0,
          aeCount: aes?.total || 0,
          openQueries: queries?.total || 0,
          pendingTasks: tasks?.total || 0,
        });

        if (queries) setRecentQueries(queries?.list || (Array.isArray(queries) ? queries : []));
        if (aes) setRecentAes(aes?.list || (Array.isArray(aes) ? aes : []));
        if (tasks) setRecentTasks(tasks?.list || (Array.isArray(tasks) ? tasks : []));
      } catch {
        // 静默失败，显示默认值
      } finally {
        setLoading(false);
      }
    };
    loadDashboard();
  }, []);

  const statCards = [
    { title: '活跃项目', value: stats.projects, icon: <ProjectOutlined />, color: '#1890ff', bg: '#e6f7ff' },
    { title: '研究中心', value: stats.sites, icon: <BankOutlined />, color: '#52c41a', bg: '#f6ffed' },
    { title: '入组受试者', value: stats.subjects, icon: <UserOutlined />, color: '#722ed1', bg: '#f9f0ff' },
    { title: 'AE/SAE 报告', value: stats.aeCount, icon: <SafetyOutlined />, color: '#f5222d', bg: '#fff1f0' },
    { title: '待处理质疑', value: stats.openQueries, icon: <FileTextOutlined />, color: '#fa8c16', bg: '#fff7e6' },
    { title: '待审工作流', value: stats.pendingTasks, icon: <ClockCircleOutlined />, color: '#13c2c2', bg: '#e6fffb' },
  ];

  const workflowTypeLabels: Record<string, string> = {
    project_approval: '项目审批', site_activation: '中心激活', budget_review: '预算审核',
    protocol_amendment: '方案修正', safety_report: '安全报告', data_lock: '数据锁定',
    contract_approval: '合同审批', other: '其他',
  };

  const taskColumns = [
    { title: '流程类型', key: 'type', render: (_: any, r: WorkflowTask) => workflowTypeLabels[r.instance?.workflowType || 'other'] || r.instance?.workflowType },
    { title: '当前阶段', dataIndex: 'stageName', key: 'stageName' },
    { title: '时间', dataIndex: 'createdAt', key: 'createdAt', render: (v: string) => dayjs(v).format('MM-DD HH:mm') },
    {
      title: '状态', dataIndex: 'status', key: 'status',
      render: (v: string) => v === 'pending' ? <Tag color="processing">待处理</Tag> : <Tag>{v}</Tag>,
    },
    {
      title: '操作', key: 'action',
      render: () => <a onClick={() => navigate('/workflow')}>去处理</a>,
    }
  ];

  return (
    <div>
      <Title level={4}>
        工作台
        <Text type="secondary" style={{ fontSize: 14, marginLeft: 12 }}>
          欢迎回来，{user?.displayName || user?.username || '用户'}
        </Text>
      </Title>

      <Spin spinning={loading}>
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          {statCards.map((item) => (
            <Col xs={24} sm={12} md={8} lg={4} key={item.title}>
              <Card hoverable style={{ borderRadius: 8, borderLeft: `4px solid ${item.color}` }}>
                <Statistic
                  title={item.title}
                  value={item.value}
                  prefix={React.cloneElement(item.icon as React.ReactElement<any>, { style: { color: item.color, fontSize: 20 } })}
                  styles={{ content: { color: item.color, fontSize: 28 } }}
                />
              </Card>
            </Col>
          ))}
        </Row>

        <Row gutter={[16, 16]}>
          <Col xs={24} lg={12}>
            <Card title="我的待办任务" size="small" style={{ borderRadius: 8, minHeight: 280 }}>
              {recentTasks.length > 0 ? (
                <Table columns={taskColumns} dataSource={recentTasks} pagination={false} size="small" rowKey="id" />
              ) : (
                <div style={{ textAlign: 'center', color: '#999', padding: '60px 0' }}>
                  <CheckCircleOutlined style={{ fontSize: 32, color: '#52c41a', marginBottom: 12 }} />
                  <div>暂无待办任务</div>
                </div>
              )}
            </Card>
          </Col>
          <Col xs={24} lg={12}>
            <Card title="待处理质疑" size="small" style={{ borderRadius: 8, minHeight: 280 }}>
              {recentQueries.length > 0 ? (
                <Table
                  dataSource={recentQueries}
                  pagination={false}
                  size="small"
                  rowKey="id"
                  columns={[
                    { title: '标题', dataIndex: 'title', key: 'title', ellipsis: true },
                    {
                      title: '优先级', dataIndex: 'priority', key: 'priority', width: 70,
                      render: (v: string) => {
                        const colorMap: Record<string, string> = { low: 'default', medium: 'processing', high: 'warning', critical: 'error' };
                        const labelMap: Record<string, string> = { low: '低', medium: '中', high: '高', critical: '紧急' };
                        return <Tag color={colorMap[v]}>{labelMap[v]}</Tag>;
                      },
                    },
                    { title: '时间', dataIndex: 'createdAt', key: 'createdAt', width: 100, render: (v: string) => dayjs(v).format('MM-DD HH:mm') },
                    { title: '操作', key: 'action', width: 70, render: () => <a onClick={() => navigate('/edc/queries')}>去处理</a> },
                  ]}
                />
              ) : (
                <div style={{ textAlign: 'center', color: '#999', padding: '60px 0' }}>
                  <CheckCircleOutlined style={{ fontSize: 32, color: '#52c41a', marginBottom: 12 }} />
                  <div>暂无待处理质疑</div>
                </div>
              )}
            </Card>
          </Col>
        </Row>

        {recentAes.length > 0 && (
          <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
            <Col span={24}>
              <Card title="最新 AE/SAE 报告" size="small" style={{ borderRadius: 8 }}>
                <Table
                  dataSource={recentAes}
                  pagination={false}
                  size="small"
                  rowKey="id"
                  columns={[
                    {
                      title: '类型', dataIndex: 'eventType', key: 'eventType', width: 70,
                      render: (v: string) => <Tag color={v === 'sae' ? 'red' : 'orange'}>{v === 'sae' ? 'SAE' : 'AE'}</Tag>,
                    },
                    { title: '不良事件术语', dataIndex: 'termPreferred', key: 'termPreferred', ellipsis: true },
                    { title: '严重程度', dataIndex: 'severity', key: 'severity', width: 80, render: (v: string) => ({ mild: '轻度', moderate: '中度', severe: '重度' }[v]) },
                    { title: '发生日期', dataIndex: 'onsetDate', key: 'onsetDate', width: 100, render: (v: string) => dayjs(v).format('YYYY-MM-DD') },
                    { title: '报告时间', dataIndex: 'createdAt', key: 'createdAt', width: 110, render: (v: string) => dayjs(v).format('MM-DD HH:mm') },
                    { title: '操作', key: 'action', width: 70, render: () => <a onClick={() => navigate('/edc/ae')}>查看</a> },
                  ]}
                />
              </Card>
            </Col>
          </Row>
        )}
      </Spin>
    </div>
  );
};

export default DashboardPage;
