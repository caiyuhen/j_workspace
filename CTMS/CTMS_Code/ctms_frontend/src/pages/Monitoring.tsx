import React, { useEffect, useState } from 'react';
import { DataGrid, type GridColDef, type GridRenderCellParams } from '@mui/x-data-grid';
import { Typography, Paper, Chip, Tabs, Tab, Box, Button, Dialog, DialogTitle, DialogContent, DialogActions, TextField, MenuItem, Stack } from '@mui/material';
import { Add as AddIcon, Download as DownloadIcon } from '@mui/icons-material';
import api from '../api/axios';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function CustomTabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`simple-tabpanel-${index}`}
      aria-labelledby={`simple-tab-${index}`}
      {...other}
      style={{ height: '100%', width: '100%' }}
    >
      {value === index && (
        <Box sx={{ p: 2, height: '100%' }}>
          {children}
        </Box>
      )}
    </div>
  );
}

interface MonitoringVisit {
  id: number;
  site: number;
  monitor: number;
  visit_type: string;
  status: string;
  planned_date: string;
  actual_date: string;
}

interface ProtocolDeviation {
  id: number;
  trial: number;
  site: number;
  subject: number;
  description: string;
  date_occurred: string;
  severity: string;
  status: string;
}

interface Query {
  id: number;
  visit: number;
  query_text: string;
  raised_by: number;
  answer_text: string;
  answered_by: number | null;
  status: string;
  created_at: string;
}

const VISIT_TYPE_CHOICES = [
  { value: 'SSV', label: '中心筛选访视 (SSV)' },
  { value: 'SIV', label: '中心启动访视 (SIV)' },
  { value: 'RMV', label: '常规监查访视 (RMV)' },
  { value: 'COV', label: '中心关闭访视 (COV)' },
];

const VISIT_STATUS_CHOICES = [
  { value: 'PLANNED', label: '计划中' },
  { value: 'SCHEDULED', label: '已排期' },
  { value: 'COMPLETED', label: '已完成' },
  { value: 'REPORT_DRAFT', label: '报告草稿' },
  { value: 'REPORT_FINAL', label: '报告已完成' },
  { value: 'CANCELED', label: '已取消' },
];

const DEVIATION_SEVERITY_CHOICES = [
  { value: 'MINOR', label: '轻微' },
  { value: 'MAJOR', label: '重大' },
  { value: 'CRITICAL', label: '严重' },
];

const DEVIATION_STATUS_CHOICES = [
  { value: 'OPEN', label: '开启' },
  { value: 'RESOLVED', label: '已解决' },
  { value: 'CAPA_REQUIRED', label: '需 CAPA' },
];

const QUERY_STATUS_CHOICES = [
  { value: 'OPEN', label: '开启' },
  { value: 'ANSWERED', label: '已回复' },
  { value: 'CLOSED', label: '已关闭' },
  { value: 'CANCELLED', label: '已取消' },
];

