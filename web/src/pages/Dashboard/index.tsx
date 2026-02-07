import React from 'react';
import { Alert, Button, Card, Col, Empty, Row, Skeleton, Space, Statistic, Typography, message } from 'antd';
import { dashboardService } from '@/services/dashboard';
import { history } from '@umijs/max';
import {
  ArrowDownOutlined,
  ArrowUpOutlined,
  FundOutlined,
  SafetyCertificateOutlined,
  SwapOutlined,
} from '@ant-design/icons';
import Playground from '../Playground';

const { Text } = Typography;

const MetricGrid: React.FC<{ title: string; items: any[]; loading: boolean }> = ({ title, items, loading }) => {
  if (loading) {
    return (
      <Card title={title} style={{ marginBottom: 16 }}>
        <Skeleton active paragraph={{ rows: 4 }} />
      </Card>
    );
  }

  if (!items?.length) {
    return (
      <Card title={title} style={{ marginBottom: 16 }}>
        <Empty description="暂无指标数据" />
      </Card>
    );
  }

  return (
    <Card title={title} style={{ marginBottom: 16 }}>
      <Row gutter={[16, 16]}>
        {items.map((m) => (
          <Col xs={24} sm={12} xl={6} key={m.key || m.metric_key}>
            <Card size="small" bordered>
              <Statistic
                title={m.name || m.metric_name}
                value={m.value ?? '-'}
                precision={typeof m.value === 'number' && m.value < 1 ? 4 : 2}
              />
              {m.sql ? (
                <Text type="secondary" style={{ fontSize: 12 }} ellipsis>
                  SQL: {m.sql}
                </Text>
              ) : null}
            </Card>
          </Col>
        ))}
      </Row>
    </Card>
  );
};

const DashboardPage: React.FC = () => {
  const [kpis, setKpis] = React.useState<any>({
    business_loan: [],
    consumer_loan: [],
    finance_risk: [],
    summary: '',
  });
  const [loading, setLoading] = React.useState(false);

  const load = React.useCallback(async () => {
    setLoading(true);
    try {
      const data = await dashboardService.getLoanKpis();
      setKpis(data || {});
    } catch (e) {
      message.error(`Dashboard 加载失败: ${String(e)}`);
      setKpis({
        business_loan: [],
        consumer_loan: [],
        finance_risk: [],
        summary: '指标服务暂不可用，请稍后重试。',
      });
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    load();
  }, [load]);

  const heroCards = [
    {
      title: '经营贷逾期率',
      value: kpis?.business_loan?.find((x: any) => x.key === 'bl_overdue_rate')?.value ?? '-',
      icon: <SafetyCertificateOutlined />,
      trend: <ArrowDownOutlined style={{ color: '#16a34a' }} />,
    },
    {
      title: '消费贷迁徙率',
      value: kpis?.consumer_loan?.find((x: any) => x.key === 'cl_migration_rate')?.value ?? '-',
      icon: <SwapOutlined />,
      trend: <ArrowDownOutlined style={{ color: '#16a34a' }} />,
    },
    {
      title: '经营贷额度使用率',
      value: kpis?.business_loan?.find((x: any) => x.key === 'bl_credit_utilization_rate')?.value ?? '-',
      icon: <FundOutlined />,
      trend: <ArrowUpOutlined style={{ color: '#0f6eff' }} />,
    },
  ];

  return (
    <div style={{ padding: 8 }}>
      <Alert
        type="info"
        showIcon
        message="贷款业务驾驶舱"
        description="围绕消费贷和经营贷的规模、收益、风险三线指标进行日常经营诊断。"
        style={{ marginBottom: 16 }}
      />

      <Card style={{ marginBottom: 16 }}>
        <Space style={{ width: '100%', justifyContent: 'space-between' }} wrap>
          <Text strong style={{ fontSize: 16 }}>
            {loading ? '经营总结生成中...' : '经营总结'}
          </Text>
          <Space>
            <Button onClick={load}>刷新指标</Button>
            <Button type="primary" onClick={() => history.push('/metric-glossary')}>
              指标口径说明
            </Button>
          </Space>
        </Space>
        <div style={{ marginTop: 12 }}>
          <Text>{kpis.summary || '暂无总结'}</Text>
        </div>
      </Card>

      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        {heroCards.map((c) => (
          <Col xs={24} md={8} key={c.title}>
            <Card>
              <Statistic title={c.title} value={c.value} prefix={c.icon} suffix={c.trend} />
            </Card>
          </Col>
        ))}
      </Row>

      <MetricGrid title="经营贷专项指标" items={kpis.business_loan} loading={loading} />
      <MetricGrid title="消费贷专项指标" items={kpis.consumer_loan} loading={loading} />
      <MetricGrid title="财务与风险扩展指标" items={kpis.finance_risk} loading={loading} />

      <Playground scene="dashboard" title="SmartBI Dashboard Assistant" />
    </div>
  );
};

export default DashboardPage;
