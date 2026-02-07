import React, { useEffect, useState } from 'react';
import { Card, Input, Select, Space, Table, Typography, message } from 'antd';
import { dashboardService } from '@/services/dashboard';

const { Title } = Typography;

const MetricGlossaryPage: React.FC = () => {
  const [rows, setRows] = useState<any[]>([]);
  const [keyword, setKeyword] = useState('');
  const [loanType, setLoanType] = useState<string | undefined>();

  useEffect(() => {
    dashboardService
      .getIndicatorDefinitions()
      .then((data) => {
        setRows(data || []);
      })
      .catch((e) => {
        setRows([]);
        message.error(`加载指标口径失败: ${String(e)}`);
      });
  }, []);

  const filtered = rows.filter((r) => {
    const hitKeyword =
      !keyword ||
      String(r.metric_name).includes(keyword) ||
      String(r.metric_key).includes(keyword) ||
      String(r.stage).includes(keyword);
    const hitType = !loanType || r.loan_product === loanType;
    return hitKeyword && hitType;
  });

  return (
    <Card>
      <Space style={{ width: '100%', justifyContent: 'space-between', marginBottom: 12 }}>
        <Title level={4} style={{ margin: 0 }}>
          指标口径说明
        </Title>
        <Space>
          <Input
            placeholder="搜索指标"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            style={{ width: 240 }}
          />
          <Select
            allowClear
            placeholder="贷款类型"
            style={{ width: 160 }}
            value={loanType}
            onChange={setLoanType}
            options={[
              { label: '经营贷', value: 'business' },
              { label: '消费贷', value: 'consumer' },
              { label: '通用', value: 'common' },
            ]}
          />
        </Space>
      </Space>
      <Table
        rowKey="metric_key"
        dataSource={filtered}
        columns={[
          { title: '贷款类型', dataIndex: 'loan_product', width: 100 },
          { title: '阶段', dataIndex: 'stage', width: 110 },
          { title: '指标名称', dataIndex: 'metric_name', width: 210 },
          { title: '指标Key', dataIndex: 'metric_key', width: 180 },
          { title: '口径定义', dataIndex: 'definition', width: 280 },
          {
            title: 'SQL模板',
            dataIndex: 'sql_template',
            render: (v) => <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{v}</pre>,
          },
        ]}
      />
    </Card>
  );
};

export default MetricGlossaryPage;
