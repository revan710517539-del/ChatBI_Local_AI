import { ChatService } from '@/services/chat';
import { logger } from '@/utils/logger';
import logo from '@/assets/logo.png';
import {
  Bubble,
  BubbleProps,
  Prompts,
  useXAgent,
  useXChat,
} from '@ant-design/x';
import { useEffect, useState } from 'react';
import useChatStore from '@/store/chat';
import { Alert, Empty, type GetProp, Space, Spin, Table, theme } from 'antd';
import MarkdownBase from '@/components/MarkdownView/MarkdownBase';
import { UserOutlined, LoadingOutlined } from '@ant-design/icons';
import AvaAdvisor from '@/components/AvaAdvisor/AvaAdvisor';
import InsightWidget, { InsightSummary } from '@/components/Chat/InsightWidget';
import { ClarificationWidget } from '@/components/Chat/ClarificationWidget';

type BubbleRoles = GetProp<typeof Bubble.List, 'roles'>;
type MessageRender = BubbleProps<Chat.IChatMessage>['messageRender'];
type BubbleItem = BubbleProps<Chat.IChatMessage> & {
  key?: string | number;
  role?: string;
};

const log = logger.extend('copilot:useChat');

const renderMarkdown: MessageRender = (message: Chat.IChatMessage) => {
  return <MarkdownBase content={message.content} />;
};

const renderInsight: MessageRender = (message: Chat.IChatMessage) => {
  return <InsightWidget data={message.data as InsightSummary} />;
};

const renderTable: MessageRender = (message: Chat.IChatMessage) => {
  log('renderTable', message);
  if (!message.data) return "Can't render table without data";

  const dataSource = message.data as Chat.IDataRow[];

  if (!dataSource || dataSource.length === 0) {
    return (
      <div style={{ padding: 16 }}>
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description="No data available"
        />
      </div>
    );
  }

  const columns = Object.keys(dataSource[0]).map((key) => ({
    title: key.charAt(0).toUpperCase() + key.slice(1).replace(/_/g, ' '),
    dataIndex: key,
    key: key,
    ellipsis: true,
    width: 150,
  }));

  return (
    <Table
      dataSource={dataSource.map((row, idx) => ({ ...row, key: idx }))}
      columns={columns}
      pagination={{
        pageSize: 10,
        showSizeChanger: true,
        showTotal: (total) => `Total ${total} records`,
        size: 'small',
      }}
      scroll={{ x: 'max-content' }}
      size="small"
      bordered
      style={{ marginTop: 8 }}
    />
  );
};

const renderAva = (message: Chat.IChatMessage) => {
  log('renderAva', message);
  if (!message.data) return "Can't render visualization without data";
  const dataSource = message.data as Chat.IDataRow[];

  if (!dataSource || dataSource.length === 0) {
    return (
      <div style={{ padding: 16 }}>
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description="No data to visualize"
        />
      </div>
    );
  }

  return (
    <div>
      <Alert
        type="info"
        showIcon
        message="Auto-generated visualization"
        description="Based on the query result"
        style={{ marginBottom: 12 }}
      />
      <AvaAdvisor data={dataSource} />
    </div>
  );
};

