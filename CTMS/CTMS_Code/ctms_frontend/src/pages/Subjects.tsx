import React, { useEffect, useState } from 'react';
import { DataGrid, type GridColDef, type GridRenderCellParams } from '@mui/x-data-grid';
import { 
  Typography, Paper, Chip, Button, Box, Dialog, DialogTitle, 
  DialogContent, DialogActions, TextField, MenuItem, Stack, IconButton, Tooltip 
} from '@mui/material';
import { 
  Add as AddIcon, Download as DownloadIcon, Assignment as VisitIcon,
  CheckCircle as CheckCircleIcon, VerifiedUser as VerifiedUserIcon,
  Edit as EditIcon
} from '@mui/icons-material';
import api from '../api/axios';
import { AxiosError } from 'axios';

interface Subject {
  id: number;
  site: number;
  subject_initials: string;
  subject_number: string;
  status: string;
  informed_consent_date: string;
}

interface Visit {
  id: number;
  subject: number;
  visit_name: string;
  visit_date: string;
  status: string;
  data_status: string;
  is_monitored: boolean;
  data: Record<string, string | number | boolean | null>;
  monitored_by_details?: { username: string };
  monitored_at?: string;
}

const STATUS_CHOICES = [
  { value: 'SCREENING', label: '筛选中' },
  { value: 'SCREEN_FAIL', label: '筛选失败' },
  { value: 'ENROLLED', label: '已入组' },
  { value: 'ACTIVE', label: '进行中' },
  { value: 'COMPLETED', label: '已完成' },
  { value: 'WITHDRAWN', label: '已退出' },
];

