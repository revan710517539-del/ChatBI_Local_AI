import React, { useState, useMemo } from 'react';
import {
  Table,
  Typography,
  Card,
  Space,
  Button,
  Input,
  Tooltip,
  Statistic,
  Tag,
  message,
} from 'antd';
import {
  DownloadOutlined,
  CopyOutlined,
  SearchOutlined,
  TableOutlined,
  FieldNumberOutlined,
  FieldStringOutlined,
  FieldTimeOutlined,
} from '@ant-design/icons';
import Papa from 'papaparse';
import { saveAs } from 'file-saver';

const { Text } = Typography;

type QueryResultProps = {
  result: {
    columns: string[];
    data: any[];
    execution_time?: number;
    row_count: number;
    status: string;
    duration_ms?: number;
  };
  scroll?: { x?: string | number | true; y?: string | number };
};

const QueryResultTable: React.FC<QueryResultProps> = ({ result, scroll }) => {
  const [searchText, setSearchText] = useState('');
  const [searchColumn, setSearchColumn] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  // Calculate column statistics
  const columnStats = useMemo(() => {
    if (!result || !result.columns || !result.data) {
      return {};
    }
    const stats: Record<
      string,
      {
        type: string;
        nullCount: number;
        uniqueCount: number;
        sampleValues: any[];
      }
    > = {};

    result.columns.forEach((col) => {
      const values = result.data.map((row) => row[col]);
      const nonNullValues = values.filter((v) => v !== null && v !== undefined);
      const uniqueValues = new Set(nonNullValues);

      // Determine column type
      let type = 'string';
      if (nonNullValues.length > 0) {
        const firstValue = nonNullValues[0];
        if (typeof firstValue === 'number') {
          type = 'number';
        } else if (
          firstValue instanceof Date ||
          !isNaN(Date.parse(firstValue))
        ) {
          type = 'datetime';
        } else if (typeof firstValue === 'boolean') {
          type = 'boolean';
        }
      }

      stats[col] = {
        type,
        nullCount: values.length - nonNullValues.length,
        uniqueCount: uniqueValues.size,
        sampleValues: Array.from(uniqueValues).slice(0, 5),
      };
    });

    return stats;
  }, [result]);

  if (!result || !result.columns || !result.data) {
    return <div>No results found</div>;
  }

  const getColumnIcon = (columnName: string) => {
    const type = columnStats[columnName]?.type;
    switch (type) {
      case 'number':
        return <FieldNumberOutlined style={{ color: '#1890ff' }} />;
      case 'datetime':
        return <FieldTimeOutlined style={{ color: '#52c41a' }} />;
      default:
        return <FieldStringOutlined style={{ color: '#faad14' }} />;
    }
  };

  const columns = result.columns.map((column) => {
    const stats = columnStats[column];
    return {
      title: (
        <Space size="small">
          {getColumnIcon(column)}
          <Text strong>{column}</Text>
          {stats && (
            <Tooltip
              title={
                <div>
                  <div>Type: {stats.type}</div>
                  <div>Unique: {stats.uniqueCount}</div>
                  <div>Nulls: {stats.nullCount}</div>
                </div>
              }
            >
              <Tag color="blue" style={{ fontSize: 10 }}>
                {stats.type}
              </Tag>
            </Tooltip>
          )}
        </Space>
      ),
      dataIndex: column,
      key: column,
      ellipsis: {
        showTitle: false,
      },
      sorter: (a: any, b: any) => {
        if (typeof a[column] === 'string') {
          return (a[column] || '').localeCompare(b[column] || '');
        }
        return (a[column] || 0) - (b[column] || 0);
      },
      filterDropdown: ({
        setSelectedKeys,
        selectedKeys,
        confirm,
        clearFilters,
      }: any) => (
        <div style={{ padding: 8 }}>
          <Input
            placeholder={`Search ${column}`}
            value={selectedKeys[0]}
            onChange={(e) =>
              setSelectedKeys(e.target.value ? [e.target.value] : [])
            }
            onPressEnter={() => {
              confirm();
              setSearchText(selectedKeys[0]);
              setSearchColumn(column);
            }}
            style={{ marginBottom: 8, display: 'block' }}
          />
          <Space>
            <Button
              type="primary"
              onClick={() => {
                confirm();
                setSearchText(selectedKeys[0]);
                setSearchColumn(column);
              }}
              icon={<SearchOutlined />}
              size="small"
              style={{ width: 90 }}
            >
              Search
            </Button>
            <Button
              onClick={() => {
                clearFilters();
                setSearchText('');
                setSearchColumn(null);
              }}
              size="small"
              style={{ width: 90 }}
            >
              Reset
            </Button>
          </Space>
        </div>
      ),
      filterIcon: (filtered: boolean) => (
        <SearchOutlined style={{ color: filtered ? '#1890ff' : undefined }} />
      ),
      onFilter: (value: string, record: any) =>
        String(record[column])
          ?.toLowerCase()
          .includes((value as string).toLowerCase()) || false,
      render: (text: any) => {
        if (text === null || text === undefined)
          return <Text type="secondary">(null)</Text>;
        if (typeof text === 'object')
          return (
            <Tooltip title={JSON.stringify(text, null, 2)}>
              <Text code ellipsis>
                {JSON.stringify(text)}
              </Text>
            </Tooltip>
          );

        // Highlight search text
        if (searchText && searchColumn === column) {
          const index = String(text)
            .toLowerCase()
            .indexOf(searchText.toLowerCase());
          if (index >= 0) {
            const beforeText = text.substring(0, index);
            const matchedText = text.substring(
              index,
              index + searchText.length,
            );
            const afterText = text.substring(index + searchText.length);
            return (
              <Tooltip title={text}>
                <span>
                  {beforeText}
                  <span style={{ backgroundColor: '#ffc069' }}>
                    {matchedText}
                  </span>
                  {afterText}
                </span>
              </Tooltip>
            );
          }
        }

        return (
          <Tooltip title={text}>
            <Text ellipsis>{String(text)}</Text>
          </Tooltip>
        );
      },
    };
  });

  // Process data for the table
  const dataWithKeys = result.data.map((row, index) => {
    return {
      key: index,
      ...row,
    };
  });

  const handleDownloadCSV = () => {
    const csv = Papa.unparse({
      fields: result.columns,
      data: result.data,
    });
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    saveAs(blob, `query_result_${new Date().toISOString()}.csv`);
  };

  const handleCopyToClipboard = () => {
    const csv = Papa.unparse({
      fields: result.columns,
      data: result.data,
    });
    navigator.clipboard.writeText(csv).then(
      () => {
        message.success('Results copied to clipboard!');
      },
      (err) => {
        console.error('Failed to copy text: ', err);
        message.error('Failed to copy to clipboard');
      },
    );
  };

  const handleJSONDownload = () => {
    const json = JSON.stringify(result.data, null, 2);
    const blob = new Blob([json], { type: 'application/json;charset=utf-8;' });
    saveAs(blob, `query_result_${new Date().toISOString()}.json`);
  };

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        overflow: 'hidden',
      }}
    >
      {/* Statistics Summary */}
      <Card size="small" style={{ marginBottom: 8, flexShrink: 0 }}>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: 8,
          }}
        >
          <Space size="large" wrap>
            <Statistic
              title="Rows"
              value={result.row_count}
              prefix={<TableOutlined />}
              valueStyle={{ fontSize: 16 }}
            />
            <Statistic
              title="Columns"
              value={result.columns.length}
              prefix={<FieldStringOutlined />}
              valueStyle={{ fontSize: 16 }}
            />
            <Statistic
              title="Time"
              value={result.duration_ms || result.execution_time || 0}
              suffix="ms"
              precision={0}
              valueStyle={{ fontSize: 16 }}
            />
          </Space>
          <Space size="small">
            <Tooltip title="Copy to clipboard">
              <Button
                size="small"
                icon={<CopyOutlined />}
                onClick={handleCopyToClipboard}
              >
                Copy
              </Button>
            </Tooltip>
            <Tooltip title="Download as CSV">
              <Button
                size="small"
                icon={<DownloadOutlined />}
                onClick={handleDownloadCSV}
              >
                CSV
              </Button>
            </Tooltip>
            <Tooltip title="Download as JSON">
              <Button
                size="small"
                icon={<DownloadOutlined />}
                onClick={handleJSONDownload}
              >
                JSON
              </Button>
            </Tooltip>
          </Space>
        </div>
      </Card>

      {/* Results Table */}
      <div style={{ flex: 1, overflow: 'auto' }}>
        <Table
          columns={columns}
          dataSource={dataWithKeys}
          size="small"
          scroll={scroll || { x: 'max-content', y: 280 }}
          pagination={{
            current: currentPage,
            pageSize: pageSize,
            total: result.row_count,
            showSizeChanger: true,
            pageSizeOptions: ['10', '20', '50', '100', '200'],
            showTotal: (total, range) =>
              `${range[0]}-${range[1]} of ${total} rows`,
            onChange: (page, size) => {
              setCurrentPage(page);
              setPageSize(size || 10);
            },
            size: 'small',
          }}
        />
      </div>
    </div>
  );
};

export default QueryResultTable;