const Monitoring: React.FC = () => {
  const [value, setValue] = useState(0);
  
  // Monitoring Visits State
  const [visits, setVisits] = useState<MonitoringVisit[]>([]);
  const [loadingVisits, setLoadingVisits] = useState(true);
  const [totalVisits, setTotalVisits] = useState(0);
  const [pageVisits, setPageVisits] = useState(0);
  const [pageSizeVisits, setPageSizeVisits] = useState(10);
  
  // Visit Dialog State
  const [visitOpen, setVisitOpen] = useState(false);
  const [newVisit, setNewVisit] = useState<Partial<MonitoringVisit>>({
    site: 1,
    monitor: 1,
    visit_type: 'RMV',
    status: 'PLANNED',
    planned_date: new Date().toISOString().split('T')[0],
  });

  // Protocol Deviations State
  const [deviations, setDeviations] = useState<ProtocolDeviation[]>([]);
  const [loadingDeviations, setLoadingDeviations] = useState(true);
  const [totalDeviations, setTotalDeviations] = useState(0);
  const [pageDeviations, setPageDeviations] = useState(0);
  const [pageSizeDeviations, setPageSizeDeviations] = useState(10);

  // Deviation Dialog State
  const [devOpen, setDevOpen] = useState(false);
  const [newDev, setNewDev] = useState<Partial<ProtocolDeviation>>({
    trial: 1,
    site: 1,
    subject: 1,
    description: '',
    date_occurred: new Date().toISOString().split('T')[0],
    severity: 'MINOR',
    status: 'OPEN',
  });

  // Queries State
  const [queries, setQueries] = useState<Query[]>([]);
  const [loadingQueries, setLoadingQueries] = useState(true);
  const [totalQueries, setTotalQueries] = useState(0);
  const [pageQueries, setPageQueries] = useState(0);
  const [pageSizeQueries, setPageSizeQueries] = useState(10);

  // Query Dialog State
  const [queryOpen, setQueryOpen] = useState(false);
  const [newQuery, setNewQuery] = useState<Partial<Query>>({
    visit: 1,
    query_text: '',
    status: 'OPEN',
  });

  // Query Answer Dialog State
  const [answerOpen, setAnswerOpen] = useState(false);
  const [selectedQuery, setSelectedQuery] = useState<Query | null>(null);
  const [answerText, setAnswerText] = useState('');

  const handleChange = (_: React.SyntheticEvent, newValue: number) => {
    setValue(newValue);
  };

  const fetchVisits = React.useCallback(async () => {
    setLoadingVisits(true);
    try {
      const response = await api.get(`monitoring-visits/?page=${pageVisits + 1}&page_size=${pageSizeVisits}`);
      setVisits(response.data.results);
      setTotalVisits(response.data.count);
    } catch (err) {
      console.error('Failed to fetch monitoring visits:', err);
    } finally {
      setLoadingVisits(false);
    }
  }, [pageVisits, pageSizeVisits]);

  const fetchDeviations = React.useCallback(async () => {
    setLoadingDeviations(true);
    try {
      const response = await api.get(`protocol-deviations/?page=${pageDeviations + 1}&page_size=${pageSizeDeviations}`);
      setDeviations(response.data.results);
      setTotalDeviations(response.data.count);
    } catch (error) {
      console.error('Failed to fetch protocol deviations:', error);
    } finally {
      setLoadingDeviations(false);
    }
  }, [pageDeviations, pageSizeDeviations]);

  const fetchQueries = React.useCallback(async () => {
    setLoadingQueries(true);
    try {
      const response = await api.get(`queries/?page=${pageQueries + 1}&page_size=${pageSizeQueries}`);
      setQueries(response.data.results);
      setTotalQueries(response.data.count);
    } catch (error) {
      console.error('Failed to fetch queries:', error);
    } finally {
      setLoadingQueries(false);
    }
  }, [pageQueries, pageSizeQueries]);

  useEffect(() => {
    if (value === 0) fetchVisits();
    else if (value === 1) fetchDeviations();
    else fetchQueries();
  }, [value, fetchVisits, fetchDeviations, fetchQueries]);

  const handleCreateVisit = async () => {
    try {
      await api.post('monitoring-visits/', newVisit);
      setVisitOpen(false);
      fetchVisits();
      setNewVisit({
        site: 1,
        monitor: 1,
        visit_type: 'RMV',
        status: 'PLANNED',
        planned_date: new Date().toISOString().split('T')[0],
      });
    } catch (err) {
      console.error('Failed to create visit:', err);
      alert('创建失败，请检查输入');
    }
  };

  const handleCreateDev = async () => {
    try {
      await api.post('protocol-deviations/', {
        ...newDev,
        date_identified: new Date().toISOString().split('T')[0], // Backend requires date_identified
      });
      setDevOpen(false);
      fetchDeviations();
      setNewDev({
        trial: 1,
        site: 1,
        subject: 1,
        description: '',
        date_occurred: new Date().toISOString().split('T')[0],
        severity: 'MINOR',
        status: 'OPEN',
      });
    } catch (error) {
      console.error('Failed to create deviation:', error);
      alert('创建失败，请检查输入');
    }
  };

  const handleCreateQuery = async () => {
    try {
      await api.post('queries/', newQuery);
      setQueryOpen(false);
      fetchQueries();
      setNewQuery({
        visit: 1,
        query_text: '',
        status: 'OPEN',
      });
    } catch (error) {
      console.error('Failed to create query:', error);
      alert('创建失败，请检查输入');
    }
  };

  const handleAnswerQuery = async () => {
    if (!selectedQuery) return;
    try {
      await api.patch(`queries/${selectedQuery.id}/`, {
        answer_text: answerText,
        status: 'ANSWERED',
        answered_by: 1 // Default to current user
      });
      setAnswerOpen(false);
      fetchQueries();
    } catch (err) {
      console.error('Failed to answer query:', err);
      alert('回复失败');
    }
  };

  const handleExportVisits = () => {
    const headers = "ID,中心ID,监查员ID,类型,状态,计划日期,实际日期\n";
    const rows = visits.map(v => {
      const typeLabel = VISIT_TYPE_CHOICES.find(t => t.value === v.visit_type)?.label || v.visit_type;
      const statusLabel = VISIT_STATUS_CHOICES.find(s => s.value === v.status)?.label || v.status;
      
      const type = `"${(typeLabel || '').replace(/"/g, '""')}"`;
      const status = `"${(statusLabel || '').replace(/"/g, '""')}"`;
      const pDate = `"${v.planned_date}"`;
      const aDate = `"${v.actual_date || ''}"`;
      
      return `${v.id},${v.site},${v.monitor},${type},${status},${pDate},${aDate}`;
    }).join("\n");

    const csvContent = "data:text/csv;charset=utf-8,%EF%BB%BF" + encodeURIComponent(headers + rows);
    const link = document.createElement("a");
    link.setAttribute("href", csvContent);
    link.setAttribute("download", `monitoring_visits_export_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleExportDeviations = () => {
    const headers = "ID,项目ID,中心ID,受试者ID,描述,发生日期,严重程度,状态\n";
    const rows = deviations.map(d => {
      const severityLabel = DEVIATION_SEVERITY_CHOICES.find(s => s.value === d.severity)?.label || d.severity;
      const statusLabel = DEVIATION_STATUS_CHOICES.find(s => s.value === d.status)?.label || d.status;
      
      const desc = `"${(d.description || '').replace(/"/g, '""')}"`;
      const severity = `"${(severityLabel || '').replace(/"/g, '""')}"`;
      const status = `"${(statusLabel || '').replace(/"/g, '""')}"`;
      const date = `"${d.date_occurred}"`;
      
      return `${d.id},${d.trial},${d.site},${d.subject},${desc},${date},${severity},${status}`;
    }).join("\n");

    const csvContent = "data:text/csv;charset=utf-8,%EF%BB%BF" + encodeURIComponent(headers + rows);
    const link = document.createElement("a");
    link.setAttribute("href", csvContent);
    link.setAttribute("download", `protocol_deviations_export_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleExportQueries = () => {
    const headers = "ID,访视ID,质疑内容,提出人ID,回复内容,回复人ID,状态,创建时间\n";
    const rows = queries.map(q => {
      const statusLabel = QUERY_STATUS_CHOICES.find(s => s.value === q.status)?.label || q.status;
      
      const queryText = `"${(q.query_text || '').replace(/"/g, '""')}"`;
      const answerText = `"${(q.answer_text || '').replace(/"/g, '""')}"`;
      const status = `"${(statusLabel || '').replace(/"/g, '""')}"`;
      const date = `"${q.created_at}"`;
      
      return `${q.id},${q.visit},${queryText},${q.raised_by},${answerText},${q.answered_by || ''},${status},${date}`;
    }).join("\n");

    const csvContent = "data:text/csv;charset=utf-8,%EF%BB%BF" + encodeURIComponent(headers + rows);
    const link = document.createElement("a");
    link.setAttribute("href", csvContent);
    link.setAttribute("download", `queries_export_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const visitColumns: GridColDef[] = [
    { field: 'site', headerName: '中心 ID', width: 80 },
    { field: 'monitor', headerName: '监查员 ID', width: 100 },
    { 
      field: 'visit_type', 
      headerName: '类型', 
      width: 150,
      valueFormatter: (value) => VISIT_TYPE_CHOICES.find(t => t.value === value)?.label || value
    },
    { 
      field: 'status', 
      headerName: '状态', 
      width: 120,
      renderCell: (params: GridRenderCellParams) => {
        const color = params.value === 'COMPLETED' ? 'success' : 'default';
        const label = VISIT_STATUS_CHOICES.find(s => s.value === params.value)?.label || params.value;
        return <Chip label={label} color={color} size="small" />;
      }
    },
    { field: 'planned_date', headerName: '计划日期', width: 120 },
    { field: 'actual_date', headerName: '实际日期', width: 120 },
  ];

  const deviationColumns: GridColDef[] = [
    { field: 'trial', headerName: '项目 ID', width: 80 },
    { field: 'site', headerName: '中心 ID', width: 80 },
    { field: 'subject', headerName: '受试者 ID', width: 100 },
    { field: 'description', headerName: '描述', width: 250 },
    { field: 'date_occurred', headerName: '发生日期', width: 120 },
    { 
      field: 'severity', 
      headerName: '严重程度', 
      width: 120,
      renderCell: (params: GridRenderCellParams) => {
        const color = params.value === 'CRITICAL' ? 'error' : params.value === 'MAJOR' ? 'warning' : 'default';
        const label = DEVIATION_SEVERITY_CHOICES.find(s => s.value === params.value)?.label || params.value;
        return <Chip label={label} color={color} size="small" />;
      }
    },
    { 
      field: 'status', 
      headerName: '状态', 
      width: 120,
      valueFormatter: (value) => DEVIATION_STATUS_CHOICES.find(s => s.value === value)?.label || value
    },
  ];

  const queryColumns: GridColDef[] = [
    { field: 'visit', headerName: '访视 ID', width: 80 },
    { field: 'query_text', headerName: '质疑内容', width: 250 },
    { field: 'raised_by', headerName: '提出人 ID', width: 100 },
    { field: 'answer_text', headerName: '回复内容', width: 250 },
    { 
      field: 'status', 
      headerName: '状态', 
      width: 120, 
      renderCell: (params: GridRenderCellParams) => {
        const color = params.value === 'CLOSED' ? 'success' : 'warning';
        const label = QUERY_STATUS_CHOICES.find(s => s.value === params.value)?.label || params.value;
        return <Chip label={label} color={color} size="small" />;
      }
    },
    { 
      field: 'actions', 
      headerName: '操作', 
      width: 120,
      renderCell: (params: GridRenderCellParams) => (
        <Button 
          size="small" 
          onClick={() => {
            setSelectedQuery(params.row);
            setAnswerText(params.row.answer_text || '');
            setAnswerOpen(true);
          }}
          disabled={params.row.status === 'CLOSED'}
        >
          回复
        </Button>
      )
    }
  ];

  return (
    <Paper sx={{ height: 800, width: '100%', p: 2 }}>
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
        <Tabs value={value} onChange={handleChange} aria-label="monitoring tabs">
          <Tab label="监查访视" />
          <Tab label="方案违背" />
          <Tab label="质疑管理 (Queries)" />
        </Tabs>
      </Box>
      
      <CustomTabPanel value={value} index={0}>
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
          <Button 
            variant="contained" 
            startIcon={<AddIcon />} 
            onClick={() => setVisitOpen(true)}
            sx={{ mr: 1 }}
          >
            新建访视
          </Button>
          <Button 
            variant="outlined" 
            startIcon={<DownloadIcon />} 
            onClick={handleExportVisits}
          >
            导出访视
          </Button>
        </Box>
        <DataGrid
          rows={visits}
          columns={visitColumns}
          loading={loadingVisits}
          rowCount={totalVisits}
          paginationModel={{ page: pageVisits, pageSize: pageSizeVisits }}
          onPaginationModelChange={(model) => {
            setPageVisits(model.page);
            setPageSizeVisits(model.pageSize);
          }}
          pageSizeOptions={[5, 10, 20]}
          paginationMode="server"
          disableRowSelectionOnClick
        />
      </CustomTabPanel>

      <CustomTabPanel value={value} index={1}>
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
          <Button 
            variant="contained" 
            startIcon={<AddIcon />} 
            onClick={() => setDevOpen(true)}
            sx={{ mr: 1 }}
          >
            记录违背
          </Button>
          <Button 
            variant="outlined" 
            startIcon={<DownloadIcon />} 
            onClick={handleExportDeviations}
          >
            导出违背
          </Button>
        </Box>
        <DataGrid
          rows={deviations}
          columns={deviationColumns}
          loading={loadingDeviations}
          rowCount={totalDeviations}
          paginationModel={{ page: pageDeviations, pageSize: pageSizeDeviations }}
          onPaginationModelChange={(model) => {
            setPageDeviations(model.page);
            setPageSizeDeviations(model.pageSize);
          }}
          pageSizeOptions={[5, 10, 20]}
          paginationMode="server"
          disableRowSelectionOnClick
        />
      </CustomTabPanel>

      <CustomTabPanel value={value} index={2}>
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
          <Button 
            variant="contained" 
            startIcon={<AddIcon />} 
            onClick={() => setQueryOpen(true)}
            sx={{ mr: 1 }}
          >
            提出质疑
          </Button>
          <Button 
            variant="outlined" 
            startIcon={<DownloadIcon />} 
            onClick={handleExportQueries}
          >
            导出质疑
          </Button>
        </Box>
        <DataGrid
          rows={queries}
          columns={queryColumns}
          loading={loadingQueries}
          rowCount={totalQueries}
          paginationModel={{ page: pageQueries, pageSize: pageSizeQueries }}
          onPaginationModelChange={(model) => {
            setPageQueries(model.page);
            setPageSizeQueries(model.pageSize);
          }}
          pageSizeOptions={[5, 10, 20]}
          paginationMode="server"
          disableRowSelectionOnClick
        />
      </CustomTabPanel>

      {/* Visit Dialog */}
      <Dialog open={visitOpen} onClose={() => setVisitOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>新建监查访视</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField
              select
              label="类型"
              value={newVisit.visit_type}
              onChange={(e) => setNewVisit({ ...newVisit, visit_type: e.target.value })}
              fullWidth
            >
              {VISIT_TYPE_CHOICES.map((option) => (
                <MenuItem key={option.value} value={option.value}>
                  {option.label}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              label="计划日期"
              type="date"
              value={newVisit.planned_date}
              onChange={(e) => setNewVisit({ ...newVisit, planned_date: e.target.value })}
              fullWidth
              InputLabelProps={{ shrink: true }}
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setVisitOpen(false)}>取消</Button>
          <Button onClick={handleCreateVisit} variant="contained">创建</Button>
        </DialogActions>
      </Dialog>

      {/* Deviation Dialog */}
      <Dialog open={devOpen} onClose={() => setDevOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>记录方案违背</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField
              label="描述"
              value={newDev.description}
              onChange={(e) => setNewDev({ ...newDev, description: e.target.value })}
              fullWidth
              multiline
              rows={3}
            />
            <TextField
              select
              label="严重程度"
              value={newDev.severity}
              onChange={(e) => setNewDev({ ...newDev, severity: e.target.value })}
              fullWidth
            >
              {DEVIATION_SEVERITY_CHOICES.map((option) => (
                <MenuItem key={option.value} value={option.value}>
                  {option.label}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              label="发生日期"
              type="date"
              value={newDev.date_occurred}
              onChange={(e) => setNewDev({ ...newDev, date_occurred: e.target.value })}
              fullWidth
              InputLabelProps={{ shrink: true }}
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDevOpen(false)}>取消</Button>
          <Button onClick={handleCreateDev} variant="contained">提交</Button>
        </DialogActions>
      </Dialog>

      {/* Query Dialog */}
      <Dialog open={queryOpen} onClose={() => setQueryOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>提出质疑</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField
              label="质疑内容"
              value={newQuery.query_text}
              onChange={(e) => setNewQuery({ ...newQuery, query_text: e.target.value })}
              fullWidth
              multiline
              rows={3}
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setQueryOpen(false)}>取消</Button>
          <Button onClick={handleCreateQuery} variant="contained">提交</Button>
        </DialogActions>
      </Dialog>

      {/* Answer Dialog */}
      <Dialog open={answerOpen} onClose={() => setAnswerOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>回复质疑</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <Typography variant="body2" color="textSecondary">
              质疑内容: {selectedQuery?.query_text}
            </Typography>
            <TextField
              label="回复内容"
              value={answerText}
              onChange={(e) => setAnswerText(e.target.value)}
              fullWidth
              multiline
              rows={3}
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAnswerOpen(false)}>取消</Button>
          <Button onClick={handleAnswerQuery} variant="contained">回复</Button>
        </DialogActions>
      </Dialog>
    </Paper>
  );
};

export default Monitoring;
