import { useEffect, useState } from 'react';
import { PageContainer } from '@ant-design/pro-components';
import { useParams, useNavigate } from '@umijs/max';
import { Spin, Result } from 'antd';
import DataSourceForm from './components/DataSourceForm';
import { getDatasource } from '@/services/datasource';

const EditDataSourcePage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [datasource, setDatasource] = useState<any>(null);

  useEffect(() => {
    const fetchDatasource = async () => {
      if (!id) {
        setError('No datasource ID provided');
        setLoading(false);
        return;
      }

      try {
        const data = await getDatasource(id);
        setDatasource(data);
      } catch (err) {
        console.error('Failed to fetch datasource:', err);
        setError('Failed to fetch datasource details');
      } finally {
        setLoading(false);
      }
    };

    fetchDatasource();
  }, [id]);

  if (loading) {
    return (
      <PageContainer>
        <div className="flex justify-center items-center h-64">
          <Spin size="large" tip="Loading datasource..." />
        </div>
      </PageContainer>
    );
  }

  if (error || !datasource) {
    return (
      <PageContainer>
        <Result
          status="error"
          title="Failed to load datasource"
          subTitle={error || 'The datasource could not be found'}
          extra={[
            <button
              key="back"
              className="ant-btn ant-btn-primary"
              onClick={() => navigate('/analysis/datasource')}
            >
              Back to Data Sources
            </button>,
          ]}
        />
      </PageContainer>
    );
  }

  return (
    <PageContainer
      header={{
        title: `Edit: ${datasource.name}`,
        subTitle: 'Modify datasource connection details',
        backIcon: true,
      }}
    >
      <DataSourceForm initialValues={datasource} id={id} isEdit={true} />
    </PageContainer>
  );
};

export default EditDataSourcePage;
