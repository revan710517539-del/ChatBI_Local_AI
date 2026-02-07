import React, { useEffect, useState } from 'react';
import {
  Button,
  Card,
  Drawer,
  Form,
  Input,
  Modal,
  Popconfirm,
  Space,
  Switch,
  Table,
  Typography,
  message,
} from 'antd';
import { agentBuilderService } from '@/services/agentBuilder';

const { Title, Text } = Typography;

const AgentBuilderPage: React.FC = () => {
  const [form] = Form.useForm();
  const [open, setOpen] = useState(false);
  const [list, setList] = useState<any[]>([]);
  const [logOpen, setLogOpen] = useState(false);
  const [activeProfile, setActiveProfile] = useState<any>(null);
  const [logs, setLogs] = useState<any[]>([]);

  const load = async () => {
    const data = await agentBuilderService.listProfiles();
    setList(data || []);
  };

  useEffect(() => {
    load().catch((e) => message.error(String(e)));
  }, []);

  const onCreate = async () => {
    try {
      const values = await form.validateFields();
      await agentBuilderService.createProfile(values);
      setOpen(false);
      form.resetFields();
      await load();
      message.success('Agent已创建');
    } catch (e) {
      message.error(String(e));
    }
  };

  const openLogs = async (profile: any) => {
    try {
      setActiveProfile(profile);
      setLogOpen(true);
      const data = await agentBuilderService.listExecutionLogs(profile.id);
      setLogs(data || []);
    } catch (e) {
      message.error(String(e));
    }
  };

  const toggleTool = async (row: any, field: string, checked: boolean) => {
    try {
      await agentBuilderService.updateProfile(row.id, { [field]: checked });
      await load();
    } catch (e) {
      message.error(String(e));
    }
  };

  return (
    <Card>
      <Space style={{ width: '100%', justifyContent: 'space-between' }}>
        <Title level={4} style={{ margin: 0 }}>
          Agent建设（可选工具链编排）
        </Title>
        <Button type="primary" onClick={() => setOpen(true)}>
          新建Agent
        </Button>
      </Space>
      <Text type="secondary">
        每个Agent可独立配置 SQL工具、RAG工具、规则校验工具。分析执行过程会记录日志。
      </Text>

      <Table
        style={{ marginTop: 16 }}
        rowKey="id"
        dataSource={list}
        columns={[
          { title: '名称', dataIndex: 'name' },
          { title: '场景', dataIndex: 'scene' },
          { title: '描述', dataIndex: 'description' },
          {
            title: 'SQL工具',
            dataIndex: 'enable_sql_tool',
            render: (v, row) => (
              <Switch checked={!!v} onChange={(checked) => toggleTool(row, 'enable_sql_tool', checked)} />
            ),
          },
          {
            title: 'RAG工具',
            dataIndex: 'enable_rag',
            render: (v, row) => (
              <Switch checked={!!v} onChange={(checked) => toggleTool(row, 'enable_rag', checked)} />
            ),
          },
          {
            title: '规则校验',
            dataIndex: 'enable_rule_validation',
            render: (v, row) => (
              <Switch checked={!!v} onChange={(checked) => toggleTool(row, 'enable_rule_validation', checked)} />
            ),
          },
          {
            title: '操作',
            render: (_, row) => (
              <Space>
                <Button size="small" onClick={() => openLogs(row)}>
                  执行日志
                </Button>
                <Popconfirm
                  title="确认删除该Agent？"
                  onConfirm={async () => {
                    await agentBuilderService.deleteProfile(row.id);
                    await load();
                  }}
                >
                  <Button danger size="small">
                    删除
                  </Button>
                </Popconfirm>
              </Space>
            ),
          },
        ]}
      />

      <Modal open={open} title="新建Agent" onCancel={() => setOpen(false)} onOk={onCreate}>
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            enable_rag: true,
            enable_sql_tool: true,
            enable_rule_validation: true,
            scene: 'loan_general',
          }}
        >
          <Form.Item name="name" label="名称" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="scene" label="场景代码" rules={[{ required: true }]}>
            <Input placeholder="business_loan_ops / consumer_loan_risk / dashboard" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input />
          </Form.Item>
          <Form.Item name="system_prompt" label="系统提示词" rules={[{ required: true }]}>
            <Input.TextArea rows={6} />
          </Form.Item>
          <Space>
            <Form.Item name="enable_sql_tool" label="SQL工具" valuePropName="checked">
              <Switch />
            </Form.Item>
            <Form.Item name="enable_rag" label="RAG工具" valuePropName="checked">
              <Switch />
            </Form.Item>
            <Form.Item
              name="enable_rule_validation"
              label="规则校验工具"
              valuePropName="checked"
            >
              <Switch />
            </Form.Item>
          </Space>
        </Form>
      </Modal>

      <Drawer
        title={`执行日志 - ${activeProfile?.name || ''}`}
        open={logOpen}
        onClose={() => setLogOpen(false)}
        width={900}
        extra={
          activeProfile ? (
            <Button
              size="small"
              onClick={async () => {
                await agentBuilderService.clearExecutionLogs(activeProfile.id);
                const data = await agentBuilderService.listExecutionLogs(activeProfile.id);
                setLogs(data || []);
              }}
            >
              清空日志
            </Button>
          ) : null
        }
      >
        <Table
          rowKey={(r, i) => `${r.timestamp}-${i}`}
          dataSource={logs}
          columns={[
            { title: '时间', dataIndex: 'timestamp', width: 200 },
            { title: '步骤', dataIndex: 'step', width: 170 },
            { title: '状态', dataIndex: 'status', width: 120 },
            { title: '描述', dataIndex: 'detail', width: 220 },
            {
              title: '元数据',
              dataIndex: 'metadata',
              render: (v) => (
                <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                  {JSON.stringify(v || {}, null, 2)}
                </pre>
              ),
            },
          ]}
        />
      </Drawer>
    </Card>
  );
};

export default AgentBuilderPage;
