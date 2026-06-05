import React, { useEffect, useState } from 'react';
import { DataGrid, type GridColDef, type GridRenderCellParams } from '@mui/x-data-grid';
import { Typography, Paper, Chip, Button, Box, Dialog, DialogTitle, DialogContent, DialogActions, TextField, MenuItem } from '@mui/material';
import { Add as AddIcon, Download as DownloadIcon } from '@mui/icons-material';
import api from '../api/axios';

interface AdverseEvent {
  id: number;
  subject: number;
  event_term: string;
  onset_date: string;
  severity: string;
  is_serious: string;
  relationship: string;
  outcome: string;
  reporter: number;
}

const SEVERITY_CHOICES = [
  { value: 'MILD', label: '轻度' },
  { value: 'MODERATE', label: '中度' },
  { value: 'SEVERE', label: '重度' },
];

const SERIOUS_CHOICES = [
  { value: 'YES', label: '是 (SAE)' },
  { value: 'NO', label: '否 (AE)' },
];

const RELATIONSHIP_CHOICES = [
  { value: 'NOT_RELATED', label: '无关' },
  { value: 'UNLIKELY', label: '可能无关' },
  { value: 'POSSIBLY', label: '可能有关' },
  { value: 'PROBABLY', label: '很可能有关' },
  { value: 'DEFINITELY', label: '肯定有关' },
];

const OUTCOME_CHOICES = [
  { value: 'RECOVERED', label: '已恢复/已解决' },
  { value: 'RECOVERING', label: '恢复中/解决中' },
  { value: 'NOT_RECOVERED', label: '未恢复/未解决' },
  { value: 'RECOVERED_WITH_SEQUELAE', label: '已恢复但留有后遗症' },
  { value: 'FATAL', label: '死亡' },
  { value: 'UNKNOWN', label: '未知' },
];

