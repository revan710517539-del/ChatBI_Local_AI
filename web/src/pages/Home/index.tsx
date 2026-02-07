import {
  DatabaseOutlined,
  DashboardOutlined,
  ExperimentOutlined,
  RobotOutlined,
} from '@ant-design/icons';
import { history, useModel } from '@umijs/max';
import { Button, Card, Col, Row, Space, Statistic, Typography } from 'antd';
import React, { useEffect, useMemo, useState } from 'react';
import { getDatasources } from '@/services/datasource';
import styles from './index.less';

const { Title, Paragraph, Text } = Typography;

const HomePage: React.FC = () => {
  const { name } = useModel('global');
  const [datasourceCount, setDatasourceCount] = useState<number>(0);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await getDatasources({ limit: 100 });
        const items = (res as any)?.data?.items || (res as any)?.items || [];
        setDatasourceCount(Array.isArray(items) ? items.length : 0);
      } catch {
        setDatasourceCount(0);
      }
    };
    fetchData();
  }, []);

  const heroDate = useMemo(
    () =>
      new Date().toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
      }),
    [],
  );

  return (
    <div className={styles.page}>
      <Card className={styles.hero}>
        <Text className={styles.kicker}>SmartBI · Loan Intelligence</Text>
        <Title level={2} className={styles.title}>
          {name}，欢迎进入贷款智能分析中台
        </Title>
        <Paragraph className={styles.desc}>
          聚焦消费贷与经营贷：统一数据源、可编排 Agent、可执行口径引擎与多模型推理。
        </Paragraph>
        <Space size={12} wrap>
          <Button type="primary" size="large" onClick={() => history.push('/dashboard')}>
            进入 Dashboard
          </Button>
          <Button size="large" onClick={() => history.push('/data-discuss')}>
            打开 DataDiscuss
          </Button>
          <Button size="large" onClick={() => history.push('/llm-source')}>
            配置模型与RAG
          </Button>
        </Space>
        <Text type="secondary" className={styles.dateText}>
          业务日：{heroDate}
        </Text>
      </Card>

      <Row gutter={[16, 16]}>
        <Col xs={24} md={12} xl={6}>
          <Card className={styles.statCard}>
            <Statistic title="已连接数据源" value={datasourceCount} prefix={<DatabaseOutlined />} />
          </Card>
        </Col>
        <Col xs={24} md={12} xl={6}>
          <Card className={styles.statCard}>
            <Statistic title="分析入口" value="DataDiscuss" prefix={<ExperimentOutlined />} />
          </Card>
        </Col>
        <Col xs={24} md={12} xl={6}>
          <Card className={styles.statCard}>
            <Statistic title="业务驾驶舱" value="Dashboard" prefix={<DashboardOutlined />} />
          </Card>
        </Col>
        <Col xs={24} md={12} xl={6}>
          <Card className={styles.statCard}>
            <Statistic title="模型调度" value="Single Runtime" prefix={<RobotOutlined />} />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        <Col xs={24} xl={12}>
          <Card title="业务场景模板" className={styles.panelCard}>
            <ul className={styles.list}>
              <li>消费贷：申请-授信-动支-还款-逾期全链路漏斗诊断</li>
              <li>经营贷：阶段授信转化、额度使用率、迁徙率、RAROC联动分析</li>
              <li>风险视角：逾期率、不良率、拨备覆盖率、资本充足率联动</li>
            </ul>
          </Card>
        </Col>
        <Col xs={24} xl={12}>
          <Card title="推荐工作流" className={styles.panelCard}>
            <ul className={styles.list}>
              <li>1. 在 DataSource 一键创建本地 Excel/MySQL 数据源</li>
              <li>2. 在 LLMSource 配置 qwen3/minicpm/TableGPT2/bge-m3 能力映射</li>
              <li>3. 在 Agent编排 开启 SQL/RAG/规则校验工具链</li>
              <li>4. 在 Dashboard 与 DataDiscuss 按场景 Prompt 进行分析</li>
            </ul>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default HomePage;
