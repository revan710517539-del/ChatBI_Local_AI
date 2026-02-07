import React, { useEffect, useState } from 'react';
import {
  PageContainer,
  ProTable,
  ActionType,
} from '@ant-design/pro-components';
import {
  Button,
  Space,
  Tag,
  Popconfirm,
  message,
  Typography,
  Card,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  ConsoleSqlOutlined,
  QuestionCircleOutlined,
} from '@ant-design/icons';
import { history } from '@umijs/max';
import type { ProColumns } from '@ant-design/pro-components';
import { getDatasources, deleteDatasource } from '@/services/datasource';

const { Text, Link } = Typography;

type DataSourceItem = {
  id: string;
  name: string;
  description?: string;
  type: string;
  status: string;
  connection_info: any;
  created_at: string;
  updated_at: string;
};

const DataSourcePage: React.FC = () => {
  const actionRef = React.useRef<ActionType>();
  const [loading, setLoading] = useState<boolean>(false);

  const refreshTable = () => {
    if (actionRef.current) {
      actionRef.current.reload();
    }
  };

  const handleDelete = async (id: string) => {
    setLoading(true);
    try {
      await deleteDatasource(id);
      message.success('Data source deleted successfully');
      refreshTable();
    } catch (error) {
      console.error('Error deleting data source:', error);
      message.error('Failed to delete data source');
    } finally {
      setLoading(false);
    }
  };

  const handleQuery = (id: string) => {
    history.push(`/datasource/query/${id}`);
  };

  const handleEdit = (id: string) => {
    history.push(`/datasource/edit/${id}`);
  };

  const dbTypeColorMap: Record<string, string> = {
    postgres: 'green',
    mysql: 'blue',
    mssql: 'purple',
    clickhouse: 'orange',
    bigquery: 'geekblue',
    snowflake: 'cyan',
    trino: 'magenta',
    duckdb: 'gold',
    sqlite: 'gray',
  };

  const columns: ProColumns<DataSourceItem>[] = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      search: false,
      render: (_, record) => (
        <Space direction="vertical" size={0}>
          <Link onClick={() => handleQuery(record.id)} strong>
            {record.name}
          </Link>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {record.id}
          </Text>
        </Space>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      valueEnum: {
        active: { text: 'Active', status: 'Success' },
        inactive: { text: 'Inactive', status: 'Default' },
        error: { text: 'Error', status: 'Error' },
      },
    },
    {
      title: 'Type',
      dataIndex: 'type',
      key: 'type',
      width: 120,
      render: (_, record) => {
        const typeStr = String(record.type || '');
        return (
          <Tag color={dbTypeColorMap[typeStr] || 'default'}>
            {typeStr.toUpperCase()}
          </Tag>
        );
      },
      filters: true,
      onFilter: true,
      valueEnum: {
        postgres: { text: 'PostgreSQL', status: 'postgres' },
        mysql: { text: 'MySQL', status: 'mysql' },
        duckdb: { text: 'DuckDB', status: 'duckdb' },
        mssql: { text: 'SQL Server', status: 'mssql' },
        clickhouse: { text: 'ClickHouse', status: 'clickhouse' },
      },
    },
    {
      title: 'Description',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
      search: false,
    },
    {
      title: 'Created At',
      dataIndex: 'created_at',
      key: 'created_at',
      valueType: 'dateTime',
      search: false,
      sorter: (a, b) =>
        new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
      width: 160,
    },
    {
      title: 'Actions',
      key: 'actions',
      search: false,
      render: (_, record) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<ConsoleSqlOutlined />}
            onClick={() => handleQuery(record.id)}
          >
            Query
          </Button>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record.id)}
          >
            Edit
          </Button>
          <Popconfirm
            title="Delete data source?"
            description="Are you sure to delete this data source?"
            onConfirm={() => handleDelete(record.id)}
            okText="Yes"
            cancelText="No"
          >
            <Button
              type="text"
              danger
              size="small"
              icon={<DeleteOutlined />}
              loading={loading}
            />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <PageContainer
      header={{
        title: 'Data Sources',
        subTitle: 'Manage your database connections',
      }}
    >
      <ProTable<DataSourceItem>
        headerTitle="Data Source List"
        actionRef={actionRef}
        rowKey="id"
        search={{
          labelWidth: 'auto',
        }}
        toolBarRender={() => [
          <Button
            key="add"
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => history.push('/datasource/new')}
          >
            New
          </Button>,
        ]}
        request={async (params) => {
          try {
            const { current = 1, pageSize = 10, type, status } = params;
            const skip = (current - 1) * pageSize;

            const response = await getDatasources({
              skip: skip,
              limit: pageSize,
              // @ts-ignore
              type: type,
              // @ts-ignore
              status: status,
            });
            // Extract from StandardResponse wrapper: response.data contains DataSourceListResponse
            const listResponse = (response as any)?.data || response;
            const datasources = Array.isArray(listResponse)
              ? listResponse
              : listResponse?.items || [];

            const total = listResponse?.total || datasources.length;

            return {
              data: datasources,
              success: true,
              total: total,
            };
          } catch (error) {
            message.error('Failed to fetch data sources');
            return {
              data: [],
              success: false,
              total: 0,
            };
          }
        }}
        columns={columns}
        pagination={{
          defaultPageSize: 10,
          showSizeChanger: true,
        }}
        cardBordered
      />
    </PageContainer>
  );
};

export default DataSourcePage;
