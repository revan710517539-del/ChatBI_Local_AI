import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { PageContainer, ProCard } from '@ant-design/pro-components';
import {
  Button,
  Space,
  Typography,
  Spin,
  message,
  Tooltip,
  notification,
  Tabs,
  Empty,
  Drawer,
  Badge,
  Divider,
  Tag,
} from 'antd';
import {
  SaveOutlined,
  HistoryOutlined,
  DatabaseOutlined,
  TableOutlined,
  DeleteOutlined,
  StarOutlined,
  BarChartOutlined,
  ArrowLeftOutlined,
} from '@ant-design/icons';
import { useSize } from 'ahooks';
import CodeEditor from './components/CodeEditor';
import QueryResultTable from './components/QueryResultTable';
import SchemaExplorer from './components/SchemaExplorer';
import SaveQueryModal from './components/SaveQueryModal';
import QueryVisualization from './components/QueryVisualization';
import {
  getDatasource,
  getDatabaseSchema,
  executeQuery,
} from '@/services/datasource';
import { useTheme } from 'antd-style';

const { Text, Title, Paragraph } = Typography;
const { TabPane } = Tabs;

const QueryPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const theme = useTheme();
  const containerRef = useRef<HTMLDivElement>(null);
  const size = useSize(containerRef);

  // Calculate responsive values based on container size
  const schemaWidth = size?.width && size.width < 1200 ? 240 : 300;
  const editorHeight = size?.height
    ? Math.max(200, Math.min(400, size.height * 0.35))
    : 300;

  const [datasource, setDatasource] = useState<any>(null);
  const [schema, setSchema] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [executing, setExecuting] = useState<boolean>(false);
  const [sqlQuery, setSqlQuery] = useState<string>('SELECT * FROM ');
  const [queryResult, setQueryResult] = useState<any>(null);
  const [resultsView, setResultsView] = useState<'table' | 'chart'>('table');
  const [saveModalVisible, setSaveModalVisible] = useState<boolean>(false);
  const [historyDrawerVisible, setHistoryDrawerVisible] =
    useState<boolean>(false);

  // Persistence keys
  const HISTORY_KEY = `query_history_${id}`;
  const SAVED_QUERIES_KEY = `saved_queries_${id}`;

  const [queryHistory, setQueryHistory] = useState<any[]>(() => {
    const saved = id ? localStorage.getItem(HISTORY_KEY) : null;
    return saved ? JSON.parse(saved) : [];
  });

  const [savedQueries, setSavedQueries] = useState<any[]>(() => {
    const saved = id ? localStorage.getItem(SAVED_QUERIES_KEY) : null;
    return saved ? JSON.parse(saved) : [];
  });

  useEffect(() => {
    if (id) {
      localStorage.setItem(HISTORY_KEY, JSON.stringify(queryHistory));
    }
  }, [queryHistory, id]);

  useEffect(() => {
    if (id) {
      localStorage.setItem(SAVED_QUERIES_KEY, JSON.stringify(savedQueries));
    }
  }, [savedQueries, id]);

  // Fetch datasource details when the component mounts
  useEffect(() => {
    if (!id) return;

    const fetchDatasource = async () => {
      setLoading(true);
      try {
        const data = await getDatasource(id);
        setDatasource(data);
        fetchSchema();
      } catch (error) {
        console.error('Error fetching datasource:', error);
        notification.error({
          message: 'Failed to fetch datasource details',
          description:
            error instanceof Error
              ? error.message
              : 'An unknown error occurred',
        });
      } finally {
        setLoading(false);
      }
    };

    fetchDatasource();
  }, [id]);

  const fetchSchema = async () => {
    if (!id) return;
    try {
      const schemaData = await getDatabaseSchema(id);
      setSchema(schemaData);
    } catch (error) {
      console.error('Error fetching schema:', error);
    }
  };

  const handleTableClick = (tableName: string) => {
    setSqlQuery(`SELECT * FROM ${tableName} LIMIT 100`);
  };

  const handleColumnClick = (tableName: string, columnName: string) => {
    setSqlQuery((prev) => {
      const newText = `${tableName}.${columnName}`;
      if (prev.trim().endsWith('FROM') || prev.trim().endsWith('SELECT')) {
        return `${prev} ${newText}`;
      } else {
        return `${prev}, ${newText}`;
      }
    });
  };

  const handleSaveQuery = (name: string, description: string) => {
    const newQuery = {
      id: Date.now(),
      name,
      description,
      query: sqlQuery,
      savedAt: new Date().toISOString(),
    };
    setSavedQueries((prev) => [newQuery, ...prev]);
    message.success('Query saved');
    setSaveModalVisible(false);
  };

  const handleLoadQuery = (query: string) => {
    setSqlQuery(query);
    setHistoryDrawerVisible(false);
  };

  const handleDeleteSavedQuery = (queryId: number) => {
    setSavedQueries((prev) => prev.filter((q) => q.id !== queryId));
    message.success('Saved query deleted');
  };

  const handleExecuteQuery = async () => {
    if (!id) return;
    if (!sqlQuery.trim()) {
      message.error('SQL query cannot be empty');
      return;
    }

    setExecuting(true);
    try {
      const result = (await executeQuery(id, sqlQuery, 30, 1000)) as any;

      // Transform backend QueryResult to what UI components expect
      const formattedResult = {
        columns:
          result.columns?.map((c: any) =>
            typeof c === 'string' ? c : c.name,
          ) || [],
        data: result.rows || [],
        row_count: result.row_count || 0,
        duration_ms: result.duration_ms || 0,
        status: result.status || 'success',
      };

      setQueryResult(formattedResult);

      if (formattedResult) {
        const historyItem = {
          timestamp: new Date().toISOString(),
          query: sqlQuery,
          rows: formattedResult.row_count,
          execution_time: formattedResult.duration_ms,
          status: formattedResult.status,
        };
        setQueryHistory((prev) => [historyItem, ...prev].slice(0, 50));
      }
    } catch (error) {
      console.error('Error executing query:', error);
      notification.error({
        message: 'Query execution failed',
        description:
          error instanceof Error ? error.message : 'An unknown error occurred',
      });
    } finally {
      setExecuting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <Spin size="large" tip="Loading datasource..." />
      </div>
    );
  }

  return (
    <PageContainer
      header={{
        title: (
          <Space>
            <Button
              type="text"
              icon={<ArrowLeftOutlined />}
              onClick={() => navigate('/datasources')}
            />
            <DatabaseOutlined />
            <span>{datasource?.name || 'Datasource'}</span>
            <Text type="secondary" style={{ fontSize: 14 }}>
              Query Editor
            </Text>
          </Space>
        ),
        extra: [
          <Badge count={queryHistory.length} size="small" key="history">
            <Button
              icon={<HistoryOutlined />}
              onClick={() => setHistoryDrawerVisible(true)}
            >
              History
            </Button>
          </Badge>,
          <Button
            key="save"
            icon={<SaveOutlined />}
            onClick={() => setSaveModalVisible(true)}
            disabled={!sqlQuery.trim()}
          >
            Save
          </Button>,
        ],
      }}
    >
      <div
        ref={containerRef}
        style={{ height: 'calc(100vh - 140px)', minHeight: 600, width: '100%' }}
      >
        <ProCard
          ghost
          gutter={[16, 16]}
          style={{
            height: '100%',
            width: '100%',
          }}
        >
          <ProCard
            colSpan={schemaWidth}
            bordered
            headerBordered
            direction="column"
            title={
              <Space>
                <DatabaseOutlined /> Schema
              </Space>
            }
            collapsible
            bodyStyle={{ padding: 12, height: '100%', overflow: 'hidden' }}
          >
            <div style={{ height: '100%' }}>
              <SchemaExplorer
                schema={schema}
                onTableClick={handleTableClick}
                onColumnClick={handleColumnClick}
              />
            </div>
          </ProCard>

          <ProCard
            split="horizontal"
            bordered
            headerBordered
            ghost
            style={{ height: '100%', flex: 1 }}
          >
            <ProCard
              bordered
              bodyStyle={{ padding: 0, height: '100%' }}
              style={{ height: editorHeight }}
            >
              <CodeEditor
                value={sqlQuery}
                onChange={setSqlQuery}
                onExecute={handleExecuteQuery}
                schema={schema}
                height={editorHeight}
              />
            </ProCard>

            <ProCard
              bordered
              bodyStyle={{
                padding: 0,
                flex: 1,
                display: 'flex',
                flexDirection: 'column',
                overflow: 'hidden',
                height: '100%',
                maxWidth: '100%',
              }}
              style={{ overflow: 'hidden', maxWidth: '100%' }}
            >
              <Tabs
                activeKey={resultsView}
                onChange={(key) => setResultsView(key as 'table' | 'chart')}
                tabBarStyle={{ margin: '0 16px' }}
                tabBarExtraContent={
                  queryResult && (
                    <Space style={{ marginRight: 16 }}>
                      <Tag color="green">{queryResult.row_count} rows</Tag>
                      <Tag>{queryResult.duration_ms.toFixed(0)}ms</Tag>
                    </Space>
                  )
                }
                style={{
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                }}
                items={[
                  {
                    key: 'table',
                    label: (
                      <span>
                        <TableOutlined /> Results
                      </span>
                    ),
                    children: (
                      <div
                        style={{
                          padding: 16,
                          height: '100%',
                          overflow: 'auto',
                          display: 'flex',
                          flexDirection: 'column',
                          maxWidth: '100%',
                        }}
                      >
                        {executing ? (
                          <div className="flex justify-center items-center h-full">
                            <Spin tip="Executing query..." />
                          </div>
                        ) : queryResult ? (
                          <div
                            style={{
                              flex: 1,
                              overflow: 'auto',
                              maxWidth: '100%',
                            }}
                          >
                            <QueryResultTable
                              result={queryResult}
                              scroll={{ x: 'max-content', y: 300 }}
                            />
                          </div>
                        ) : (
                          <Empty description="Run a query to see results" />
                        )}
                      </div>
                    ),
                  },
                  {
                    key: 'chart',
                    label: (
                      <span>
                        <BarChartOutlined /> Visualization
                      </span>
                    ),
                    children: (
                      <div
                        style={{
                          padding: 16,
                          height: '100%',
                          overflow: 'auto',
                        }}
                      >
                        {executing ? (
                          <div className="flex justify-center items-center h-full">
                            <Spin tip="Preparing chart..." />
                          </div>
                        ) : queryResult ? (
                          <QueryVisualization result={queryResult} />
                        ) : (
                          <Empty description="Run a query to see visualization" />
                        )}
                      </div>
                    ),
                  },
                ]}
              />
            </ProCard>
          </ProCard>
        </ProCard>

        {/* History and Saved Queries Drawer */}
        <Drawer
          title="Query History & Saved Queries"
          placement="right"
          width={500}
          onClose={() => setHistoryDrawerVisible(false)}
          open={historyDrawerVisible}
        >
          <Tabs defaultActiveKey="history">
            <TabPane
              tab={
                <span>
                  <HistoryOutlined /> Recent
                </span>
              }
              key="history"
            >
              <div style={{ padding: '0 4px' }}>
                {queryHistory.length === 0 ? (
                  <Empty description="No query history" />
                ) : (
                  queryHistory.map((item, index) => (
                    <ProCard
                      key={`${item.timestamp}-${index}`}
                      style={{ marginBottom: 12 }}
                      bordered
                      hoverable
                      bodyStyle={{ padding: 12 }}
                      onClick={() => handleLoadQuery(item.query)}
                    >
                      <Text
                        code
                        style={{
                          fontSize: 12,
                          display: 'block',
                          maxHeight: 80,
                          overflow: 'hidden',
                          whiteSpace: 'pre-wrap',
                        }}
                      >
                        {item.query}
                      </Text>
                      <div
                        style={{
                          marginTop: 8,
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                        }}
                      >
                        <Space size="small">
                          <Tag size="small">{item.rows} rows</Tag>
                          <Text type="secondary" style={{ fontSize: 11 }}>
                            {item.execution_time?.toFixed(0)}ms
                          </Text>
                        </Space>
                        <Text type="secondary" style={{ fontSize: 11 }}>
                          {new Date(item.timestamp).toLocaleString()}
                        </Text>
                      </div>
                    </ProCard>
                  ))
                )}
              </div>
            </TabPane>
            <TabPane
              tab={
                <span>
                  <StarOutlined /> Saved
                </span>
              }
              key="saved"
            >
              <div style={{ padding: '0 4px' }}>
                {savedQueries.length === 0 ? (
                  <Empty description="No saved queries" />
                ) : (
                  savedQueries.map((item) => (
                    <ProCard
                      key={item.id}
                      title={item.name}
                      style={{ marginBottom: 12 }}
                      bordered
                      extra={
                        <Space>
                          <Button
                            type="text"
                            size="small"
                            icon={<DeleteOutlined />}
                            danger
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDeleteSavedQuery(item.id);
                            }}
                          />
                        </Space>
                      }
                      headerBordered
                      bodyStyle={{ padding: 12 }}
                      hoverable
                      onClick={() => handleLoadQuery(item.query)}
                    >
                      {item.description && (
                        <Paragraph
                          type="secondary"
                          style={{ fontSize: 12, marginBottom: 8 }}
                        >
                          {item.description}
                        </Paragraph>
                      )}
                      <Text
                        code
                        style={{
                          fontSize: 11,
                          display: 'block',
                          whiteSpace: 'pre-wrap',
                        }}
                      >
                        {item.query.length > 200
                          ? `${item.query.substring(0, 200)}...`
                          : item.query}
                      </Text>
                    </ProCard>
                  ))
                )}
              </div>
            </TabPane>
          </Tabs>
        </Drawer>

        <SaveQueryModal
          visible={saveModalVisible}
          query={sqlQuery}
          onClose={() => setSaveModalVisible(false)}
          onSave={handleSaveQuery}
        />
      </div>
    </PageContainer>
  );
};

export default QueryPage;
