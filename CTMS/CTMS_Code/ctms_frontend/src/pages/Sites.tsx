import React, { useEffect, useState } from 'react';
import { DataGrid, type GridColDef, type GridRenderCellParams } from '@mui/x-data-grid';
import { Typography, Paper, Chip, Button, Box, Dialog, DialogTitle, DialogContent, DialogActions, TextField, MenuItem } from '@mui/material';
import { Add as AddIcon, Download as DownloadIcon } from '@mui/icons-material';
import api from '../api/axios';

interface Site {
  id: number;
  trial: number;
  site_number: string;
  name: string;
  status: string;
  principal_investigator: number;
  assigned_cra: number;
  address?: string;
}

const STATUS_CHOICES = [
  { value: 'SELECTED', label: '已选择' },
  { value: 'INITIATED', label: '已启动' },
  { value: 'ACTIVE', label: '进行中' },
  { value: 'CLOSED', label: '已关闭' },
  { value: 'TERMINATED', label: '已终止' },
];

const Sites: React.FC = () => {
  const [sites, setSites] = useState<Site[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);
  
  // Dialog State
  const [open, setOpen] = useState(false);
  const [newSite, setNewSite] = useState<Partial<Site>>({
    trial: 1, // Default trial ID
    site_number: '',
    name: '',
    status: 'SELECTED',
    principal_investigator: 1, // Default user ID
    address: '',
  });

  const fetchSites = React.useCallback(async () => {
    setLoading(true);
    try {
      const response = await api.get(`sites/?page=${page + 1}&page_size=${pageSize}`);
      setSites(response.data.results);
      setTotal(response.data.count);
    } catch (error) {
      console.error('Failed to fetch sites:', error);
    } finally {
      setLoading(false);
    }
  }, [page, pageSize]);

  useEffect(() => {
    fetchSites();
  }, [fetchSites]);

  const handleCreate = async () => {
    try {
      await api.post('sites/', newSite);
      setOpen(false);
      fetchSites();
      setNewSite({
        trial: 1,
        site_number: '',
        name: '',
        status: 'SELECTED',
        principal_investigator: 1,
        address: '',
      });
    } catch (err) {
      console.error('Failed to create site:', err);
      alert('创建失败，请检查输入');
    }
  };

  const handleExport = () => {
    const headers = "ID,中心编号,中心名称,项目 ID,PI ID,状态\n";
    const rows = sites.map(s => {
      const statusLabel = STATUS_CHOICES.find(c => c.value === s.status)?.label || s.status;
      
      const siteNumber = `"${(s.site_number || '').replace(/"/g, '""')}"`;
      const name = `"${(s.name || '').replace(/"/g, '""')}"`;
      const staLabel = `"${(statusLabel || '').replace(/"/g, '""')}"`;
      
      return `${s.id},${siteNumber},${name},${s.trial},${s.principal_investigator},${staLabel}`;
    }).join("\n");

    const csvContent = "data:text/csv;charset=utf-8,%EF%BB%BF" + encodeURIComponent(headers + rows);
    const link = document.createElement("a");
    link.setAttribute("href", csvContent);
    link.setAttribute("download", `sites_export_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const columns: GridColDef[] = [
    { field: 'site_number', headerName: '中心编号', width: 100 },
    { field: 'name', headerName: '中心名称', width: 200 },
    { field: 'trial', headerName: '项目 ID', width: 100 },
    { field: 'principal_investigator', headerName: 'PI ID', width: 100 },
    { field: 'assigned_cra', headerName: 'CRA ID', width: 100 },
    { 
      field: 'status', 
      headerName: '状态', 
      width: 150,
      renderCell: (params: GridRenderCellParams) => {
        let color: 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning' = 'default';
        if (params.value === 'ACTIVE') color = 'success';
        else if (params.value === 'SELECTED') color = 'info';
        else if (params.value === 'CLOSED') color = 'error';
        return <Chip label={params.value} color={color} size="small" />;
      }
    },
  ];

  return (
    <Paper sx={{ height: 700, width: '100%', p: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
        <Typography variant="h4">中心列表</Typography>
        <Box>
          <Button 
            variant="contained" 
            startIcon={<AddIcon />} 
            onClick={() => setOpen(true)}
            sx={{ mr: 1 }}
          >
            新建中心
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
        rows={sites}
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
        <DialogTitle>新建临床中心</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
            <TextField
              label="中心编号"
              value={newSite.site_number}
              onChange={(e) => setNewSite({ ...newSite, site_number: e.target.value })}
              fullWidth
              required
            />
            <TextField
              label="中心名称"
              value={newSite.name}
              onChange={(e) => setNewSite({ ...newSite, name: e.target.value })}
              fullWidth
              required
            />
            <TextField
              label="项目ID"
              type="number"
              value={newSite.trial}
              onChange={(e) => setNewSite({ ...newSite, trial: parseInt(e.target.value) })}
              fullWidth
              required
              helperText="请输入关联的项目ID"
            />
            <TextField
              label="PI ID (主要研究者)"
              type="number"
              value={newSite.principal_investigator}
              onChange={(e) => setNewSite({ ...newSite, principal_investigator: parseInt(e.target.value) })}
              fullWidth
              required
              helperText="请输入PI的用户ID"
            />
            <TextField
              select
              label="状态"
              value={newSite.status}
              onChange={(e) => setNewSite({ ...newSite, status: e.target.value })}
              fullWidth
            >
              {STATUS_CHOICES.map((option) => (
                <MenuItem key={option.value} value={option.value}>
                  {option.label}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              label="地址"
              value={newSite.address}
              onChange={(e) => setNewSite({ ...newSite, address: e.target.value })}
              fullWidth
              multiline
              rows={2}
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

export default Sites;
