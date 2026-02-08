import React, { useEffect, useState } from 'react';
import { Button, Card, Input, Space, Table, Typography, message } from 'antd';
import { monitoringService } from '@/services/monitoring';

const { Title, Text } = Typography;

const MonitoringDiagnosisPage: React.FC = () => {
  const [attributionRulesJson, setAttributionRulesJson] = useState('[]');
  const [defaultActionsJson, setDefaultActionsJson] = useState('[]');
  const [previewRows, setPreviewRows] = useState<any[]>([]);

  const load = async () => {
    try {
      const cfg = await monitoringService.getDiagnosisConfig();
      const rules = cfg?.attribution_rules || [];
      const actions = cfg?.default_actions || [];
      setAttributionRulesJson(JSON.stringify(rules, null, 2));
      setDefaultActionsJson(JSON.stringify(actions, null, 2));
      setPreviewRows(rules);
    } catch (e) {
      message.error(String(e));
    }
  };

  useEffect(() => {
    load();
  }, []);

  const save = async () => {
    try {
      const attributionRules = JSON.parse(attributionRulesJson);
      const defaultActions = JSON.parse(defaultActionsJson);
      await monitoringService.updateDiagnosisConfig({
        attribution_rules: attributionRules,
        default_actions: defaultActions,
      });
      setPreviewRows(attributionRules);
      message.success('诊断配置已保存');
    } catch (e) {
      message.error(`配置格式错误: ${String(e)}`);
    }
  };

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Card>
        <Title level={4} style={{ margin: 0 }}>
          诊断配置
        </Title>
        <Text type="secondary">
          为每个异常指标配置归因模板和建议动作，触发异常后会自动生成“原因解释 + 处理建议”。
        </Text>
      </Card>

      <Card title="归因规则（JSON）">
        <Input.TextArea
          rows={14}
          value={attributionRulesJson}
          onChange={(e) => setAttributionRulesJson(e.target.value)}
        />
      </Card>

      <Card title="默认动作（JSON）">
        <Input.TextArea
          rows={6}
          value={defaultActionsJson}
          onChange={(e) => setDefaultActionsJson(e.target.value)}
        />
        <Space style={{ marginTop: 12 }}>
          <Button type="primary" onClick={save}>
            保存诊断配置
          </Button>
          <Button onClick={load}>重新加载</Button>
        </Space>
      </Card>

      <Card title="规则预览">
        <Table
          rowKey={(r) => `${r.metric_key || 'unknown'}`}
          dataSource={previewRows}
          pagination={false}
          columns={[
            { title: '指标键', dataIndex: 'metric_key', width: 180 },
            {
              title: '可能原因',
              dataIndex: 'possible_causes',
              render: (v) => (v || []).join('；') || '-',
            },
            {
              title: '建议动作',
              dataIndex: 'suggested_actions',
              render: (v) => (v || []).join('；') || '-',
            },
          ]}
        />
      </Card>
    </Space>
  );
};

export default MonitoringDiagnosisPage;
