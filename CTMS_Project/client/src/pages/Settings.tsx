import React, { useState, useEffect, useCallback } from 'react';
import {  Table, Modal, Form, Input, Select, Space, Button, Tabs, Row, Col, Tag, Popconfirm , App, Switch } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, UserOutlined, TeamOutlined, BankOutlined } from '@ant-design/icons';
import PageHeader from '@/components/PageHeader';
import { settingsApi } from '@/api/settings';
import type { User, Role, CreateRoleParams, Organization } from '@/types';

const orgTypeOptions = [
  { value: 'sponsor', label: '申办方' },
  { value: 'cro', label: 'CRO' },
  { value: 'site', label: '中心' },
  { value: 'vendor', label: '供应商' },
  { value: 'regulatory', label: '监管机构' },
  { value: 'other', label: '其他' },
];

const permissionGroups = [
  { group: '项目管理', permissions: ['project:create', 'project:read', 'project:update', 'project:delete'] },
  { group: '中心管理', permissions: ['site:create', 'site:read', 'site:update', 'site:delete'] },
  { group: '受试者管理', permissions: ['edc:subject:create', 'edc:subject:read', 'edc:subject:update'] },
  { group: '数据录入', permissions: ['edc:data:create', 'edc:data:read', 'edc:data:update'] },
  { group: '质疑管理', permissions: ['edc:query:create', 'edc:query:read', 'edc:query:update', 'edc:query:close'] },
  { group: 'AE管理', permissions: ['edc:ae:create', 'edc:ae:read', 'edc:ae:update'] },
  { group: 'SDV核查', permissions: ['edc:sdv:create', 'edc:sdv:read', 'edc:sdv:update', 'edc:sdv:complete'] },
  { group: '药物管理', permissions: ['ctms:drug:create', 'ctms:drug:read', 'ctms:drug:update', 'ctms:drug:supply'] },
  { group: '文档管理', permissions: ['ctms:document:create', 'ctms:document:read', 'ctms:document:update', 'ctms:document:approve'] },
  { group: '财务管理', permissions: ['finance:income:create', 'finance:income:read', 'finance:expense:create', 'finance:expense:read', 'finance:view'] },
  { group: '工作流', permissions: ['workflow:create', 'workflow:read', 'workflow:approve'] },
  { group: '审计', permissions: ['audit:read'] },
  { group: 'AI', permissions: ['ai:chat', 'ai:analyze', 'ai:batch'] },
  { group: '系统管理', permissions: ['user:create', 'user:read', 'user:update', 'user:delete', 'role:create', 'role:read', 'role:update', 'role:delete'] },
];

