import { PageContainer } from '@ant-design/pro-components';
import DataSourceForm from './components/DataSourceForm';

const NewDataSourcePage: React.FC = () => {
  return (
    <PageContainer
      header={{
        title: 'New Data Source',
        subTitle: 'Connect to a new database',
        backIcon: true,
      }}
    >
      <DataSourceForm />
    </PageContainer>
  );
};

export default NewDataSourcePage;
