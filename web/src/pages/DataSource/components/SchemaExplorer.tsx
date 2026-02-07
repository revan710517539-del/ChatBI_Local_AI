import React, { useState } from 'react';
import {
  Tree,
  Input,
  Typography,
  Empty,
  Spin,
  Tag,
  Space,
  Tooltip,
  Card,
  Statistic,
  Row,
  Col,
} from 'antd';
import {
  SearchOutlined,
  TableOutlined,
  KeyOutlined,
  FieldTimeOutlined,
  DatabaseOutlined,
  LinkOutlined,
  CheckCircleOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons';
import type { DataNode } from 'antd/es/tree';

const { Text } = Typography;

type SchemaExplorerProps = {
  schema: any;
  onTableClick?: (tableName: string) => void;
  onColumnClick?: (tableName: string, columnName: string) => void;
};

const SchemaExplorer: React.FC<SchemaExplorerProps> = ({
  schema,
  onTableClick,
  onColumnClick,
}) => {
  const [searchText, setSearchText] = useState('');
  const [expandedKeys, setExpandedKeys] = useState<string[]>([]);
  const [autoExpandParent, setAutoExpandParent] = useState<boolean>(true);

  if (!schema || !schema.tables) {
    return (
      <Empty
        description="No schema information available"
        image={Empty.PRESENTED_IMAGE_SIMPLE}
      />
    );
  }

  const generateTreeData = () => {
    const treeData: DataNode[] = [];

    // Sort tables alphabetically
    const sortedTables = [...schema.tables].sort((a, b) =>
      a.name.localeCompare(b.name),
    );

    sortedTables.forEach((table) => {
      const tableName = table.name;
      const tableKey = `table-${tableName}`;

      // Skip tables that don't match the search filter
      if (
        searchText &&
        !tableName.toLowerCase().includes(searchText.toLowerCase())
      ) {
        let hasMatchingColumn = false;
        table.columns.forEach((column: any) => {
          if (column.name.toLowerCase().includes(searchText.toLowerCase())) {
            hasMatchingColumn = true;
          }
        });
        if (!hasMatchingColumn) return;
      }

      // Sort columns: first primary keys, then foreign keys, then regular columns
      const sortedColumns = [...table.columns].sort((a: any, b: any) => {
        if (a.primary_key && !b.primary_key) return -1;
        if (!a.primary_key && b.primary_key) return 1;
        if (a.foreign_key && !b.foreign_key) return -1;
        if (!a.foreign_key && b.foreign_key) return 1;
        return a.name.localeCompare(b.name);
      });

      // Count column types
      const pkCount = table.columns.filter((c: any) => c.primary_key).length;
      const fkCount = table.columns.filter((c: any) => c.foreign_key).length;

      const children: DataNode[] = sortedColumns
        .map((column: any) => {
          if (
            searchText &&
            !column.name.toLowerCase().includes(searchText.toLowerCase()) &&
            !tableName.toLowerCase().includes(searchText.toLowerCase())
          ) {
            return null;
          }

          const dataType = column.type || 'unknown';
          const isPrimaryKey = column.primary_key;
          const isForeignKey = !!column.foreign_key;
          const isNullable = column.nullable;

          // Build column info tags
          const tags = [];
          if (isPrimaryKey)
            tags.push(
              <Tag color="gold" key="pk">
                PK
              </Tag>,
            );
          if (isForeignKey)
            tags.push(
              <Tag color="blue" key="fk">
                FK
              </Tag>,
            );
          if (!isNullable)
            tags.push(
              <Tag color="red" key="nn">
                NOT NULL
              </Tag>,
            );

          return {
            title: (
              <div
                onClick={(e) => {
                  e.stopPropagation();
                  if (onColumnClick) {
                    onColumnClick(tableName, column.name);
                  }
                }}
                className="cursor-pointer hover:bg-gray-100 py-1 px-2 rounded flex items-center justify-between"
                style={{ width: '100%' }}
              >
                <Space size="small" style={{ flex: 1 }}>
                  {isPrimaryKey ? (
                    <KeyOutlined style={{ color: '#faad14' }} />
                  ) : isForeignKey ? (
                    <LinkOutlined style={{ color: '#1677ff' }} />
                  ) : (
                    <FieldTimeOutlined style={{ color: '#52c41a' }} />
                  )}
                  <Text strong={isPrimaryKey}>{column.name}</Text>
                  <Text type="secondary" style={{ fontSize: 11 }}>
                    {dataType}
                  </Text>
                </Space>
                <Space size={2}>{tags}</Space>
              </div>
            ),
            key: `${tableKey}-${column.name}`,
            isLeaf: true,
          };
        })
        .filter(Boolean) as DataNode[];

      treeData.push({
        title: (
          <div
            onClick={(e) => {
              e.stopPropagation();
              if (onTableClick) {
                onTableClick(tableName);
              }
            }}
            className="cursor-pointer hover:bg-gray-100 py-1 px-2 rounded"
          >
            <Space size="small">
              <TableOutlined style={{ color: '#1890ff' }} />
              <Text strong>{tableName}</Text>
              <Text type="secondary" style={{ fontSize: 11 }}>
                ({table.columns.length} cols)
              </Text>
              {pkCount > 0 && (
                <Tooltip title={`${pkCount} Primary Key(s)`}>
                  <Tag color="gold" style={{ fontSize: 10 }}>
                    PK: {pkCount}
                  </Tag>
                </Tooltip>
              )}
              {fkCount > 0 && (
                <Tooltip title={`${fkCount} Foreign Key(s)`}>
                  <Tag color="blue" style={{ fontSize: 10 }}>
                    FK: {fkCount}
                  </Tag>
                </Tooltip>
              )}
            </Space>
          </div>
        ),
        key: tableKey,
        children,
      });
    });

    return treeData;
  };

  const treeData = generateTreeData();

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { value } = e.target;
    setSearchText(value);

    if (value) {
      // Find all table keys that have a match
      const matchedTableKeys = schema.tables
        .filter(
          (table: any) =>
            table.name.toLowerCase().includes(value.toLowerCase()) ||
            table.columns.some((column: any) =>
              column.name.toLowerCase().includes(value.toLowerCase()),
            ),
        )
        .map((table: any) => `table-${table.name}`);

      setExpandedKeys(matchedTableKeys);
      setAutoExpandParent(true);
    } else {
      setExpandedKeys([]);
      setAutoExpandParent(false);
    }
  };

  const handleExpand = (newExpandedKeys: string[]) => {
    setExpandedKeys(newExpandedKeys);
    setAutoExpandParent(false);
  };

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Schema Statistics */}
      {schema && schema.tables && (
        <Card size="small" style={{ marginBottom: 12, flexShrink: 0 }}>
          <Row gutter={8}>
            <Col span={12}>
              <Statistic
                title="Tables"
                value={schema.tables.length}
                prefix={<DatabaseOutlined />}
                valueStyle={{ fontSize: 14 }}
              />
            </Col>
            <Col span={12}>
              <Statistic
                title="Columns"
                value={schema.tables.reduce(
                  (acc: number, t: any) => acc + t.columns.length,
                  0,
                )}
                prefix={<InfoCircleOutlined />}
                valueStyle={{ fontSize: 14 }}
              />
            </Col>
          </Row>
        </Card>
      )}

      <div style={{ marginBottom: 12, paddingRight: 8, flexShrink: 0 }}>
        <Input
          placeholder="Search tables & columns"
          value={searchText}
          onChange={handleSearch}
          prefix={<SearchOutlined />}
          allowClear
          size="small"
        />
      </div>

      <div style={{ flex: 1, overflow: 'auto', paddingRight: 8 }}>
        {treeData.length > 0 ? (
          <Tree
            showLine={{ showLeafIcon: false }}
            showIcon={false}
            treeData={treeData}
            expandedKeys={expandedKeys}
            onExpand={handleExpand}
            autoExpandParent={autoExpandParent}
            defaultExpandAll={treeData.length < 10}
            blockNode
            height={500} // Virtual scroll hint but not strictly required if not using virtual prop
          />
        ) : (
          <Empty
            description={
              searchText
                ? 'No matches found'
                : 'No schema information available'
            }
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        )}
      </div>
    </div>
  );
};

export default SchemaExplorer;
