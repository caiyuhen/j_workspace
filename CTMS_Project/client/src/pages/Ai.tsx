import React, { useState, useEffect, useRef } from 'react';
import {  Select, Button, Input, Space, Tag, Typography, Avatar, Spin, Empty, Tabs, Card, Table , App } from 'antd';
import { SendOutlined, RobotOutlined, UserOutlined, ClearOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import PageHeader from '@/components/PageHeader';
import { aiApi } from '@/api/ai';
import type { AiAgent, ChatMessage, AiLogEntry } from '@/types';

const { TextArea } = Input;
const { Text } = Typography;

const AiPage: React.FC = () => {
  const { message } = App.useApp();
  const [agents, setAgents] = useState<AiAgent[]>([]);
  // // const [agentsLoading, setAgentsLoading] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState<AiAgent | null>(null);

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | undefined>(undefined);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const [logs, setLogs] = useState<AiLogEntry[]>([]);
  const [logsLoading, setLogsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('chat');

  useEffect(() => {
    const fetchAgents = async () => {
      try {
        const list = await aiApi.getAgentList();
        setAgents(list || []);
        if (list?.length > 0) setSelectedAgent(list[0]);
      } catch { message.error('加载 Agent 列表失败'); }
    };
    fetchAgents();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!inputMessage.trim() || !selectedAgent) return;

    const userMsg: ChatMessage = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content: inputMessage.trim(),
      timestamp: new Date().toISOString(),
      agentId: selectedAgent.id };
    setMessages(prev => [...prev, userMsg]);
    setInputMessage('');
    setChatLoading(true);

    try {
      const res = await aiApi.chat({
        agentId: selectedAgent.id,
        message: inputMessage.trim(),
        conversationId });
      setMessages(prev => [...prev, res.message]);
      setConversationId(res.conversationId);
    } catch {
      setMessages(prev => [...prev, {
        id: `err-${Date.now()}`,
        role: 'assistant',
        content: '抱歉，处理请求时发生错误。请稍后重试。',
        timestamp: new Date().toISOString() }]);
    } finally {
      setChatLoading(false);
    }
  };

  const handleClearChat = () => {
    setMessages([]);
    setConversationId(undefined);
  };

  const fetchLogs = async () => {
    setLogsLoading(true);
    try {
      const l = await aiApi.getLogs();
      setLogs(l || []);
    } catch { message.error('加载日志失败'); }
    finally { setLogsLoading(false); }
  };

  const handleTabChange = (key: string) => {
    setActiveTab(key);
    if (key === 'logs' && logs.length === 0) fetchLogs();
  };

  const logColumns = [
    { title: '时间', dataIndex: 'createdAt', width: 160, render: (v: string) => v ? dayjs(v).format('YYYY-MM-DD HH:mm:ss') : '-' },
    { title: 'Agent', dataIndex: 'agentName', width: 120 },
    { title: '操作', dataIndex: 'action', width: 120 },
    { title: '输入摘要', dataIndex: 'inputSummary', ellipsis: true },
    { title: '输出摘要', dataIndex: 'outputSummary', ellipsis: true },
    { title: '耗时', dataIndex: 'duration', width: 80, render: (v: number) => `${(v / 1000).toFixed(1)}s` },
    {
      title: '状态', dataIndex: 'status', width: 80,
      render: (v: string) => <Tag color={v === 'success' ? 'success' : 'error'}>{v === 'success' ? '成功' : '失败'}</Tag> },
  ];

  return (
    <>
      <PageHeader title="AI 智能助手">
        {agents.length > 0 && (
          <Select
            style={{ width: 200 }}
            value={selectedAgent?.id}
            onChange={(id) => setSelectedAgent(agents.find(a => a.id === id) || null)}
            options={agents.map(a => ({ value: a.id, label: a.name }))}
          />
        )}
      </PageHeader>

      <Tabs activeKey={activeTab} onChange={handleTabChange} items={[
      {
        key: 'chat',
        label: '智能对话',
        children: (
          <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 300px)' }}>
            {/* Agent 信息 */}
            {selectedAgent && (
              <Card size="small" style={{ marginBottom: 12 }}>
                <Space>
                  <RobotOutlined style={{ fontSize: 20, color: '#1890ff' }} />
                  <div>
                    <Text strong>{selectedAgent.name}</Text>
                    <br />
                    <Text type="secondary" style={{ fontSize: 12 }}>{selectedAgent.description}</Text>
                    <div style={{ marginTop: 4 }}>
                      {selectedAgent.capabilities?.map(c => (
                        <Tag key={c} style={{ fontSize: 11 }}>{c}</Tag>
                      ))}
                    </div>
                  </div>
                </Space>
              </Card>
            )}

            {/* 消息区域 */}
            <div style={{ flex: 1, overflowY: 'auto', background: '#fafafa', borderRadius: 8, padding: 16 }}>
              {messages.length === 0 ? (
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
                  <Empty description={`选择 Agent 后开始对话，当前: ${selectedAgent?.name || '未选择'}`} />
                </div>
              ) : (
                messages.map((msg) => (
                  <div
                    key={msg.id}
                    style={{
                      display: 'flex',
                      justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
                      marginBottom: 16 }}
                  >
                    {msg.role === 'assistant' && (
                      <Avatar icon={<RobotOutlined />} style={{ marginRight: 8, background: '#1890ff' }} />
                    )}
                    <div
                      style={{
                        maxWidth: '70%',
                        padding: '10px 14px',
                        borderRadius: 12,
                        background: msg.role === 'user' ? '#1890ff' : '#fff',
                        color: msg.role === 'user' ? '#fff' : '#333',
                        boxShadow: '0 1px 2px rgba(0,0,0,0.1)',
                        wordBreak: 'break-word',
                        lineHeight: 1.6 }}
                    >
                      {msg.role === 'assistant' && (msg as any).type === 'data' && (msg as any).data ? (
                        <div>
                          <Typography.Paragraph style={{ marginBottom: 12 }}>{msg.content}</Typography.Paragraph>
                          <Card size="small" title="分析数据" style={{ marginBottom: 0 }}>
                            <pre style={{ margin: 0, fontSize: 12, whiteSpace: 'pre-wrap' }}>
                              {JSON.stringify((msg as any).data, null, 2)}
                            </pre>
                          </Card>
                        </div>
                      ) : (
                        <div style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</div>
                      )}
                      <div style={{ fontSize: 11, opacity: 0.7, marginTop: 4, textAlign: 'right' }}>
                        {msg.timestamp ? dayjs(msg.timestamp).format('HH:mm') : ''}
                      </div>
                    </div>
                    {msg.role === 'user' && (
                      <Avatar icon={<UserOutlined />} style={{ marginLeft: 8, background: '#87d068' }} />
                    )}
                  </div>
                ))
              )}
              {chatLoading && (
                <div style={{ display: 'flex', justifyContent: 'flex-start', marginBottom: 16 }}>
                  <Avatar icon={<RobotOutlined />} style={{ marginRight: 8, background: '#1890ff' }} />
                  <div style={{ padding: '10px 14px', borderRadius: 12, background: '#fff', boxShadow: '0 1px 2px rgba(0,0,0,0.1)' }}>
                    <Spin size="small" /> <Text type="secondary">思考中...</Text>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* 输入区域 */}
            <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
              <TextArea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                placeholder="输入问题或指令..."
                autoSize={{ minRows: 1, maxRows: 4 }}
                onPressEnter={(e) => { if (!e.shiftKey) { e.preventDefault(); handleSend(); } }}
                style={{ flex: 1 }}
                disabled={chatLoading || !selectedAgent}
              />
              <Button type="primary" icon={<SendOutlined />} onClick={handleSend} loading={chatLoading} disabled={!selectedAgent}>
                发送
              </Button>
              <Button icon={<ClearOutlined />} onClick={handleClearChat}>清空</Button>
            </div>
          </div>
        ) },
      {
        key: 'logs',
        label: '操作日志',
        children: (
          <Table
            rowKey="id"
            columns={logColumns}
            dataSource={logs}
            loading={logsLoading}
            pagination={{ pageSize: 20 }}
            size="small"
            scroll={{ x: 900 }}
          />
        ) },
    ]} />
    </>
  );
};

export default AiPage;
