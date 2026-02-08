import React, { useEffect, useMemo, useState } from 'react';
import {
  Button,
  Card,
  Col,
  Progress,
  Row,
  Select,
  Space,
  Statistic,
  Table,
  Tag,
  Typography,
  message,
} from 'antd';
import { strategyLabService } from '@/services/strategyLab';
import { mcpSkillService } from '@/services/mcpSkill';
import TrendAreaChart from '@/components/TrendAreaChart';

const { Title, Text } = Typography;

const StrategyAttributionPage: React.FC = () => {
  const [summary, setSummary] = useState<any>({});
  const [experiments, setExperiments] = useState<any[]>([]);
  const [strategies, setStrategies] = useState<any[]>([]);
  const [selectedExperimentId, setSelectedExperimentId] = useState<string | undefined>();
  const [selectedStrategyId, setSelectedStrategyId] = useState<string | undefined>();
  const [activeExperiment, setActiveExperiment] = useState<any>(null);
  const [trend, setTrend] = useState<any[]>([]);

  const load = async () => {
    try {
      const [sum, exps, sts] = await Promise.all([
        strategyLabService.getSummary(),
        strategyLabService.listExperiments(100),
        mcpSkillService.listStrategies(100),
      ]);
      setSummary(sum || {});
      setExperiments(exps || []);
      setStrategies(sts || []);

      const exp = (exps || [])[0];
      if (exp) {
        setSelectedExperimentId(exp.id);
        setActiveExperiment(exp);
        const tr = await strategyLabService.getExperimentTrend(exp.id);
        setTrend(tr || []);
      }
    } catch (e) {
      message.error(String(e));
    }
  };

  useEffect(() => {
    load();
  }, []);

  const loadExperiment = async (id: string) => {
    try {
      setSelectedExperimentId(id);
      const [exp, tr] = await Promise.all([
        strategyLabService.getExperiment(id),
        strategyLabService.getExperimentTrend(id),
      ]);
      setActiveExperiment(exp);
      setTrend(tr || []);
    } catch (e) {
      message.error(String(e));
    }
  };

  const trendData = useMemo(() => trend || [], [trend]);

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Card>
        <Space style={{ width: '100%', justifyContent: 'space-between' }} align="start">
          <div>
            <Title level={4} style={{ margin: 0 }}>
              策略实验归因看板
            </Title>
            <Text type="secondary">
              A/B 实验跟踪策略效果，输出转化、逾期、RAROC 的效果归因。
            </Text>
          </div>
          <Space wrap>
            <Select
              style={{ width: 360 }}
              placeholder="选择策略生成实验"
              value={selectedStrategyId}
              onChange={setSelectedStrategyId}
              options={(strategies || []).map((x: any) => ({
                label: `${x.content?.topic || '未命名策略'} (${x.status})`,
                value: x.id,
              }))}
            />
            <Button
              type="primary"
              disabled={!selectedStrategyId}
              onClick={async () => {
                if (!selectedStrategyId) return;
                const created = await strategyLabService.createFromStrategy({
                  strategy_id: selectedStrategyId,
                });
                message.success('已创建A/B实验');
                await load();
                if (created?.id) {
                  await loadExperiment(created.id);
                }
              }}
            >
              从策略创建实验
            </Button>
          </Space>
        </Space>
      </Card>

      <Row gutter={[16, 16]}>
        <Col xs={24} md={8} xl={4}>
          <Card>
            <Statistic title="实验总数" value={summary.experiment_count || 0} />
          </Card>
        </Col>
        <Col xs={24} md={8} xl={4}>
          <Card>
            <Statistic title="运行中" value={summary.running_count || 0} />
          </Card>
        </Col>
        <Col xs={24} md={8} xl={4}>
          <Card>
            <Statistic title="已完成" value={summary.completed_count || 0} />
          </Card>
        </Col>
        <Col xs={24} md={8} xl={4}>
          <Card>
            <Statistic title="平均转化提升" value={summary.avg_conversion_uplift || 0} precision={4} />
          </Card>
        </Col>
        <Col xs={24} md={8} xl={4}>
          <Card>
            <Statistic title="平均逾期变化" value={summary.avg_overdue_uplift || 0} precision={4} />
          </Card>
        </Col>
        <Col xs={24} md={8} xl={4}>
          <Card>
            <Statistic title="平均RAROC提升" value={summary.avg_raroc_uplift || 0} precision={4} />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        <Col xs={24} xl={10}>
          <Card title="实验列表">
            <Table
              size="small"
              rowKey="id"
              dataSource={experiments}
              pagination={{ pageSize: 6 }}
              onRow={(record) => ({
                onClick: () => loadExperiment(record.id),
              })}
              columns={[
                { title: '实验名称', dataIndex: 'name' },
                { title: '贷款类型', dataIndex: 'loan_type', width: 90 },
                {
                  title: '状态',
                  dataIndex: 'status',
                  width: 100,
                  render: (v) => (
                    <Tag color={v === 'completed' ? 'green' : v === 'running' ? 'blue' : 'default'}>
                      {v}
                    </Tag>
                  ),
                },
                {
                  title: '操作',
                  width: 120,
                  render: (_, row) => (
                    <Space>
                      <Button
                        size="small"
                        onClick={async (e) => {
                          e.stopPropagation();
                          await strategyLabService.updateStatus(row.id, 'running');
                          await load();
                        }}
                      >
                        运行
                      </Button>
                      <Button
                        size="small"
                        onClick={async (e) => {
                          e.stopPropagation();
                          await strategyLabService.updateStatus(row.id, 'completed');
                          await load();
                        }}
                      >
                        完成
                      </Button>
                    </Space>
                  ),
                },
              ]}
            />
          </Card>

          <Card title="效果归因" style={{ marginTop: 16 }}>
            {(activeExperiment?.attribution || []).map((x: any, idx: number) => (
              <div key={`${x.factor}-${idx}`} style={{ marginBottom: 10 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Text>{x.factor}</Text>
                  <Text type="secondary">{Math.round((x.contribution || 0) * 100)}%</Text>
                </div>
                <Progress
                  percent={Math.round((x.contribution || 0) * 100)}
                  showInfo={false}
                  strokeColor="#18b46b"
                />
                <Text type="secondary" style={{ fontSize: 12 }}>
                  {x.evidence}
                </Text>
              </div>
            ))}
          </Card>
        </Col>

        <Col xs={24} xl={14}>
          <Card
            title="实验趋势（A/B 对比）"
            extra={
              <Select
                style={{ width: 320 }}
                value={selectedExperimentId}
                onChange={loadExperiment}
                options={experiments.map((x) => ({ label: x.name, value: x.id }))}
              />
            }
          >
            <TrendAreaChart
              data={trendData}
              xKey="date"
              height={320}
              series={[
                {
                  key: 'conversion_control',
                  name: '转化率-对照组',
                  color: '#7aa2ff',
                  fill: 'rgba(122,162,255,0.16)',
                },
                {
                  key: 'conversion_treatment',
                  name: '转化率-实验组',
                  color: '#18b46b',
                  fill: 'rgba(24,180,107,0.14)',
                },
                {
                  key: 'overdue_treatment',
                  name: '逾期率-实验组',
                  color: '#f59e0b',
                  fill: 'rgba(245,158,11,0.08)',
                },
              ]}
            />

            <Row gutter={[12, 12]} style={{ marginTop: 12 }}>
              <Col span={8}>
                <Card size="small">
                  <Statistic
                    title="转化率提升"
                    value={activeExperiment?.metrics?.conversion_rate?.uplift || 0}
                    precision={4}
                  />
                </Card>
              </Col>
              <Col span={8}>
                <Card size="small">
                  <Statistic
                    title="逾期率变化"
                    value={activeExperiment?.metrics?.overdue_rate?.uplift || 0}
                    precision={4}
                  />
                </Card>
              </Col>
              <Col span={8}>
                <Card size="small">
                  <Statistic
                    title="RAROC提升"
                    value={activeExperiment?.metrics?.raroc?.uplift || 0}
                    precision={4}
                  />
                </Card>
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>
    </Space>
  );
};

export default StrategyAttributionPage;
