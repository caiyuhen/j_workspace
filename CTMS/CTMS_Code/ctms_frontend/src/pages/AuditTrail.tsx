import React, { useState, useEffect } from 'react';
import { 
  Box, Typography, Paper, FormControl, InputLabel, Select, MenuItem, 
  Chip, Stack, Button, Dialog, DialogTitle, DialogContent, DialogActions 
} from '@mui/material';
import { Download as DownloadIcon } from '@mui/icons-material';
import { DataGrid, type GridColDef, type GridRenderCellParams } from '@mui/x-data-grid';
import api from '../api/axios';
import { format } from 'date-fns';

interface AuditLog {
  id: number;
  date: string;
  user: string;
  action: string;
  object_repr: string;
  changes: { field: string; old: string; new: string }[];
  ip_address: string;
}

const AuditTrail: React.FC = () => {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(false);
  const [model, setModel] = useState('Trial');
  const [rowCount, setRowCount] = useState(0);
  const [paginationModel, setPaginationModel] = useState({ page: 0, pageSize: 20 });
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null);
  const [detailsOpen, setDetailsOpen] = useState(false);

  const fetchLogs = React.useCallback(async () => {
    setLoading(true);
    try {
      const response = await api.get('audit-logs/', {
        params: {
          model,
          page: paginationModel.page + 1,
          page_size: paginationModel.pageSize
        }
      });
      setLogs(response.data.results);
      setRowCount(response.data.count);
    } catch (err) {
      console.error('Failed to fetch audit logs:', err);
    } finally {
      setLoading(false);
    }
  }, [model, paginationModel]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  const handleOpenDetails = (log: AuditLog) => {
    setSelectedLog(log);
    setDetailsOpen(true);
  };

  const handleExport = () => {
    const headers = "时间,操作用户,动作,资源类型,对象描述,变更详情\n";
    const rows = logs.map(log => {
      const actionMap: Record<string, string> = { 'Created': '创建', 'Updated': '更新', 'Deleted': '删除' };
      const actionLabel = actionMap[log.action] || log.action;
      
      const changes = `"${JSON.stringify(log.changes).replace(/"/g, '""')}"`;
      const objectRepr = `"${(log.object_repr || '').replace(/"/g, '""')}"`;
      const date = `"${format(new Date(log.date), 'yyyy-MM-dd HH:mm:ss')}"`;
      const user = `"${(log.user || '').replace(/"/g, '""')}"`;
      const action = `"${(actionLabel || '').replace(/"/g, '""')}"`;
      const resource = `"${(model || '').replace(/"/g, '""')}"`;
      
      return `${date},${user},${action},${resource},${objectRepr},${changes}`;
    }).join("\n");

    const csvContent = "data:text/csv;charset=utf-8,%EF%BB%BF" + encodeURIComponent(headers + rows);
    const link = document.createElement("a");
    link.setAttribute("href", csvContent);
    link.setAttribute("download", `audit_trail_${model}_export_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const columns: GridColDef[] = [
    { 
      field: 'date', 
      headerName: '时间', 
      width: 180,
      valueFormatter: (value: string) => {
          if (!value) return '';
          return format(new Date(value), 'yyyy-MM-dd HH:mm:ss');
      }
    },
    { field: 'user', headerName: '操作用户', width: 150 },
    { 
      field: 'action', 
      headerName: '动作', 
      width: 120,
      renderCell: (params) => {
        let color: 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning' = 'default';
        if (params.value === 'Created') color = 'success';
        if (params.value === 'Updated') color = 'info';
        if (params.value === 'Deleted') color = 'error';
        return <Chip label={params.value} color={color} size="small" />;
      }
    },
    { field: 'object_repr', headerName: '对象描述', width: 300 },
    {
      field: 'changes',
      headerName: '变更详情',
      width: 150,
      renderCell: (params: GridRenderCellParams) => (
        <Button size="small" onClick={() => handleOpenDetails(params.row)}>
          查看详情
        </Button>
      )
    }
  ];

  return (
    <Box sx={{ height: '100%', width: '100%' }}>
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h4">审计追踪 (Audit Trail)</Typography>
        <Stack direction="row" spacing={2}>
          <FormControl sx={{ minWidth: 200 }}>
            <InputLabel>资源类型</InputLabel>
            <Select
              value={model}
              label="资源类型"
              onChange={(e) => setModel(e.target.value)}
            >
              <MenuItem value="Trial">项目 (Trial)</MenuItem>
              <MenuItem value="Site">中心 (Site)</MenuItem>
              <MenuItem value="Subject">受试者 (Subject)</MenuItem>
              <MenuItem value="Visit">访视 (Visit)</MenuItem>
              <MenuItem value="Query">质疑 (Query)</MenuItem>
              <MenuItem value="MonitoringVisit">监查访视 (Monitoring Visit)</MenuItem>
              <MenuItem value="ProtocolDeviation">方案违背 (Protocol Deviation)</MenuItem>
              <MenuItem value="AdverseEvent">不良事件 (AE)</MenuItem>
              <MenuItem value="Document">文档 (Document)</MenuItem>
              <MenuItem value="InvestigationalProduct">药物 (Drug)</MenuItem>
              <MenuItem value="Specimen">样本 (Specimen)</MenuItem>
              <MenuItem value="User">用户 (User)</MenuItem>
            </Select>
          </FormControl>
          <Button 
            variant="outlined" 
            startIcon={<DownloadIcon />} 
            onClick={handleExport}
          >
            导出
          </Button>
        </Stack>
      </Stack>

      <Paper sx={{ height: 600, width: '100%' }}>
        <DataGrid
          rows={logs}
          columns={columns}
          rowCount={rowCount}
          loading={loading}
          paginationMode="server"
          paginationModel={paginationModel}
          onPaginationModelChange={setPaginationModel}
          pageSizeOptions={[20, 50, 100]}
          disableRowSelectionOnClick
        />
      </Paper>

      <Dialog open={detailsOpen} onClose={() => setDetailsOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>变更详情</DialogTitle>
        <DialogContent dividers>
          {selectedLog && (
            <Box>
              <Typography variant="subtitle1" gutterBottom>
                对象: {selectedLog.object_repr}
              </Typography>
              <Typography variant="body2" color="textSecondary" gutterBottom>
                时间: {format(new Date(selectedLog.date), 'yyyy-MM-dd HH:mm:ss')} | 用户: {selectedLog.user}
              </Typography>
              
              <Box sx={{ mt: 2 }}>
                {selectedLog.changes.length > 0 ? (
                  <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead>
                      <tr style={{ borderBottom: '1px solid #ddd', textAlign: 'left' }}>
                        <th style={{ padding: 8 }}>字段</th>
                        <th style={{ padding: 8 }}>旧值</th>
                        <th style={{ padding: 8 }}>新值</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selectedLog.changes.map((change, index) => (
                        <tr key={index} style={{ borderBottom: '1px solid #eee' }}>
                          <td style={{ padding: 8 }}>{change.field}</td>
                          <td style={{ padding: 8, color: 'red' }}>{change.old}</td>
                          <td style={{ padding: 8, color: 'green' }}>{change.new}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : (
                  <Typography>无变更记录</Typography>
                )}
              </Box>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailsOpen(false)}>关闭</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AuditTrail;
