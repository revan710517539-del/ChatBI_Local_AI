import React, { useEffect, useState } from 'react';
import {
  Button,
  Card,
  Input,
  Select,
  Space,
  Switch,
  Table,
  Tag,
  Typography,
  message,
} from 'antd';
import { memoryService } from '@/services/memory';

const { Title, Text } = Typography;

const MemoryCenterPage: React.FC = () => {
  const [settings, setSettings] = useState<Record<string, any>>({});
  const [events, setEvents] = useState<any[]>([]);
  const [keyword, setKeyword] = useState('');
  const [scene, setScene] = useState<string | undefined>();
  const [eventType, setEventType] = useState<string | undefined>();

  const load = async () => {
    try {
      const [s, e] = await Promise.all([
        memoryService.getSettings(),
        memoryService.listEvents({ limit: 200, scene, event_type: eventType }),
      ]);
      setSettings(s || {});
      setEvents(e || []);
    } catch (e) {
      message.error(String(e));
    }
  };

  useEffect(() => {
    load();
  }, [scene, eventType]);

  const filtered = (events || []).filter((x) => {
    if (!keyword) return true;
    const text = `${x.user_text || ''} ${x.voice_text || ''} ${x.result_summary || ''} ${x.sql || ''}`;
    return text.toLowerCase().includes(keyword.toLowerCase());
  });

  const saveSettings = async (patch: Record<string, any>) => {
    try {
      const next = await memoryService.updateSettings(patch);
      setSettings(next || {});
      message.success('记忆配置已更新');
    } catch (e) {
      message.error(String(e));
    }
  };

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Card>
        <Title level={4} style={{ marginTop: 0 }}>记忆中心（参考 OpenClaw：交互记忆 + 语义检索 + 近期偏好）</Title>
        <Text type="secondary">
          该模块记录用户文字/语音/文件/图片与指标操作轨迹，用于补充模型对贷款业务背景与口径偏好的理解。
        </Text>
      </Card>

      <Card title="记忆配置">
        <Space direction="vertical" style={{ width: '100%' }}>
          <Space>
            <Text style={{ width: 180 }}>启用记忆</Text>
            <Switch checked={!!settings.enabled} onChange={(v) => saveSettings({ enabled: v })} />
          </Space>
          <Space>
            <Text style={{ width: 180 }}>记录文字输入</Text>
            <Switch checked={!!settings.capture_text} onChange={(v) => saveSettings({ capture_text: v })} />
            <Text style={{ width: 180 }}>记录语音输入</Text>
            <Switch checked={!!settings.capture_voice} onChange={(v) => saveSettings({ capture_voice: v })} />
          </Space>
          <Space>
            <Text style={{ width: 180 }}>记录文件上传</Text>
            <Switch checked={!!settings.capture_files} onChange={(v) => saveSettings({ capture_files: v })} />
            <Text style={{ width: 180 }}>记录图片上传</Text>
            <Switch checked={!!settings.capture_images} onChange={(v) => saveSettings({ capture_images: v })} />
          </Space>
          <Space>
            <Text style={{ width: 180 }}>记录指标操作</Text>
            <Switch
              checked={!!settings.capture_metric_actions}
              onChange={(v) => saveSettings({ capture_metric_actions: v })}
            />
            <Text style={{ width: 180 }}>语义增强检索</Text>
            <Switch
              checked={!!settings.semantic_enhance}
              onChange={(v) => saveSettings({ semantic_enhance: v })}
            />
          </Space>
        </Space>
      </Card>

      <Card title="记忆事件检索">
        <Space style={{ width: '100%', justifyContent: 'space-between', marginBottom: 12 }} wrap>
          <Space>
            <Input
              placeholder="搜索记忆内容"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              style={{ width: 280 }}
            />
            <Select
              allowClear
              placeholder="场景"
              style={{ width: 150 }}
              value={scene}
              onChange={setScene}
              options={[
                { label: 'DataDiscuss', value: 'data_discuss' },
                { label: 'Dashboard', value: 'dashboard' },
              ]}
            />
            <Select
              allowClear
              placeholder="事件类型"
              style={{ width: 160 }}
              value={eventType}
              onChange={setEventType}
              options={[
                { label: '文字输入', value: 'text_input' },
                { label: '语音输入', value: 'voice_input' },
                { label: '文件上传', value: 'file_upload' },
                { label: '图片上传', value: 'image_upload' },
                { label: '指标操作', value: 'metric_action' },
                { label: '分析结果', value: 'analysis_result' },
              ]}
            />
          </Space>
          <Button onClick={load}>刷新</Button>
        </Space>

        <Table
          rowKey="id"
          dataSource={filtered}
          columns={[
            { title: '时间', dataIndex: 'ts', width: 220 },
            {
              title: '类型',
              dataIndex: 'event_type',
              width: 130,
              render: (v) => <Tag>{v}</Tag>,
            },
            { title: '场景', dataIndex: 'scene', width: 120 },
            {
              title: '内容',
              render: (_, row) =>
                row.user_text || row.voice_text || row.result_summary || row.sql || '-',
            },
          ]}
        />
      </Card>
    </Space>
  );
};

export default MemoryCenterPage;
