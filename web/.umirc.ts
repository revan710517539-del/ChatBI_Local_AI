import { defineConfig } from '@umijs/max';

export default defineConfig({
  mako: {},
  antd: {},
  access: {},
  model: {},
  initialState: {},
  request: {},
  layout: {
    title: 'SmartBI',
  },
  routes: [
    {
      path: '/',
      redirect: '/home',
    },
    {
      name: '首页',
      path: '/home',
      component: './Home',
      icon: 'HomeOutlined',
    },
    {
      name: '机会洞察',
      icon: 'BulbOutlined',
      routes: [
        {
          name: '市场洞察',
          path: '/market-watch',
          component: './MarketWatch',
          icon: 'RadarChartOutlined',
        },
        {
          name: '客户洞察',
          path: '/customer-insights',
          component: './CustomerInsights',
          icon: 'UsergroupAddOutlined',
        },
      ],
    },
    {
      name: '数据分析',
      icon: 'BarChartOutlined',
      routes: [
        {
          name: '数据表现',
          path: '/dashboard',
          component: './Dashboard',
          icon: 'DashboardOutlined',
        },
        {
          name: '策略归因',
          path: '/strategy-attribution',
          component: './StrategyAttribution',
          icon: 'LineChartOutlined',
        },
        {
          name: '指标口径',
          path: '/metric-glossary',
          component: './MetricGlossary',
          icon: 'ProfileOutlined',
        },
        {
          name: '数据源',
          path: '/datasource',
          component: './DataSource',
          icon: 'DatabaseOutlined',
        },
      ],
    },
    {
      name: '策略讨论',
      path: '/data-discuss',
      component: './DataDiscuss',
      icon: 'ExperimentOutlined',
    },
    {
      name: '监控诊断',
      icon: 'AlertOutlined',
      routes: [
        {
          name: '监控规则配置',
          path: '/monitoring/rules',
          component: './MonitoringRules',
          icon: 'ControlOutlined',
        },
        {
          name: '诊断配置',
          path: '/monitoring/diagnosis',
          component: './MonitoringDiagnosis',
          icon: 'MedicineBoxOutlined',
        },
        {
          name: '异常通知',
          path: '/monitoring/alerts',
          component: './MonitoringAlerts',
          icon: 'NotificationOutlined',
        },
      ],
    },
    {
      name: 'Agent管理',
      icon: 'DeploymentUnitOutlined',
      routes: [
        {
          name: 'Agent编排',
          path: '/agent-builder',
          component: './AgentBuilder',
          icon: 'DeploymentUnitOutlined',
        },
        {
          name: '知识库',
          path: '/rag-source',
          component: './RagSource',
          icon: 'BookOutlined',
        },
        {
          name: '技能库',
          path: '/mcp-skills',
          component: './McpSkillHub',
          icon: 'ApiOutlined',
        },
        {
          name: '记忆中心',
          path: '/memory-center',
          component: './MemoryCenter',
          icon: 'HistoryOutlined',
        },
      ],
    },
    {
      name: '模型管理',
      path: '/llm-source',
      component: './LLMSource',
      icon: 'RobotOutlined',
    },
    {
      path: '/datasource/new',
      component: './DataSource/New',
      hideInMenu: true,
    },
    {
      path: '/datasource/edit/:id',
      component: './DataSource/Edit',
      hideInMenu: true,
    },
    {
      path: '/datasource/query/:id',
      component: './DataSource/Query',
      hideInMenu: true,
    },
  ],
  npmClient: 'pnpm',

  plugins: [require.resolve('@umijs/plugins/dist/unocss')],
  unocss: {
    // 检测 className 的文件范围，若项目不包含 src 目录，可使用 `pages/**/*.tsx`
    watch: ['src/**/*.tsx'],
  },

  // Define environment variables for client-side access
  define: {
    'process.env.UMI_APP_SERVER_URL':
      process.env.UMI_APP_SERVER_URL || 'http://127.0.0.1:8000',
  },

  // Add proxy for development to avoid CORS issues
  proxy: {
    '/api': {
      target: process.env.UMI_APP_SERVER_URL || 'http://127.0.0.1:8000',
      changeOrigin: true,
    },
  },
});
