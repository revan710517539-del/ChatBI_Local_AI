import React, { useEffect, useMemo, useState } from 'react';
import {
  Button,
  Card,
  Input,
  InputNumber,
  Select,
  Space,
  Statistic,
  Switch,
  Table,
  Tag,
  Typography,
  message,
} from 'antd';
import { monitoringService } from '@/services/monitoring';

const { Title, Text } = Typography;

const OPS = ['>', '>=', '<', '<=', '=='];
const SEVERITY = ['low', 'medium', 'high'];

const MonitoringRulesPage: React.FC = () => {
  const [rules, setRules] = useState<any[]>([]);
  const [snapshot, setSnapshot] = useState<any>(null);
  const [saving, setSaving] = useState(false);

  const load = async () => {
    try {
      const [ruleData, snap] = await Promise.all([
        monitoringService.getRuleConfig(),
        monitoringService.getSnapshot(),
      ]);
      setRules(ruleData || []);
      setSnapshot(snap || null);
    } catch (e) {
      message.error(String(e));
    }
  };

  useEffect(() => {
    load();
  }, []);

  const updateRow = (id: string, patch: Record<string, any>) => {
    setRules((prev) => prev.map((x) => (x.id === id ? { ...x, ...patch } : x)));
  };

  const addRule = () => {
    const ts = `${Date.now()}`;
    setRules((prev) => [
      {
        id: `rule_${ts}`,
        name: '新监控规则',
        metric_key: 'bl_overdue_rate',
        operator: '>',
        threshold: 0,
        severity: 'medium',
        scope: 'data',
        enabled: true,
      },
      ...prev,
    ]);
  };

  const save = async () => {
    setSaving(true);
    try {
      await monitoringService.updateRuleConfig(rules);
      message.success('监控规则已保存');
      await load();
    } catch (e) {
      message.error(String(e));
    } finally {
      setSaving(false);
    }
  };

  const runCheck = async () => {
    try {
      const result = await monitoringService.checkAlerts(true);
      message.success(`监控检查完成，新增异常 ${result?.new_alerts?.length || 0} 条`);
      await load();
    } catch (e) {
      message.error(String(e));
    }
  };

  const metricsRows = useMemo(() => {
    const m = snapshot?.metrics || {};
    return Object.keys(m).map((k) => ({ key: k, metric_key: k, value: m[k] }));
  }, [snapshot]);

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Card>
        <Space style={{ width: '100%', justifyContent: 'space-between' }}>
          <div>
            <Title level={4} style={{ margin: 0 }}>
              监控规则配置
            </Title>
            <Text type="secondary">
              对市场信号和贷款核心指标配置阈值监控，触发异常后自动进入邮件提醒与归因流程。
            </Text>
          </div>
          <Space>
            <Button onClick={addRule}>新增规则</Button>
            <Button onClick={runCheck}>执行监控检查</Button>
            <Button type="primary" loading={saving} onClick={save}>
              保存规则
            </Button>
          </Space>
        </Space>
      </Card>

      <Card>
        <Space size={24} wrap>
          <Statistic title="规则总数" value={rules.length} />
          <Statistic
            title="启用规则"
            value={rules.filter((x) => x.enabled).length}
          />
          <Statistic title="快照时间" value={snapshot?.collected_at || '-'} />
        </Space>
      </Card>

      <Card title="规则列表">
        <Table
          rowKey="id"
          dataSource={rules}
          pagination={false}
          columns={[
            {
              title: '规则名称',
              dataIndex: 'name',
              width: 220,
              render: (v, row) => (
                <Input value={v} onChange={(e) => updateRow(row.id, { name: e.target.value })} />
              ),
            },
            {
              title: '指标键',
              dataIndex: 'metric_key',
              width: 180,
              render: (v, row) => (
                <Input
                  value={v}
                  onChange={(e) => updateRow(row.id, { metric_key: e.target.value })}
                />
              ),
            },
            {
              title: '运算',
              dataIndex: 'operator',
              width: 90,
              render: (v, row) => (
                <Select
                  value={v}
                  style={{ width: 80 }}
                  onChange={(op) => updateRow(row.id, { operator: op })}
                  options={OPS.map((x) => ({ label: x, value: x }))}
                />
              ),
            },
            {
              title: '阈值',
              dataIndex: 'threshold',
              width: 120,
              render: (v, row) => (
                <InputNumber
                  value={v}
                  style={{ width: 110 }}
                  onChange={(n) => updateRow(row.id, { threshold: Number(n || 0) })}
                />
              ),
            },
            {
              title: '级别',
              dataIndex: 'severity',
              width: 120,
              render: (v, row) => (
                <Select
                  value={v}
                  style={{ width: 110 }}
                  onChange={(s) => updateRow(row.id, { severity: s })}
                  options={SEVERITY.map((x) => ({ label: x, value: x }))}
                />
              ),
            },
            {
              title: '范围',
              dataIndex: 'scope',
              width: 120,
              render: (v, row) => (
                <Select
                  value={v}
                  style={{ width: 110 }}
                  onChange={(s) => updateRow(row.id, { scope: s })}
                  options={[
                    { label: 'data', value: 'data' },
                    { label: 'market', value: 'market' },
                  ]}
                />
              ),
            },
            {
              title: '启用',
              dataIndex: 'enabled',
              width: 90,
              render: (v, row) => (
                <Switch checked={!!v} onChange={(checked) => updateRow(row.id, { enabled: checked })} />
              ),
            },
          ]}
        />
      </Card>

      <Card title="监控快照（当前值）">
        <Table
          rowKey="metric_key"
          dataSource={metricsRows}
          pagination={{ pageSize: 8 }}
          columns={[
            { title: '指标键', dataIndex: 'metric_key' },
            {
              title: '值',
              dataIndex: 'value',
              render: (v) => <Tag color="blue">{v}</Tag>,
            },
          ]}
        />
      </Card>
    </Space>
  );
};

export default MonitoringRulesPage;
