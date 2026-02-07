import React from 'react';
import { Card, Typography, List, Space } from 'antd';
import { BulbOutlined } from '@ant-design/icons';

const { Paragraph } = Typography;

export interface InsightSummary {
  summary: string;
  key_points: string[];
}

interface InsightWidgetProps {
  data: InsightSummary;
  loading?: boolean;
}

const InsightWidget: React.FC<InsightWidgetProps> = ({ data, loading }) => {
  if (!data) return null;

  return (
    <Card
      size="small"
      title={
        <Space>
          <BulbOutlined style={{ color: '#faad14' }} /> Data Insights
        </Space>
      }
      loading={loading}
      style={{
        marginTop: 16,
        backgroundColor: '#fffbe6',
        borderColor: '#ffe58f',
      }}
      styles={{ body: { padding: '12px 16px' } }}
    >
      <Paragraph style={{ marginBottom: 8 }}>{data.summary}</Paragraph>
      <List
        size="small"
        split={false}
        dataSource={data.key_points}
        renderItem={(item) => (
          <List.Item style={{ padding: '2px 0' }}>
            <Typography.Text>• {item}</Typography.Text>
          </List.Item>
        )}
      />
    </Card>
  );
};

export default InsightWidget;
