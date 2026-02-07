import React, { useState } from 'react';
import { Modal, Form, Input, message } from 'antd';

type SaveQueryModalProps = {
  visible: boolean;
  query: string;
  onClose: () => void;
  onSave: (name: string, description: string) => void;
};

const SaveQueryModal: React.FC<SaveQueryModalProps> = ({
  visible,
  query,
  onClose,
  onSave,
}) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);

  const handleOk = async () => {
    try {
      const values = await form.validateFields();
      setLoading(true);
      onSave(values.name, values.description);
      message.success('Query saved successfully!');
      form.resetFields();
      onClose();
    } catch (error) {
      console.error('Validation failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    form.resetFields();
    onClose();
  };

  return (
    <Modal
      title="Save Query"
      open={visible}
      onOk={handleOk}
      onCancel={handleCancel}
      confirmLoading={loading}
      destroyOnClose
    >
      <Form form={form} layout="vertical">
        <Form.Item
          name="name"
          label="Query Name"
          rules={[
            { required: true, message: 'Please enter a name for this query' },
          ]}
        >
          <Input placeholder="e.g., Daily Sales Report" />
        </Form.Item>
        <Form.Item name="description" label="Description">
          <Input.TextArea
            rows={3}
            placeholder="Optional description of what this query does"
          />
        </Form.Item>
        <Form.Item label="Query Preview">
          <Input.TextArea
            value={query}
            rows={4}
            disabled
            style={{ fontFamily: 'monospace', fontSize: 12 }}
          />
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default SaveQueryModal;
