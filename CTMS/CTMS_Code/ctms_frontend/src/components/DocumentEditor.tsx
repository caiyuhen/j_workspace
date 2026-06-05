import React, { useState, useEffect, useCallback } from 'react';
import { 
  Dialog, 
  DialogTitle, 
  DialogContent, 
  DialogActions, 
  Button, 
  Typography, 
  Box, 
  CircularProgress,
  Alert,
  Tooltip,
  IconButton
} from '@mui/material';
import { Refresh as RefreshIcon } from '@mui/icons-material';
import ReactQuill from 'react-quill';
import 'react-quill/dist/quill.snow.css';
import { AxiosError } from 'axios';
import api from '../api/axios';
import { useAuth } from '../context/AuthContext';
import type { User } from '../types/auth';

interface DocumentEditorProps {
  open: boolean;
  documentId: number | null;
  onClose: () => void;
  onSave?: () => void;
}

interface DocumentDetails {
  id: number;
  title: string;
  content: string;
  is_online: boolean;
  locked_by: number | null;
  locked_by_details: User | null;
  locked_at: string | null;
}

const DocumentEditor: React.FC<DocumentEditorProps> = ({ open, documentId, onClose, onSave }) => {
  const { user, isLoading: authLoading } = useAuth();
  const [document, setDocument] = useState<DocumentDetails | null>(null);
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Use useCallback to prevent infinite loops if fetchDocument is added to dependencies
  const fetchDocument = useCallback(async () => {
    if (!documentId) return;
    setLoading(true);
    setError(null);
    try {
      const response = await api.get(`documents/${documentId}/`);
      setDocument(response.data);
      // Only set content if we don't have local changes? 
      // For now, always overwrite local content on refresh to ensure sync
      setContent(response.data.content || '');
    } catch (err: unknown) {
      console.error(err);
      const error = err as AxiosError;
      if (error.response?.status === 401) {
        setError('Unauthorized: Please log in again.');
      } else {
        setError('Failed to load document');
      }
    } finally {
      setLoading(false);
    }
  }, [documentId]);

  useEffect(() => {
    if (open && documentId) {
      fetchDocument();
    } else {
      setDocument(null);
      setContent('');
      setError(null);
    }
  }, [open, documentId, fetchDocument]);

  const handleLock = async () => {
    if (!documentId) return;
    setLoading(true);
    try {
      const response = await api.post(`documents/${documentId}/lock/`);
      setDocument(response.data);
      setError(null);
    } catch (err: unknown) {
      const error = err as AxiosError<{ error: string }>;
      const msg = error.response?.data?.error || 'Failed to lock document';
      setError(msg);
      // Refresh document state in case it was locked by someone else in the meantime
      fetchDocument();
    } finally {
      setLoading(false);
    }
  };

  const handleUnlock = async () => {
    if (!documentId) return;
    setLoading(true);
    try {
      const response = await api.post(`documents/${documentId}/unlock/`);
      setDocument(response.data);
      setError(null);
    } catch (err: unknown) {
      const error = err as AxiosError<{ error: string }>;
      setError(error.response?.data?.error || 'Failed to unlock document');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!documentId) return;
    setSaving(true);
    try {
      const response = await api.post(`documents/${documentId}/save_content/`, { content });
      setDocument(response.data);
      if (onSave) onSave();
    } catch (err: unknown) {
      const error = err as AxiosError<{ error: string }>;
      setError(error.response?.data?.error || 'Failed to save content');
    } finally {
      setSaving(false);
    }
  };

  const handleClose = async () => {
    // If locked by current user, verify if they want to unlock
    // Strict comparison after converting to string to be safe
    const isLockedByMe = document?.locked_by && user?.id ? String(document.locked_by) === String(user.id) : false;
    
    if (isLockedByMe) {
       if (window.confirm('您当前锁定了该文档。关闭前是否解锁？\n点击“确定”解锁并关闭。\n点击“取消”保留锁定并关闭。')) {
           await handleUnlock();
       }
    }
    onClose();
  };

  // Status determination logic
  const isLockedByMe = document?.locked_by && user?.id ? String(document.locked_by) === String(user.id) : false;
  const isLockedByOther = document?.locked_by && (!user?.id || String(document.locked_by) !== String(user.id));
  const isUnlocked = !document?.locked_by;

  // Editor modules configuration
  const modules = {
    toolbar: isLockedByMe ? [
      [{ 'header': [1, 2, 3, false] }],
      ['bold', 'italic', 'underline', 'strike', 'blockquote'],
      [{'list': 'ordered'}, {'list': 'bullet'}, {'indent': '-1'}, {'indent': '+1'}],
      ['link', 'image'],
      ['clean']
    ] : false // Hide toolbar if read-only
  };

  return (
    <Dialog open={open} onClose={handleClose} fullWidth maxWidth="lg">
      <DialogTitle>
        <Box display="flex" justifyContent="space-between" alignItems="center">
            <Box display="flex" alignItems="center" gap={1}>
                <Typography variant="h6">{document?.title || '在线编辑文档'}</Typography>
                <Tooltip title="刷新状态">
                    <IconButton size="small" onClick={fetchDocument} disabled={loading}>
                        <RefreshIcon />
                    </IconButton>
                </Tooltip>
            </Box>
            
            {document && (
                <Box>
                    {isLockedByMe && <Typography variant="caption" sx={{ color: 'green', fontWeight: 'bold', border: '1px solid green', px: 1, py: 0.5, borderRadius: 1 }}>✅ 您正在编辑 (已锁定)</Typography>}
                    {isLockedByOther && <Typography variant="caption" sx={{ color: 'red', fontWeight: 'bold', border: '1px solid red', px: 1, py: 0.5, borderRadius: 1 }}>🔒 被 {document.locked_by_details?.username || '其他用户'} 锁定</Typography>}
                    {isUnlocked && <Typography variant="caption" sx={{ color: 'text.secondary', border: '1px solid #ccc', px: 1, py: 0.5, borderRadius: 1 }}>🔓 未锁定 (只读模式)</Typography>}
                </Box>
            )}
        </Box>
      </DialogTitle>
      <DialogContent dividers sx={{ display: 'flex', flexDirection: 'column', height: '60vh', p: 0 }}>
        {(loading || authLoading) && (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', p: 2 }}>
                <CircularProgress size={24} sx={{ mr: 1 }} />
                <Typography>正在加载文档状态...</Typography>
            </Box>
        )}
        
        {error && <Alert severity="error" sx={{ m: 2 }}>{error}</Alert>}
        
        {!loading && !authLoading && document && !document.is_online && (
             <Alert severity="info" sx={{ m: 2, mb: 0 }}>
                 这是一个文件上传类型的文档。在线编辑只会修改附加的文本内容，不会更改原始上传的文件。
             </Alert>
        )}
        
        {!loading && !authLoading && document && (
          <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', p: 2, overflow: 'hidden' }}>
            <ReactQuill 
                theme="snow" 
                value={content} 
                onChange={setContent} 
                readOnly={!isLockedByMe}
                modules={modules}
                style={{ 
                    height: '100%', 
                    display: 'flex', 
                    flexDirection: 'column',
                    backgroundColor: isLockedByMe ? '#fff' : '#fafafa'
                }}
                className={!isLockedByMe ? 'read-only-editor' : ''}
            />
            {/* Custom styles to fix Quill height issues */}
            <style>{`
                .quill { display: flex; flex-direction: column; height: 100%; }
                .ql-container { flex: 1; overflow-y: auto; font-size: 16px; }
                .read-only-editor .ql-container { border-top: 1px solid #ccc; }
            `}</style>
          </Box>
        )}
      </DialogContent>
      <DialogActions sx={{ p: 2 }}>
        <Button onClick={handleClose} color="inherit">
            关闭
        </Button>
        
        {isUnlocked && (
            <Button onClick={handleLock} variant="contained" color="primary">
                锁定并编辑
            </Button>
        )}

        {isLockedByMe && (
            <>
                <Button onClick={handleUnlock} color="warning">
                    解锁 (停止编辑)
                </Button>
                <Button onClick={handleSave} variant="contained" color="success" disabled={saving}>
                    {saving ? '保存中...' : '保存内容'}
                </Button>
            </>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default DocumentEditor;