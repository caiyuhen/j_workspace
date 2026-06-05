import React, { useState, useEffect, useCallback } from 'react';
import {  Table, Modal, Form, Input, Select, Space, Button, Drawer , App } from 'antd';
import { EditOutlined, PlusOutlined, TeamOutlined } from '@ant-design/icons';
import PageHeader from '@/components/PageHeader';
import StatusTag from '@/components/StatusTag';
import { siteApi } from '@/api/site';
import { projectApi } from '@/api/project';
import { settingsApi } from '@/api/settings';
import type { Site, CreateSiteParams, SiteStaff, AddSiteStaffParams } from '@/types';

const statusOptions = [
  { value: 'active', label: '活跃' },
  { value: 'inactive', label: '停用' },
  { value: 'suspended', label: '暂停' },
  { value: 'closed', label: '关闭' },
];

const SitesPage: React.FC = () => {
  const { message } = App.useApp();
  const [data, setData] = useState<Site[]>([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({ page: 1, pageSize: 10, total: 0 });
  const [keyword, setKeyword] = useState('');

  // 中心弹窗
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Site | null>(null);
  const [form] = Form.useForm();
  const [submitLoading, setSubmitLoading] = useState(false);

  // 工作人员抽屉
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [selectedSite, setSelectedSite] = useState<Site | null>(null);
  const [staffList, setStaffList] = useState<SiteStaff[]>([]);
  const [staffLoading, setStaffLoading] = useState(false);
  const [staffForm] = Form.useForm();
  const [staffModalOpen, setStaffModalOpen] = useState(false);
  const [projects, setProjects] = useState<{label: string, value: string}[]>([]);
  const [projectsLoading, setProjectsLoading] = useState(false);
  const [users, setUsers] = useState<{label: string, value: string}[]>([]);
  const [usersLoading, setUsersLoading] = useState(false);
  const [siteOrgs, setSiteOrgs] = useState<{label: string, value: string, org: any}[]>([]);

  const fetchProjects = useCallback(async () => {
    setProjectsLoading(true);
    try {
      const res = await projectApi.list({ page: 1, pageSize: 1000 });
      setProjects((res?.list || []).map((p: any) => ({
        label: p.projectName,
        value: p.id })));
    } catch {
      // ignore
    } finally {
      setProjectsLoading(false);
    }
  }, []);

  const fetchUsers = useCallback(async () => {
    setUsersLoading(true);
    try {
      const res = await settingsApi.listUsers({ page: 1, pageSize: 1000 });
      setUsers((res?.list || []).map((u: any) => ({
        label: u.displayName || u.username,
        value: u.id,
        roleName: u.role?.name || u.userRoles?.[0]?.role?.roleName || '无角色'
      })));
    } catch {
      // ignore
    } finally {
      setUsersLoading(false);
    }
  }, []);

  const fetchSiteOrgs = useCallback(async () => {
    try {
      const res = await settingsApi.listOrganizations({ page: 1, pageSize: 1000 });
      const orgs = (res?.list || []).filter((o: any) => o.orgType === 'site' || o.type === 'site');
      setSiteOrgs(orgs.map((o: any) => ({
        label: o.orgName || o.name,
        value: o.orgName || o.name,
        org: o
      })));
    } catch {}
  }, []);

  const handleOpenAddStaff = () => {
    staffForm.resetFields();
    setStaffModalOpen(true);
  };

  const fetchData = useCallback(async (page = 1, pageSize = 10) => {
    setLoading(true);
    try {
      const res = await siteApi.list({ page, pageSize, keyword });
      setData(res?.list || []);
      setPagination({ page: res?.page || 1, pageSize: res?.pageSize || 10, total: res?.total || 0 });
    } catch {
      message.error('加载中心列表失败');
    } finally {
      setLoading(false);
    }
  }, [keyword]);

  useEffect(() => {
    fetchData();
    fetchProjects();
    fetchUsers();
    fetchSiteOrgs();
  }, [fetchData, fetchProjects, fetchUsers, fetchSiteOrgs]);

  const handleCreate = () => {
    setEditing(null);
    form.resetFields();
    // Auto-generate siteCode
    const randomSuffix = Math.floor(Math.random() * 1000).toString().padStart(3, '0');
    form.setFieldsValue({ siteCode: `SITE-${randomSuffix}` });
    setModalOpen(true);
  };

  const handleEdit = (record: Site) => {
    setEditing(record);
    form.setFieldsValue(record);
    setModalOpen(true);
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setSubmitLoading(true);
      if (editing) {
        await siteApi.update(editing.id, values);
        message.success('更新中心成功');
      } else {
        await siteApi.create(values as CreateSiteParams);
        message.success('创建中心成功');
      }
      setModalOpen(false);
      fetchData(pagination.page, pagination.pageSize);
    } catch (err: any) {
      if (err.errorFields) {
        message.warning('请检查表单填写是否正确');
        return;
      }
      const errorMsg = err.response?.data?.error?.message || err.message || '操作失败';
      const details = err.response?.data?.error?.details;
      if (details && Array.isArray(details)) {
        message.error(`校验失败: ${details.map((d: any) => d.message).join(', ')}`);
      } else {
        message.error(errorMsg);
      }
    } finally {
      setSubmitLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await siteApi.delete(id);
      message.success('中心已删除');
      fetchData(pagination.page, pagination.pageSize);
    } catch {
      message.error('删除失败');
    }
  };

  // 工作人员管理
  const openStaff = (record: Site) => {
    setSelectedSite(record);
    setDrawerOpen(true);
    loadStaff(record.id);
  };

  const loadStaff = async (siteId: string) => {
    setStaffLoading(true);
    try {
      const res = await siteApi.getById(siteId);
      setStaffList(res.siteStaff || []);
    } catch {
      message.error('加载工作人员失败');
    } finally {
      setStaffLoading(false);
    }
  };

  const handleAddStaff = async () => {
    try {
      const values = await staffForm.validateFields();
      await siteApi.addStaff(selectedSite!.id, { ...values, roleAtSite: 'OTHER' } as AddSiteStaffParams);
      message.success('工作人员已添加');
      setStaffModalOpen(false);
      staffForm.resetFields();
      loadStaff(selectedSite!.id);
    } catch (err: any) {
      if (err.errorFields) {
        message.warning('请检查表单填写是否正确');
        return;
      }
      message.error('添加失败');
    }
  };

  const handleRemoveStaff = async (staffId: string) => {
    try {
      await siteApi.deleteStaff(selectedSite!.id, staffId);
      message.success('已移除');
      loadStaff(selectedSite!.id);
    } catch {
      message.error('移除失败');
    }
  };

  const columns = [
    { title: '中心编号', dataIndex: 'siteCode', key: 'siteCode', width: 140 },
    { title: '中心名称', dataIndex: 'siteName', key: 'siteName', ellipsis: true },
    { title: '地址', dataIndex: 'address', key: 'address', ellipsis: true, width: 200 },
    { title: '联系电话', dataIndex: 'contactPhone', key: 'contactPhone', width: 130 },
    {
      title: '中心状态', dataIndex: 'status', key: 'status', width: 100,
      render: (v: string) => <StatusTag status={v} category="site" /> },
    {
      title: '操作', key: 'actions', width: 200, fixed: 'right' as const,
      render: (_: any, record: Site) => (
        <Space>
          <Button type="link" size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)}>编辑</Button>
          <Button type="link" size="small" icon={<TeamOutlined />} onClick={() => openStaff(record)}>人员</Button>
          <Button type="link" size="small" danger onClick={() => handleDelete(record.id)}>删除</Button>
        </Space>
      ) },
  ];

  return (
    <div>
      <PageHeader
        title="中心管理"
        subtitle="研究中心的激活、管理和监查计划"
        showCreate
        onCreateClick={handleCreate}
        onSearch={setKeyword}
        searchPlaceholder="搜索中心编号或名称"
      />

      <Table
        rowKey="id"
        columns={columns}
        dataSource={data}
        loading={loading}
        scroll={{ x: 1100 }}
        pagination={{
          current: pagination.page,
          pageSize: pagination.pageSize,
          total: pagination.total,
          showSizeChanger: true,
          showTotal: (total) => `共 ${total} 条`,
          onChange: (page, pageSize) => fetchData(page, pageSize) }}
      />

      {/* 新建/编辑中心弹窗 */}
      <Modal
        title={editing ? '编辑中心' : '新建中心'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        width={640}
        confirmLoading={submitLoading}
        okText="保存"
        cancelText="取消"
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item name="projectId" label="所属项目">
            <Select placeholder="请选择项目" options={projects} loading={projectsLoading} showSearch optionFilterProp="label" allowClear />
          </Form.Item>
          <Space style={{ width: '100%' }} size="large">
            <Form.Item name="siteCode" label="中心编号" rules={[{ required: true }]}>
              <Input 
                placeholder="如 SITE-001" 
                style={{ width: 250 }} 
                suffix={
                  <a onClick={() => {
                    const randomSuffix = Math.floor(Math.random() * 1000).toString().padStart(3, '0');
                    form.setFieldsValue({ siteCode: `SITE-${randomSuffix}` });
                  }}>自动生成</a>
                }
              />
            </Form.Item>
            <Form.Item name="siteName" label="中心名称" rules={[{ required: true }]}>
              <Select 
                placeholder="请选择组织机构" 
                style={{ width: 320 }}
                options={siteOrgs}
                showSearch
                onChange={(_, option: any) => {
                  if (option && option.org) {
                    const code = option.org.orgCode || option.org.code;
                    if (code) {
                      form.setFieldsValue({ siteCode: code });
                    }
                  }
                }}
              />
            </Form.Item>
          </Space>
          {editing && (
            <Form.Item name="status" label="中心状态">
              <Select placeholder="请选择" style={{ width: 200 }} options={statusOptions} />
            </Form.Item>
          )}
        </Form>
      </Modal>

      {/* 工作人员抽屉 */}
      <Drawer
        title={`${selectedSite?.siteName || ''} - 工作人员`}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        size="large"
      >
        <div style={{ marginBottom: 16 }}>
          <Button type="primary" icon={<PlusOutlined />} onClick={handleOpenAddStaff}>
            添加人员
          </Button>
        </div>
        <Table
          rowKey="id"
          dataSource={staffList}
          loading={staffLoading}
          pagination={false}
          size="small"
          columns={[
            { title: '用户名称', dataIndex: ['user', 'displayName'], key: 'userName', ellipsis: true, render: (_, record) => record.user?.displayName || record.user?.username || record.userId },
            { title: '角色名称', dataIndex: 'roleAtSite', key: 'roleAtSite', render: (_, record: any) => record.user?.role?.name || record.user?.userRoles?.[0]?.role?.roleName || '无角色' },
            { title: '加入日期', dataIndex: 'joinedAt', key: 'joinedAt', render: (v: string) => v ? new Date(v).toLocaleDateString() : '-' },
            { title: '状态', dataIndex: 'status', key: 'status', render: (v: string) => <StatusTag status={v} category="site" /> },
            {
              title: '操作', key: 'actions', width: 80,
              render: (_: any, record: SiteStaff) => (
                <Button type="link" size="small" danger onClick={() => handleRemoveStaff(record.id)}>移除</Button>
              ) },
          ]}
        />
        {staffList.length === 0 && !staffLoading && (
          <div style={{ textAlign: 'center', color: '#999', padding: 24 }}>暂无工作人员，请添加</div>
        )}

        {/* 添加工作人员弹窗 */}
        <Modal
          title="添加工作人员"
          open={staffModalOpen}
          onOk={handleAddStaff}
          onCancel={() => setStaffModalOpen(false)}
          confirmLoading={submitLoading}
          okText="添加"
          cancelText="取消"
        >
          <Form form={staffForm} layout="vertical" style={{ marginTop: 16 }}>
            <Form.Item name="userId" label="用户名称" rules={[{ required: true, message: '请选择用户' }]}>
              <Select 
                placeholder="请选择用户" 
                options={users} 
                loading={usersLoading} 
                showSearch 
                optionFilterProp="label"
                onChange={(_, option: any) => {
                  if (option && option.roleName) {
                    staffForm.setFieldsValue({ roleName: option.roleName });
                  }
                }}
              />
            </Form.Item>
            <Form.Item name="roleName" label="角色名称">
              <Input disabled placeholder="选择用户后自动带出" />
            </Form.Item>
            <Form.Item name="joinedAt" label="加入日期">
              <Input type="date" />
            </Form.Item>
          </Form>
        </Modal>
      </Drawer>
    </div>
  );
};

export default SitesPage;
