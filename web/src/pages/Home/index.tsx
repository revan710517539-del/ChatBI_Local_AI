import {
  PageContainer,
  ProCard,
  StatisticCard,
} from '@ant-design/pro-components';
import { history, useModel } from '@umijs/max';
import {
  DatabaseOutlined,
  ExperimentOutlined,
  RocketOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons';
import { Button, Space, Typography } from 'antd';
import React, { useEffect, useState } from 'react';
import { getDatasources } from '@/services/datasource';
import styles from './index.less';

const { Divider } = StatisticCard;
const { Title, Paragraph } = Typography;

const HomePage: React.FC = () => {
  const { name } = useModel('global');
  // const { token } = theme.useToken();
  const token = {
    colorPrimary: '#1677ff',
    colorSuccess: '#52c41a',
    colorWarning: '#faad14',
  };
  const [datasourceCount, setDatasourceCount] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await getDatasources();
        setDatasourceCount(res?.data?.items?.length || 0);
      } catch (e) {
        console.error('Failed to fetch datasources info', e);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  return (
    <PageContainer
      ghost
      header={{
        title: `Welcome back, ${name}! 👋`,
        subTitle: 'Ready to explore your data insights today?',
      }}
    >
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* Statistics Section */}
        <StatisticCard.Group direction="row">
          <StatisticCard
            statistic={{
              title: 'Connected Data Sources',
              value: datasourceCount,
              icon: <DatabaseOutlined style={{ color: token.colorPrimary }} />,
              suffix: 'DBs',
            }}
            loading={loading}
          />
          <Divider />
          <StatisticCard
            statistic={{
              title: 'System Status',
              value: 'Online',
              status: 'success',
              icon: (
                <ThunderboltOutlined style={{ color: token.colorSuccess }} />
              ),
            }}
          />
          <Divider />
          <StatisticCard
            statistic={{
              title: 'AI Model',
              value: 'GPT-4o',
              icon: <RocketOutlined style={{ color: token.colorWarning }} />,
            }}
          />
        </StatisticCard.Group>

        {/* Quick Actions */}
        <ProCard title="Quick Actions" headerBordered gutter={16} ghost>
          <ProCard colSpan={12} layout="center" bordered>
            <div className={styles.actionCard}>
              <ExperimentOutlined
                className={styles.actionIcon}
                style={{ color: token.colorPrimary }}
              />
              <Title level={4}>AI Playground</Title>
              <Paragraph type="secondary">
                Ask questions in natural language and get instant SQL + Charts.
              </Paragraph>
              <Button
                type="primary"
                size="large"
                onClick={() => history.push('/playground')}
              >
                Start Analysis 🚀
              </Button>
            </div>
          </ProCard>
          <ProCard colSpan={12} layout="center" bordered>
            <div className={styles.actionCard}>
              <DatabaseOutlined
                className={styles.actionIcon}
                style={{ color: token.colorSuccess }}
              />
              <Title level={4}>Data Sources</Title>
              <Paragraph type="secondary">
                Connect to PostgreSQL, MySQL, DuckDB and more.
              </Paragraph>
              <Button size="large" onClick={() => history.push('/data-source')}>
                Manage Data 🔌
              </Button>
            </div>
          </ProCard>
        </ProCard>

        {/* Features / Info */}
        <ProCard
          title="System Capabilities"
          split="vertical"
          bordered
          headerBordered
        >
          <ProCard title="Natural Language to SQL" colSpan="33%">
            Translate human questions into complex SQL queries automatically
            using advanced LLMs.
          </ProCard>
          <ProCard title="Auto Visualization" colSpan="33%">
            Intelligent chart generation powered by AntV AVA based on your data
            results.
          </ProCard>
          <ProCard title="Multi-Database Support" colSpan="33%">
            Seamlessly connect to various database types including PostgreSQL,
            MySQL, SQLite, and DuckDB.
          </ProCard>
        </ProCard>

        {/* Footer info */}
        <div style={{ textAlign: 'center', padding: '24px 0', color: '#888' }}>
          ChatBI ©{new Date().getFullYear()} Created with ❤️ by{' '}
          <a
            href="https://github.com/yugasun"
            target="_blank"
            rel="noreferrer"
            style={{ color: 'inherit', fontWeight: 600 }}
          >
            yugasun
          </a>
        </div>
      </Space>
    </PageContainer>
  );
};

export default HomePage;
