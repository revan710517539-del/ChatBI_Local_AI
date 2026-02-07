// 运行时配置

import { RequestConfig, RunTimeLayoutConfig, history } from '@umijs/max';
import logo from '@/assets/logo.png';
import './global.less';
import { GithubOutlined } from '@ant-design/icons';

// 全局初始化数据配置，用于 Layout 用户信息和权限初始化
// 更多信息见文档：https://umijs.org/docs/api/runtime-config#getinitialstate
export async function getInitialState(): Promise<{ name: string }> {
  return { name: 'SmartBI' };
}

// ProLayout 支持的api https://procomponents.ant.design/components/layout
export const layout: RunTimeLayoutConfig = () => {
  return {
    title: 'SmartBI',
    logo: logo,
    layout: 'mix',
    splitMenus: false,
    onPageChange: () => {
      // 如果是登录页面，不执行
    },

    menuHeaderRender: undefined,
    // 自定义 403 页面
    // unAccessible: <div>unAccessible</div>,
    // 增加一个 loading 的状态
    childrenRender: (children) => {
      // if (initialState?.loading) return <PageLoading />;
      return <>{children}</>;
    },
    contentStyle: {
      minHeight: '100vh',
      padding: 0,
      background:
        'radial-gradient(1200px 600px at 100% -5%, rgba(15,110,255,0.12), rgba(15,110,255,0) 60%), radial-gradient(800px 500px at 0% 0%, rgba(3,166,120,0.14), rgba(3,166,120,0) 55%), #f4f7fb',
    },
    token: {
      bgLayout: 'transparent',
      pageContainer: {
        colorBgPageContainer: 'transparent',
      },
    },

    actionsRender: () => {
      return [
        <div
          key="github"
          style={{
            display: 'flex',
            alignItems: 'center',
            cursor: 'pointer',
            padding: '0 12px',
            height: '100%',
          }}
          onClick={() => {
            window.open('https://github.com/chatbi/chatbi', '_blank');
          }}
        >
          <GithubOutlined style={{ fontSize: 20 }} />
        </div>,
      ];
    },

    // Add Footer
    footerRender: () => {
      // Only show footer on home page
      if (
        history.location.pathname !== '/' &&
        history.location.pathname !== '/welcome'
      ) {
        return null;
      }
      return (
        <div style={{ textAlign: 'center', padding: '16px 0', color: '#888' }}>
          SmartBI ©{new Date().getFullYear()} Loan Intelligence Platform by{' '}
          <a
            href="https://github.com/yugasun"
            target="_blank"
            rel="noreferrer"
            style={{ color: 'inherit', fontWeight: 600 }}
          >
            yugasun
          </a>
        </div>
      );
    },

    settings: {},
  };
};

console.log('UMI_APP_SERVER_URL', process.env.UMI_APP_SERVER_URL);

export const request: RequestConfig = {
  // timeout 10 mins
  timeout: 600000,
  baseURL: process.env.UMI_APP_SERVER_URL
    ? process.env.UMI_APP_SERVER_URL
    : '/',
  // other axios options you want
  errorConfig: {
    errorHandler() {
      // noop
    },
    errorThrower() {
      // noop
    },
  },
  requestInterceptors: [],
  responseInterceptors: [],
};