const Safety: React.FC = () => {
  const [aes, setAes] = useState<AdverseEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);
  
  // Dialog State
  const [open, setOpen] = useState(false);
  const [newAe, setNewAe] = useState<Partial<AdverseEvent>>({
    subject: 1, // Default subject ID
    event_term: '',
    onset_date: new Date().toISOString().split('T')[0],
    severity: 'MILD',
    is_serious: 'NO',
    relationship: 'POSSIBLY',
    outcome: 'RECOVERING',
  });

  const fetchAes = React.useCallback(async () => {
    setLoading(true);
    try {
      const response = await api.get(`adverse-events/?page=${page + 1}&page_size=${pageSize}`);
      setAes(response.data.results);
      setTotal(response.data.count);
    } catch (error) {
      console.error('Failed to fetch adverse events:', error);
    } finally {
      setLoading(false);
    }
  }, [page, pageSize]);

  useEffect(() => {
    fetchAes();
  }, [fetchAes]);

  const handleCreate = async () => {
    try {
      // API expects onset_date as full ISO string or just date if backend supports it
      await api.post('adverse-events/', {
        ...newAe,
        onset_date: new Date(newAe.onset_date!).toISOString(),
      });
      setOpen(false);
      fetchAes();
      setNewAe({
        subject: 1,
        event_term: '',
        onset_date: new Date().toISOString().split('T')[0],
        severity: 'MILD',
        is_serious: 'NO',
        relationship: 'POSSIBLY',
        outcome: 'RECOVERING',
      });
    } catch (err) {
      console.error('Failed to create adverse event:', err);
      alert('创建失败，请检查输入');
    }
  };

  const handleExport = () => {
    const headers = "ID,受试者ID,事件描述,发生日期,严重程度,是否SAE,相关性,转归\n";
    const rows = aes.map(ae => {
      const severityLabel = SEVERITY_CHOICES.find(c => c.value === ae.severity)?.label || ae.severity;
      const seriousLabel = SERIOUS_CHOICES.find(c => c.value === ae.is_serious)?.label || ae.is_serious;
      const relationshipLabel = RELATIONSHIP_CHOICES.find(c => c.value === ae.relationship)?.label || ae.relationship;
      const outcomeLabel = OUTCOME_CHOICES.find(c => c.value === ae.outcome)?.label || ae.outcome;
      
      const eventTerm = `"${(ae.event_term || '').replace(/"/g, '""')}"`;
      const sevLabel = `"${(severityLabel || '').replace(/"/g, '""')}"`;
      const serLabel = `"${(seriousLabel || '').replace(/"/g, '""')}"`;
      const relLabel = `"${(relationshipLabel || '').replace(/"/g, '""')}"`;
      const outLabel = `"${(outcomeLabel || '').replace(/"/g, '""')}"`;
      const onsetDate = `"${ae.onset_date}"`;
      
      return `${ae.id},${ae.subject},${eventTerm},${onsetDate},${sevLabel},${serLabel},${relLabel},${outLabel}`;
    }).join("\n");

    const csvContent = "data:text/csv;charset=utf-8,%EF%BB%BF" + encodeURIComponent(headers + rows);
    const link = document.createElement("a");
    link.setAttribute("href", csvContent);
    link.setAttribute("download", `adverse_events_export_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const columns: GridColDef[] = [
    { field: 'subject', headerName: '受试者 ID', width: 100 },
    { field: 'event_term', headerName: '事件描述', width: 250 },
    { field: 'onset_date', headerName: '发生日期', width: 150 },
    { 
      field: 'severity', 
      headerName: '严重程度', 
      width: 120,
      renderCell: (params: GridRenderCellParams) => {
        let color: 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning' = 'default';
        if (params.value === 'SEVERE') color = 'error';
        else if (params.value === 'MODERATE') color = 'warning';
        else if (params.value === 'MILD') color = 'success';
        return <Chip label={params.value} color={color} size="small" />;
      }
    },
    { 
      field: 'is_serious', 
      headerName: '是否 SAE', 
      width: 100,
      renderCell: (params: GridRenderCellParams) => {
        return <Chip label={params.value} color={params.value === 'YES' ? 'error' : 'default'} size="small" />;
      }
    },
    { field: 'relationship', headerName: '相关性', width: 150 },
    { field: 'outcome', headerName: '转归', width: 150 },
  ];

  return (
    <Paper sx={{ height: 700, width: '100%', p: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
        <Typography variant="h4">AE/SAE 管理</Typography>
        <Box>
          <Button 
            variant="contained" 
            startIcon={<AddIcon />} 
            onClick={() => setOpen(true)}
            sx={{ mr: 1 }}
          >
            报告事件
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
        rows={aes}
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

      <Dialog open={open} onClose={() => setOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>报告不良事件 (AE/SAE)</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
            <TextField
              label="受试者 ID"
              type="number"
              value={newAe.subject}
              onChange={(e) => setNewAe({ ...newAe, subject: parseInt(e.target.value) })}
              fullWidth
              required
            />
            <TextField
              label="事件描述"
              value={newAe.event_term}
              onChange={(e) => setNewAe({ ...newAe, event_term: e.target.value })}
              fullWidth
              required
            />
            <TextField
              label="发生日期"
              type="date"
              value={newAe.onset_date}
              onChange={(e) => setNewAe({ ...newAe, onset_date: e.target.value })}
              fullWidth
              InputLabelProps={{ shrink: true }}
              required
            />
            <TextField
              select
              label="严重程度"
              value={newAe.severity}
              onChange={(e) => setNewAe({ ...newAe, severity: e.target.value })}
              fullWidth
            >
              {SEVERITY_CHOICES.map((option) => (
                <MenuItem key={option.value} value={option.value}>
                  {option.label}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              select
              label="是否 SAE"
              value={newAe.is_serious}
              onChange={(e) => setNewAe({ ...newAe, is_serious: e.target.value })}
              fullWidth
            >
              {SERIOUS_CHOICES.map((option) => (
                <MenuItem key={option.value} value={option.value}>
                  {option.label}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              select
              label="因果关系判定"
              value={newAe.relationship}
              onChange={(e) => setNewAe({ ...newAe, relationship: e.target.value })}
              fullWidth
            >
              {RELATIONSHIP_CHOICES.map((option) => (
                <MenuItem key={option.value} value={option.value}>
                  {option.label}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              select
              label="转归情况"
              value={newAe.outcome}
              onChange={(e) => setNewAe({ ...newAe, outcome: e.target.value })}
              fullWidth
            >
              {OUTCOME_CHOICES.map((option) => (
                <MenuItem key={option.value} value={option.value}>
                  {option.label}
                </MenuItem>
              ))}
            </TextField>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>取消</Button>
          <Button onClick={handleCreate} variant="contained">提交</Button>
        </DialogActions>
      </Dialog>
    </Paper>
  );
};

export default Safety;
