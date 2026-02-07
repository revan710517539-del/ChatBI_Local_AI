import { Card, Space, Button, Typography, Radio } from 'antd';
import React, { useState } from 'react';

const { Text } = Typography;

export interface ClarificationOption {
  label: string;
  value: string;
  description?: string;
}

interface ClarificationWidgetProps {
  question: string;
  options?: ClarificationOption[];
  onSelect: (option: string) => void;
}

export const ClarificationWidget: React.FC<ClarificationWidgetProps> = ({
  question,
  options = [],
  onSelect,
}) => {
  const [selected, setSelected] = useState<string>('');

  const handleConfirm = () => {
    if (selected) {
      onSelect(selected);
    }
  };

  return (
    <Card
      size="small"
      style={{
        background: '#fffbe6',
        borderColor: '#ffe58f',
        marginTop: 8,
        maxWidth: 600,
      }}
      styles={{ body: { padding: '12px' } }}
    >
      <Space direction="vertical" style={{ width: '100%' }} size="middle">
        <Space>
          <span role="img" aria-label="thinking">
            🤔
          </span>
          <Text strong>I need a bit more detail:</Text>
        </Space>

        <Text>{question}</Text>

        {Array.isArray(options) && options.length > 0 ? (
          <Radio.Group
            onChange={(e) => setSelected(e.target.value)}
            value={selected}
          >
            <Space direction="vertical">
              {options.map((opt) => (
                <Radio key={opt.value} value={opt.value}>
                  <Space direction="vertical" size={0}>
                    <Text>{opt.label}</Text>
                    {opt.description && (
                      <Text type="secondary" style={{ fontSize: '12px' }}>
                        {opt.description}
                      </Text>
                    )}
                  </Space>
                </Radio>
              ))}
            </Space>
          </Radio.Group>
        ) : (
          <Text type="secondary" italic>
            Please provide more details in the chat below.
          </Text>
        )}

        {Array.isArray(options) && options.length > 0 && (
          <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
            <Button
              type="primary"
              size="small"
              disabled={!selected}
              onClick={handleConfirm}
            >
              Confirm
            </Button>
          </div>
        )}
      </Space>
    </Card>
  );
};
