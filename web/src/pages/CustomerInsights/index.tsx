import React, { useEffect, useState } from 'react';
import {
  Card,
  Col,
  Descriptions,
  Row,
  Select,
  Space,
  Statistic,
  Table,
  Tag,
  Typography,
  message,
} from 'antd';
import { customerInsightService } from '@/services/customerInsight';

const { Title, Text } = Typography;

const CustomerInsightsPage: React.FC = () => {
  const [customers, setCustomers] = useState<any[]>([]);
  const [segments, setSegments] = useState<any[]>([]);
  const [selectedCustomer, setSelectedCustomer] = useState<string>();
  const [selectedSegment, setSelectedSegment] = useState<string>();
  const [customerDetail, setCustomerDetail] = useState<any>(null);
  const [segmentDetail, setSegmentDetail] = useState<any>(null);

  const load = async () => {
    try {
      const [cs, ss] = await Promise.all([
        customerInsightService.listCustomers(),
        customerInsightService.listSegments(),
      ]);
      setCustomers(cs || []);
      setSegments(ss || []);
      const c0 = cs?.[0]?.customer_id;
      const s0 = ss?.[0]?.segment_id;
      if (c0) {
        setSelectedCustomer(c0);
        setCustomerDetail(await customerInsightService.getCustomer(c0));
      }
      if (s0) {
        setSelectedSegment(s0);
        setSegmentDetail(await customerInsightService.getSegment(s0));
      }
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
        <Title level={4} style={{ margin: 0 }}>
          客户洞察
        </Title>
        <Text type="secondary">
          支持单客户与客群画像，聚焦消费贷/经营贷运营过程中的客群理解、风险识别与策略建议。
        </Text>
      </Card>

      <Row gutter={[16, 16]}>
        <Col xs={24} xl={12}>
          <Card title="单客户洞察">
            <Space direction="vertical" style={{ width: '100%' }}>
              <Select
                value={selectedCustomer}
                style={{ width: 320 }}
                options={customers.map((x) => ({
                  label: `${x.customer_id} - ${x.name}`,
                  value: x.customer_id,
                }))}
                onChange={async (v) => {
                  setSelectedCustomer(v);
                  setCustomerDetail(await customerInsightService.getCustomer(v));
                }}
              />
              {customerDetail && (
                <>
                  <Descriptions bordered size="small" column={2}>
                    <Descriptions.Item label="客户名">{customerDetail.name}</Descriptions.Item>
                    <Descriptions.Item label="贷款类型">{customerDetail.loan_type}</Descriptions.Item>
                    <Descriptions.Item label="城市">{customerDetail.city}</Descriptions.Item>
                    <Descriptions.Item label="行业">{customerDetail.industry}</Descriptions.Item>
                    <Descriptions.Item label="风险等级">
                      <Tag color={customerDetail.risk_level.includes('高') ? 'red' : 'gold'}>
                        {customerDetail.risk_level}
                      </Tag>
                    </Descriptions.Item>
                    <Descriptions.Item label="迁徙标签">{customerDetail.migration_tag}</Descriptions.Item>
                  </Descriptions>
                  <Row gutter={12}>
                    <Col span={8}>
                      <Statistic title="授信额度" value={customerDetail.credit_limit} />
                    </Col>
                    <Col span={8}>
                      <Statistic title="已用额度" value={customerDetail.used_limit} />
                    </Col>
                    <Col span={8}>
                      <Statistic
                        title="额度使用率"
                        value={customerDetail.utilization_rate}
                        precision={2}
                        suffix=""
                      />
                    </Col>
                  </Row>
                  <Card size="small" title="下一最佳动作">
                    {customerDetail.next_best_action}
                  </Card>
                </>
              )}
            </Space>
          </Card>
        </Col>

        <Col xs={24} xl={12}>
          <Card title="客群洞察">
            <Space direction="vertical" style={{ width: '100%' }}>
              <Select
                value={selectedSegment}
                style={{ width: 320 }}
                options={segments.map((x) => ({ label: x.name, value: x.segment_id }))}
                onChange={async (v) => {
                  setSelectedSegment(v);
                  setSegmentDetail(await customerInsightService.getSegment(v));
                }}
              />

              {segmentDetail && (
                <>
                  <Row gutter={12}>
                    <Col span={8}>
                      <Statistic title="客群规模" value={segmentDetail.size} />
                    </Col>
                    <Col span={8}>
                      <Statistic title="平均额度" value={segmentDetail.avg_credit_limit} />
                    </Col>
                    <Col span={8}>
                      <Statistic
                        title="平均额度使用率"
                        value={segmentDetail.avg_utilization_rate}
                        precision={3}
                      />
                    </Col>
                  </Row>
                  <Descriptions bordered size="small" column={1}>
                    <Descriptions.Item label="逾期率">
                      {segmentDetail.overdue_rate}
                    </Descriptions.Item>
                    <Descriptions.Item label="RAROC">{segmentDetail.raroc}</Descriptions.Item>
                    <Descriptions.Item label="洞察结论">
                      {segmentDetail.insight}
                    </Descriptions.Item>
                  </Descriptions>
                </>
              )}

              <Table
                rowKey="segment_id"
                size="small"
                dataSource={segments}
                columns={[
                  { title: '客群', dataIndex: 'name' },
                  { title: '类型', dataIndex: 'loan_type' },
                  { title: '逾期率', dataIndex: 'overdue_rate' },
                  { title: 'RAROC', dataIndex: 'raroc' },
                ]}
              />
            </Space>
          </Card>
        </Col>
      </Row>
    </Space>
  );
};

export default CustomerInsightsPage;
