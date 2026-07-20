import React, { useState, useEffect, useCallback } from 'react';
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
import {  Table, Form, Input, Select, Space, Button, Drawer, Tag, Card, Row, Col, Spin, Empty, App } from 'antd';
=======
import {  Table, Form, Input, Select, Space, Button, Drawer, Tag, Card, Row, Col, Spin, Empty, List , App } from 'antd';
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
=======
import {  Table, Form, Input, Select, Space, Button, Drawer, Tag, Card, Row, Col, Spin, Empty, List , App } from 'antd';
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
=======
import {  Table, Form, Input, Select, Space, Button, Drawer, Tag, Card, Row, Col, Spin, Empty, List , App } from 'antd';
>>>>>>> origin/main
import { SaveOutlined, HistoryOutlined, CheckCircleOutlined, EditOutlined, QuestionCircleOutlined, LockOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import PageHeader from '@/components/PageHeader';
import { subjectApi } from '@/api/subject';
import { dataEntryApi } from '@/api/dataEntry';
import type { VisitFormData, ChangeHistory, FieldDefinition } from '@/types';

const formStatusMap: Record<string, { color: string; label: string }> = {
  not_started: { color: 'default', label: '未开始' },
  in_progress: { color: 'processing', label: '进行中' },
  completed: { color: 'success', label: '已完成' },
  verified: { color: 'blue', label: '已核实' },
  locked: { color: 'warning', label: '已锁定' },
  query: { color: 'error', label: '有质疑' } };

const DataEntryPage: React.FC = () => {
  const { message } = App.useApp();
  const [subjects, setSubjects] = useState<any[]>([]);
  const [subjectsLoading, setSubjectsLoading] = useState(false);

  const [selectedSubject, setSelectedSubject] = useState<any | null>(null);
  const [visits, setVisits] = useState<VisitFormData[]>([]);
  const [visitsLoading, setVisitsLoading] = useState(false);

  const [activeVisit, setActiveVisit] = useState<VisitFormData | null>(null);
  const [fields, setFields] = useState<FieldDefinition[]>([]);
  const [fieldsLoading, setFieldsLoading] = useState(false);

  const [form] = Form.useForm();
  const [saveLoading, setSaveLoading] = useState(false);

  const [historyOpen, setHistoryOpen] = useState(false);
  const [changeHistory, setChangeHistory] = useState<ChangeHistory[]>([]);
  const [, setKeyword] = useState('');

  const fetchSubjects = useCallback(async () => {
    setSubjectsLoading(true);
    try {
      const res = await subjectApi.list({ page: 1, pageSize: 100 });
      setSubjects(res?.list || []);
    } catch { message.error('加载受试者列表失败'); }
    finally { setSubjectsLoading(false); }
  }, []);

  useEffect(() => { fetchSubjects(); }, [fetchSubjects]);

  const handleSelectSubject = async (subject: any) => {
    setSelectedSubject(subject);
    setActiveVisit(null);
    setVisitsLoading(true);
    try {
      const v = await dataEntryApi.getVisits(subject.id);
      setVisits(v || []);
    } catch {
      message.error('加载访视数据失败');
      setVisits([]);
    } finally {
      setVisitsLoading(false);
    }
  };

  const handleSelectVisit = async (visit: VisitFormData) => {
    setActiveVisit(visit);
    if (visit.formId) {
      setFieldsLoading(true);
      try {
        const f = await dataEntryApi.getFieldDefinitions(visit.formId);
        setFields(f || []);
      } catch { setFields([]); }
      finally { setFieldsLoading(false); }
    }
    form.setFieldsValue(visit.data || {});
  };

  const handleSave = async () => {
    if (!selectedSubject || !activeVisit) return;
    try {
      const values = await form.validateFields();
      setSaveLoading(true);
      await dataEntryApi.saveData(selectedSubject.id, activeVisit.id, values);
      message.success('数据保存成功');
      // 刷新访视列表
      const v = await dataEntryApi.getVisits(selectedSubject.id);
      setVisits(v || []);
    } catch { /* validation */ }
    finally { setSaveLoading(false); }
  };

  const handleChangeHistory = async () => {
    if (!activeVisit) return;
    setHistoryOpen(true);
    try {
      const res = await dataEntryApi.getChangeHistory({ recordId: activeVisit.id });
      setChangeHistory(res?.list || [] || []);
    } catch { setChangeHistory([]); }
  };

  const summary = {
    total: visits.length,
    completed: visits.filter(v => v.status === 'completed' || v.status === 'verified' || v.status === 'locked').length,
    inProgress: visits.filter(v => v.status === 'in_progress').length,
    queried: visits.filter(v => v.status === 'query').length };

  const visitColumns = [
    { title: '访视名称', dataIndex: 'visitName', width: 140 },
    { title: '表单', dataIndex: 'formName', ellipsis: true },
    {
      title: '状态', dataIndex: 'status', width: 100,
      render: (v: string) => {
        const cfg = formStatusMap[v] || { color: 'default', label: v };
        return <Tag color={cfg.color} icon={
            v === 'completed' || v === 'verified' ? <CheckCircleOutlined /> :
            v === 'locked' ? <LockOutlined /> :
            v === 'query' ? <QuestionCircleOutlined /> : undefined
          }>{cfg.label}</Tag>;
      } },
    { title: '填写人', dataIndex: ['completedBy', 'displayName'], width: 100 },
    { title: '填写时间', dataIndex: 'completedAt', width: 140, render: (v: string) => v ? dayjs(v).format('YYYY-MM-DD HH:mm') : '-' },
    { title: '变更次数', dataIndex: 'changeCount', width: 80 },
    {
      title: '操作', width: 140,
      render: (_: any, record: VisitFormData) => (
        <Space size="small">
          <Button type="link" size="small" icon={<EditOutlined />}
            disabled={record.status === 'locked'}
            onClick={() => handleSelectVisit(record)}>
            {record.status === 'not_started' ? '录入' : '编辑'}
          </Button>
          {record.changeCount > 0 && (
            <Button type="link" size="small" icon={<HistoryOutlined />} onClick={handleChangeHistory}>历史</Button>
          )}
        </Space>
      ) },
  ];

  return (
    <>
      <PageHeader
        title="数据录入"
        searchPlaceholder="搜索受试者/访视"
        onSearch={(v) => setKeyword(v)}
      />
      <Row gutter={16}>
        {/* 受试者列表 */}
        <Col span={6}>
          <Card title="受试者" size="small" style={{ height: 'calc(100vh - 260px)', overflow: 'auto' }}>
            {subjectsLoading ? <Spin /> : subjects.length === 0 ? <Empty description="暂无受试者" /> : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                {subjects.map((s: any) => (
                  <div
                    key={s.id}
                    onClick={() => handleSelectSubject(s)}
                    style={{
                      padding: '8px 12px',
                      cursor: 'pointer',
                      borderRadius: 6,
                      background: selectedSubject?.id === s.id ? '#e6f7ff' : 'transparent',
                      border: selectedSubject?.id === s.id ? '1px solid #1890ff' : '1px solid transparent',
                      transition: 'all 0.2s' }}
                  >
                    <div style={{ fontWeight: 500 }}>{s.subjectCode || s.id}</div>
                    <div style={{ fontSize: 12, color: '#999' }}>{s.site?.name || ''}</div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </Col>

        {/* 访视数据表 */}
        <Col span={activeVisit ? 12 : 18}>
          <Card
            title={selectedSubject ? `访视列表 - ${selectedSubject.subjectCode || selectedSubject.id}` : '访视列表'}
            size="small"
            style={{ marginBottom: 16 }}
          >
            {summary && summary.total > 0 && (
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={6}><div>总表单: {summary.total}</div></Col>
          <Col span={6}><div>已完成: {summary.completed}</div></Col>
          <Col span={6}><div>进行中: {summary.inProgress}</div></Col>
          <Col span={6}><div>有质疑: {summary.queried}</div></Col>
        </Row>
      )}
            <Table
              rowKey="id"
              columns={visitColumns}
              dataSource={visits}
              loading={visitsLoading}
              pagination={{ pageSize: 20, showSizeChanger: false }}
              size="small"
              scroll={{ y: 400 }}
              locale={{ emptyText: selectedSubject ? '暂无访视数据' : '请先选择受试者' }}
            />
          </Card>
        </Col>

        {/* 数据录入表单 */}
        {activeVisit && (
          <Col span={6}>
            <Card
              title={`数据录入 - ${activeVisit.visitName}`}
              size="small"
              extra={<Space><Button type="primary" size="small" icon={<SaveOutlined />} loading={saveLoading} onClick={handleSave}>保存</Button></Space>}
              style={{ height: 'calc(100vh - 260px)', overflow: 'auto' }}
            >
              {fieldsLoading ? <Spin /> : fields.length === 0 ? <Empty description="无表单字段" /> : (
                <Form form={form} layout="vertical" size="small">
                  {fields.map((field) => (
                    <Form.Item key={field.fieldName} name={field.fieldName} label={field.fieldLabel}
                      rules={field.required ? [{ required: true, message: `${field.fieldLabel}为必填项` }] : undefined}>
                      {field.fieldType === 'text' && <Input placeholder={`请输入${field.fieldLabel}`} maxLength={field.maxLength} />}
                      {field.fieldType === 'number' && <Input type="number" placeholder={`请输入${field.fieldLabel}`} />}
                      {field.fieldType === 'date' && <Input type="date" />}
                      {field.fieldType === 'textarea' && <Input.TextArea rows={3} maxLength={field.maxLength} />}
                      {field.fieldType === 'select' && (
                        <Select placeholder={`请选择${field.fieldLabel}`} options={field.options} allowClear />
                      )}
                      {field.fieldType === 'radio' && (
                        <Select placeholder={`请选择${field.fieldLabel}`} options={field.options} />
                      )}
                      {field.fieldType === 'checkbox' && (
                        <Select mode="multiple" placeholder={`请选择${field.fieldLabel}`} options={field.options} />
                      )}
                    </Form.Item>
                  ))}
                </Form>
              )}
            </Card>
          </Col>
        )}
      </Row>

      {/* 变更历史抽屉 */}
      <Drawer title="变更历史" open={historyOpen} onClose={() => setHistoryOpen(false)} size="large">
        {changeHistory.length === 0 ? (
          <Empty description="无变更记录" />
        ) : (
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {changeHistory.map((h, index) => (
              <Card key={index} size="small" title={h.reason || '数据修改'}>
                <div>
                  从 <b>{h.oldValue != null ? JSON.stringify(h.oldValue) : '空'}</b> 修改为 <b>{h.newValue != null ? JSON.stringify(h.newValue) : '空'}</b>
                </div>
                <div style={{ fontSize: 12, color: '#999', marginTop: 4 }}>
                  {h.changedBy?.displayName || h.changedBy?.id || '未知用户'} - {h.changedAt ? dayjs(h.changedAt).format('YYYY-MM-DD HH:mm:ss') : ''}
                </div>
              </Card>
            ))}
          </div>
=======
=======
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
=======
>>>>>>> origin/main
          <List
            dataSource={changeHistory}
            renderItem={(h) => {
          
              return (
                <List.Item>
                  <List.Item.Meta
                    title={h.reason || '数据修改'}
                    description={
                      <>
                        <div>
                          从 <b>{h.oldValue != null ? JSON.stringify(h.oldValue) : '空'}</b> 修改为 <b>{h.newValue != null ? JSON.stringify(h.newValue) : '空'}</b>
                        </div>
                        <div style={{ fontSize: 12, color: '#999', marginTop: 4 }}>
                          {h.changedBy?.displayName || h.changedBy?.id || '未知用户'} - {h.changedAt ? dayjs(h.changedAt).format('YYYY-MM-DD HH:mm:ss') : ''}
                        </div>
                      </>
                    }
                  />
                </List.Item>
              );
            }}
          />
<<<<<<< HEAD
<<<<<<< HEAD
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
=======
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
=======
>>>>>>> origin/main
        )}
      </Drawer>
    </>
  );
};

export default DataEntryPage;
