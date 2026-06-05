import React, { useEffect, useState } from 'react';
import { Grid, Paper, Typography, Box } from '@mui/material';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  PieChart, Pie
} from 'recharts';
import api from '../api/axios';
import type { DashboardStats } from '../types/dashboard';

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await api.get('dashboard/');
        setStats(response.data);
      } catch (error) {
        console.error('Failed to fetch dashboard stats:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  if (loading) return <Typography>加载中...</Typography>;
  if (!stats) return <Typography>无法加载数据</Typography>;

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042'];

  const siteDistributionData = stats.charts.site_distribution.map((entry, index) => ({
    ...entry,
    fill: COLORS[index % COLORS.length]
  }));

  const aeSeverityData = stats.charts.ae_severity.map((entry, index) => ({
    ...entry,
    fill: COLORS[index % COLORS.length]
  }));

  return (
    <Grid container spacing={3}>
      <Grid size={{ xs: 12 }}>
        <Typography variant="h4" gutterBottom>仪表盘</Typography>
      </Grid>

      {/* Summary Cards */}
      <Grid size={{ xs: 12, md: 6, lg: 3 }}>
        <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column', height: 140 }}>
          <Typography component="h2" variant="h6" color="primary" gutterBottom>
            进行中的项目
          </Typography>
          <Typography component="p" variant="h3">
            {stats.trials.active} / {stats.trials.total}
          </Typography>
          <Typography color="text.secondary" sx={{ flex: 1 }}>
            总计 {stats.trials.total} 个项目
          </Typography>
        </Paper>
      </Grid>
      
      <Grid size={{ xs: 12, md: 6, lg: 3 }}>
        <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column', height: 140 }}>
          <Typography component="h2" variant="h6" color="primary" gutterBottom>
            受试者总数
          </Typography>
          <Typography component="p" variant="h3">
            {stats.subjects.total}
          </Typography>
          <Typography color="text.secondary" sx={{ flex: 1 }}>
            已入组: {stats.subjects.enrolled}
          </Typography>
        </Paper>
      </Grid>

      <Grid size={{ xs: 12, md: 6, lg: 3 }}>
        <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column', height: 140 }}>
          <Typography component="h2" variant="h6" color="primary" gutterBottom>
            活跃中心
          </Typography>
          <Typography component="p" variant="h3">
            {stats.sites.active}
          </Typography>
          <Typography color="text.secondary" sx={{ flex: 1 }}>
            总计 {stats.sites.total} 个中心
          </Typography>
        </Paper>
      </Grid>

      <Grid size={{ xs: 12, md: 6, lg: 3 }}>
        <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column', height: 140 }}>
          <Typography component="h2" variant="h6" color="error" gutterBottom>
            待处理 SAE
          </Typography>
          <Typography component="p" variant="h3" color="error">
            {stats.safety.pending_saes}
          </Typography>
          <Typography color="text.secondary" sx={{ flex: 1 }}>
            需立即关注
          </Typography>
        </Paper>
      </Grid>

      {/* Charts */}
      <Grid size={{ xs: 12, md: 8 }}>
        <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column', height: 400 }}>
          <Typography component="h2" variant="h6" color="primary" gutterBottom>
            受试者入组趋势 (近6个月)
          </Typography>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={stats.charts.recruitment_trend}
              margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="subjects" name="入组人数" fill="#8884d8" />
            </BarChart>
          </ResponsiveContainer>
        </Paper>
      </Grid>

      <Grid size={{ xs: 12, md: 4 }}>
        <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column', height: 400 }}>
          <Typography component="h2" variant="h6" color="primary" gutterBottom>
            中心状态分布
          </Typography>
          <Box sx={{ flexGrow: 1, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={siteDistributionData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  // eslint-disable-next-line @typescript-eslint/no-explicit-any
                  label={({ name, percent }: any) => `${name} ${((percent || 0) * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Box>
        </Paper>
      </Grid>

      {/* New Charts Row */}
      <Grid size={{ xs: 12, md: 4 }}>
        <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column', height: 300 }}>
          <Typography component="h2" variant="h6" color="primary" gutterBottom>
            AE/SAE 严重程度分布
          </Typography>
          <Box sx={{ flexGrow: 1, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={aeSeverityData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  // eslint-disable-next-line @typescript-eslint/no-explicit-any
                  label={({ name, percent }: any) => `${name} ${((percent || 0) * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Box>
        </Paper>
      </Grid>

      <Grid size={{ xs: 12, md: 4 }}>
        <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column', height: 300 }}>
          <Typography component="h2" variant="h6" color="primary" gutterBottom>
            质疑 (Query) 状态
          </Typography>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={stats.charts.query_status}
              margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" name="数量" fill="#82ca9d" />
            </BarChart>
          </ResponsiveContainer>
        </Paper>
      </Grid>

      <Grid size={{ xs: 12, md: 4 }}>
        <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column', height: 300 }}>
          <Typography component="h2" variant="h6" color="primary" gutterBottom>
            访视 (Visit) 状态
          </Typography>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={stats.charts.visit_status}
              margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" name="数量" fill="#ffc658" />
            </BarChart>
          </ResponsiveContainer>
        </Paper>
      </Grid>

      <Grid size={{ xs: 12, md: 6 }}>
        <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column', height: 300 }}>
          <Typography component="h2" variant="h6" color="primary" gutterBottom>
            方案违背 (Protocol Deviation) 状态
          </Typography>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={stats.charts.deviation_status}
              margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" name="数量" fill="#ff8042" />
            </BarChart>
          </ResponsiveContainer>
        </Paper>
      </Grid>

      <Grid size={{ xs: 12, md: 6 }}>
        <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column', height: 300 }}>
          <Typography component="h2" variant="h6" color="primary" gutterBottom>
            监查访视 (Monitoring Visit) 状态
          </Typography>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={stats.charts.monitoring_status}
              margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" name="数量" fill="#8884d8" />
            </BarChart>
          </ResponsiveContainer>
        </Paper>
      </Grid>
    </Grid>
  );
};

export default Dashboard;
