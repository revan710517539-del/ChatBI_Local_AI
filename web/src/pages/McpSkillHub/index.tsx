import React, { useEffect, useState } from 'react';
import {
  Button,
  Card,
  Form,
  Input,
  InputNumber,
  Segmented,
  Space,
  Switch,
  Table,
  Tag,
  Typography,
  message,
} from 'antd';
import { mcpSkillService } from '@/services/mcpSkill';

const { Title, Text } = Typography;

const McpSkillHubPage: React.FC = () => {
  const [mode, setMode] = useState<'mcp' | 'skills' | 'strategy' | 'email'>('mcp');
  const [mcpServers, setMcpServers] = useState<any[]>([]);
  const [skills, setSkills] = useState<any[]>([]);
  const [strategies, setStrategies] = useState<any[]>([]);
  const [emailConfig, setEmailConfig] = useState<any>({});
  const [strategyTopic, setStrategyTopic] = useState('经营贷低动支客群激活与风险稳定策略');
  const [strategyLoanType, setStrategyLoanType] = useState('business');

  const load = async () => {
    try {
      const [servers, sks, sts, cfg] = await Promise.all([
        mcpSkillService.listMcpServers(),
        mcpSkillService.listSkills(),
        mcpSkillService.listStrategies(50),
        mcpSkillService.getEmailConfig(),
      ]);
      setMcpServers(servers || []);
      setSkills(sks || []);
      setStrategies(sts || []);
      setEmailConfig(cfg || {});
    } catch (e) {
      message.error(String(e));
    }
  };

  useEffect(() => {
    load();
  }, []);

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Card>
        <Space style={{ width: '100%', justifyContent: 'space-between' }}>
          <Title level={4} style={{ margin: 0 }}>
            技能库协同中心
          </Title>
          <Segmented
            value={mode}
            onChange={(v) => setMode(v as any)}
            options={[
              { label: 'MCP', value: 'mcp' },
              { label: 'Skills', value: 'skills' },
              { label: '策略中心', value: 'strategy' },
              { label: '邮件配置', value: 'email' },
            ]}
          />
        </Space>
        <Text type="secondary">
          对标 OpenClaw 的外部协作能力：策略先生成并发送审批邮件，待你回邮同意后再执行。
        </Text>
      </Card>

      {mode === 'mcp' && (
        <Card title="MCP 服务器管理">
          <Table
            rowKey="id"
            dataSource={mcpServers}
            columns={[
              { title: '名称', dataIndex: 'name' },
              { title: 'Endpoint', dataIndex: 'endpoint' },
              { title: '说明', dataIndex: 'description' },
              {
                title: '能力',
                dataIndex: 'capabilities',
                render: (v: string[]) =>
                  (v || []).map((x) => (
                    <Tag key={x} style={{ marginBottom: 4 }}>
                      {x}
                    </Tag>
                  )),
              },
              {
                title: '启用',
                dataIndex: 'enabled',
                render: (v, row) => (
                  <Switch
                    checked={!!v}
                    onChange={async (checked) => {
                      await mcpSkillService.updateMcpServer(row.id, { enabled: checked });
                      await load();
                    }}
                  />
                ),
              },
            ]}
          />
        </Card>
      )}

      {mode === 'skills' && (
        <Card title="Skills 管理">
          <Table
            rowKey="id"
            dataSource={skills}
            columns={[
              { title: '名称', dataIndex: 'name' },
              { title: '分类', dataIndex: 'category' },
              { title: '触发条件', dataIndex: 'trigger' },
              { title: '说明', dataIndex: 'description' },
              {
                title: '启用',
                dataIndex: 'enabled',
                render: (v, row) => (
                  <Switch
                    checked={!!v}
                    onChange={async (checked) => {
                      await mcpSkillService.updateSkill(row.id, { enabled: checked });
                      await load();
                    }}
                  />
                ),
              },
            ]}
          />
        </Card>
      )}

      {mode === 'strategy' && (
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <Card title="策略生成（贷款运营）">
            <Space wrap>
              <Input
                style={{ width: 520 }}
                value={strategyTopic}
                onChange={(e) => setStrategyTopic(e.target.value)}
                placeholder="输入策略主题"
              />
              <Input
                style={{ width: 160 }}
                value={strategyLoanType}
                onChange={(e) => setStrategyLoanType(e.target.value)}
                placeholder="business/consumer/mixed"
              />
              <Button
                type="primary"
                onClick={async () => {
                  await mcpSkillService.generateStrategy({
                    topic: strategyTopic,
                    loan_type: strategyLoanType,
                  });
                  message.success('策略草案已生成');
                  await load();
                }}
              >
                生成策略草案
              </Button>
            </Space>
          </Card>

          <Card title="策略审批与执行">
            <Table
              rowKey="id"
              dataSource={strategies}
              columns={[
                { title: '主题', render: (_, row) => row.content?.topic || '-' },
                { title: '状态', dataIndex: 'status' },
                {
                  title: '策略依据',
                  render: (_, row) => (
                    <span>{(row.content?.evidence || []).join(' | ') || '-'}</span>
                  ),
                },
                {
                  title: '操作',
                  render: (_, row) => (
                    <Space>
                      <Button
                        size="small"
                        onClick={async () => {
                          await mcpSkillService.sendStrategyEmail(row.id);
                          message.success('已发送策略审批邮件');
                          await load();
                        }}
                      >
                        发送审批邮件
                      </Button>
                      <Button
                        size="small"
                        onClick={async () => {
                          await mcpSkillService.approveStrategy(row.id, 'AGREE', true);
                          message.success('已模拟回邮同意并执行');
                          await load();
                        }}
                      >
                        模拟回邮同意并执行
                      </Button>
                    </Space>
                  ),
                },
              ]}
            />
          </Card>
        </Space>
      )}

      {mode === 'email' && (
        <Card title="审批邮件配置">
          <Form
            layout="vertical"
            initialValues={emailConfig}
            key={JSON.stringify(emailConfig)}
            onFinish={async (values) => {
              await mcpSkillService.updateEmailConfig(values);
              message.success('邮件配置已保存');
              await load();
            }}
          >
            <Space style={{ width: '100%' }} align="start" wrap>
              <Form.Item name="sender" label="发件人邮箱">
                <Input style={{ width: 280 }} />
              </Form.Item>
              <Form.Item name="recipient" label="收件人邮箱（你的邮箱）">
                <Input style={{ width: 280 }} />
              </Form.Item>
              <Form.Item name="smtp_host" label="SMTP Host">
                <Input style={{ width: 220 }} />
              </Form.Item>
              <Form.Item name="smtp_port" label="SMTP Port">
                <InputNumber style={{ width: 140 }} />
              </Form.Item>
              <Form.Item name="smtp_user" label="SMTP 用户">
                <Input style={{ width: 200 }} />
              </Form.Item>
              <Form.Item name="smtp_password" label="SMTP 密码">
                <Input.Password style={{ width: 220 }} />
              </Form.Item>
              <Form.Item name="use_tls" label="TLS" valuePropName="checked">
                <Switch />
              </Form.Item>
            </Space>
            <Button type="primary" htmlType="submit">
              保存配置
            </Button>
          </Form>
        </Card>
      )}
    </Space>
  );
};

export default McpSkillHubPage;
