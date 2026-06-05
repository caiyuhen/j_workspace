import React, { useState, useEffect, useCallback } from 'react';
import {  Table, Modal, Form, Input, Select, Space, Button, Drawer, Descriptions, Tag, DatePicker, Tabs, Row, Col , App } from 'antd';
import { EditOutlined, EyeOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import PageHeader from '@/components/PageHeader';
import { drugApi } from '@/api/drug';
import { projectApi } from '@/api/project';
import type { Drug, CreateDrugParams, SupplyPlan, Shipment, Inventory, Destruction } from '@/types';

const dosageFormOptions = [
  { value: 'tablet', label: '片剂' },
  { value: 'capsule', label: '胶囊' },
  { value: 'injection', label: '注射剂' },
  { value: 'oral_solution', label: '口服液' },
  { value: 'powder', label: '粉剂' },
  { value: 'other', label: '其他' },
];

const storageOptions = [
  { value: '2-8C', label: '2-8°C 冷藏' },
  { value: 'room_temp', label: '室温保存' },
  { value: 'frozen', label: '冷冻保存 (-20°C)' },
  { value: 'ultra_frozen', label: '超低温保存 (-80°C)' },
  { value: 'protected_light', label: '避光保存' },
];

const blindStatusMap: Record<string, { color: string; label: string }> = {
  blinded: { color: 'blue', label: '盲态' },
  unblinded: { color: 'green', label: '非盲' },
  partially_blinded: { color: 'orange', label: '部分盲' } };

const drugStatusMap: Record<string, { color: string; label: string }> = {
  active: { color: 'success', label: '在用' },
  inactive: { color: 'default', label: '停用' },
  recall: { color: 'warning', label: '召回' },
  destroyed: { color: 'error', label: '已销毁' } };

const DrugsPage: React.FC = () => {
  const { message } = App.useApp();
  const [data, setData] = useState<Drug[]>([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({ page: 1, pageSize: 10, total: 0 });
  const [keyword, setKeyword] = useState('');

  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Drug | null>(null);
  const [form] = Form.useForm();
  const [submitLoading, setSubmitLoading] = useState(false);

  const [detailOpen, setDetailOpen] = useState(false);
  const [selectedDrug, setSelectedDrug] = useState<Drug | null>(null);
  const [activeDetailTab, setActiveDetailTab] = useState('supply');
  const [supplyPlans, setSupplyPlans] = useState<SupplyPlan[]>([]);
  const [shipments, setShipments] = useState<Shipment[]>([]);
  const [inventories, setInventories] = useState<Inventory[]>([]);
  const [destructions, setDestructions] = useState<Destruction[]>([]);
  const [projects, setProjects] = useState<{label: string, value: string}[]>([]);

  // 发药与收回弹窗
  const [dispenseModalOpen, setDispenseModalOpen] = useState(false);
  const [dispenseType, setDispenseType] = useState<'dispense' | 'return' | 'destroy'>('dispense');
  const [selectedInventory, setSelectedInventory] = useState<Inventory | null>(null);
  const [dispenseForm] = Form.useForm();
  const [dispenseSubmitLoading, setDispenseSubmitLoading] = useState(false);

  const fetchProjects = useCallback(async () => {
    try {
      const res = await projectApi.list({ page: 1, pageSize: 1000 });
      setProjects((res?.list || []).map((p: any) => ({ label: p.projectName, value: p.id })));
    } catch {}
  }, []);

  const fetchData = useCallback(async (page = 1, pageSize = 10) => {
    setLoading(true);
    try {
      const res = await drugApi.list({ page, pageSize, keyword });
      setData(res?.list || []);
      setPagination({ page: res?.page || 1, pageSize: res?.pageSize || 10, total: res?.total || 0 });
    } catch {
      message.error('加载药物列表失败');
    } finally {
      setLoading(false);
    }
  }, [keyword]);

  useEffect(() => { fetchData(); fetchProjects(); }, [fetchData, fetchProjects]);


  const handleCreate = () => {
    setEditing(null);
    form.resetFields();
    setModalOpen(true);
  };

  const handleEdit = (record: Drug) => {
    setEditing(record);
    form.setFieldsValue({
      ...record,
      expiryDate: record.expiryDate ? dayjs(record.expiryDate) : undefined });
    setModalOpen(true);
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setSubmitLoading(true);
      const params: any = {
        ...values,
        isBlinded: values.blindStatus === 'blinded',
      };
      
      delete params.lotNumber;
      delete params.expiryDate;
      delete params.quantity;
      delete params.blindStatus;

      let drugId = '';
      if (editing) {
        await drugApi.update(editing.id, params);
        drugId = editing.id;
        message.success('更新药物信息成功');
      } else {
        const newDrug = await drugApi.create(params);
        drugId = newDrug.id;
        message.success('创建药物信息成功');
      }

      // 如果有初始数量和批号，创建初始库存
      if (!editing && values.quantity && values.lotNumber) {
        await drugApi.createInventory(drugId, {
          location: '默认仓库',
          batchNumber: values.lotNumber,
          expiryDate: values.expiryDate?.format('YYYY-MM-DD'),
          quantityOnHand: Number(values.quantity)
        });
      }

      setModalOpen(false);
      fetchData(pagination.page, pagination.pageSize);
    } catch (err: any) {
      if (err.errorFields) {
        message.warning('请检查表单填写是否正确');
        return;
      }
      message.error(err.response?.data?.error?.message || '操作失败');
    } finally {
      setSubmitLoading(false);
    }
  };

  const handleViewDetail = async (record: Drug) => {
    setSelectedDrug(record);
    setDetailOpen(true);
    setActiveDetailTab('supply');
    loadDetailData(record.id);
  };

  const loadDetailData = async (id: string) => {
    try {
      const [sp, sh, inv, dest] = await Promise.all([
        drugApi.getSupplyPlans(id),
        drugApi.getShipments(id),
        drugApi.getInventories(id),
        drugApi.getDestructions(id),
      ]);
      setSupplyPlans(sp);
      setShipments(sh);
      setInventories(inv);
      setDestructions(dest);
    } catch {
      message.error('加载药物详情失败');
    }
  };

  const handleOpenDispense = (inv: Inventory, type: 'dispense' | 'return' | 'destroy') => {
    setSelectedInventory(inv);
    setDispenseType(type);
    dispenseForm.resetFields();
    setDispenseModalOpen(true);
  };

  const handleDispenseSubmit = async () => {
    try {
      const values = await dispenseForm.validateFields();
      setDispenseSubmitLoading(true);
      const qty = parseInt(values.quantity, 10);
      
      if (dispenseType === 'destroy') {
        await drugApi.createDestruction(selectedDrug!.id, {
          batchNumber: selectedInventory!.batchNumber || '未知批号',
          quantity: qty,
          destructionDate: new Date().toISOString(),
          destructionMethod: '常规销毁',
          reason: values.reason || '未提供原因',
        });
        const updateData: Partial<Inventory> = {
          quantityDestroyed: (selectedInventory!.quantityDestroyed || 0) + qty,
          quantityOnHand: (selectedInventory!.quantityOnHand || 0) - qty,
        };
        await drugApi.adjustInventory(selectedDrug!.id, selectedInventory!.id, updateData);
        message.success('销毁成功');
      } else {
        const updateData: Partial<Inventory> = {};
        if (dispenseType === 'dispense') {
          updateData.quantityDispensed = (selectedInventory!.quantityDispensed || 0) + qty;
          updateData.quantityOnHand = (selectedInventory!.quantityOnHand || 0) - qty;
        } else {
          updateData.quantityReturned = ((selectedInventory as any).quantityReturned || 0) + qty;
          updateData.quantityOnHand = (selectedInventory!.quantityOnHand || 0) + qty;
        }
        await drugApi.adjustInventory(selectedDrug!.id, selectedInventory!.id, updateData);
        message.success(`${dispenseType === 'dispense' ? '发药' : '收回'}成功`);
      }
      
      setDispenseModalOpen(false);
      loadDetailData(selectedDrug!.id);
    } catch (err: any) {
      if (err.errorFields) {
        message.warning('请检查表单填写是否正确');
        return;
      }
      message.error(err.response?.data?.error?.message || '操作失败');
    } finally {
      setDispenseSubmitLoading(false);
    }
  };

  const columns = [
    { title: '药物名称', dataIndex: 'drugName', width: 180, ellipsis: true },
    { title: '药物编码', dataIndex: 'drugCode', width: 120 },
    { title: '剂型', dataIndex: 'dosageForm', width: 100, render: (v: string) => dosageFormOptions.find(o => o.value === v)?.label || v },
    { title: '规格', dataIndex: 'strength', width: 100 },
    { title: '生产商', dataIndex: 'manufacturer', width: 140, ellipsis: true },
    { title: '批号', dataIndex: 'lotNumber', width: 120 },
    {
      title: '有效期',
      dataIndex: 'expiryDate',
      width: 110,
      render: (v: string) => v ? dayjs(v).format('YYYY-MM-DD') : '-' },
    {
      title: '盲态',
      dataIndex: 'isBlinded',
      width: 100,
      render: (v: boolean) => {
        const statusStr = v ? 'blinded' : 'unblinded';
        const cfg = blindStatusMap[statusStr] || { color: 'default', label: statusStr };
        return <Tag color={cfg.color}>{cfg.label}</Tag>;
      } },
    {
      title: '状态',
      dataIndex: 'status',
      width: 80,
      render: (v: string) => {
        const cfg = drugStatusMap[v] || { color: 'default', label: v };
        return <Tag color={cfg.color}>{cfg.label}</Tag>;
      } },
    {
      title: '操作',
      width: 140,
      render: (_: any, record: Drug) => (
        <Space size="small">
          <Button type="link" size="small" icon={<EyeOutlined />} onClick={() => handleViewDetail(record)}>详情</Button>
          <Button type="link" size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)}>编辑</Button>
        </Space>
      ) },
  ];

  return (
    <>
      <PageHeader
        title="药物管理"
        searchPlaceholder="搜索药物名称/编码"
        onSearch={(v) => setKeyword(v)}
      >
        <Space>
          <Button type="primary" onClick={handleCreate}>添加药物</Button>
        </Space>
      </PageHeader>

      <Tabs defaultActiveKey="list" items={[
        {
          key: 'list',
          label: '药物列表',
          children: (
            <Table
              rowKey="id"
              columns={columns}
              dataSource={data}
              loading={loading}
              pagination={{
                current: pagination.page, pageSize: pagination.pageSize, total: pagination.total,
                showSizeChanger: true, showTotal: (t) => `共 ${t} 条`,
                onChange: (p, ps) => fetchData(p, ps) }}
              scroll={{ x: 1300 }}
            />
          )
        },
        {
          key: 'stats',
          label: '统计概览',
          children: <div style={{ padding: 40, textAlign: 'center', color: '#999' }}>暂无统计数据</div>
        }
      ]} />

      {/* 创建/编辑弹窗 */}
      <Modal
        title={editing ? '编辑药物信息' : '新增药物'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        confirmLoading={submitLoading}
        width={640}
      >
        <Form form={form} layout="vertical" initialValues={{ blindStatus: 'blinded', storageCondition: '2-8C' }}>
          <Form.Item name="projectId" label="关联项目" rules={[{ required: true, message: '请选择关联项目' }]}>
            <Select options={projects} placeholder="请选择项目" showSearch optionFilterProp="label" />
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="drugName" label="药物名称" rules={[{ required: true }]}>
                <Input placeholder="请输入" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="drugCode" label="药物编码" rules={[{ required: true }]}>
                <Input placeholder="请输入" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="dosageForm" label="剂型" rules={[{ required: true }]}>
                <Select options={dosageFormOptions} placeholder="请选择" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="strength" label="规格" rules={[{ required: true }]}>
                <Input placeholder="如: 100mg" />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="manufacturer" label="生产商" rules={[{ required: true }]}>
            <Input placeholder="请输入生产商名称" />
          </Form.Item>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="lotNumber" label="批号">
                <Input placeholder="请输入批号" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="quantity" label="初始数量">
                <Input type="number" placeholder="初始库存" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="expiryDate" label="有效期">
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="storageCondition" label="储存条件" rules={[{ required: true }]}>
            <Select options={storageOptions} placeholder="请选择" />
          </Form.Item>
          <Form.Item name="blindStatus" label="盲态" rules={[{ required: true }]}>
            <Select options={Object.entries(blindStatusMap).map(([v, c]) => ({ value: v, label: c.label }))} placeholder="请选择" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 详情抽屉 */}
      <Drawer
        title={selectedDrug ? `${selectedDrug.drugName} - ${selectedDrug.drugCode}` : '药物详情'}
        open={detailOpen}
        onClose={() => setDetailOpen(false)}
        size="large"
      >
        {selectedDrug && (
          <>
            <Descriptions column={2} bordered size="small" style={{ marginBottom: 16 }}>
              <Descriptions.Item label="药物名称">{selectedDrug.drugName}</Descriptions.Item>
              <Descriptions.Item label="药物编码">{selectedDrug.drugCode}</Descriptions.Item>
              <Descriptions.Item label="剂型">{dosageFormOptions.find(o => o.value === selectedDrug.dosageForm)?.label}</Descriptions.Item>
              <Descriptions.Item label="规格">{selectedDrug.strength}</Descriptions.Item>
              <Descriptions.Item label="生产商">{selectedDrug.manufacturer}</Descriptions.Item>
              <Descriptions.Item label="批号">{selectedDrug.lotNumber || '-'}</Descriptions.Item>
              <Descriptions.Item label="有效期">{selectedDrug.expiryDate ? dayjs(selectedDrug.expiryDate).format('YYYY-MM-DD') : '-'}</Descriptions.Item>
              <Descriptions.Item label="储存条件">{selectedDrug.storageCondition}</Descriptions.Item>
            </Descriptions>

            <Tabs activeKey={activeDetailTab} onChange={setActiveDetailTab} items={[
              { key: 'supply', label: '发药计划', children: (
                <Table rowKey="id" size="small" dataSource={supplyPlans} pagination={false}
                  columns={[
                    { title: '计划数量', dataIndex: 'plannedQuantity', width: 90 },
                    { title: '实际数量', dataIndex: 'actualQuantity', width: 90 },
                    { title: '计划日期', dataIndex: 'plannedDate', width: 110, render: (v: string) => v ? dayjs(v).format('YYYY-MM-DD') : '-' },
                    { title: '状态', dataIndex: 'status', width: 90, render: (v: string) => <Tag>{v}</Tag> },
                    { title: '操作', key: 'actions', width: 150, render: (_: any) => (
                      <Space size="small">
                        {inventories.length > 0 && (
                          <Button type="link" size="small" onClick={() => handleOpenDispense(inventories[0], 'dispense')}>发药</Button>
                        )}
                      </Space>
                    )}
                  ]}
                />
              )},
              { key: 'destruction', label: '回收销毁', children: (
                <Table rowKey="id" size="small" dataSource={destructions} pagination={false}
                  columns={[
                    { title: '数量', dataIndex: 'quantity', width: 70 },
                    { title: '原因', dataIndex: 'reason', ellipsis: true },
                    { title: '方式', dataIndex: 'method', width: 100 },
                    { title: '销毁日期', dataIndex: 'destructionDate', width: 110, render: (v: string) => v ? dayjs(v).format('YYYY-MM-DD') : '-' },
                    { title: '状态', dataIndex: 'status', width: 90, render: (v: string) => <Tag>{v}</Tag> },
                    { title: '操作', key: 'actions', width: 150, render: (_: any, record: Destruction) => (
                      <Space size="small">
                        {inventories.length > 0 && (
                           <>
                             <Button type="link" size="small" onClick={() => handleOpenDispense(inventories[0], 'return')}>收回</Button>
                             <Button type="link" size="small" danger onClick={() => handleOpenDispense(inventories[0], 'destroy')}>销毁</Button>
                           </>
                        )}
                      </Space>
                    )}
                  ]}
                />
              )},
            ]} />
          </>
        )}

        {/* 发药与收回弹窗 */}
        <Modal
          title={dispenseType === 'dispense' ? '发药' : (dispenseType === 'return' ? '收回药品' : '销毁药品')}
          open={dispenseModalOpen}
          onOk={handleDispenseSubmit}
          onCancel={() => setDispenseModalOpen(false)}
          confirmLoading={dispenseSubmitLoading}
          width={400}
        >
          <Form form={dispenseForm} layout="vertical">
            <Form.Item name="quantity" label={`${dispenseType === 'dispense' ? '发药' : (dispenseType === 'return' ? '收回' : '销毁')}数量`} rules={[{ required: true, message: '请输入数量' }]}>
              <Input type="number" min={1} max={dispenseType === 'dispense' || dispenseType === 'destroy' ? selectedInventory?.quantityOnHand : undefined} />
            </Form.Item>
            <Form.Item name="reason" label="备注说明">
              <Input.TextArea rows={2} />
            </Form.Item>
          </Form>
        </Modal>

      </Drawer>
    </>
  );
};

export default DrugsPage;

