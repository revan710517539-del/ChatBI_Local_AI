import React, { useEffect, useState } from 'react';
import {
  Button,
  Card,
  Descriptions,
  Form,
  Input,
  Modal,
  Popconfirm,
  Select,
  Space,
  Table,
  Tag,
  Typography,
  message,
} from 'antd';
import {
  aiConfigService,
  type LLMSource,
  type RuntimeStatus,
  type SceneType,
} from '@/services/aiConfig';

const { Title, Text } = Typography;

const capabilityItems = [
  { key: 'chat', label: '对话分析模型' },
  { key: 'vision', label: '图片读取模型' },
  { key: 'table', label: '表格分析模型' },
  { key: 'embedding', label: '向量嵌入模型' },
];

const LLMSourcePage: React.FC = () => {
  const [form] = Form.useForm();
  const [promptForm] = Form.useForm();
  const [list, setList] = useState<LLMSource[]>([]);
  const [bindings, setBindings] = useState<Record<SceneType, string>>({
    dashboard: '',
    data_discuss: '',
  });
  const [runtime, setRuntime] = useState<RuntimeStatus>({
    active_runtime_model: null,
    running_models: [],
    model_capabilities: {},
  });
  const [capabilityModels, setCapabilityModels] = useState<Record<string, string>>({});
  const [open, setOpen] = useState(false);

  const load = async () => {
    const [sources, promptData, bindingData, runtimeData, capabilityData] = await Promise.all([
      aiConfigService.listLLMSources(),
      aiConfigService.listPrompts(),
      aiConfigService.listSceneBindings(),
      aiConfigService.getRuntimeStatus(),
      aiConfigService.getCapabilityModels(),
    ]);
    setList(sources || []);
    setBindings(bindingData || { dashboard: '', data_discuss: '' });
    setRuntime(runtimeData || { active_runtime_model: null, running_models: [] });
    setCapabilityModels(capabilityData || {});
    promptForm.setFieldsValue(promptData || { dashboard: '', data_discuss: '' });
  };

  useEffect(() => {
    load().catch((e) => message.error(String(e)));
  }, []);

  const createSource = async () => {
    try {
      const values = await form.validateFields();
      await aiConfigService.createLLMSource(values);
      setOpen(false);
      form.resetFields();
      await load();
      message.success('LLMSource 已创建');
    } catch (e) {
      message.error(String(e));
    }
  };

  const savePrompt = async (scene: SceneType) => {
    try {
      const values = await promptForm.validateFields();
      await aiConfigService.updatePrompt(scene, values[scene] || '');
      message.success(`Prompt 已更新: ${scene}`);
      await load();
    } catch (e) {
      message.error(String(e));
    }
  };

  const bindScene = async (scene: SceneType, id: string) => {
    try {
      await aiConfigService.updateSceneBinding(scene, id);
      message.success(`已绑定 ${scene} 模型`);
      await load();
    } catch (e) {
      message.error(String(e));
    }
  };

  const saveCapabilityModel = async (capability: string, model: string) => {
    if (!model) {
      message.warning('请先选择模型');
      return;
    }
    try {
      await aiConfigService.updateCapabilityModel(capability, model);
      message.success(`已更新 ${capability} 能力模型`);
      await load();
    } catch (e) {
      message.error(String(e));
    }
  };

  const activateCapability = async (capability: string) => {
    try {
      await aiConfigService.activateRuntimeModel(capability);
      message.success(`已激活 ${capability} 模型（自动卸载其他模型）`);
      await load();
    } catch (e) {
      message.error(String(e));
    }
  };

  const modelOptions = Array.from(
    new Set([
      ...list.map((x) => x.model).filter(Boolean),
      ...(runtime.local_models || []),
      ...Object.values(capabilityModels || {}),
    ]),
  ).map((m) => ({
    label: m,
    value: m,
  }));

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Card>
        <Space style={{ width: '100%', justifyContent: 'space-between' }}>
          <Title level={4} style={{ margin: 0 }}>
            LLMSource 管理（Ollama / OpenAI Compatible）
          </Title>
          <Button type="primary" onClick={() => setOpen(true)}>
            新增模型源
          </Button>
        </Space>
        <Table
          rowKey="id"
          style={{ marginTop: 16 }}
          dataSource={list}
          columns={[
            { title: '名称', dataIndex: 'name' },
            { title: 'Provider', dataIndex: 'provider' },
            { title: 'Base URL', dataIndex: 'base_url' },
            { title: 'Model', dataIndex: 'model' },
            { title: '能力', dataIndex: 'capability' },
            {
              title: '默认',
              dataIndex: 'is_default',
              render: (v) => (v ? '是' : '否'),
            },
            {
              title: '启用',
              dataIndex: 'enabled',
              render: (v) => (v ? '是' : '否'),
            },
            {
              title: '操作',
              render: (_, row) => (
                <Popconfirm
                  title="确认删除该模型源？"
                  onConfirm={async () => {
                    await aiConfigService.deleteLLMSource(row.id);
                    await load();
                  }}
                >
                  <Button danger size="small">
                    删除
                  </Button>
                </Popconfirm>
              ),
            },
          ]}
        />
      </Card>

      <Card title="运行时模型状态（单模型运行）">
        <Descriptions column={1} size="small">
          <Descriptions.Item label="当前激活模型">
            {runtime.active_runtime_model || '-'}
          </Descriptions.Item>
          <Descriptions.Item label="当前内存中模型">
            {(runtime.running_models || []).length ? (
              (runtime.running_models || []).map((m) => (
                <Tag key={m} color={m === runtime.active_runtime_model ? 'blue' : 'default'}>
                  {m}
                </Tag>
              ))
            ) : (
              <Text type="secondary">无</Text>
            )}
          </Descriptions.Item>
          <Descriptions.Item label="本地已安装模型">
            {(runtime.local_models || []).length ? (
              (runtime.local_models || []).map((m) => <Tag key={m}>{m}</Tag>)
            ) : (
              <Text type="secondary">未检测到</Text>
            )}
          </Descriptions.Item>
        </Descriptions>
        <Text type="secondary">
          SmartBI 会在切换能力模型时自动卸载其他模型，避免 16G 机器内存过载。
        </Text>
      </Card>

      <Card title="能力模型配置（LangChain + 工具链）">
        <Space direction="vertical" style={{ width: '100%' }}>
          {capabilityItems.map((x) => (
            <Space key={x.key} style={{ width: '100%', justifyContent: 'space-between' }}>
              <Text style={{ width: 160 }}>{x.label}</Text>
              <Select
                style={{ width: 420 }}
                showSearch
                value={capabilityModels[x.key]}
                onChange={(v) =>
                  setCapabilityModels((prev) => ({
                    ...prev,
                    [x.key]: v,
                  }))
                }
                options={modelOptions}
                placeholder={
                  x.key === 'chat'
                    ? 'qwen3-4B-instruct-2507_q8'
                    : x.key === 'vision'
                      ? 'minicpm-v4'
                      : x.key === 'table'
                        ? 'TableGPT2-7B'
                        : 'bge-m3'
                }
              />
              <Button onClick={() => saveCapabilityModel(x.key, capabilityModels[x.key])}>
                保存
              </Button>
              <Button type="primary" onClick={() => activateCapability(x.key)}>
                激活并独占
              </Button>
            </Space>
          ))}
        </Space>
      </Card>

      <Card title="Prompt 场景配置">
        <Form form={promptForm} layout="vertical">
          <Form.Item label="Dashboard Prompt（用于 Dashboard 菜单）" name="dashboard">
            <Input.TextArea rows={6} />
          </Form.Item>
          <Button onClick={() => savePrompt('dashboard')}>保存 Dashboard Prompt</Button>

          <Form.Item
            style={{ marginTop: 16 }}
            label="DataDiscuss Prompt（用于 DataDiscuss 菜单）"
            name="data_discuss"
          >
            <Input.TextArea rows={6} />
          </Form.Item>
          <Button onClick={() => savePrompt('data_discuss')}>保存 DataDiscuss Prompt</Button>
        </Form>
      </Card>

      <Card title="场景模型绑定">
        <Space direction="vertical" style={{ width: '100%' }}>
          <Space>
            <Text style={{ width: 140 }}>Dashboard 模型</Text>
            <Select
              style={{ width: 320 }}
              value={bindings.dashboard}
              onChange={(id) => bindScene('dashboard', id)}
              options={list.map((x) => ({
                label: `${x.name} (${x.model})`,
                value: x.id,
              }))}
            />
          </Space>
          <Space>
            <Text style={{ width: 140 }}>DataDiscuss 模型</Text>
            <Select
              style={{ width: 320 }}
              value={bindings.data_discuss}
              onChange={(id) => bindScene('data_discuss', id)}
              options={list.map((x) => ({
                label: `${x.name} (${x.model})`,
                value: x.id,
              }))}
            />
          </Space>
        </Space>
      </Card>

      <Modal title="新增 LLMSource" open={open} onCancel={() => setOpen(false)} onOk={createSource}>
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="名称" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="provider" label="Provider" initialValue="ollama">
            <Input />
          </Form.Item>
          <Form.Item
            name="base_url"
            label="Base URL"
            initialValue="http://127.0.0.1:11434/v1"
            rules={[{ required: true }]}
          >
            <Input />
          </Form.Item>
          <Form.Item name="model" label="Model" rules={[{ required: true }]}>
            <Input placeholder="qwen3-4B-instruct-2507_q8 / minicpm-v4 / TableGPT2-7B / bge-m3" />
          </Form.Item>
          <Form.Item name="capability" label="能力类型" initialValue="chat">
            <Select
              options={[
                { label: 'chat', value: 'chat' },
                { label: 'vision', value: 'vision' },
                { label: 'table', value: 'table' },
                { label: 'embedding', value: 'embedding' },
              ]}
            />
          </Form.Item>
          <Form.Item name="api_key" label="API Key" initialValue="ollama">
            <Input />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input />
          </Form.Item>
        </Form>
      </Modal>
    </Space>
  );
};

export default LLMSourcePage;
