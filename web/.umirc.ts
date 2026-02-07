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
      name: 'Dashboard',
      path: '/dashboard',
      component: './Dashboard',
      icon: 'DashboardOutlined',
    },
    {
      name: '指标口径',
      path: '/metric-glossary',
      component: './MetricGlossary',
      icon: 'ProfileOutlined',
    },
    {
      name: 'DataDiscuss',
      path: '/data-discuss',
      component: './DataDiscuss',
      icon: 'ExperimentOutlined',
    },
    {
      name: 'DataSource',
      path: '/datasource',
      component: './DataSource',
      icon: 'DatabaseOutlined',
    },
    {
      name: 'RagSource',
      path: '/rag-source',
      component: './RagSource',
      icon: 'BookOutlined',
    },
    {
      name: 'LLMSource',
      path: '/llm-source',
      component: './LLMSource',
      icon: 'RobotOutlined',
    },
    {
      name: 'Agent编排',
      path: '/agent-builder',
      component: './AgentBuilder',
      icon: 'DeploymentUnitOutlined',
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