const SettingsPage: React.FC = () => {
  const { message } = App.useApp();
  const [activeTab, setActiveTab] = useState('users');

  // 用户管理
  const [users, setUsers] = useState<User[]>([]);
  const [usersLoading, setUsersLoading] = useState(false);
  const [userPagination, setUserPagination] = useState({ page: 1, pageSize: 10, total: 0 });
  const [userModalOpen, setUserModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [userForm] = Form.useForm();
  const [userSubmitLoading, setUserSubmitLoading] = useState(false);

  // 角色管理
  const [roles, setRoles] = useState<Role[]>([]);
  const [rolesLoading, setRolesLoading] = useState(false);
  const [roleModalOpen, setRoleModalOpen] = useState(false);
  const [editingRole, setEditingRole] = useState<Role | null>(null);
  const [roleForm] = Form.useForm();
  const [roleSubmitLoading, setRoleSubmitLoading] = useState(false);
  const [selectedPermissions, setSelectedPermissions] = useState<string[]>([]);

  // 组织机构
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [orgsLoading, setOrgsLoading] = useState(false);
  const [orgModalOpen, setOrgModalOpen] = useState(false);
  const [editingOrg, setEditingOrg] = useState<Organization | null>(null);
  const [orgForm] = Form.useForm();
  const [orgSubmitLoading, setOrgSubmitLoading] = useState(false);

  // ===== 数据获取 =====
  const fetchUsers = useCallback(async (page = 1, pageSize = 10) => {
    setUsersLoading(true);
    try {
      const res = await settingsApi.listUsers({ page, pageSize });
      setUsers((res?.list || []).map((u: any) => {
        const primaryRole = u.userRoles?.[0]?.role;
        return {
          ...u,
          roleId: primaryRole?.id,
          role: primaryRole ? { id: primaryRole.id, name: primaryRole.roleName, code: primaryRole.roleCode } : undefined
        };
      }));
      setUserPagination({ page: res?.page || 1, pageSize: res?.pageSize || 10, total: res?.total || 0 });
    } catch { message.error('加载用户列表失败'); }
    finally { setUsersLoading(false); }
  }, []);

  const fetchRoles = useCallback(async () => {
    setRolesLoading(true);
    try { 
      const res = await settingsApi.listRoles({ page: 1, pageSize: 100 });
      setRoles((res?.list || []).map((r: any) => ({
        ...r,
        name: r.roleName,
        code: r.roleCode,
        isSystem: r.isSystemRole,
        permissions: r.rolePermissions?.map((rp: any) => rp.permission?.permissionCode) || []
      }))); 
    }
    catch { message.error('加载角色列表失败'); }
    finally { setRolesLoading(false); }
  }, []);

  const fetchOrganizations = useCallback(async () => {
    setOrgsLoading(true);
    try { 
      const res = await settingsApi.listOrganizations({ page: 1, pageSize: 100 });
      setOrganizations((res?.list || []).map((o: any) => ({
        ...o,
        name: o.orgName,
        code: o.orgCode,
        type: o.orgType
      }))); 
    }
    catch { message.error('加载组织机构失败'); }
    finally { setOrgsLoading(false); }
  }, []);

  useEffect(() => { fetchUsers(); fetchRoles(); fetchOrganizations(); }, [fetchUsers, fetchRoles, fetchOrganizations]);

  // ===== 用户管理 =====
  const handleCreateUser = () => {
    setEditingUser(null);
    userForm.resetFields();
    setUserModalOpen(true);
  };

  const handleEditUser = (user: User) => {
    setEditingUser(user);
    userForm.setFieldsValue({ ...user, roleId: user.roleId });
    setUserModalOpen(true);
  };

  const handleUserSubmit = async () => {
    try {
      const values = await userForm.validateFields();
      setUserSubmitLoading(true);
      const submitData = { ...values, roleIds: [values.roleId] };
      delete submitData.roleId;

      if (editingUser) {
        await settingsApi.updateUser(editingUser.id, submitData);
        message.success('更新用户成功');
      } else {
        await settingsApi.createUser(submitData);
        message.success('创建用户成功');
      }
      setUserModalOpen(false);
      fetchUsers(userPagination.page, userPagination.pageSize);
    } catch (err: any) {
      if (err.errorFields) {
        message.warning('请检查表单填写是否正确');
        return;
      }
      const errorMsg = err.response?.data?.error?.message || err.message || '操作失败';
      const details = err.response?.data?.error?.details;
      if (details && Array.isArray(details)) {
        message.error(`校验失败: ${details.map(d => d.message).join(', ')}`);
      } else {
        message.error(errorMsg);
      }
    }
    finally { setUserSubmitLoading(false); }
  };

  const handleDeleteUser = (user: User) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定删除用户「${user.displayName}」吗？`,
      onOk: async () => {
        try {
          await settingsApi.deleteUser(user.id);
          message.success('已删除');
          fetchUsers(userPagination.page, userPagination.pageSize);
        } catch (err: any) {
          message.error(err.response?.data?.error?.message || '删除失败');
        }
      } });
  };

  const handleToggleUserStatus = async (record: User, checked: boolean) => {
    try {
      const newStatus = checked ? 'active' : 'inactive';
      await settingsApi.updateUser(record.id, { status: newStatus });
      message.success(`已${checked ? '启用' : '停用'}该用户`);
      fetchUsers(userPagination.page, userPagination.pageSize);
    } catch (err: any) {
      message.error(err.response?.data?.error?.message || '操作失败');
    }
  };

  const userColumns = [
    { title: '用户名', dataIndex: 'username', width: 120 },
    { title: '显示名', dataIndex: 'displayName', width: 120 },
    { title: '邮箱', dataIndex: 'email', ellipsis: true },
    { title: '部门', dataIndex: 'department', width: 100 },
    { title: '角色', dataIndex: ['role', 'name'], width: 120 },
    {
      title: '状态', dataIndex: 'status', width: 100,
      render: (v: string, record: User) => {
        if (v === 'locked') return <Tag color="error">锁定</Tag>;
        return (
          <Switch 
            checked={v === 'active'} 
            checkedChildren="启用" 
            unCheckedChildren="停用"
            onChange={(checked) => handleToggleUserStatus(record, checked)}
          />
        );
      } },
    { title: '最后登录', dataIndex: 'lastLoginAt', width: 140, render: (v: string) => v ? new Date(v).toLocaleString('zh-CN') : '-' },
    {
      title: '操作', width: 140,
      render: (_: any, record: User) => (
        <Space size="small">
          <Button type="link" size="small" icon={<EditOutlined />} onClick={() => handleEditUser(record)}>编辑</Button>
          <Popconfirm title="确认删除？" onConfirm={() => handleDeleteUser(record)}>
            <Button type="link" size="small" danger icon={<DeleteOutlined />}>删除</Button>
          </Popconfirm>
        </Space>
      ) },
  ];

  // ===== 角色管理 =====
  const handleCreateRole = () => {
    setEditingRole(null);
    roleForm.resetFields();
    setSelectedPermissions([]);
    setRoleModalOpen(true);
  };

  const handleEditRole = (role: Role) => {
    setEditingRole(role);
    roleForm.setFieldsValue({ name: role.name, code: role.code, description: role.description });
    setSelectedPermissions(role.permissions || []);
    setRoleModalOpen(true);
  };

  const handleRoleSubmit = async () => {
    try {
      const values = await roleForm.validateFields();
      setRoleSubmitLoading(true);
      const params: CreateRoleParams = { ...values, permissions: selectedPermissions };
      if (editingRole) {
        await settingsApi.updateRole(editingRole.id, params);
        message.success('更新角色成功');
      } else {
        await settingsApi.createRole(params);
        message.success('创建角色成功');
      }
      setRoleModalOpen(false);
      fetchRoles();
    } catch (err: any) {
      if (err.errorFields) {
        message.warning('请检查表单填写是否正确');
        return;
      }
      const errorMsg = err.response?.data?.error?.message || err.message || '操作失败';
      const details = err.response?.data?.error?.details;
      if (details && Array.isArray(details)) {
        message.error(`校验失败: ${details.map(d => d.message).join(', ')}`);
      } else {
        message.error(errorMsg);
      }
    }
    finally { setRoleSubmitLoading(false); }
  };

  const togglePermission = (perm: string) => {
    setSelectedPermissions(prev =>
      prev.includes(perm) ? prev.filter(p => p !== perm) : [...prev, perm]
    );
  };

  const roleColumns = [
    { title: '角色名称', dataIndex: 'name', width: 150 },
    { title: '角色编码', dataIndex: 'code', width: 150 },
    { title: '描述', dataIndex: 'description', ellipsis: true },
    { title: '权限数', dataIndex: 'permissions', width: 80, render: (v: string[]) => v?.length || 0 },
    { title: '用户数', dataIndex: 'userCount', width: 80 },
    {
      title: '系统角色', dataIndex: 'isSystem', width: 80,
      render: (v: boolean) => v ? <Tag color="blue">系统</Tag> : <Tag>自定义</Tag> },
    {
      title: '操作', width: 140,
      render: (_: any, record: Role) => (
        <Space size="small">
          <Button type="link" size="small" icon={<EditOutlined />} onClick={() => handleEditRole(record)}>编辑</Button>
          {!record.isSystem && (
            <Popconfirm title="确认删除？" onConfirm={async () => { 
            try {
              await settingsApi.deleteRole(record.id); 
              message.success('已删除'); 
              fetchRoles(); 
            } catch (err: any) {
              message.error(err.response?.data?.error?.message || '删除失败');
            }
          }}>
            <Button type="link" size="small" danger icon={<DeleteOutlined />}>删除</Button>
          </Popconfirm>
          )}
        </Space>
      ) },
  ];

  // ===== 组织机构 =====
  const handleCreateOrg = () => {
    setEditingOrg(null);
    orgForm.resetFields();
    const randomSuffix = Math.floor(Math.random() * 1000).toString().padStart(3, '0');
    orgForm.setFieldsValue({ type: 'site', status: 'active', code: `ORG-${randomSuffix}` });
    setOrgModalOpen(true);
  };

  const handleEditOrg = (org: Organization) => {
    setEditingOrg(org);
    orgForm.setFieldsValue(org);
    setOrgModalOpen(true);
  };

  const handleOrgSubmit = async () => {
    try {
      const values = await orgForm.validateFields();
      setOrgSubmitLoading(true);
      
      const submitData = {
        ...values,
        orgName: values.name,
        orgCode: values.code,
        orgType: values.type,
      };
      
      delete submitData.name;
      delete submitData.code;
      delete submitData.type;

      if (editingOrg) {
        await settingsApi.updateOrganization(editingOrg.id, submitData);
        message.success('更新组织成功');
      } else {
        await settingsApi.createOrganization(submitData);
        message.success('创建组织成功');
      }
      setOrgModalOpen(false);
      fetchOrganizations();
    } catch (err: any) { 
      if (err.errorFields) {
        message.warning('请检查表单填写是否正确');
        return;
      }
      const errorMsg = err.response?.data?.error?.message || err.message || '操作失败';
      const details = err.response?.data?.error?.details;
      if (details && Array.isArray(details)) {
        message.error(`校验失败: ${details.map(d => d.message).join(', ')}`);
      } else {
        message.error(errorMsg);
      }
    }
    finally { setOrgSubmitLoading(false); }
  };

  const handleToggleOrgStatus = async (record: Organization, checked: boolean) => {
    try {
      const newStatus = checked ? 'active' : 'inactive';
      await settingsApi.updateOrganization(record.id, { status: newStatus });
      message.success(`已${checked ? '启用' : '停用'}该组织`);
      fetchOrganizations();
    } catch (err: any) {
      message.error(err.response?.data?.error?.message || '操作失败');
    }
  };

  const orgColumns = [
    { title: '组织名称', dataIndex: 'name', width: 180 },
    { title: '编码', dataIndex: 'code', width: 120 },
    {
      title: '类型', dataIndex: 'type', width: 100,
      render: (v: string) => orgTypeOptions.find(o => o.value === v)?.label || v },
    { title: '联系人', dataIndex: 'contactPerson', width: 100 },
    { title: '联系电话', dataIndex: 'contactPhone', width: 120 },
    { title: '邮箱', dataIndex: 'contactEmail', ellipsis: true },
    {
      title: '状态', dataIndex: 'status', width: 100,
      render: (v: string, record: Organization) => (
        <Switch 
          checked={v === 'active'} 
          checkedChildren="启用" 
          unCheckedChildren="停用"
          onChange={(checked) => handleToggleOrgStatus(record, checked)}
        />
      ) },
    {
      title: '操作', width: 140,
      render: (_: any, record: Organization) => (
        <Space size="small">
          <Button type="link" size="small" icon={<EditOutlined />} onClick={() => handleEditOrg(record)}>编辑</Button>
          <Popconfirm title="确认删除？" onConfirm={async () => { 
            try {
              await settingsApi.deleteOrganization(record.id); 
              message.success('已删除'); 
              fetchOrganizations(); 
            } catch (err: any) {
              message.error(err.response?.data?.error?.message || '删除失败');
            }
          }}>
            <Button type="link" size="small" danger icon={<DeleteOutlined />}>删除</Button>
          </Popconfirm>
        </Space>
      ) },
  ];

  return (
    <>
      <PageHeader title="系统设置">
        {activeTab === 'users' && <Button type="primary" icon={<PlusOutlined />} onClick={handleCreateUser}>新增用户</Button>}
        {activeTab === 'roles' && <Button type="primary" icon={<PlusOutlined />} onClick={handleCreateRole}>新增角色</Button>}
        {activeTab === 'organizations' && <Button type="primary" icon={<PlusOutlined />} onClick={handleCreateOrg}>新增组织</Button>}
      </PageHeader>

      <Tabs activeKey={activeTab} onChange={setActiveTab} items={[
      {
        key: 'users', label: <span><UserOutlined /> 用户管理</span>, children: (
          <Table rowKey="id" columns={userColumns} dataSource={users} loading={usersLoading}
            pagination={{
              current: userPagination.page, pageSize: userPagination.pageSize, total: userPagination.total,
              showSizeChanger: true, showTotal: (t) => `共 ${t} 条`,
              onChange: (p, ps) => fetchUsers(p, ps) }}
            scroll={{ x: 1100 }} />
        ) },
      {
        key: 'roles', label: <span><TeamOutlined /> 角色管理</span>, children: (
          <Table rowKey="id" columns={roleColumns} dataSource={roles} loading={rolesLoading}
            pagination={false} scroll={{ x: 900 }} />
        ) },
      {
        key: 'organizations', label: <span><BankOutlined /> 组织机构</span>, children: (
          <Table rowKey="id" columns={orgColumns} dataSource={organizations} loading={orgsLoading}
            pagination={false} scroll={{ x: 1100 }} />
        ) },
    ]} />

    {/* 用户弹窗 */}
    <Modal title={editingUser ? '编辑用户' : '新增用户'} open={userModalOpen} onOk={handleUserSubmit}
      onCancel={() => setUserModalOpen(false)} confirmLoading={userSubmitLoading} width={560}>
      <Form form={userForm} layout="vertical">
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item name="username" label="用户名" rules={[{ required: true }]}>
              <Input placeholder="登录用户名" />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item name="displayName" label="显示名" rules={[{ required: true }]}>
              <Input placeholder="显示名称" />
            </Form.Item>
          </Col>
        </Row>
        <Form.Item name="email" label="邮箱" rules={[{ required: true, type: 'email' }]}>
          <Input placeholder="用户邮箱" />
        </Form.Item>
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item name="phone" label="手机号">
              <Input placeholder="可选" />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item name="department" label="部门">
              <Input placeholder="可选" />
            </Form.Item>
          </Col>
        </Row>
        <Form.Item name="roleId" label="角色" rules={[{ required: true }]}>
          <Select placeholder="请选择角色" options={roles.map(r => ({ value: r.id, label: r.name }))} />
        </Form.Item>
        {!editingUser && (
          <Form.Item name="password" label="密码" rules={[{ required: true, min: 8 }]}>
            <Input.Password placeholder="至少8位" />
          </Form.Item>
        )}
      </Form>
    </Modal>

    {/* 角色弹窗 */}
    <Modal title={editingRole ? '编辑角色' : '新增角色'} open={roleModalOpen} onOk={handleRoleSubmit}
      onCancel={() => setRoleModalOpen(false)} confirmLoading={roleSubmitLoading} width={640}>
      <Form form={roleForm} layout="vertical">
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item name="name" label="角色名称" rules={[{ required: true }]}>
              <Select
                placeholder="如: 数据管理员"
                showSearch
                options={[
                  { value: '数据管理员', label: '数据管理员' },
                  { value: '监查员', label: '监查员' },
                  { value: '主要研究者', label: '主要研究者' },
                  { value: '系统管理员', label: '系统管理员' },
                  { value: '申办方', label: '申办方' },
                  { value: '项目经理', label: '项目经理' },
                  { value: '药物管理员', label: '药物管理员' }
                ]}
              />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item name="code" label="角色编码" rules={[{ required: true }]}>
              <Select
                placeholder="如: DATA_MANAGER"
                showSearch
                options={[
                  { value: 'DATA_MANAGER', label: 'DATA_MANAGER' },
                  { value: 'CRA', label: 'CRA' },
                  { value: 'PI', label: 'PI' },
                  { value: 'SYS_ADMIN', label: 'SYS_ADMIN' },
                  { value: 'SPONSOR', label: 'SPONSOR' },
                  { value: 'PM', label: 'PM' },
                  { value: 'DRUG_ADMIN', label: 'DRUG_ADMIN' }
                ]}
              />
            </Form.Item>
          </Col>
        </Row>
        <Form.Item name="description" label="描述">
          <Input.TextArea rows={2} placeholder="角色描述" />
        </Form.Item>
        <Form.Item label={`权限配置 (已选 ${selectedPermissions.length} 项)`}>
          <div style={{ maxHeight: 300, overflowY: 'auto', border: '1px solid #f0f0f0', borderRadius: 8, padding: 12 }}>
            {permissionGroups.map(pg => (
              <div key={pg.group} style={{ marginBottom: 12 }}>
                <div style={{ fontWeight: 500, marginBottom: 4 }}>{pg.group}</div>
                <Row gutter={[8, 4]}>
                  {pg.permissions.map(perm => (
                    <Col span={8} key={perm}>
                      <Tag.CheckableTag
                        checked={selectedPermissions.includes(perm)}
                        onChange={() => togglePermission(perm)}
                        style={{ fontSize: 12 }}
                      >
                        {perm}
                      </Tag.CheckableTag>
                    </Col>
                  ))}
                </Row>
              </div>
            ))}
          </div>
        </Form.Item>
      </Form>
    </Modal>

    {/* 组织机构弹窗 */}
    <Modal title={editingOrg ? '编辑组织' : '新增组织'} open={orgModalOpen} onOk={handleOrgSubmit}
      onCancel={() => setOrgModalOpen(false)} confirmLoading={orgSubmitLoading} width={560}>
      <Form form={orgForm} layout="vertical" initialValues={{ type: 'site', status: 'active' }}>
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item name="name" label="组织名称" rules={[{ required: true }]}>
              <Input placeholder="组织名称" />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item name="code" label="编码" rules={[{ required: true }]}>
              <Input
                placeholder="组织编码"
                disabled
                suffix={
                  <a onClick={() => {
                    const randomSuffix = Math.floor(Math.random() * 1000).toString().padStart(3, '0');
                    orgForm.setFieldsValue({ code: `ORG-${randomSuffix}` });
                  }}>自动生成</a>
                }
              />
            </Form.Item>
          </Col>
        </Row>
        <Form.Item name="type" label="类型" rules={[{ required: true }]}>
          <Select options={orgTypeOptions} />
        </Form.Item>
        <Form.Item name="address" label="地址">
          <Input placeholder="可选" />
        </Form.Item>
        <Form.Item noStyle shouldUpdate={(prev, curr) => prev.type !== curr.type}>
          {({ getFieldValue }) => {
            const type = getFieldValue('type');
            if (type === 'site') {
              return (
                <>
                  <Row gutter={16}>
                    <Col span={12}>
                      <Form.Item name="gcpContactName" label="GCP办公室联系人">
                        <Input placeholder="姓名" />
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item name="gcpContactPhone" label="GCP办公室电话">
                        <Input placeholder="联系电话" />
                      </Form.Item>
                    </Col>
                  </Row>
                  <Row gutter={16}>
                    <Col span={12}>
                      <Form.Item name="researchContactName" label="科研处联系人">
                        <Input placeholder="姓名" />
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item name="researchContactPhone" label="科研处电话">
                        <Input placeholder="联系电话" />
                      </Form.Item>
                    </Col>
                  </Row>
                </>
              );
            }
            if (type !== 'site') {
              return (
                <Row gutter={16}>
                  <Col span={12}>
                    <Form.Item name="contactPerson" label="联系人">
                      <Input placeholder="可选" />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item name="contactPhone" label="联系电话">
                      <Input placeholder="可选" />
                    </Form.Item>
                  </Col>
                </Row>
              );
            }
            return null;
          }}
        </Form.Item>
        <Form.Item name="contactEmail" label="联系邮箱">
          <Input placeholder="可选" />
        </Form.Item>
      </Form>
    </Modal>
  </>
  );
};

export default SettingsPage;
