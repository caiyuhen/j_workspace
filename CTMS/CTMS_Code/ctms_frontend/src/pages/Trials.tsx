import React, { useEffect, useState } from 'react';
import { DataGrid, type GridColDef, type GridRenderCellParams } from '@mui/x-data-grid';
import { Typography, Paper, Chip, Button, Box, Dialog, DialogTitle, DialogContent, DialogActions, TextField, MenuItem } from '@mui/material';
import { Add as AddIcon, Download as DownloadIcon } from '@mui/icons-material';
import api from '../api/axios';

interface Trial {
  id: number;
  protocol_number: string;
  title: string;
  phase: string;
  sponsor: string;
  status: string;
  project_manager: number; // or object depending on serializer
  start_date?: string;
  end_date?: string;
  description?: string;
  irb_approval_date?: string;
  irb_approval_number?: string;
  db_lock_date?: string;
  archive_date?: string;
}

const PHASE_CHOICES = [
  { value: 'I', label: 'I期' },
  { value: 'II', label: 'II期' },
  { value: 'III', label: 'III期' },
  { value: 'IV', label: 'IV期' },
  { value: 'BE', label: '生物等效性' },
];

const STATUS_CHOICES = [
  { value: 'DRAFT', label: '草稿' },
  { value: 'SUBMITTED', label: '已提交伦理' },
  { value: 'APPROVED', label: '伦理已批' },
  { value: 'ACTIVE', label: '进行中' },
  { value: 'LOCKED', label: '已锁库' },
  { value: 'COMPLETED', label: '已完成' },
  { value: 'TERMINATED', label: '已终止' },
];

