import React, { useState } from 'react';
import {
  Form,
  Input,
  Button,
  Select,
  Card,
  Space,
  message,
  Spin,
  Alert,
  InputNumber,
  Divider,
} from 'antd';
import { ArrowLeftOutlined, CheckCircleOutlined } from '@ant-design/icons';
import { useNavigate } from '@umijs/max';
import {
  createDatasource,
  testConnection,
  updateDatasource,
} from '@/services/datasource';

const { Option } = Select;
const { TextArea } = Input;

export type DataSourceFormProps = {
  initialValues?: any;
  id?: string;
  isEdit?: boolean;
};

const DataSourceForm: React.FC<DataSourceFormProps> = ({
  initialValues,
  id,
  isEdit = false,
}) => {
  const [form] = Form.useForm();
  const navigate = useNavigate();
  const [submitting, setSubmitting] = useState(false);
  const [testing, setTesting] = useState(false);
  const [dbType, setDbType] = useState(initialValues?.type || 'postgres');
  const [testResult, setTestResult] = useState<{
    success: boolean;
    message: string;
  } | null>(null);

  const handleTypeChange = (value: string) => {
    setDbType(value);
    setTestResult(null);
  };

  const handleTestConnection = async () => {
    try {
      await form.validateFields();
      const values = form.getFieldsValue();

      setTesting(true);
      const testData = {
        type: values.type,
        connection_info: values.connection_info,
        datasource_id: id,
      };
      // @ts-ignore
      const result = await testConnection(testData);

      setTestResult({
        success: result.status === 'success',
        message: result.message,
      });

      if (result.status === 'success') {
        message.success('Connection successful!');
      } else {
        message.error(`Connection failed: ${result.message}`);
      }
    } catch (error) {
      console.error('Validation failed:', error);
    } finally {
      setTesting(false);
    }
  };

  const handleSubmit = async (values: any) => {
    setSubmitting(true);
    try {
      if (isEdit && id) {
        await updateDatasource(id, values);
        message.success('Data source updated successfully');
      } else {
        await createDatasource(values);
        message.success('Data source created successfully');
      }
      navigate('/analysis/datasource');
    } catch (error) {
      console.error('Submit failed:', error);
      message.error('Failed to save data source');
    } finally {
      setSubmitting(false);
    }
  };

  const renderConnectionFields = () => {
    switch (dbType) {
      case 'postgres':
      case 'mysql':
      case 'mssql':
      case 'clickhouse':
        return (
          <>
            <Form.Item
              name={['connection_info', 'host']}
              label="Host"
              rules={[{ required: true, message: 'Host is required' }]}
            >
              <Input placeholder="localhost" />
            </Form.Item>
            <Form.Item
              name={['connection_info', 'port']}
              label="Port"
              rules={[{ required: true, message: 'Port is required' }]}
            >
              <InputNumber
                style={{ width: '100%' }}
                placeholder={
                  dbType === 'postgres'
                    ? '5432'
                    : dbType === 'mysql'
                      ? '3306'
                      : dbType === 'mssql'
                        ? '1433'
                        : dbType === 'clickhouse'
                          ? '8123'
                          : ''
                }
              />
            </Form.Item>
            <Form.Item
              name={['connection_info', 'database']}
              label="Database"
              rules={[{ required: true, message: 'Database is required' }]}
            >
              <Input placeholder="database_name" />
            </Form.Item>
            <Form.Item
              name={['connection_info', 'user']}
              label="Username"
              rules={[{ required: true, message: 'Username is required' }]}
            >
              <Input placeholder="username" />
            </Form.Item>
            <Form.Item
              name={['connection_info', 'password']}
              label="Password"
              rules={[{ required: true, message: 'Password is required' }]}
            >
              <Input.Password placeholder="password" />
            </Form.Item>
            {dbType === 'mssql' && (
              <Form.Item
                name={['connection_info', 'driver']}
                label="Driver"
                initialValue="FreeTDS"
                tooltip="On Mac and Linux this is usually FreeTDS. On Windows, it is usually ODBC Driver 18 for SQL Server"
              >
                <Input placeholder="FreeTDS" />
              </Form.Item>
            )}
          </>
        );
      case 'snowflake':
        return (
          <>
            <Form.Item
              name={['connection_info', 'account']}
              label="Account"
              rules={[{ required: true, message: 'Account is required' }]}
            >
              <Input placeholder="your_account" />
            </Form.Item>
            <Form.Item
              name={['connection_info', 'user']}
              label="Username"
              rules={[{ required: true, message: 'Username is required' }]}
            >
              <Input placeholder="username" />
            </Form.Item>
            <Form.Item
              name={['connection_info', 'password']}
              label="Password"
              rules={[{ required: true, message: 'Password is required' }]}
            >
              <Input.Password placeholder="password" />
            </Form.Item>
            <Form.Item
              name={['connection_info', 'database']}
              label="Database"
              rules={[{ required: true, message: 'Database is required' }]}
            >
              <Input placeholder="database_name" />
            </Form.Item>
            <Form.Item
              name={['connection_info', 'schema']}
              label="Schema"
              rules={[{ required: true, message: 'Schema is required' }]}
              initialValue="PUBLIC"
            >
              <Input placeholder="PUBLIC" />
            </Form.Item>
          </>
        );
      case 'bigquery':
        return (
          <>
            <Form.Item
              name={['connection_info', 'project_id']}
              label="Project ID"
              rules={[{ required: true, message: 'Project ID is required' }]}
            >
              <Input placeholder="your-project-id" />
            </Form.Item>
            <Form.Item
              name={['connection_info', 'dataset_id']}
              label="Dataset ID"
              rules={[{ required: true, message: 'Dataset ID is required' }]}
            >
              <Input placeholder="your_dataset_id" />
            </Form.Item>
            <Form.Item
              name={['connection_info', 'credentials']}
              label="Credentials"
              rules={[{ required: true, message: 'Credentials are required' }]}
              tooltip="Base64 encoded credentials.json"
            >
              <TextArea
                rows={4}
                placeholder="Base64 encoded credentials.json"
              />
            </Form.Item>
          </>
        );
      case 'trino':
        return (
          <>
            <Form.Item
              name={['connection_info', 'host']}
              label="Host"
              rules={[{ required: true, message: 'Host is required' }]}
            >
              <Input placeholder="localhost" />
            </Form.Item>
            <Form.Item
              name={['connection_info', 'port']}
              label="Port"
              rules={[{ required: true, message: 'Port is required' }]}
              initialValue="8080"
            >
              <InputNumber style={{ width: '100%' }} placeholder="8080" />
            </Form.Item>
            <Form.Item
              name={['connection_info', 'catalog']}
              label="Catalog"
              rules={[{ required: true, message: 'Catalog is required' }]}
            >
              <Input placeholder="catalog" />
            </Form.Item>
            <Form.Item
              name={['connection_info', 'schema']}
              label="Schema"
              rules={[{ required: true, message: 'Schema is required' }]}
            >
              <Input placeholder="schema" />
            </Form.Item>
            <Form.Item name={['connection_info', 'user']} label="Username">
              <Input placeholder="username (optional)" />
            </Form.Item>
            <Form.Item name={['connection_info', 'password']} label="Password">
              <Input.Password placeholder="password (optional)" />
            </Form.Item>
          </>
        );
      case 'duckdb':
        return (
          <>
            <Form.Item
              name={['connection_info', 'connection_url']}
              label="Connection URL"
              rules={[
                { required: true, message: 'Connection URL is required' },
              ]}
            >
              <Input placeholder="duckdb:///:memory:" />
            </Form.Item>
          </>
        );
      default:
        return null;
    }
  };

  return (
    <Card>
      <Form
        form={form}
        layout="vertical"
        initialValues={
          initialValues || { type: 'postgres', connection_info: {} }
        }
        onFinish={handleSubmit}
      >
        <Form.Item
          name="name"
          label="Name"
          rules={[{ required: true, message: 'Name is required' }]}
        >
          <Input placeholder="My Database Connection" />
        </Form.Item>

        <Form.Item
          name="description"
          label="Description"
          rules={[
            {
              max: 255,
              message: 'Description must be less than 255 characters',
            },
          ]}
        >
          <TextArea
            rows={3}
            placeholder="Optional description for this data source"
          />
        </Form.Item>

        <Form.Item
          name="type"
          label="Database Type"
          rules={[{ required: true, message: 'Database type is required' }]}
        >
          <Select onChange={handleTypeChange}>
            <Option value="postgres">PostgreSQL</Option>
            <Option value="mysql">MySQL</Option>
            <Option value="mssql">SQL Server</Option>
            <Option value="clickhouse">ClickHouse</Option>
            <Option value="bigquery">BigQuery</Option>
            <Option value="snowflake">Snowflake</Option>
            <Option value="trino">Trino</Option>
            <Option value="duckdb">DuckDB</Option>
          </Select>
        </Form.Item>

        <Divider>Connection Details</Divider>
        {renderConnectionFields()}

        {testResult && (
          <Alert
            message={
              testResult.success ? 'Connection Successful' : 'Connection Failed'
            }
            description={testResult.message}
            type={testResult.success ? 'success' : 'error'}
            showIcon
            className="mb-4"
          />
        )}

        <Form.Item>
          <Space>
            <Button onClick={() => navigate('/analysis/datasource')}>
              <ArrowLeftOutlined /> Back
            </Button>
            <Button onClick={handleTestConnection} loading={testing}>
              Test Connection
            </Button>
            <Button
              type="primary"
              htmlType="submit"
              loading={submitting}
              icon={<CheckCircleOutlined />}
            >
              {isEdit ? 'Update' : 'Create'} Data Source
            </Button>
          </Space>
        </Form.Item>
      </Form>
    </Card>
  );
};

export default DataSourceForm;
