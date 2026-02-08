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
      path: '/insight',
      icon: 'BulbOutlined',
      routes: [
        {
          path: '/insight',
          redirect: '/insight/market-watch',
          hideInMenu: true,
        },
        {
          name: '市场洞察',
          path: '/insight/market-watch',
          component: './MarketWatch',
          icon: 'RadarChartOutlined',
        },
        {
          name: '客户洞察',
          path: '/insight/customer-insights',
          component: './CustomerInsights',
          icon: 'UsergroupAddOutlined',
        },
      ],
    },
    {
      name: '数据分析',
      path: '/analysis',
      icon: 'BarChartOutlined',
      routes: [
        {
          path: '/analysis',
          redirect: '/analysis/dashboard',
          hideInMenu: true,
        },
        {
          name: '数据表现',
          path: '/analysis/dashboard',
          component: './Dashboard',
          icon: 'DashboardOutlined',
        },
        {
          name: '策略归因',
          path: '/analysis/strategy-attribution',
          component: './StrategyAttribution',
          icon: 'LineChartOutlined',
        },
        {
          name: '指标口径',
          path: '/analysis/metric-glossary',
          component: './MetricGlossary',
          icon: 'ProfileOutlined',
        },
        {
          name: '数据源',
          path: '/analysis/datasource',
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
      path: '/monitoring',
      icon: 'AlertOutlined',
      routes: [
        {
          path: '/monitoring',
          redirect: '/monitoring/rules',
          hideInMenu: true,
        },
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
      path: '/agent',
      icon: 'DeploymentUnitOutlined',
      routes: [
        {
          path: '/agent',
          redirect: '/agent/agent-builder',
          hideInMenu: true,
        },
        {
          name: 'Agent编排',
          path: '/agent/agent-builder',
          component: './AgentBuilder',
          icon: 'DeploymentUnitOutlined',
        },
        {
          name: '知识库',
          path: '/agent/rag-source',
          component: './RagSource',
          icon: 'BookOutlined',
        },
        {
          name: '技能库',
          path: '/agent/mcp-skills',
          component: './McpSkillHub',
          icon: 'ApiOutlined',
        },
        {
          name: '记忆中心',
          path: '/agent/memory-center',
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
      path: '/market-watch',
      redirect: '/insight/market-watch',
      hideInMenu: true,
    },
    {
      path: '/customer-insights',
      redirect: '/insight/customer-insights',
      hideInMenu: true,
    },
    {
      path: '/dashboard',
      redirect: '/analysis/dashboard',
      hideInMenu: true,
    },
    {
      path: '/strategy-attribution',
      redirect: '/analysis/strategy-attribution',
      hideInMenu: true,
    },
    {
      path: '/metric-glossary',
      redirect: '/analysis/metric-glossary',
      hideInMenu: true,
    },
    {
      path: '/datasource',
      redirect: '/analysis/datasource',
      hideInMenu: true,
    },
    {
      path: '/agent-builder',
      redirect: '/agent/agent-builder',
      hideInMenu: true,
    },
    {
      path: '/rag-source',
      redirect: '/agent/rag-source',
      hideInMenu: true,
    },
    {
      path: '/mcp-skills',
      redirect: '/agent/mcp-skills',
      hideInMenu: true,
    },
    {
      path: '/memory-center',
      redirect: '/agent/memory-center',
      hideInMenu: true,
    },
    {
      path: '/analysis/datasource/new',
      component: './DataSource/New',
      hideInMenu: true,
    },
    {
      path: '/analysis/datasource/edit/:id',
      component: './DataSource/Edit',
      hideInMenu: true,
    },
    {
      path: '/analysis/datasource/query/:id',
      component: './DataSource/Query',
      hideInMenu: true,
    },
    {
      path: '/datasource/new',
      redirect: '/analysis/datasource/new',
      hideInMenu: true,
    },
    {
      path: '/datasource/edit/:id',
      redirect: '/analysis/datasource/edit/:id',
      hideInMenu: true,
    },
    {
      path: '/datasource/query/:id',
      redirect: '/analysis/datasource/query/:id',
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