const Trials: React.FC = () => {
  const [trials, setTrials] = useState<Trial[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);
  
  // Dialog State
  const [open, setOpen] = useState(false);
  const [newTrial, setNewTrial] = useState<Partial<Trial>>({
    protocol_number: '',
    title: '',
    phase: 'I',
    sponsor: '',
    status: 'DRAFT',
    description: '',
    irb_approval_date: '',
    irb_approval_number: '',
    db_lock_date: '',
    archive_date: '',
    start_date: '',
    end_date: '',
  });

  const fetchTrials = React.useCallback(async () => {
    setLoading(true);
    try {
      // API page is 1-based
      const response = await api.get(`trials/?page=${page + 1}&page_size=${pageSize}`);
      setTrials(response.data.results);
      setTotal(response.data.count);
    } catch (error) {
      console.error('Failed to fetch trials:', error);
    } finally {
      setLoading(false);
    }
  }, [page, pageSize]);

  useEffect(() => {
    fetchTrials();
  }, [fetchTrials]);

  const handleCreate = async () => {
    try {
      await api.post('trials/', newTrial);
      setOpen(false);
      fetchTrials();
      // Reset form
      setNewTrial({
        protocol_number: '',
        title: '',
        phase: 'I',
        sponsor: '',
        status: 'DRAFT',
        description: '',
        irb_approval_date: '',
        irb_approval_number: '',
        db_lock_date: '',
        archive_date: '',
        start_date: '',
        end_date: '',
      });
    } catch (err) {
      console.error('Failed to create trial:', err);
      alert('创建失败，请检查输入');
    }
  };

  const handleExport = () => {
    // Client-side export with BOM for Excel compatibility
    const headers = "ID,方案编号,项目名称,分期,申办方,状态,伦理批准日期,锁库日期,归档日期\n";
    const rows = trials.map(t => {
      const statusLabel = STATUS_CHOICES.find(c => c.value === t.status)?.label || t.status;
      // Handle commas in content by wrapping in quotes and escaping internal quotes
      const title = `"${(t.title || '').replace(/"/g, '""')}"`;
      const sponsor = `"${(t.sponsor || '').replace(/"/g, '""')}"`;
      const protocol = `"${(t.protocol_number || '').replace(/"/g, '""')}"`;
      const phase = `"${(t.phase || '').replace(/"/g, '""')}"`;
      const status = `"${(statusLabel || '').replace(/"/g, '""')}"`;
      const irbDate = `"${t.irb_approval_date || ''}"`;
      const dbDate = `"${t.db_lock_date || ''}"`;
      const archiveDate = `"${t.archive_date || ''}"`;
      
      return `${t.id},${protocol},${title},${phase},${sponsor},${status},${irbDate},${dbDate},${archiveDate}`;
    }).join("\n");

    const csvContent = "data:text/csv;charset=utf-8,%EF%BB%BF" + encodeURIComponent(headers + rows);
    const link = document.createElement("a");
    link.setAttribute("href", csvContent);
    link.setAttribute("download", "trials_export.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const columns: GridColDef[] = [
    { field: 'protocol_number', headerName: '方案编号', width: 150 },
    { field: 'title', headerName: '项目名称', width: 300 },
    { field: 'phase', headerName: '分期', width: 100 },
    { field: 'sponsor', headerName: '申办方', width: 200 },
    { field: 'irb_approval_date', headerName: '伦理批准日期', width: 120 },
    { field: 'db_lock_date', headerName: '锁库日期', width: 120 },
    { field: 'archive_date', headerName: '归档日期', width: 120 },
    { 
      field: 'status', 
      headerName: '状态', 
      width: 150,
      renderCell: (params: GridRenderCellParams) => (
        <Chip label={STATUS_CHOICES.find(c => c.value === params.value)?.label || params.value} color="primary" variant="outlined" />
      )
    },
  ];

  return (
    <Paper sx={{ height: 700, width: '100%', p: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
        <Typography variant="h4">项目管理</Typography>
        <Box>
          <Button 
            variant="contained" 
            startIcon={<AddIcon />} 
            onClick={() => setOpen(true)}
            sx={{ mr: 1 }}
          >
            新建项目
          </Button>
          <Button 
            variant="outlined" 
            startIcon={<DownloadIcon />} 
            onClick={handleExport}
          >
            导出列表
          </Button>
        </Box>
      </Box>
      
      <DataGrid
        rows={trials}
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

      <Dialog open={open} onClose={() => setOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>新建临床试验项目</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
            <TextField
              label="方案编号"
              value={newTrial.protocol_number}
              onChange={(e) => setNewTrial({ ...newTrial, protocol_number: e.target.value })}
              fullWidth
              required
            />
            <TextField
              label="项目名称"
              value={newTrial.title}
              onChange={(e) => setNewTrial({ ...newTrial, title: e.target.value })}
              fullWidth
              required
            />
            <TextField
              select
              label="试验分期"
              value={newTrial.phase}
              onChange={(e) => setNewTrial({ ...newTrial, phase: e.target.value })}
              fullWidth
            >
              {PHASE_CHOICES.map((option) => (
                <MenuItem key={option.value} value={option.value}>
                  {option.label}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              label="申办方"
              value={newTrial.sponsor}
              onChange={(e) => setNewTrial({ ...newTrial, sponsor: e.target.value })}
              fullWidth
              required
            />
            <TextField
              select
              label="项目状态"
              value={newTrial.status}
              onChange={(e) => setNewTrial({ ...newTrial, status: e.target.value })}
              fullWidth
            >
              {STATUS_CHOICES.map((option) => (
                <MenuItem key={option.value} value={option.value}>
                  {option.label}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              label="项目描述"
              value={newTrial.description}
              onChange={(e) => setNewTrial({ ...newTrial, description: e.target.value })}
              fullWidth
              multiline
              rows={3}
            />
            <TextField
              label="开始日期"
              type="date"
              fullWidth
              InputLabelProps={{ shrink: true }}
              value={newTrial.start_date}
              onChange={(e) => setNewTrial({ ...newTrial, start_date: e.target.value })}
            />
            <TextField
              label="结束日期"
              type="date"
              fullWidth
              InputLabelProps={{ shrink: true }}
              value={newTrial.end_date}
              onChange={(e) => setNewTrial({ ...newTrial, end_date: e.target.value })}
            />
            <TextField
              label="伦理批件号"
              fullWidth
              value={newTrial.irb_approval_number}
              onChange={(e) => setNewTrial({ ...newTrial, irb_approval_number: e.target.value })}
            />
            <TextField
              label="伦理批准日期"
              type="date"
              fullWidth
              InputLabelProps={{ shrink: true }}
              value={newTrial.irb_approval_date}
              onChange={(e) => setNewTrial({ ...newTrial, irb_approval_date: e.target.value })}
            />
            <TextField
              label="锁库日期"
              type="date"
              fullWidth
              InputLabelProps={{ shrink: true }}
              value={newTrial.db_lock_date}
              onChange={(e) => setNewTrial({ ...newTrial, db_lock_date: e.target.value })}
            />
            <TextField
              label="归档日期"
              type="date"
              fullWidth
              InputLabelProps={{ shrink: true }}
              value={newTrial.archive_date}
              onChange={(e) => setNewTrial({ ...newTrial, archive_date: e.target.value })}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>取消</Button>
          <Button onClick={handleCreate} variant="contained">创建</Button>
        </DialogActions>
      </Dialog>
    </Paper>
  );
};

export default Trials;
