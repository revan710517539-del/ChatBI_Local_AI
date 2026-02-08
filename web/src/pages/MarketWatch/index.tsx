import React, { useEffect, useMemo, useState } from 'react';
import {
  Button,
  Card,
  Col,
  Row,
  Segmented,
  Space,
  Statistic,
  Table,
  Tag,
  Typography,
  message,
} from 'antd';
import { marketWatchService } from '@/services/marketWatch';

const { Title, Text } = Typography;

const MarketWatchPage: React.FC = () => {
  const [tab, setTab] = useState<'news' | 'policy' | 'product'>('news');
  const [snapshot, setSnapshot] = useState<any>(null);
  const [analysis, setAnalysis] = useState<any>(null);

  const load = async (forceRefresh = false) => {
    try {
      const [snap, ana] = await Promise.all([
        marketWatchService.getSnapshot(10, forceRefresh),
        marketWatchService.getAnalysis(10, forceRefresh),
      ]);
      setSnapshot(snap);
      setAnalysis(ana);
    } catch (e) {
      message.error(String(e));
    }
  };

  useEffect(() => {
    load();
  }, []);

  const rows = useMemo(
    () => snapshot?.items?.[tab] || [],
    [snapshot, tab],
  );

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Card>
        <Space style={{ width: '100%', justifyContent: 'space-between' }}>
          <div>
            <Title level={4} style={{ margin: 0 }}>
              市场观察
            </Title>
            <Text type="secondary">
              抓取最新贷款新闻、政策与产品动态，形成市场脉搏分析并反哺策略建议。
            </Text>
          </div>
          <Space>
            <Text type="secondary">最近刷新：{snapshot?.fetched_at || '-'}</Text>
            <Button onClick={() => load(true)} type="primary">
              刷新市场情报
            </Button>
          </Space>
        </Space>
      </Card>

      <Row gutter={[16, 16]}>
        <Col xs={24} md={6}>
          <Card>
            <Statistic
              title="风险热度"
              value={analysis?.market_pulse?.risk_heat || 0}
            />
          </Card>
        </Col>
        <Col xs={24} md={6}>
          <Card>
            <Statistic
              title="增长热度"
              value={analysis?.market_pulse?.growth_heat || 0}
            />
          </Card>
        </Col>
        <Col xs={24} md={6}>
          <Card>
            <Statistic
              title="合规热度"
              value={analysis?.market_pulse?.compliance_heat || 0}
            />
          </Card>
        </Col>
        <Col xs={24} md={6}>
          <Card>
            <Statistic title="市场态势" value={analysis?.market_pulse?.stance || '-'} />
          </Card>
        </Col>
      </Row>

      <Card title="市场建议">
        <ul style={{ margin: 0, paddingLeft: 18, lineHeight: 1.9 }}>
          {(analysis?.recommendations || []).map((x: string, i: number) => (
            <li key={`${x}-${i}`}>{x}</li>
          ))}
        </ul>
      </Card>

      <Card
        title="市场信息流"
        extra={
          <Segmented
            value={tab}
            onChange={(v) => setTab(v as any)}
            options={[
              { label: '贷款新闻', value: 'news' },
              { label: '政策动态', value: 'policy' },
              { label: '产品动态', value: 'product' },
            ]}
          />
        }
      >
        <Table
          rowKey={(r) => `${r.title}-${r.link}`}
          dataSource={rows}
          columns={[
            {
              title: '标题',
              dataIndex: 'title',
              render: (v, row) =>
                row.link ? (
                  <a href={row.link} target="_blank" rel="noreferrer">
                    {v}
                  </a>
                ) : (
                  v
                ),
            },
            { title: '摘要', dataIndex: 'summary' },
            {
              title: '来源',
              dataIndex: 'source',
              width: 180,
              render: (v) => <Tag>{v}</Tag>,
            },
            { title: '发布时间', dataIndex: 'published_at', width: 220 },
          ]}
        />
      </Card>
    </Space>
  );
};

export default MarketWatchPage;
