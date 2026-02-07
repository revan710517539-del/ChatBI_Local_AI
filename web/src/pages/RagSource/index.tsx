import React, { useEffect, useState } from 'react';
import {
  Alert,
  Button,
  Card,
  Popconfirm,
  Space,
  Table,
  Typography,
  Upload,
  message,
} from 'antd';
import { UploadOutlined } from '@ant-design/icons';
import { aiConfigService } from '@/services/aiConfig';

const { Title, Text } = Typography;

const RagSourcePage: React.FC = () => {
  const [docs, setDocs] = useState<any[]>([]);
  const [presets, setPresets] = useState<any>({});

  const load = async () => {
    const [docRes, presetRes] = await Promise.all([
      aiConfigService.listRagDocs(),
      aiConfigService.listDatasourcePresets(),
    ]);
    setDocs(docRes || []);
    setPresets(presetRes || {});
  };

  useEffect(() => {
    load().catch((e) => message.error(String(e)));
  }, []);

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Card>
        <Title level={4} style={{ marginTop: 0 }}>
          RagSource 知识库文件管理
        </Title>
        <Alert
          type="info"
          showIcon
          message="建议上传贷款产品说明、审批流程、贷后流程、风险策略文档"
          style={{ marginBottom: 16 }}
        />
        <Space>
          <Upload
            multiple
            showUploadList={false}
            customRequest={async (options) => {
              try {
                await aiConfigService.uploadRagDoc(options.file as File);
                message.success(`${(options.file as File).name} 上传成功`);
                await load();
                options.onSuccess?.({}, options.file as any);
              } catch (e) {
                message.error(String(e));
                options.onError?.(e as any);
              }
            }}
          >
            <Button icon={<UploadOutlined />}>上传知识库文件</Button>
          </Upload>
          <Button
            onClick={async () => {
              try {
                await aiConfigService.syncRagVectors();
                message.success('RAG向量索引已同步');
              } catch (e) {
                message.error(String(e));
              }
            }}
          >
            向量同步到Qdrant
          </Button>
        </Space>
        <Table
          rowKey="id"
          style={{ marginTop: 16 }}
          dataSource={docs}
          columns={[
            { title: '文件名', dataIndex: 'filename' },
            { title: '大小(bytes)', dataIndex: 'size' },
            { title: '更新时间', dataIndex: 'updated_at' },
            {
              title: '操作',
              render: (_, row) => (
                <Popconfirm
                  title="确认删除文件？"
                  onConfirm={async () => {
                    try {
                      await aiConfigService.deleteRagDoc(row.filename);
                      await load();
                    } catch (e) {
                      message.error(String(e));
                    }
                  }}
                >
                  <Button danger size="small">
                    删除
                  </Button>
                </Popconfirm>
              ),
            },
          ]}
        />
      </Card>

      <Card title="DataSource 预置检查">
        <Space direction="vertical" style={{ width: '100%' }}>
          <Space>
            <Button
              type="primary"
              onClick={async () => {
                try {
                  await aiConfigService.quickCreateMysqlDatasource();
                  message.success('MySQL数据源已一键创建');
                } catch (e) {
                  message.error(String(e));
                }
              }}
            >
              一键创建MySQL数据源
            </Button>
            <Button
              onClick={async () => {
                try {
                  await aiConfigService.quickCreateExcelDatasource();
                  message.success('Excel数据源已一键创建');
                } catch (e) {
                  message.error(String(e));
                }
              }}
            >
              一键创建Excel数据源
            </Button>
          </Space>
          <Text strong>本地 Excel/CSV 文件（data/Data 目录）</Text>
          <Table
            rowKey="path"
            pagination={false}
            dataSource={presets?.local_files || []}
            columns={[
              { title: '名称', dataIndex: 'name' },
              { title: '类型', dataIndex: 'type' },
              { title: '路径', dataIndex: 'path' },
              { title: '大小(bytes)', dataIndex: 'size' },
            ]}
          />

          <Text strong style={{ marginTop: 8 }}>
            本机 MySQL 预置
          </Text>
          <pre style={{ background: '#fafafa', padding: 12, borderRadius: 8 }}>
{JSON.stringify(presets?.mysql || {}, null, 2)}
          </pre>
        </Space>
      </Card>
    </Space>
  );
};

export default RagSourcePage;
