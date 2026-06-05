import React from 'react';
import { Modal } from 'antd';
import { ExclamationCircleOutlined } from '@ant-design/icons';

interface ConfirmModalProps {
  open: boolean;
  title?: string;
  content: string;
  onOk: () => void;
  onCancel: () => void;
  okText?: string;
  cancelText?: string;
  okDanger?: boolean;
  loading?: boolean;
}

const ConfirmModal: React.FC<ConfirmModalProps> = ({
  open,
  title = '确认操作',
  content,
  onOk,
  onCancel,
  okText = '确认',
  cancelText = '取消',
  okDanger = true,
  loading = false,
}) => (
  <Modal
    open={open}
    title={title}
    okText={okText}
    cancelText={cancelText}
    okButtonProps={{ danger: okDanger }}
    confirmLoading={loading}
    onOk={onOk}
    onCancel={onCancel}
  >
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 0' }}>
      <ExclamationCircleOutlined style={{ fontSize: 20, color: '#faad14' }} />
      <span>{content}</span>
    </div>
  </Modal>
);

export default ConfirmModal;