const Subjects: React.FC = () => {
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);
  
  // Create Subject Dialog
  const [open, setOpen] = useState(false);
  const [newSubject, setNewSubject] = useState<Partial<Subject>>({
    site: 1,
    subject_initials: '',
    subject_number: '',
    status: 'SCREENING',
    informed_consent_date: new Date().toISOString().split('T')[0],
  });

  // Visits Dialog
  const [visitDialogOpen, setVisitDialogOpen] = useState(false);
  const [currentSubject, setCurrentSubject] = useState<Subject | null>(null);
  const [visits, setVisits] = useState<Visit[]>([]);
  const [visitLoading, setVisitLoading] = useState(false);

  // Signature Dialog
  const [signDialogOpen, setSignDialogOpen] = useState(false);
  const [signatureData, setSignatureData] = useState({ password: '', reason: 'SDV Confirmation' });
  const [selectedVisitId, setSelectedVisitId] = useState<number | null>(null);

  // Data Entry Dialog
  const [dataDialogOpen, setDataDialogOpen] = useState(false);
  const [currentVisit, setCurrentVisit] = useState<Visit | null>(null);
  const [visitData, setVisitData] = useState<Record<string, string | number | boolean | null>>({});

  const fetchSubjects = React.useCallback(async () => {
    setLoading(true);
    try {
      const response = await api.get(`subjects/?page=${page + 1}&page_size=${pageSize}`);
      setSubjects(response.data.results);
      setTotal(response.data.count);
    } catch (error) {
      console.error('Failed to fetch subjects:', error);
    } finally {
      setLoading(false);
    }
  }, [page, pageSize]);

  useEffect(() => {
    fetchSubjects();
  }, [fetchSubjects]);

  const handleCreate = async () => {
    try {
      await api.post('subjects/', newSubject);
      setOpen(false);
      fetchSubjects();
      setNewSubject({
        site: 1,
        subject_initials: '',
        subject_number: '',
        status: 'SCREENING',
        informed_consent_date: new Date().toISOString().split('T')[0],
      });
    } catch (error) {
      console.error('Failed to create subject:', error);
      alert('创建失败，请检查输入');
    }
  };

  const handleOpenVisits = async (subject: Subject) => {
    setCurrentSubject(subject);
    setVisitDialogOpen(true);
    setVisitLoading(true);
    try {
      const response = await api.get(`visits/?subject=${subject.id}`);
      setVisits(response.data.results || response.data);
    } catch (err) {
      console.error('Failed to fetch visits:', err);
    } finally {
      setVisitLoading(false);
    }
  };

  const handleSDV = async (visitId: number) => {
    try {
      await api.post(`visits/${visitId}/sdv/`);
      if (currentSubject) handleOpenVisits(currentSubject); // Refresh
      alert('SDV 操作成功');
    } catch (error) {
      console.error('Failed to SDV visit:', error);
      alert('SDV 操作失败：权限不足或网络错误');
    }
  };

  const handleOpenDataEntry = (visit: Visit) => {
    setCurrentVisit(visit);
    setVisitData(visit.data || {
      weight: '',
      height: '',
      systolic_bp: '',
      diastolic_bp: '',
      temperature: '',
      notes: ''
    });
    setDataDialogOpen(true);
  };

  const handleSaveData = async () => {
    if (!currentVisit) return;
    try {
      await api.patch(`visits/${currentVisit.id}/`, { 
        data: visitData,
        data_status: 'PARTIAL' // Or COMPLETE based on logic, keeping simple for now
      });
      setDataDialogOpen(false);
      if (currentSubject) handleOpenVisits(currentSubject);
      alert('数据保存成功');
    } catch (error) {
      console.error('Failed to save visit data:', error);
      alert('数据保存失败');
    }
  };

  const handleOpenSign = (visitId: number) => {
    setSelectedVisitId(visitId);
    setSignatureData({ password: '', reason: 'Investigator Approval' });
    setSignDialogOpen(true);
  };

  const handleSign = async () => {
    if (!signatureData.password) {
      alert('请输入密码进行电子签名');
      return;
    }
    
    try {
      await api.post(`visits/${selectedVisitId}/sign/`, { 
        password: signatureData.password,
        reason: signatureData.reason
      });
      
      setSignDialogOpen(false);
      if (currentSubject) handleOpenVisits(currentSubject);
      alert('电子签名成功');
    } catch (err) {
      console.error('Failed to sign visit:', err);
      let errorMessage = '签名失败，请检查密码';
      if (err instanceof AxiosError && err.response?.data?.detail) {
        errorMessage = err.response.data.detail;
      }
      alert(errorMessage);
    }
  };

  const handleExport = () => {
    const headers = "ID,受试者编号,姓名缩写,中心ID,状态,知情同意日期\n";
    const rows = subjects.map(s => {
      const statusLabel = STATUS_CHOICES.find(c => c.value === s.status)?.label || s.status;
      const subjectNumber = `"${(s.subject_number || '').replace(/"/g, '""')}"`;
      const initials = `"${(s.subject_initials || '').replace(/"/g, '""')}"`;
      const site = `"${s.site}"`;
      const status = `"${(statusLabel || '').replace(/"/g, '""')}"`;
      const date = `"${s.informed_consent_date || ''}"`;
      
      return `${s.id},${subjectNumber},${initials},${site},${status},${date}`;
    }).join("\n");
    
    const csvContent = "data:text/csv;charset=utf-8,%EF%BB%BF" + encodeURIComponent(headers + rows);
    const link = document.createElement("a");
    link.setAttribute("href", csvContent);
    link.setAttribute("download", `subjects_export_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const columns: GridColDef[] = [
    { field: 'subject_number', headerName: '受试者编号', width: 150 },
    { field: 'subject_initials', headerName: '缩写', width: 100 },
    { field: 'site', headerName: '中心 ID', width: 100 },
    { 
      field: 'status', 
      headerName: '状态', 
      width: 150,
      renderCell: (params: GridRenderCellParams) => {
        let color: 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning' = 'default';
        if (params.value === 'ACTIVE') color = 'success';
        else if (params.value === 'SCREENING') color = 'warning';
        else if (params.value === 'COMPLETED') color = 'info';
        else if (params.value === 'WITHDRAWN') color = 'error';
        
        const label = STATUS_CHOICES.find(s => s.value === params.value)?.label || params.value;
        return <Chip label={label} color={color} size="small" />;
      }
    },
    { field: 'informed_consent_date', headerName: '知情同意日期', width: 150 },
    {
      field: 'actions',
      headerName: '操作',
      width: 150,
      renderCell: (params: GridRenderCellParams) => (
        <Button 
          startIcon={<VisitIcon />} 
          size="small" 
          onClick={() => handleOpenVisits(params.row)}
        >
          访视
        </Button>
      )
    }
  ];

  const visitColumns: GridColDef[] = [
    { field: 'visit_name', headerName: '访视名称', width: 150 },
    { field: 'visit_date', headerName: '访视日期', width: 150 },
    { field: 'status', headerName: '状态', width: 120 },
    { 
      field: 'data_status', 
      headerName: '数据状态', 
      width: 120,
      renderCell: (params) => {
        const color = params.value === 'SIGNED' ? 'success' : 
                      params.value === 'VERIFIED' ? 'info' : 'default';
        return <Chip label={params.value} color={color} size="small" />;
      }
    },
    {
      field: 'actions',
      headerName: '操作',
      width: 250,
      renderCell: (params) => (
        <Stack direction="row" spacing={1}>
          <Tooltip title="数据录入 (CRF)">
            <IconButton size="small" color="primary" onClick={() => handleOpenDataEntry(params.row)}>
              <EditIcon />
            </IconButton>
          </Tooltip>
          {params.row.data_status !== 'VERIFIED' && params.row.data_status !== 'SIGNED' && (
            <Tooltip title="Source Data Verification (SDV)">
              <IconButton size="small" color="info" onClick={() => handleSDV(params.row.id)}>
                <CheckCircleIcon />
              </IconButton>
            </Tooltip>
          )}
          {params.row.data_status === 'VERIFIED' && (
            <Tooltip title="电子签名">
              <IconButton size="small" color="secondary" onClick={() => handleOpenSign(params.row.id)}>
                <VerifiedUserIcon />
              </IconButton>
            </Tooltip>
          )}
        </Stack>
      )
    }
  ];

  return (
    <Paper sx={{ height: 600, width: '100%', p: 2 }}>
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h4">受试者管理</Typography>
        <Stack direction="row" spacing={2}>
          <Button 
            variant="contained" 
            startIcon={<AddIcon />}
            onClick={() => setOpen(true)}
          >
            新建受试者
          </Button>
          <Button 
            variant="outlined" 
            startIcon={<DownloadIcon />}
            onClick={handleExport}
          >
            导出CSV
          </Button>
        </Stack>
      </Stack>
      
      <DataGrid
        rows={subjects}
        columns={columns}
        loading={loading}
        rowCount={total}
        paginationModel={{ page, pageSize }}
        onPaginationModelChange={(model) => {
          setPage(model.page);
          setPageSize(model.pageSize);
        }}
        pageSizeOptions={[5, 10, 20]}
        paginationMode="server"
        disableRowSelectionOnClick
      />

      {/* Create Subject Dialog */}
      <Dialog open={open} onClose={() => setOpen(false)}>
        <DialogTitle>新建受试者</DialogTitle>
        <DialogContent>
          <Box component="form" sx={{ mt: 1, display: 'flex', flexDirection: 'column', gap: 2, minWidth: 400 }}>
            <TextField
              label="中心 ID"
              type="number"
              fullWidth
              value={newSubject.site}
              onChange={(e) => setNewSubject({ ...newSubject, site: Number(e.target.value) })}
            />
            <TextField
              label="受试者编号"
              fullWidth
              value={newSubject.subject_number}
              onChange={(e) => setNewSubject({ ...newSubject, subject_number: e.target.value })}
            />
            <TextField
              label="姓名缩写"
              fullWidth
              value={newSubject.subject_initials}
              onChange={(e) => setNewSubject({ ...newSubject, subject_initials: e.target.value })}
            />
            <TextField
              select
              label="状态"
              fullWidth
              value={newSubject.status}
              onChange={(e) => setNewSubject({ ...newSubject, status: e.target.value })}
            >
              {STATUS_CHOICES.map((option) => (
                <MenuItem key={option.value} value={option.value}>
                  {option.label}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              label="知情同意日期"
              type="date"
              fullWidth
              InputLabelProps={{ shrink: true }}
              value={newSubject.informed_consent_date}
              onChange={(e) => setNewSubject({ ...newSubject, informed_consent_date: e.target.value })}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>取消</Button>
          <Button onClick={handleCreate} variant="contained">提交</Button>
        </DialogActions>
      </Dialog>

      {/* Visits Dialog */}
      <Dialog open={visitDialogOpen} onClose={() => setVisitDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          访视管理 - {currentSubject?.subject_number} ({currentSubject?.subject_initials})
        </DialogTitle>
        <DialogContent>
          <Box sx={{ height: 400, width: '100%' }}>
            <DataGrid
              rows={visits}
              columns={visitColumns}
              loading={visitLoading}
              hideFooter
              disableRowSelectionOnClick
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setVisitDialogOpen(false)}>关闭</Button>
        </DialogActions>
      </Dialog>

      {/* Signature Dialog */}
      <Dialog open={signDialogOpen} onClose={() => setSignDialogOpen(false)}>
        <DialogTitle>电子签名</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="textSecondary" paragraph>
             本人声明上述数据真实有效。请输入密码确认签名。
             (符合 21 CFR Part 11 要求)
          </Typography>
          <Stack spacing={2} sx={{ mt: 1, minWidth: 300 }}>
            <TextField
              label="签名原因"
              fullWidth
              value={signatureData.reason}
              onChange={(e) => setSignatureData({...signatureData, reason: e.target.value})}
            />
            <TextField
              label="密码"
              type="password"
              fullWidth
              value={signatureData.password}
              onChange={(e) => setSignatureData({...signatureData, password: e.target.value})}
              helperText="请输入您的登录密码以确认签名"
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSignDialogOpen(false)}>取消</Button>
          <Button onClick={handleSign} variant="contained" color="primary">确认签名</Button>
        </DialogActions>
      </Dialog>
      {/* Data Entry Dialog */}
      <Dialog open={dataDialogOpen} onClose={() => setDataDialogOpen(false)}>
        <DialogTitle>访视数据录入 (CRF) - {currentVisit?.visit_name}</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1, minWidth: 400 }}>
            <TextField
              label="身高 (cm)"
              type="number"
              fullWidth
              value={visitData.height || ''}
              onChange={(e) => setVisitData({...visitData, height: e.target.value})}
            />
            <TextField
              label="体重 (kg)"
              type="number"
              fullWidth
              value={visitData.weight || ''}
              onChange={(e) => setVisitData({...visitData, weight: e.target.value})}
            />
            <Stack direction="row" spacing={2}>
              <TextField
                label="收缩压 (mmHg)"
                type="number"
                fullWidth
                value={visitData.systolic_bp || ''}
                onChange={(e) => setVisitData({...visitData, systolic_bp: e.target.value})}
              />
              <TextField
                label="舒张压 (mmHg)"
                type="number"
                fullWidth
                value={visitData.diastolic_bp || ''}
                onChange={(e) => setVisitData({...visitData, diastolic_bp: e.target.value})}
              />
            </Stack>
            <TextField
              label="体温 (°C)"
              type="number"
              fullWidth
              value={visitData.temperature || ''}
              onChange={(e) => setVisitData({...visitData, temperature: e.target.value})}
            />
            <TextField
              label="备注 / 其他数据"
              multiline
              rows={3}
              fullWidth
              value={visitData.notes || ''}
              onChange={(e) => setVisitData({...visitData, notes: e.target.value})}
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDataDialogOpen(false)}>取消</Button>
          <Button onClick={handleSaveData} variant="contained" color="primary">保存</Button>
        </DialogActions>
      </Dialog>
    </Paper>
  );
};

export default Subjects;