import React, { useEffect, useState } from 'react';
import { DataGrid, type GridColDef } from '@mui/x-data-grid';
import { Typography, Paper, Link, Button, Box, Dialog, DialogTitle, DialogContent, DialogActions, TextField, MenuItem, Tabs, Tab } from '@mui/material';
import { CloudUpload as UploadIcon, Download as DownloadIcon, Edit as EditIcon, Add as AddIcon } from '@mui/icons-material';
import api from '../api/axios';
import DocumentEditor from '../components/DocumentEditor';

interface DocumentItem {
  id: number;
  title: string;
  category: string;
  version: string;
  file: string | null;
  is_online: boolean;
  uploaded_by: number;
  trial?: number;
  site?: number;
  description?: string;
  created_at: string;
}

const CATEGORY_CHOICES = [
  { value: 'PROTOCOL', label: '试验方案 (Protocol)' },
  { value: 'ICF', label: '知情同意书 (ICF)' },
  { value: 'IB', label: '研究者手册 (IB)' },
  { value: 'CRF', label: '病例报告表 (CRF)' },
  { value: 'MVR', label: '监查报告 (MVR)' },
  { value: 'ETHICS', label: '伦理批件' },
  { value: 'OTHER', label: '其他' },
];

const Documents: React.FC = () => {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);
  
  // Editor State
  const [editorOpen, setEditorOpen] = useState(false);
  const [selectedDocId, setSelectedDocId] = useState<number | null>(null);

  // Dialog State
  const [open, setOpen] = useState(false);
  const [docMode, setDocMode] = useState<'upload' | 'online'>('upload');
  const [newDoc, setNewDoc] = useState<{
    title: string;
    category: string;
    version: string;
    trial: string;
    site: string;
    description: string;
    file: File | null;
  }>({
    title: '',
    category: 'PROTOCOL',
    version: '1.0',
    trial: '',
    site: '',
    description: '',
    file: null,
  });

  const fetchDocuments = React.useCallback(async () => {
    setLoading(true);
    try {
      const response = await api.get(`documents/?page=${page + 1}&page_size=${pageSize}`);
      setDocuments(response.data.results);
      setTotal(response.data.count);
    } catch (error) {
      console.error('Failed to fetch documents:', error);
    } finally {
      setLoading(false);
    }
  }, [page, pageSize]);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setNewDoc({ ...newDoc, file: e.target.files[0] });
    }
  };

  const handleSaveDocument = async () => {
    try {
        if (!newDoc.title.trim()) {
            alert('请输入文档标题');
            return;
        }
        if (!newDoc.version.trim()) {
            alert('请输入版本号');
            return;
        }

        if (docMode === 'upload') {
            if (!newDoc.file) {
                alert('请选择文件');
                return;
            }
            const formData = new FormData();
            formData.append('title', newDoc.title);
            formData.append('category', newDoc.category);
            formData.append('version', newDoc.version);
            formData.append('file', newDoc.file);
            if (newDoc.trial) formData.append('trial', newDoc.trial);
            if (newDoc.site) formData.append('site', newDoc.site);
            formData.append('description', newDoc.description);
            formData.append('is_online', 'false');

            await api.post('documents/', formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
            });
        } else {
            // Online Document
            await api.post('documents/', {
                title: newDoc.title,
                category: newDoc.category,
                version: newDoc.version,
                trial: newDoc.trial || null,
                site: newDoc.site || null,
                description: newDoc.description,
                is_online: true
            });
        }

      setOpen(false);
      fetchDocuments();
      setNewDoc({
        title: '',
        category: 'PROTOCOL',
        version: '1.0',
        trial: '',
        site: '',
        description: '',
        file: null,
      });
    } catch (error) {
      console.error('Failed to save document:', error);
      alert('保存失败，请检查输入');
    }
  };

  const handleEdit = (id: number) => {
      setSelectedDocId(id);
      setEditorOpen(true);
  };

  const handleExport = () => {
    const headers = "ID,标题,类别,版本,项目ID,中心ID,上传时间\n";
    const rows = documents.map(d => {
      const categoryLabel = CATEGORY_CHOICES.find(c => c.value === d.category)?.label || d.category;
      
      const title = `"${(d.title || '').replace(/"/g, '""')}"`;
      const catLabel = `"${(categoryLabel || '').replace(/"/g, '""')}"`;
      const version = `"${(d.version || '').replace(/"/g, '""')}"`;
      const createdAt = `"${d.created_at}"`;
      
      return `${d.id},${title},${catLabel},${version},${d.trial || ''},${d.site || ''},${createdAt}`;
    }).join("\n");

    const csvContent = "data:text/csv;charset=utf-8,%EF%BB%BF" + encodeURIComponent(headers + rows);
    const link = document.createElement("a");
    link.setAttribute("href", csvContent);
    link.setAttribute("download", `documents_list_export_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const columns: GridColDef[] = [
    { field: 'title', headerName: '标题', width: 250 },
    { field: 'category', headerName: '类别', width: 150 },
    { field: 'version', headerName: '版本', width: 80 },
    { field: 'trial', headerName: '项目 ID', width: 80 },
    { field: 'site', headerName: '中心 ID', width: 80 },
    { field: 'uploaded_by', headerName: '上传者 ID', width: 100 },
    { field: 'created_at', headerName: '上传时间', width: 180 },
    { 
      field: 'file', 
      headerName: '文件', 
      width: 120,
      renderCell: (params) => (
          params.value ? (
            <Link href={params.value} target="_blank" rel="noopener noreferrer">
            下载
            </Link>
          ) : (
              <Typography variant="body2" color="textSecondary">在线文档</Typography>
          )
      )
    },
    {
        field: 'actions',
        headerName: '操作',
        width: 150,
        renderCell: (params) => (
            <Button 
                size="small" 
                startIcon={<EditIcon />} 
                onClick={() => handleEdit(params.row.id)}
            >
                {params.row.is_online ? '在线编辑' : '编辑内容'}
            </Button>
        )
    }
  ];

  return (
    <Paper sx={{ height: 700, width: '100%', p: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
        <Typography variant="h4">文档管理</Typography>
        <Box>
          <Button 
            variant="contained" 
            startIcon={<UploadIcon />} 
            onClick={() => { setDocMode('upload'); setOpen(true); }}
            sx={{ mr: 1 }}
          >
            上传文档
          </Button>
          <Button 
            variant="contained" 
            color="secondary"
            startIcon={<AddIcon />} 
            onClick={() => { setDocMode('online'); setOpen(true); }}
            sx={{ mr: 1 }}
          >
            创建在线文档
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
        rows={documents}
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

      {/* Upload/Create Dialog */}
      <Dialog open={open} onClose={() => setOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
            {docMode === 'upload' ? '上传新文档' : '创建在线文档'}
        </DialogTitle>
        <DialogContent>
            <Tabs value={docMode} onChange={(_, val) => setDocMode(val)} sx={{ mb: 2 }}>
                <Tab label="上传文件" value="upload" />
                <Tab label="在线文档" value="online" />
            </Tabs>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
            <TextField
              label="文档标题"
              value={newDoc.title}
              onChange={(e) => setNewDoc({ ...newDoc, title: e.target.value })}
              fullWidth
              required
            />
            <TextField
              select
              label="文档类别"
              value={newDoc.category}
              onChange={(e) => setNewDoc({ ...newDoc, category: e.target.value })}
              fullWidth
            >
              {CATEGORY_CHOICES.map((option) => (
                <MenuItem key={option.value} value={option.value}>
                  {option.label}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              label="版本号"
              value={newDoc.version}
              onChange={(e) => setNewDoc({ ...newDoc, version: e.target.value })}
              fullWidth
              required
            />
            <TextField
              label="关联项目 ID (可选)"
              type="number"
              value={newDoc.trial}
              onChange={(e) => setNewDoc({ ...newDoc, trial: e.target.value })}
              fullWidth
            />
            <TextField
              label="关联中心 ID (可选)"
              type="number"
              value={newDoc.site}
              onChange={(e) => setNewDoc({ ...newDoc, site: e.target.value })}
              fullWidth
            />
            <TextField
              label="描述"
              value={newDoc.description}
              onChange={(e) => setNewDoc({ ...newDoc, description: e.target.value })}
              fullWidth
              multiline
              rows={2}
            />
            
            {docMode === 'upload' && (
                <>
                    <Button
                    variant="outlined"
                    component="label"
                    startIcon={<UploadIcon />}
                    >
                    选择文件
                    <input
                        type="file"
                        hidden
                        onChange={handleFileChange}
                    />
                    </Button>
                    {newDoc.file && <Typography variant="body2">{newDoc.file.name}</Typography>}
                </>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>取消</Button>
          <Button onClick={handleSaveDocument} variant="contained">
              {docMode === 'upload' ? '上传' : '创建'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Editor Dialog */}
      <DocumentEditor 
        open={editorOpen} 
        documentId={selectedDocId} 
        onClose={() => setEditorOpen(false)} 
        onSave={() => {
            fetchDocuments();
            // Optional: Don't close, just save
        }}
      />
    </Paper>
  );
};

export default Documents;