const useChat = () => {
  const { token } = theme.useToken();

  const roles: BubbleRoles = {
    assistant: {
      placement: 'start',
      avatar: {
        icon: <img src={logo} alt="AI" style={{ width: 18, height: 18 }} />,
        style: { background: token.colorBgContainer, padding: 4 },
      },
      typing: { step: 5, interval: 20 },
      styles: {
        content: {
          borderRadius: 16,
          boxShadow: token.boxShadowSecondary,
          border: `1px solid ${token.colorBorderSecondary}`,
        },
      },
      loadingRender: () => (
        <Space>
          <Spin
            size="small"
            indicator={<LoadingOutlined style={{ fontSize: 16 }} spin />}
          />
          <span style={{ color: token.colorTextSecondary, fontSize: 13 }}>
            ChatBI is analyzing...
          </span>
        </Space>
      ),
    },
    user: {
      placement: 'end',
      variant: 'shadow',
      avatar: {
        icon: <UserOutlined />,
        style: {
          background: `linear-gradient(135deg, ${token.colorPrimary} 0%, ${token.colorInfo} 100%)`,
        },
      },
      styles: {
        content: {
          borderRadius: 16,
          color: token.colorWhite,
          background: `linear-gradient(135deg, ${token.colorPrimary} 0%, ${token.colorInfo} 100%)`,
          border: 'none',
        },
      },
    },
  };
  const chatStore = useChatStore();
  // const messages = useChatStore((state) => state.messages);
  const prompt = useChatStore((state) => state.prompt);
  const setPrompt = useChatStore((state) => state.setPrompt);
  const datasourceId = useChatStore((state) => state.datasourceId);
  const setDatasourceId = useChatStore((state) => state.setDatasourceId);
  const [loading, setLoading] = useState(false);
  const [sql, setSql] = useState('');

  const [id, setId] = useState('');
  const [isVisualizing, setIsVisualizing] = useState(false);
  const [isCanVisualize, setIsCanVisualize] = useState(false);
  const [tableData, setTableData] = useState<Chat.IDataRow>([]);
  const [bubbleItems, setBubbleItems] = useState<BubbleItem[]>([]);

  async function generateSql(
    message: Chat.IChatMessage,
    onSuccess: (msg: Chat.IChatMessage) => void,
  ) {
    try {
      log('analyze question:', message.content);
      const res = await ChatService.analyze(message.content, datasourceId);
      log('analyze response:', res);

      const msgId = id || 'temp-' + Date.now();
      setId(msgId);

      const analysisData = res.data;
      if (!analysisData) {
        throw new Error('No data returned');
      }

      // 0. Clarification
      if ((analysisData as any).intent === 'clarification') {
        const clarifyMsg = {
          role: 'assistant',
          content: (analysisData as any).answer || 'Please clarify:',
          type: 'clarification',
          data: (analysisData as any).metadata?.options || [],
        } as Chat.IChatMessage;
        addMessage({
          id: msgId,
          message: clarifyMsg,
          status: 'success',
        });
        onSuccess(clarifyMsg);
        return;
      }

      // 1. SQL Message
      if (analysisData.sql) {
        const sqlMsg = {
          role: 'assistant',
          content: `📝 **Generated SQL**\n\n\`\`\`sql\n${analysisData.sql}\n\`\`\``,
        } as Chat.IChatMessage;
        addMessage({
          id: msgId,
          message: sqlMsg,
          status: 'success',
        });
      }

      // 2. Data & Viz
      if (analysisData.data) {
        let rows = [];
        try {
          rows =
            typeof analysisData.data === 'string'
              ? JSON.parse(analysisData.data)
              : analysisData.data;
        } catch (e) {
          console.error('Failed to parse data json', e);
          rows = [];
        }

        setTableData(rows);

        if (rows.length > 0) {
          const tableMsg = {
            role: 'assistant',
            content: `✅ **Query Results**\n\nFound ${rows.length} records`,
            type: 'table',
            data: rows,
          } as Chat.IChatMessage;
          addMessage({
            id: msgId,
            message: tableMsg,
            status: 'success',
          });

          if (analysisData.should_visualize) {
            const vizMsg = {
              role: 'assistant',
              content: '📊 **Data Visualization**',
              type: 'ava',
              data: rows,
            } as Chat.IChatMessage;
            addMessage({
              id: msgId,
              message: vizMsg,
              status: 'success',
            });
          }

          if ((analysisData as any).insight) {
            const insightMsg = {
              role: 'assistant',
              content: '💡 **Data Insights**',
              type: 'insight',
              data: (analysisData as any).insight,
            } as Chat.IChatMessage;
            addMessage({
              id: msgId,
              message: insightMsg,
              status: 'success',
            });
          }
        } else {
          addMessage({
            id: msgId,
            message: {
              role: 'assistant',
              content: 'Query executed but returned no data.',
            },
            status: 'success',
          });
        }
      }

      // Signal completion
      // We pass a dummy message because we manually added messages to the store.
      // If we return a message here, XChat might add it too.
      // Let's pass null or ensure the XChat behavior handles it.
      // The `request` callback in `useXAgent` expects specific behavior.
      // If I don't execute `onSuccess`, `loading` might stay true.
      onSuccess({ role: 'assistant', content: '' });
    } catch (e) {
      log('analyze error:', e);
      const errorMessage = {
        role: 'assistant',
        content: `❌ **Error during analysis**\n\n${
          e instanceof Error ? e.message : 'Unknown error occurred'
        }`,
      } as Chat.IChatMessage;

      addMessage({
        id: id,
        message: errorMessage,
        status: 'error',
      });
      onSuccess(errorMessage);
    }
  }

  const [agent] = useXAgent<Chat.IChatMessage>({
    request: async ({ message }, { onSuccess }) => {
      if (!message) return;

      await generateSql(message, onSuccess);
    },
  });

  useEffect(() => {
    setLoading(agent.isRequesting());
  }, [agent]);

  const { onRequest, messages, setMessages } = useXChat({
    agent,
  });

  function updateMessages() {
    setMessages(chatStore.messages);
  }

  useEffect(() => {
    log('Init Messages', chatStore.messages);
    updateMessages();
  }, []);

  useEffect(() => {
    const newItems = chatStore.messages.map(
      ({ id, message, status }, index) => {
        log('message', message);
        let render = renderMarkdown;
        if (message.type === 'table') {
          render = renderTable;
        }
        if (message.type === 'ava') {
          render = renderAva;
        }
        if (message.type === 'insight') {
          render = renderInsight;
        }
        if (message.type === 'clarification') {
          render = (msg: Chat.IChatMessage) => (
            <ClarificationWidget
              question={msg.content}
              options={msg.data as any}
              onSelect={(val) => onSubmit(val)}
            />
          );
        }
        return {
          key: `${id}-${index}`,
          loading: status === 'loading',
          role: message.role,
          content: message,
          messageRender: render,
        };
      },
    );
    setBubbleItems(newItems);
  }, [chatStore.messages]);

  const addMessage = (newStoreMessage: Chat.IMessage) => {
    chatStore.addMessage([newStoreMessage]);
  };

  // ==================== Event ====================
  const onSubmit = (nextContent: string) => {
    if (!nextContent) return;
    onRequest({
      role: 'user',
      content: nextContent,
    });
    setPrompt('');

    // add message to store
    addMessage({
      id: id,
      message: {
        role: 'user',
        content: nextContent,
      },
      status: 'success',
    });
  };

  const clearMessages = () => {
    chatStore.clearMessages();

    setMessages([]);
  };

  const onPromptsItemClick: GetProp<typeof Prompts, 'onItemClick'> = (info) => {
    onSubmit(info.data.description as string);
  };

  return {
    loading,
    agent,
    roles,
    messages,
    prompt,
    setPrompt,
    bubbleItems,

    onSubmit,
    clearMessages,

    onPromptsItemClick,
    setDatasourceId,
  };
};

export default useChat;
