import React, { useEffect, useState } from 'react';
import {
  Button,
  Card,
  Drawer,
  Form,
  Input,
  Modal,
  Popconfirm,
  Select,
  Segmented,
  Space,
  Switch,
  Table,
  Tag,
  Typography,
  message,
} from 'antd';
import { agentBuilderService } from '@/services/agentBuilder';
import { planningService } from '@/services/planning';

const { Title, Text } = Typography;

const AgentBuilderPage: React.FC = () => {
  const [mode, setMode] = useState<'agent' | 'planning' | 'state'>('agent');

  const [form] = Form.useForm();
  const [open, setOpen] = useState(false);
  const [list, setList] = useState<any[]>([]);
  const [logOpen, setLogOpen] = useState(false);
  const [activeProfile, setActiveProfile] = useState<any>(null);
  const [logs, setLogs] = useState<any[]>([]);

  const [rulesJson, setRulesJson] = useState('[]');
  const [chainsJson, setChainsJson] = useState('[]');
  const [planQuestion, setPlanQuestion] = useState(
    '请分析经营贷近30天逾期率与额度使用率，并给出可执行策略。',
  );
  const [planPreview, setPlanPreview] = useState<any>(null);

  const [executions, setExecutions] = useState<any[]>([]);
  const [executionId, setExecutionId] = useState<string | undefined>();
  const [executionDetail, setExecutionDetail] = useState<any>(null);

  const loadAgents = async () => {
    const data = await agentBuilderService.listProfiles();
    setList(data || []);
  };

  const loadPlanning = async () => {
    const [rules, chains, exes] = await Promise.all([
      planningService.listRules(),
      planningService.listChains(),
      planningService.listExecutions(100),
    ]);
    setRulesJson(JSON.stringify(rules || [], null, 2));
    setChainsJson(JSON.stringify(chains || [], null, 2));
    setExecutions(exes || []);

    const first = (exes || [])[0];
    if (!executionId && first?.execution_id) {
      setExecutionId(first.execution_id);
      setExecutionDetail(first);
    }
  };

  const load = async () => {
    await Promise.all([loadAgents(), loadPlanning()]);
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
      await loadAgents();
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
      await loadAgents();
    } catch (e) {
      message.error(String(e));
    }
  };

  const saveRules = async () => {
    try {
      const payload = JSON.parse(rulesJson);
      await planningService.updateRules(payload);
      message.success('规划规则已更新');
      await loadPlanning();
    } catch (e) {
      message.error(`规则JSON格式错误: ${String(e)}`);
    }
  };

  const saveChains = async () => {
    try {
      const payload = JSON.parse(chainsJson);
      await planningService.updateChains(payload);
      message.success('规划链路已更新');
      await loadPlanning();
    } catch (e) {
      message.error(`链路JSON格式错误: ${String(e)}`);
    }
  };

  const runPlan = async () => {
    try {
      const data = await planningService.buildPlan(planQuestion, 'data_discuss');
      setPlanPreview(data);
      message.success('A2A规划完成');
    } catch (e) {
      message.error(String(e));
    }
  };

  const refreshExecutionDetail = async (id?: string) => {
    const target = id || executionId;
    if (!target) return;
    const detail = await planningService.getExecution(target);
    setExecutionDetail(detail);
    setExecutionId(target);
  };

  const startExecution = async () => {
    try {
      const created = await planningService.startExecution({
        plan_id: planPreview?.plan_id,
        question: planPreview ? undefined : planQuestion,
        scene: 'data_discuss',
        auto_start: true,
      });
      message.success('执行实例已启动');
      await loadPlanning();
      await refreshExecutionDetail(created.execution_id);
    } catch (e) {
      message.error(String(e));
    }
  };

  const tickExecution = async () => {
    if (!executionId) {
      message.warning('请先选择执行实例');
      return;
    }
    await planningService.tickExecution(executionId);
    await loadPlanning();
    await refreshExecutionDetail(executionId);
  };

  const runToEnd = async () => {
    if (!executionId) {
      message.warning('请先选择执行实例');
      return;
    }
    await planningService.runExecution(executionId, 30);
    message.success('状态机已自动推进');
    await loadPlanning();
    await refreshExecutionDetail(executionId);
  };

  const taskAction = async (
    taskId: string,
    action: 'start' | 'complete' | 'fail' | 'retry' | 'skip',
  ) => {
    if (!executionId) return;
    await planningService.taskAction(executionId, taskId, action);
    await loadPlanning();
    await refreshExecutionDetail(executionId);
  };

  return (
    <Card>
      <Space style={{ width: '100%', justifyContent: 'space-between', marginBottom: 8 }}>
        <Title level={4} style={{ margin: 0 }}>
          Agent编排中心
        </Title>
        <Segmented
          value={mode}
          options={[
            { label: 'Agent工具链', value: 'agent' },
            { label: 'Planning规则', value: 'planning' },
            { label: 'A2A状态机', value: 'state' },
          ]}
          onChange={(v) => setMode(v as 'agent' | 'planning' | 'state')}
        />
      </Space>

      {mode === 'agent' ? (
        <>
          <Space style={{ width: '100%', justifyContent: 'space-between' }}>
            <Text type="secondary">
              每个Agent可独立配置 SQL工具、RAG工具、规则校验工具。分析执行过程会记录日志。
            </Text>
            <Button type="primary" onClick={() => setOpen(true)}>
              新建Agent
            </Button>
          </Space>

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
                  <Switch
                    checked={!!v}
                    onChange={(checked) => toggleTool(row, 'enable_sql_tool', checked)}
                  />
                ),
              },
              {
                title: 'RAG工具',
                dataIndex: 'enable_rag',
                render: (v, row) => (
                  <Switch
                    checked={!!v}
                    onChange={(checked) => toggleTool(row, 'enable_rag', checked)}
                  />
                ),
              },
              {
                title: '规则校验',
                dataIndex: 'enable_rule_validation',
                render: (v, row) => (
                  <Switch
                    checked={!!v}
                    onChange={(checked) =>
                      toggleTool(row, 'enable_rule_validation', checked)
                    }
                  />
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
                        await loadAgents();
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
        </>
      ) : null}

      {mode === 'planning' ? (
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <Text type="secondary">
            规划能力用于将贷款分析任务按规则拆分，自动分派给不同执行Agent，形成A2A协作链。
          </Text>

          <Card title="规划规则（Rule）" size="small">
            <Space direction="vertical" style={{ width: '100%' }}>
              <Input.TextArea
                value={rulesJson}
                onChange={(e) => setRulesJson(e.target.value)}
                rows={12}
              />
              <Button onClick={saveRules} type="primary">
                保存规则
              </Button>
            </Space>
          </Card>

          <Card title="协作链路（Chain）" size="small">
            <Space direction="vertical" style={{ width: '100%' }}>
              <Input.TextArea
                value={chainsJson}
                onChange={(e) => setChainsJson(e.target.value)}
                rows={12}
              />
              <Button onClick={saveChains} type="primary">
                保存链路
              </Button>
            </Space>
          </Card>

          <Card title="A2A 规划模拟" size="small">
            <Space direction="vertical" style={{ width: '100%' }}>
              <Input.TextArea
                value={planQuestion}
                onChange={(e) => setPlanQuestion(e.target.value)}
                rows={4}
              />
              <Space>
                <Button type="primary" onClick={runPlan}>
                  生成任务拆分与分派
                </Button>
                <Button onClick={startExecution}>从当前问题启动状态机执行</Button>
              </Space>
              {planPreview && (
                <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                  {JSON.stringify(planPreview, null, 2)}
                </pre>
              )}
            </Space>
          </Card>
        </Space>
      ) : null}

      {mode === 'state' ? (
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <Text type="secondary">
            该状态机将 A2A 从“规划”升级为“可执行编排”，支持逐步推进、自动推进、失败重试。
          </Text>

          <Card title="执行实例">
            <Space direction="vertical" style={{ width: '100%' }}>
              <Space wrap>
                <Select
                  style={{ width: 420 }}
                  placeholder="选择执行实例"
                  value={executionId}
                  onChange={async (v) => {
                    setExecutionId(v);
                    await refreshExecutionDetail(v);
                  }}
                  options={executions.map((x) => ({
                    label: `${x.execution_id} | ${x.state} | ${x.question}`,
                    value: x.execution_id,
                  }))}
                />
                <Button type="primary" onClick={startExecution}>
                  新建执行
                </Button>
                <Button onClick={tickExecution}>单步推进</Button>
                <Button onClick={runToEnd}>自动跑完</Button>
                <Button onClick={() => refreshExecutionDetail(executionId)}>刷新详情</Button>
              </Space>

              {executionDetail ? (
                <Space wrap>
                  <Tag color="blue">状态: {executionDetail.state}</Tag>
                  <Tag>计划ID: {executionDetail.plan_id}</Tag>
                  <Tag>贷款类型: {executionDetail.loan_type}</Tag>
                </Space>
              ) : null}
            </Space>
          </Card>

          <Card title="任务状态">
            <Table
              rowKey="task_id"
              dataSource={executionDetail?.tasks || []}
              pagination={false}
              columns={[
                { title: '任务ID', dataIndex: 'task_id', width: 100 },
                { title: '任务', dataIndex: 'title' },
                { title: '执行Agent', dataIndex: 'assigned_agent', width: 180 },
                {
                  title: '状态',
                  dataIndex: 'status',
                  width: 120,
                  render: (v) => (
                    <Tag
                      color={
                        v === 'completed'
                          ? 'green'
                          : v === 'running'
                            ? 'blue'
                            : v === 'failed'
                              ? 'red'
                              : v === 'ready'
                                ? 'gold'
                                : 'default'
                      }
                    >
                      {v}
                    </Tag>
                  ),
                },
                { title: '依赖', dataIndex: 'depends_on', render: (v) => (v || []).join(', ') || '-' },
                {
                  title: '动作',
                  width: 280,
                  render: (_, row) => (
                    <Space>
                      <Button size="small" onClick={() => taskAction(row.task_id, 'start')}>
                        开始
                      </Button>
                      <Button size="small" onClick={() => taskAction(row.task_id, 'complete')}>
                        完成
                      </Button>
                      <Button size="small" onClick={() => taskAction(row.task_id, 'retry')}>
                        重试
                      </Button>
                      <Button danger size="small" onClick={() => taskAction(row.task_id, 'fail')}>
                        失败
                      </Button>
                    </Space>
                  ),
                },
              ]}
            />
          </Card>
        </Space>
      ) : null}

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
