import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Database, Server, Link as LinkIcon, Plus, Loader2, Edit, Trash2 } from "lucide-react"
import { toast } from "sonner"

export interface DataSource {
  id: string;
  name: string;
  type: string;
  status: string;
  connection_string?: string;
}

interface DataSourceListProps {
  initialData: DataSource[];
  isLoading: boolean;
  onSourceAdded: () => void;
}

const DataSourceList: React.FC<DataSourceListProps> = ({ initialData, isLoading, onSourceAdded }) => {
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [testPassed, setTestPassed] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [formData, setFormData] = useState({ name: '', type: '', connection_string: '' });

  const openAddDialog = () => {
    setEditingId(null);
    setFormData({ name: '', type: '', connection_string: '' });
    setTestPassed(false);
    setIsDialogOpen(true);
  };

  const openEditDialog = (source: DataSource) => {
    setEditingId(source.id);
    setFormData({
      name: source.name,
      type: source.type,
      connection_string: source.connection_string || ''
    });
    // 如果已有连接字符串，默认认为需要重新测试，或者您可以选择放宽
    setTestPassed(false); 
    setIsDialogOpen(true);
  };

  const handleDelete = async (id: string) => {
    if (!confirm('确定要删除这个数据源吗？')) return;
    try {
      const res = await fetch(`http://127.0.0.1:8080/api/v1/sources/${id}`, {
        method: 'DELETE'
      });
      if (!res.ok) throw new Error('删除失败');
      toast.success('删除成功');
      onSourceAdded();
    } catch (err: any) {
      toast.error('删除失败', { description: err.message });
    }
  };

  const handleTestConnection = async () => {
    if (!formData.type || !formData.connection_string) {
      toast.error('请先选择数据库类型并填写连接字符串');
      return;
    }

    setIsTesting(true);
    setTestPassed(false);
    
    try {
      const res = await fetch('http://127.0.0.1:8080/api/v1/sources/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: formData.type,
          connection_string: formData.connection_string
        })
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || '连接测试失败');
      }
      
      toast.success('测试成功！', { description: '成功连接到目标数据库系统' });
      setTestPassed(true);
    } catch (err: any) {
      toast.error('连接失败', { description: err.message });
      setTestPassed(false);
    } finally {
      setIsTesting(false);
    }
  };

  const handleSaveSource = async () => {
    if (!formData.name || !formData.type) {
      toast.error('请填写必填项（名称和类型）');
      return;
    }

    if (!testPassed) {
      toast.error('请先成功完成连接测试');
      return;
    }

    setIsSubmitting(true);
    try {
      const method = editingId ? 'PUT' : 'POST';
      const url = editingId 
        ? `http://127.0.0.1:8080/api/v1/sources/${editingId}`
        : 'http://127.0.0.1:8080/api/v1/sources';

      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });

      if (!res.ok) throw new Error('网络请求失败');
      
      toast.success(editingId ? '数据源更新成功' : '数据源添加成功');
      setIsDialogOpen(false);
      setFormData({ name: '', type: '', connection_string: '' });
      setTestPassed(false);
      setEditingId(null);
      onSourceAdded(); // 触发父组件重新拉取数据
    } catch (err: any) {
      toast.error(editingId ? '更新失败' : '添加失败', { description: err.message });
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>数据源列表</CardTitle>
          <CardDescription>正在加载可用连接...</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="flex flex-row items-start justify-between pb-4">
        <div className="space-y-1.5">
          <CardTitle className="flex items-center gap-2">
            <Server className="w-5 h-5 text-blue-600" />
            数据源列表
          </CardTitle>
          <CardDescription>已配置的医院系统连接信息。</CardDescription>
        </div>
        
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button size="sm" className="bg-blue-600 hover:bg-blue-700" onClick={openAddDialog}>
              <Plus className="w-4 h-4 mr-1" />
              配置连接
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[425px] bg-white text-slate-900 border-slate-200 shadow-lg">
            <DialogHeader>
              <DialogTitle>{editingId ? '编辑数据源' : '添加新数据源'}</DialogTitle>
              <DialogDescription>
                {editingId ? '修改现有的医院信息系统连接配置。' : '配置新的医院信息系统连接，目前支持主流关系型数据库。'}
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="name" className="text-right">系统名称</Label>
                <Input 
                  id="name" 
                  placeholder="例如: 影像中心 PACS" 
                  className="col-span-3"
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label className="text-right">数据库类型</Label>
                <div className="col-span-3">
                  <Select 
                    value={formData.type} 
                    onValueChange={(val) => setFormData({...formData, type: val})}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="选择数据库类型" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="PostgreSQL">PostgreSQL</SelectItem>
                      <SelectItem value="MySQL">MySQL</SelectItem>
                      <SelectItem value="Oracle">Oracle</SelectItem>
                      <SelectItem value="SQL Server">SQL Server</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="conn" className="text-right">连接字符串</Label>
                <Input 
                  id="conn" 
                  placeholder="postgresql://user:pass@localhost/db" 
                  className="col-span-3"
                  value={formData.connection_string}
                  onChange={(e) => {
                    setFormData({...formData, connection_string: e.target.value});
                    setTestPassed(false); // 修改连接字符串后需重新测试
                  }}
                />
              </div>
            </div>
            <DialogFooter className="flex justify-between items-center sm:justify-between w-full">
              <Button type="button" variant="secondary" onClick={handleTestConnection} disabled={isTesting}>
                {isTesting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <LinkIcon className="mr-2 h-4 w-4" />}
                测试连接
              </Button>
              <div className="flex gap-2">
                <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>取消</Button>
                <Button type="submit" onClick={handleSaveSource} disabled={!testPassed || isSubmitting}>
                  {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  保存数据源
                </Button>
              </div>
            </DialogFooter>
          </DialogContent>
        </Dialog>

      </CardHeader>
      <CardContent className="flex-1">
        {initialData.length === 0 ? (
          <div className="text-center py-10 text-slate-500 flex flex-col items-center gap-2 border-2 border-dashed rounded-lg">
            <LinkIcon className="w-8 h-8 text-slate-300" />
            <p>暂无活动的数据源</p>
          </div>
        ) : (
          <ul className="space-y-3">
            {initialData.map((source) => (
              <li 
                key={source.id} 
                className="flex items-center justify-between p-3 rounded-lg border bg-white hover:border-blue-200 hover:shadow-sm transition-all"
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-blue-50 text-blue-600 rounded-md">
                    <Database className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-slate-900">{source.name}</h4>
                    <p className="text-xs text-slate-500 uppercase tracking-wider">{source.type}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <Badge 
                    variant="outline" 
                    className={source.status === 'active' ? 'bg-green-50 text-green-700 border-green-200' : 'bg-slate-50 text-slate-500'}
                  >
                    {source.status === 'active' ? '活跃' : '离线'}
                  </Badge>
                  <div className="flex items-center gap-1">
                    <Button 
                      variant="ghost" 
                      size="icon" 
                      className="h-8 w-8 text-slate-500 hover:text-blue-600"
                      onClick={() => openEditDialog(source)}
                      title="编辑"
                    >
                      <Edit className="h-4 w-4" />
                    </Button>
                    <Button 
                      variant="ghost" 
                      size="icon" 
                      className="h-8 w-8 text-slate-500 hover:text-red-600"
                      onClick={() => handleDelete(source.id)}
                      title="删除"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
};

export default DataSourceList;
