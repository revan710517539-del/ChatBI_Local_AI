import React, { useEffect, useMemo, useState } from 'react';
import {
  Button,
  Card,
  Col,
  Input,
  Row,
  Select,
  Space,
  Table,
  Tag,
  Typography,
  message,
} from 'antd';
import Playground from '../Playground';
import { mcpSkillService } from '@/services/mcpSkill';

const { Title, Text } = Typography;

const DataDiscussPage: React.FC = () => {
  const [strategies, setStrategies] = useState<any[]>([]);
  const [activeStrategyId, setActiveStrategyId] = useState<string | undefined>();
  const [discussion, setDiscussion] = useState('');
  const [topic, setTopic] = useState('经营贷低动支客群激活与风险稳定策略');
  const [loanType, setLoanType] = useState<'business' | 'consumer' | 'mixed'>('mixed');

  const loadStrategies = async () => {
    try {
      const list = await mcpSkillService.listStrategies(50);
      setStrategies(list || []);
      if (!activeStrategyId && list?.length) {
        setActiveStrategyId(list[0].id);
      }
    } catch (e) {
      message.error(String(e));
    }
  };

  useEffect(() => {
    const bootstrap = async () => {
      const list = await mcpSkillService.listStrategies(50);
      if (!list?.length) {
        await mcpSkillService.generateStrategy({
          topic: '基于贷款指标看板的首版运营策略',
          loan_type: 'mixed',
        });
      }
      await loadStrategies();
    };
    bootstrap().catch((e) => message.error(String(e)));
  }, []);

  const activeStrategy = useMemo(
    () => strategies.find((x) => x.id === activeStrategyId) || strategies[0],
    [strategies, activeStrategyId],
  );

  const generateStrategy = async () => {
    try {
      const created = await mcpSkillService.generateStrategy({
        topic,
        loan_type: loanType,
      });
      message.success('已生成新的策略草案');
      await loadStrategies();
      setActiveStrategyId(created?.id);
    } catch (e) {
      message.error(String(e));
    }
  };

  const refineStrategy = async () => {
    if (!activeStrategy?.id) {
      message.warning('请先选择策略');
      return;
    }
    if (!discussion.trim()) {
      message.warning('请输入协同讨论内容');
      return;
    }
    try {
      await mcpSkillService.refineStrategy(activeStrategy.id, discussion, 'human');
      message.success('策略已根据人机讨论更新');
      setDiscussion('');
      await loadStrategies();
      setActiveStrategyId(activeStrategy.id);
    } catch (e) {
      message.error(String(e));
    }
  };

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Card>
        <Space style={{ width: '100%', justifyContent: 'space-between' }} align="start">
          <div>
            <Title level={4} style={{ margin: 0 }}>
              策略讨论 · 人机协同策略台
            </Title>
            <Text type="secondary">
              页面先展示数据分析形成的新策略，再通过人机深度讨论持续修正策略内容。
            </Text>
          </div>
          <Space wrap>
            <Input
              style={{ width: 320 }}
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="策略主题"
            />
            <Select
              style={{ width: 140 }}
              value={loanType}
              onChange={(v) => setLoanType(v)}
              options={[
                { label: '经营贷', value: 'business' },
                { label: '消费贷', value: 'consumer' },
                { label: '混合', value: 'mixed' },
              ]}
            />
            <Button type="primary" onClick={generateStrategy}>
              生成新策略
            </Button>
          </Space>
        </Space>
      </Card>

      <Row gutter={[16, 16]}>
        <Col xs={24} xl={10}>
          <Card title="策略展示">
            <Space direction="vertical" style={{ width: '100%' }} size="middle">
              <Select
                style={{ width: '100%' }}
                value={activeStrategy?.id}
                onChange={setActiveStrategyId}
                options={strategies.map((x) => ({
                  label: `${x.content?.topic || '未命名策略'} (${x.status})`,
                  value: x.id,
                }))}
                placeholder="选择策略"
              />

              {activeStrategy ? (
                <>
                  <Card size="small" title="策略摘要">
                    <Space direction="vertical" style={{ width: '100%' }}>
                      <Text>{activeStrategy.content?.summary || '-'}</Text>
                      <Space wrap>
                        <Tag color="blue">{activeStrategy.content?.loan_type || '-'}</Tag>
                        <Tag color="gold">状态: {activeStrategy.status}</Tag>
                        <Tag color="green">
                          审批: {activeStrategy.approval?.reply_status || 'pending'}
                        </Tag>
                      </Space>
                    </Space>
                  </Card>

                  <Card size="small" title="策略依据">
                    <ul style={{ margin: 0, paddingLeft: 18, lineHeight: 1.9 }}>
                      {(activeStrategy.content?.evidence || []).map((x: string, i: number) => (
                        <li key={`${x}-${i}`}>{x}</li>
                      ))}
                    </ul>
                  </Card>

                  <Table
                    size="small"
                    rowKey={(r, i) => `${r.channel}-${i}`}
                    dataSource={activeStrategy.content?.actions || []}
                    pagination={false}
                    columns={[
                      { title: '渠道', dataIndex: 'channel', width: 120 },
                      { title: '目标客群', dataIndex: 'target', width: 150 },
                      { title: '策略动作', dataIndex: 'action' },
                      { title: '约束', dataIndex: 'guardrail' },
                    ]}
                  />
                </>
              ) : (
                <Text type="secondary">暂无策略，请先生成。</Text>
              )}
            </Space>
          </Card>

          <Card title="人机协同讨论（调整策略）" style={{ marginTop: 16 }}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Input.TextArea
                rows={5}
                value={discussion}
                onChange={(e) => setDiscussion(e.target.value)}
                placeholder="示例：消费贷M1迁徙上升，建议降低高风险新客准入并提高老客复贷激励。"
              />
              <Space>
                <Button type="primary" onClick={refineStrategy}>
                  根据讨论更新策略
                </Button>
                {activeStrategy?.id && (
                  <Button
                    onClick={async () => {
                      await mcpSkillService.sendStrategyEmail(activeStrategy.id);
                      message.success('已发送策略审批邮件（未配置SMTP时为模拟发送）');
                      await loadStrategies();
                    }}
                  >
                    发送审批邮件
                  </Button>
                )}
              </Space>

              {(activeStrategy?.collaboration || []).length > 0 && (
                <Card size="small" title="协同历史">
                  <ul style={{ margin: 0, paddingLeft: 18, lineHeight: 1.8 }}>
                    {(activeStrategy.collaboration || [])
                      .slice(-6)
                      .reverse()
                      .map((x: any, i: number) => (
                        <li key={`${x.ts}-${i}`}>
                          [{x.ts}] {x.operator}: {x.discussion}
                        </li>
                      ))}
                  </ul>
                </Card>
              )}
            </Space>
          </Card>
        </Col>

        <Col xs={24} xl={14}>
          <Card title="深度讨论对话框">
            <Playground scene="data_discuss" title="SmartBI 协同分析助手" />
          </Card>
        </Col>
      </Row>
    </Space>
  );
};

export default DataDiscussPage;
