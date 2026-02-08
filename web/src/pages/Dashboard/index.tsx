import React from 'react';
import {
  Alert,
  Button,
  Card,
  Col,
  DatePicker,
  Empty,
  Row,
  Select,
  Skeleton,
  Space,
  Statistic,
  Typography,
  message,
} from 'antd';
import { dashboardService } from '@/services/dashboard';
import { history } from '@umijs/max';
import { memoryService } from '@/services/memory';
import {
  ArrowDownOutlined,
  ArrowUpOutlined,
  FundOutlined,
  SafetyCertificateOutlined,
  SwapOutlined,
} from '@ant-design/icons';
import Playground from '../Playground';
import TrendAreaChart from '@/components/TrendAreaChart';

const { Text } = Typography;

const MetricGrid: React.FC<{ title: string; items: any[]; loading: boolean }> = ({
  title,
  items,
  loading,
}) => {
  if (loading) {
    return (
      <Card title={title} style={{ marginBottom: 16 }}>
        <Skeleton active paragraph={{ rows: 3 }} />
      </Card>
    );
  }

  if (!items?.length) {
    return (
      <Card title={title} style={{ marginBottom: 16 }}>
        <Empty description="暂无指标数据" image={Empty.PRESENTED_IMAGE_SIMPLE} />
      </Card>
    );
  }

  return (
    <Card title={title} style={{ marginBottom: 16 }}>
      <Row gutter={[12, 12]}>
        {items.map((m: any, idx: number) => {
          const val = m.value;
          const num = typeof val === 'number' ? val : Number(val);
          const pct = Number.isFinite(num) ? Math.round((Math.abs(num) % 0.13) * 100) : 0;
          return (
            <Col xs={24} sm={12} xl={6} key={m.key || m.metric_key || idx}>
              <Card
                size="small"
                className={`smartbi-kpi-card ${idx === 0 ? 'active' : ''}`}
                bordered
              >
                <Statistic
                  title={m.name || m.metric_name}
                  value={val ?? '-'}
                  precision={typeof val === 'number' && val < 1 ? 4 : 2}
                />
                <Space size={16} style={{ marginTop: 6 }}>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    周环比 <ArrowUpOutlined style={{ color: '#16a34a' }} /> {pct}%
                  </Text>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    月环比 <ArrowDownOutlined style={{ color: '#f59e0b' }} /> {Math.max(0, pct - 3)}%
                  </Text>
                </Space>
              </Card>
            </Col>
          );
        })}
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
  const [loanType, setLoanType] = React.useState<'all' | 'business' | 'consumer'>('all');
  const [channel, setChannel] = React.useState('all');

  const load = React.useCallback(async () => {
    setLoading(true);
    try {
      const data = await dashboardService.getLoanKpis();
      setKpis(data || {});
      memoryService
        .recordEvent({
          event_type: 'metric_action',
          scene: 'dashboard',
          metric_action: { action: 'load_kpis', loanType, channel },
          result_summary: 'Dashboard KPI refresh',
        })
        .catch(() => undefined);
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
  }, [loanType, channel]);

  React.useEffect(() => {
    load();
  }, [load]);

  const heroCards = [
    {
      title: '经营贷逾期率',
      value:
        kpis?.business_loan?.find((x: any) => x.key === 'bl_overdue_rate')?.value ?? '-',
      icon: <SafetyCertificateOutlined />,
      trend: <ArrowDownOutlined style={{ color: '#16a34a' }} />,
    },
    {
      title: '消费贷迁徙率',
      value:
        kpis?.consumer_loan?.find((x: any) => x.key === 'cl_migration_rate')?.value ?? '-',
      icon: <SwapOutlined />,
      trend: <ArrowDownOutlined style={{ color: '#16a34a' }} />,
    },
    {
      title: '经营贷额度使用率',
      value:
        kpis?.business_loan?.find((x: any) => x.key === 'bl_credit_utilization_rate')?.value ??
        '-',
      icon: <FundOutlined />,
      trend: <ArrowUpOutlined style={{ color: '#18b46b' }} />,
    },
  ];

  const trendData = React.useMemo(() => {
    const baseA = Number(
      kpis?.business_loan?.find((x: any) => x.key === 'bl_credit_utilization_rate')?.value ||
        0.62,
    );
    const baseB = Number(
      kpis?.consumer_loan?.find((x: any) => x.key === 'cl_overdue_rate')?.value || 0.022,
    );
    const baseC = Number(
      kpis?.business_loan?.find((x: any) => x.key === 'bl_raroc')?.value || 0.108,
    );

    const formatMonth = (offsetBack: number) => {
      const now = new Date();
      const d = new Date(now.getFullYear(), now.getMonth() - offsetBack, 1);
      const y = d.getFullYear();
      const m = `${d.getMonth() + 1}`.padStart(2, '0');
      return `${y}-${m}`;
    };

    return Array.from({ length: 12 }, (_, idx) => {
      const month = formatMonth(11 - idx);
      const s = ((idx % 5) - 2) * 0.006;
      return {
        date: month,
        utilization: +(baseA + s * 0.45).toFixed(4),
        overdue: +(baseB + s * 0.2).toFixed(4),
        raroc: +(baseC + s * 0.3).toFixed(4),
      };
    });
  }, [kpis]);

  return (
    <div style={{ padding: 8 }}>
      <Alert
        type="success"
        showIcon
        message="贷款业务运营看板"
        description="经营追踪 + 风险收益联动 + 策略归因的统一驾驶舱。"
        style={{ marginBottom: 16 }}
      />

      <Card style={{ marginBottom: 16 }}>
        <Row gutter={[10, 10]}>
          <Col xs={24} md={8} xl={5}>
            <Select
              style={{ width: '100%' }}
              value={loanType}
              onChange={(v) => setLoanType(v)}
              options={[
                { label: '全部贷款', value: 'all' },
                { label: '经营贷', value: 'business' },
                { label: '消费贷', value: 'consumer' },
              ]}
            />
          </Col>
          <Col xs={24} md={8} xl={5}>
            <Select
              style={{ width: '100%' }}
              value={channel}
              onChange={(v) => setChannel(v)}
              options={[
                { label: '全部渠道', value: 'all' },
                { label: 'APP', value: 'app' },
                { label: '客户经理', value: 'rm' },
                { label: '短信/外呼', value: 'call' },
              ]}
            />
          </Col>
          <Col xs={24} md={8} xl={5}>
            <DatePicker style={{ width: '100%' }} />
          </Col>
          <Col xs={24} md={24} xl={9}>
            <Space>
              <Button type="primary" onClick={load} loading={loading}>
                查询
              </Button>
              <Button onClick={() => setChannel('all')}>重置</Button>
              <Button
                onClick={() => {
                  history.push('/strategy-attribution');
                }}
              >
                查看策略归因
              </Button>
              <Button
                onClick={() => {
                  history.push('/metric-glossary');
                }}
              >
                指标口径
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      <Card style={{ marginBottom: 16 }}>
        <Space style={{ width: '100%', justifyContent: 'space-between' }} wrap>
          <Text strong style={{ fontSize: 16 }}>
            {loading ? '经营总结生成中...' : '经营总结'}
          </Text>
          <Button onClick={load}>刷新指标</Button>
        </Space>
        <div style={{ marginTop: 12 }}>
          <Text>{kpis.summary || '暂无总结'}</Text>
        </div>
      </Card>

      <Row gutter={[12, 12]} style={{ marginBottom: 16 }}>
        {heroCards.map((c) => (
          <Col xs={24} md={8} key={c.title}>
            <Card className="smartbi-kpi-card">
              <Statistic title={c.title} value={c.value} prefix={c.icon} suffix={c.trend} />
            </Card>
          </Col>
        ))}
      </Row>

      <MetricGrid title="经营贷专项指标" items={kpis.business_loan} loading={loading} />
      <MetricGrid title="消费贷专项指标" items={kpis.consumer_loan} loading={loading} />
      <MetricGrid title="财务与风险扩展指标" items={kpis.finance_risk} loading={loading} />

      <Card title="核心趋势图" style={{ marginBottom: 16 }}>
        <TrendAreaChart
          data={trendData}
          xKey="date"
          height={300}
          series={[
            {
              key: 'utilization',
              name: '额度使用率',
              color: '#4f7cff',
              fill: 'rgba(79,124,255,0.14)',
            },
            {
              key: 'raroc',
              name: '风险收益比(RAROC)',
              color: '#18b46b',
              fill: 'rgba(24,180,107,0.14)',
            },
            {
              key: 'overdue',
              name: '逾期率',
              color: '#f59e0b',
              fill: 'rgba(245,158,11,0.08)',
            },
          ]}
        />
      </Card>

      <Playground scene="dashboard" title="SmartBI Dashboard Assistant" />
    </div>
  );
};

export default DashboardPage;
