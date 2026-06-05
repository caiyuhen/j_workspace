import React, { useEffect, useState } from 'react';
import { DataGrid, type GridColDef } from '@mui/x-data-grid';
import { 
  Typography, Paper, Button, Stack, Dialog, DialogTitle, 
  DialogContent, DialogActions, TextField, MenuItem 
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import DownloadIcon from '@mui/icons-material/Download';
import api from '../api/axios';

interface InvestigationalProduct {
  id: number;
  trial: number;
  name: string;
  product_type: string;
  batch_number: string;
  expiry_date: string;
  quantity: number;
  description: string;
}

const PRODUCT_TYPES = [
  { value: 'DRUG', label: '药物' },
  { value: 'DEVICE', label: '器械' },
  { value: 'BIOLOGIC', label: '生物制剂' },
  { value: 'SUPPLY', label: '耗材' },
];

const Drugs: React.FC = () => {
  const [products, setProducts] = useState<InvestigationalProduct[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);
  
  // Dialog state
  const [open, setOpen] = useState(false);
  const [newProduct, setNewProduct] = useState({
    trial: '',
    name: '',
    product_type: 'DRUG',
    batch_number: '',
    expiry_date: '',
    quantity: '',
    description: ''
  });

  const [filters, setFilters] = useState({
    trial: '',
    product_type: ''
  });

  const fetchProducts = React.useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append('page', (page + 1).toString());
      params.append('page_size', pageSize.toString());
      if (filters.trial) params.append('trial', filters.trial);
      if (filters.product_type) params.append('product_type', filters.product_type);

      const response = await api.get(`products/?${params.toString()}`);
      setProducts(response.data.results);
      setTotal(response.data.count);
    } catch (error) {
      console.error('Failed to fetch products:', error);
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, filters]);

  useEffect(() => {
    fetchProducts();
  }, [fetchProducts]);

  const handleCreate = async () => {
    try {
      await api.post('products/', newProduct);
      setOpen(false);
      fetchProducts();
      // Reset form
      setNewProduct({
        trial: '',
        name: '',
        product_type: 'DRUG',
        batch_number: '',
        expiry_date: '',
        quantity: '',
        description: ''
      });
    } catch (err) {
      console.error('Failed to create product:', err);
      alert('创建失败，请检查输入');
    }
  };

  const handleExport = () => {
    const headers = "ID,试验ID,名称,类型,批号,有效期,数量,描述\n";
    const rows = products.map(p => {
      const typeLabel = PRODUCT_TYPES.find(t => t.value === p.product_type)?.label || p.product_type;
      
      const name = `"${(p.name || '').replace(/"/g, '""')}"`;
      const type = `"${(typeLabel || '').replace(/"/g, '""')}"`;
      const batch = `"${(p.batch_number || '').replace(/"/g, '""')}"`;
      const desc = `"${(p.description || '').replace(/"/g, '""')}"`;
      const expiry = `"${p.expiry_date}"`;
      
      return `${p.id},${p.trial},${name},${type},${batch},${expiry},${p.quantity},${desc}`;
    }).join("\n");

    const csvContent = "data:text/csv;charset=utf-8,%EF%BB%BF" + encodeURIComponent(headers + rows);
    const link = document.createElement("a");
    link.setAttribute("href", csvContent);
    link.setAttribute("download", `drugs_export_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const columns: GridColDef[] = [
    { field: 'id', headerName: 'ID', width: 70 },
    { field: 'name', headerName: '名称', width: 200 },
    { 
      field: 'product_type', 
      headerName: '类型', 
      width: 120,
      valueFormatter: (value: string) => PRODUCT_TYPES.find(t => t.value === value)?.label || value
    },
    { field: 'batch_number', headerName: '批号', width: 150 },
    { field: 'expiry_date', headerName: '有效期', width: 150 },
    { field: 'quantity', headerName: '数量', width: 100 },
    { field: 'trial', headerName: '试验ID', width: 100 },
  ];

  return (
    <Paper sx={{ height: 600, width: '100%', p: 2 }}>
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h4">药物管理</Typography>
        <Stack direction="row" spacing={2} alignItems="center">
          <TextField
            label="试验ID"
            size="small"
            value={filters.trial}
            onChange={(e) => setFilters({...filters, trial: e.target.value})}
            sx={{ width: 100 }}
          />
          <TextField
            select
            label="类型"
            size="small"
            value={filters.product_type}
            onChange={(e) => setFilters({...filters, product_type: e.target.value})}
            sx={{ width: 150 }}
          >
            <MenuItem value="">全部</MenuItem>
            {PRODUCT_TYPES.map((option) => (
              <MenuItem key={option.value} value={option.value}>
                {option.label}
              </MenuItem>
            ))}
          </TextField>
          <Button variant="contained" onClick={() => fetchProducts()}>搜索</Button>
          <Button 
            variant="contained" 
            startIcon={<AddIcon />}
            onClick={() => setOpen(true)}
          >
            新建药物
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
        rows={products}
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
        <DialogTitle>新建药物</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1, minWidth: 400 }}>
            <TextField
              label="试验ID"
              fullWidth
              value={newProduct.trial}
              onChange={(e) => setNewProduct({...newProduct, trial: e.target.value})}
              helperText="输入关联的试验ID"
            />
            <TextField
              label="名称"
              fullWidth
              value={newProduct.name}
              onChange={(e) => setNewProduct({...newProduct, name: e.target.value})}
            />
            <TextField
              select
              label="类型"
              fullWidth
              value={newProduct.product_type}
              onChange={(e) => setNewProduct({...newProduct, product_type: e.target.value})}
            >
              {PRODUCT_TYPES.map((option) => (
                <MenuItem key={option.value} value={option.value}>
                  {option.label}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              label="批号"
              fullWidth
              value={newProduct.batch_number}
              onChange={(e) => setNewProduct({...newProduct, batch_number: e.target.value})}
            />
            <TextField
              label="有效期"
              type="date"
              fullWidth
              InputLabelProps={{ shrink: true }}
              value={newProduct.expiry_date}
              onChange={(e) => setNewProduct({...newProduct, expiry_date: e.target.value})}
            />
            <TextField
              label="数量"
              type="number"
              fullWidth
              value={newProduct.quantity}
              onChange={(e) => setNewProduct({...newProduct, quantity: e.target.value})}
            />
            <TextField
              label="描述"
              fullWidth
              multiline
              rows={3}
              value={newProduct.description}
              onChange={(e) => setNewProduct({...newProduct, description: e.target.value})}
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

export default Drugs;
