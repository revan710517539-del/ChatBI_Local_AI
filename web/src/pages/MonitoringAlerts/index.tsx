import React, { useEffect, useState } from 'react';
import {
  Button,
  Card,
  Form,
  Input,
  InputNumber,
  Segmented,
  Space,
  Switch,
  Table,
  Tag,
  Typography,
  message,
} from 'antd';
import { monitoringService } from '@/services/monitoring';

const { Title, Text } = Typography;

const MonitoringAlertsPage: React.FC = () => {
  const [mode, setMode] = useState<'alerts' | 'email'>('alerts');
  const [alerts, setAlerts] = useState<any[]>([]);
  const [emailConfig, setEmailConfig] = useState<any>({});

  const load = async () => {
    try {
      const [rows, cfg] = await Promise.all([
        monitoringService.listAlerts(300),
        monitoringService.getEmailConfig(),
      ]);
      setAlerts(rows || []);
      setEmailConfig(cfg || {});
    } catch (e) {
      message.error(String(e));
    }
  };

  useEffect(() => {
    load();
  }, []);

  const runCheck = async () => {
    try {
      const result = await monitoringService.checkAlerts(true);
      message.success(`已执行监控检查，新增异常 ${result?.new_alerts?.length || 0} 条`);
      await load();
    } catch (e) {
      message.error(String(e));
    }
  };

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Card>
        <Space style={{ width: '100%', justifyContent: 'space-between' }}>
          <div>
            <Title level={4} style={{ margin: 0 }}>
              异常通知
            </Title>
            <Text type="secondary">
              异常触发后自动生成归因说明并支持邮件通知，运营人员可在此确认、补发、闭环处理。
            </Text>
          </div>
          <Segmented
            value={mode}
            onChange={(v) => setMode(v as any)}
            options={[
              { label: '异常列表', value: 'alerts' },
              { label: '邮箱配置', value: 'email' },
            ]}
          />
        </Space>
      </Card>

      {mode === 'alerts' && (
        <Card
          title="异常事件"
          extra={
            <Space>
              <Button onClick={load}>刷新</Button>
              <Button type="primary" onClick={runCheck}>
                执行监控检查并通知
              </Button>
            </Space>
          }
        >
          <Table
            rowKey="id"
            dataSource={alerts}
            pagination={{ pageSize: 8 }}
            columns={[
              { title: '时间', dataIndex: 'triggered_at', width: 210 },
              {
                title: '状态',
                dataIndex: 'status',
                width: 120,
                render: (v) => (
                  <Tag color={v === 'acknowledged' ? 'green' : v === 'notified' ? 'blue' : 'gold'}>
                    {v}
                  </Tag>
                ),
              },
              { title: '规则', dataIndex: 'rule_name', width: 180 },
              { title: '指标', dataIndex: 'metric_key', width: 180 },
              {
                title: '触发值',
                render: (_, row) => `${row.current_value} ${row.operator} ${row.threshold}`,
                width: 170,
              },
              {
                title: '归因摘要',
                render: (_, row) => row.diagnosis?.summary || '-',
              },
              {
                title: '通知结果',
                render: (_, row) => row.notification?.result || '-',
                width: 220,
              },
              {
                title: '操作',
                width: 220,
                render: (_, row) => (
                  <Space>
                    <Button
                      size="small"
                      onClick={async () => {
                        await monitoringService.ackAlert(row.id, '运营已确认处理');
                        await load();
                      }}
                    >
                      确认
                    </Button>
                    <Button
                      size="small"
                      onClick={async () => {
                        await monitoringService.resendAlertEmail(row.id);
                        message.success('补发邮件完成');
                        await load();
                      }}
                    >
                      补发邮件
                    </Button>
                  </Space>
                ),
              },
            ]}
          />
        </Card>
      )}

      {mode === 'email' && (
        <Card title="告警邮箱配置">
          <Form
            layout="vertical"
            key={JSON.stringify(emailConfig)}
            initialValues={emailConfig}
            onFinish={async (values) => {
              await monitoringService.updateEmailConfig(values);
              message.success('告警邮箱配置已保存');
              await load();
            }}
          >
            <Space wrap align="start">
              <Form.Item name="sender" label="发件人邮箱">
                <Input style={{ width: 260 }} />
              </Form.Item>
              <Form.Item name="recipient" label="告警收件人邮箱">
                <Input style={{ width: 260 }} />
              </Form.Item>
              <Form.Item name="smtp_host" label="SMTP Host">
                <Input style={{ width: 220 }} />
              </Form.Item>
              <Form.Item name="smtp_port" label="SMTP Port">
                <InputNumber style={{ width: 140 }} />
              </Form.Item>
              <Form.Item name="smtp_user" label="SMTP 用户">
                <Input style={{ width: 220 }} />
              </Form.Item>
              <Form.Item name="smtp_password" label="SMTP 密码">
                <Input.Password style={{ width: 220 }} />
              </Form.Item>
              <Form.Item name="use_tls" label="TLS" valuePropName="checked">
                <Switch />
              </Form.Item>
            </Space>
            <Button type="primary" htmlType="submit">
              保存配置
            </Button>
          </Form>
        </Card>
      )}
    </Space>
  );
};

export default MonitoringAlertsPage;
