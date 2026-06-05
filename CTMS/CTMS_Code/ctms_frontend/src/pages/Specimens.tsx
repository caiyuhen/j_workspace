import React, { useEffect, useState } from 'react';
import { DataGrid, type GridColDef } from '@mui/x-data-grid';
import { format } from 'date-fns';
import { 
  Typography, Paper, Button, Stack, Dialog, DialogTitle, 
  DialogContent, DialogActions, TextField, MenuItem 
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import DownloadIcon from '@mui/icons-material/Download';
import api from '../api/axios';

interface Specimen {
  id: number;
  subject: number;
  specimen_id: string;
  specimen_type: string;
  collection_date: string;
  storage_location: string;
  status: string;
}

const SPECIMEN_TYPES = [
  { value: 'BLOOD', label: '血液' },
  { value: 'URINE', label: '尿液' },
  { value: 'TISSUE', label: '组织' },
  { value: 'SERUM', label: '血清' },
  { value: 'OTHER', label: '其他' },
];

const Specimens: React.FC = () => {
  const [specimens, setSpecimens] = useState<Specimen[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);
  
  // Dialog state
  const [open, setOpen] = useState(false);
  const [newSpecimen, setNewSpecimen] = useState({
    subject: '',
    specimen_id: '',
    specimen_type: 'BLOOD',
    collection_date: '',
    storage_location: '',
    status: 'COLLECTED'
  });

  const [filters, setFilters] = useState({
    subject: '',
    specimen_type: ''
  });

  const fetchSpecimens = React.useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append('page', (page + 1).toString());
      params.append('page_size', pageSize.toString());
      if (filters.subject) params.append('subject', filters.subject);
      if (filters.specimen_type) params.append('specimen_type', filters.specimen_type);

      const response = await api.get(`specimens/?${params.toString()}`);
      setSpecimens(response.data.results);
      setTotal(response.data.count);
    } catch (error) {
      console.error('Failed to fetch specimens:', error);
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, filters]);

  useEffect(() => {
    fetchSpecimens();
  }, [fetchSpecimens]);

  const handleCreate = async () => {
    try {
      await api.post('specimens/', newSpecimen);
      setOpen(false);
      fetchSpecimens();
      // Reset form
      setNewSpecimen({
        subject: '',
        specimen_id: '',
        specimen_type: 'BLOOD',
        collection_date: '',
        storage_location: '',
        status: 'COLLECTED'
      });
    } catch (err) {
      console.error('Failed to create specimen:', err);
      alert('创建失败，请检查输入');
    }
  };

  const handleExport = () => {
    const headers = "ID,受试者ID,样本ID,类型,采集时间,存储位置,状态\n";
    const rows = specimens.map(s => {
      const typeLabel = SPECIMEN_TYPES.find(t => t.value === s.specimen_type)?.label || s.specimen_type;
      
      const specimenId = `"${(s.specimen_id || '').replace(/"/g, '""')}"`;
      const type = `"${(typeLabel || '').replace(/"/g, '""')}"`;
      const storage = `"${(s.storage_location || '').replace(/"/g, '""')}"`;
      const status = `"${(s.status || '').replace(/"/g, '""')}"`;
      const collectionDate = `"${s.collection_date}"`;
      
      return `${s.id},${s.subject},${specimenId},${type},${collectionDate},${storage},${status}`;
    }).join("\n");

    const csvContent = "data:text/csv;charset=utf-8,%EF%BB%BF" + encodeURIComponent(headers + rows);
    const link = document.createElement("a");
    link.setAttribute("href", csvContent);
    link.setAttribute("download", `specimens_export_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const columns: GridColDef[] = [
    { field: 'specimen_id', headerName: '样本ID', width: 150 },
    { field: 'subject', headerName: '受试者ID', width: 100 },
    { 
      field: 'specimen_type', 
      headerName: '类型', 
      width: 120,
      valueFormatter: (value: string) => SPECIMEN_TYPES.find(t => t.value === value)?.label || value
    },
    { 
      field: 'collection_date', 
      headerName: '采集时间', 
      width: 180,
      valueFormatter: (value: string) => {
        if (!value) return '';
        try {
          return format(new Date(value), 'yyyy-MM-dd HH:mm');
        } catch {
          return value;
        }
      }
    },
    { field: 'storage_location', headerName: '存储位置', width: 200 },
    { field: 'status', headerName: '状态', width: 120 },
  ];

  return (
    <Paper sx={{ height: 600, width: '100%', p: 2 }}>
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h4">样本管理</Typography>
        <Stack direction="row" spacing={2} alignItems="center">
          <TextField
            label="受试者ID"
            size="small"
            value={filters.subject}
            onChange={(e) => setFilters({...filters, subject: e.target.value})}
            sx={{ width: 120 }}
          />
          <TextField
            select
            label="类型"
            size="small"
            value={filters.specimen_type}
            onChange={(e) => setFilters({...filters, specimen_type: e.target.value})}
            sx={{ width: 120 }}
          >
            <MenuItem value="">全部</MenuItem>
            {SPECIMEN_TYPES.map((option) => (
              <MenuItem key={option.value} value={option.value}>
                {option.label}
              </MenuItem>
            ))}
          </TextField>
          <Button variant="contained" onClick={() => fetchSpecimens()}>搜索</Button>
          <Button 
            variant="contained" 
            startIcon={<AddIcon />}
            onClick={() => setOpen(true)}
          >
            新建样本
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
        rows={specimens}
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

      <Dialog open={open} onClose={() => setOpen(false)}>
        <DialogTitle>新建样本</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1, minWidth: 400 }}>
            <TextField
              label="受试者ID"
              fullWidth
              value={newSpecimen.subject}
              onChange={(e) => setNewSpecimen({...newSpecimen, subject: e.target.value})}
              helperText="输入关联的受试者ID"
            />
            <TextField
              label="样本ID"
              fullWidth
              value={newSpecimen.specimen_id}
              onChange={(e) => setNewSpecimen({...newSpecimen, specimen_id: e.target.value})}
            />
            <TextField
              select
              label="类型"
              fullWidth
              value={newSpecimen.specimen_type}
              onChange={(e) => setNewSpecimen({...newSpecimen, specimen_type: e.target.value})}
            >
              {SPECIMEN_TYPES.map((option) => (
                <MenuItem key={option.value} value={option.value}>
                  {option.label}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              label="采集时间"
              type="datetime-local"
              fullWidth
              InputLabelProps={{ shrink: true }}
              value={newSpecimen.collection_date}
              onChange={(e) => setNewSpecimen({...newSpecimen, collection_date: e.target.value})}
            />
            <TextField
              label="存储位置"
              fullWidth
              value={newSpecimen.storage_location}
              onChange={(e) => setNewSpecimen({...newSpecimen, storage_location: e.target.value})}
            />
            <TextField
              label="状态"
              fullWidth
              value={newSpecimen.status}
              onChange={(e) => setNewSpecimen({...newSpecimen, status: e.target.value})}
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>取消</Button>
          <Button onClick={handleCreate} variant="contained">提交</Button>
        </DialogActions>
      </Dialog>
    </Paper>
  );
};

export default Specimens;
