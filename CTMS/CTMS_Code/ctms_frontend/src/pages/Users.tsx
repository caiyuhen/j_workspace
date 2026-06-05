import React, { useEffect, useState } from 'react';
import { DataGrid, type GridColDef, type GridRenderCellParams } from '@mui/x-data-grid';
import { 
  Typography, Paper, Chip, Button, Stack, Dialog, DialogTitle, 
  DialogContent, DialogActions, TextField, FormControl, InputLabel, 
  Select, MenuItem 
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import DownloadIcon from '@mui/icons-material/Download';
import api from '../api/axios';

interface User {
  id: number;
  username: string;
  email: string;
  role: string;
  organization: string;
  phone_number: string;
  is_verified: boolean;
}

const ROLE_MAP: Record<string, string> = {
  'PM': '项目经理',
  'CRA': '临床监查员',
  'DM': '数据管理员',
  'STAT': '统计师',
  'PV': '药物警戒',
  'QA': '质量保证',
  'INV': '研究者',
  'IRB': '伦理委员会',
  'ADMIN': '系统管理员',
};

const Users: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);
  
  // Dialog state
  const [open, setOpen] = useState(false);
  const [newUser, setNewUser] = useState({
    username: '',
    email: '',
    password: '',
    role: 'CRA',
    organization: '',
    phone_number: ''
  });

  const fetchUsers = React.useCallback(async () => {
    setLoading(true);
    try {
      const response = await api.get(`users/?page=${page + 1}&page_size=${pageSize}`);
      setUsers(response.data.results);
      setTotal(response.data.count);
    } catch (error) {
      console.error('Failed to fetch users:', error);
    } finally {
      setLoading(false);
    }
  }, [page, pageSize]);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const handleCreateUser = async () => {
    try {
      await api.post('users/', newUser);
      setOpen(false);
      fetchUsers();
      // Reset form
      setNewUser({
        username: '',
        email: '',
        password: '',
        role: 'CRA',
        organization: '',
        phone_number: ''
      });
    } catch (err) {
      console.error('Failed to create user:', err);
      alert('创建用户失败，请检查输入');
    }
  };

  const handleExport = () => {
    const headers = "ID,用户名,邮箱,角色,所属机构,电话,已认证\n";
    const rows = users.map(u => {
      const roleLabel = ROLE_MAP[u.role] || u.role;
      const username = `"${(u.username || '').replace(/"/g, '""')}"`;
      const email = `"${(u.email || '').replace(/"/g, '""')}"`;
      const role = `"${(roleLabel || '').replace(/"/g, '""')}"`;
      const organization = `"${(u.organization || '').replace(/"/g, '""')}"`;
      const phone = `"${(u.phone_number || '').replace(/"/g, '""')}"`;
      const isVerified = `"${u.is_verified ? '是' : '否'}"`;
      
      return `${u.id},${username},${email},${role},${organization},${phone},${isVerified}`;
    }).join("\n");

    const csvContent = "data:text/csv;charset=utf-8,%EF%BB%BF" + encodeURIComponent(headers + rows);
    const link = document.createElement("a");
    link.setAttribute("href", csvContent);
    link.setAttribute("download", `users_export_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const columns: GridColDef[] = [
    { field: 'username', headerName: '用户名', width: 150 },
    { field: 'email', headerName: '邮箱', width: 250 },
    { 
      field: 'role', 
      headerName: '角色', 
      width: 150,
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
          valueFormatter: (value: any) => ROLE_MAP[value as string] || value
    },
    { field: 'organization', headerName: '所属机构', width: 200 },
    { field: 'phone_number', headerName: '电话', width: 150 },
    { 
      field: 'is_verified', 
      headerName: '已认证', 
      width: 100,
      renderCell: (params: GridRenderCellParams) => {
        return <Chip label={params.value ? '是' : '否'} color={params.value ? 'success' : 'default'} size="small" />;
      }
    },
  ];

  return (
    <Paper sx={{ height: 600, width: '100%', p: 2 }}>
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h4">用户管理</Typography>
        <Stack direction="row" spacing={2}>
          <Button 
            variant="contained" 
            startIcon={<AddIcon />}
            onClick={() => setOpen(true)}
          >
            新建用户
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
        rows={users}
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
        <DialogTitle>新建用户</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1, minWidth: 400 }}>
            <TextField
              label="用户名"
              fullWidth
              value={newUser.username}
              onChange={(e) => setNewUser({...newUser, username: e.target.value})}
            />
            <TextField
              label="邮箱"
              fullWidth
              value={newUser.email}
              onChange={(e) => setNewUser({...newUser, email: e.target.value})}
            />
            <TextField
              label="密码"
              type="password"
              fullWidth
              value={newUser.password}
              onChange={(e) => setNewUser({...newUser, password: e.target.value})}
            />
            <FormControl fullWidth>
              <InputLabel>角色</InputLabel>
              <Select
                value={newUser.role}
                label="角色"
                onChange={(e) => setNewUser({...newUser, role: e.target.value})}
              >
                {Object.entries(ROLE_MAP).map(([key, label]) => (
                  <MenuItem key={key} value={key}>{label}</MenuItem>
                ))}
              </Select>
            </FormControl>
            <TextField
              label="所属机构"
              fullWidth
              value={newUser.organization}
              onChange={(e) => setNewUser({...newUser, organization: e.target.value})}
            />
            <TextField
              label="电话"
              fullWidth
              value={newUser.phone_number}
              onChange={(e) => setNewUser({...newUser, phone_number: e.target.value})}
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>取消</Button>
          <Button onClick={handleCreateUser} variant="contained">创建</Button>
        </DialogActions>
      </Dialog>
    </Paper>
  );
};

export default Users;
