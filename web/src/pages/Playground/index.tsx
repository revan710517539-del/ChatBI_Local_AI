import { Attachments, Bubble, Prompts, Sender } from '@ant-design/x';
import { createStyles } from 'antd-style';
import React, { useEffect, useMemo, useState } from 'react';

import {
  CloudUploadOutlined,
  EllipsisOutlined,
  FireOutlined,
  PaperClipOutlined,
  VerticalAlignBottomOutlined,
  DatabaseOutlined,
} from '@ant-design/icons';
import { Badge, theme, Button, type GetProp, Space, Select } from 'antd';

import useChat from '@/models/chat';
import { logger } from '@/utils/logger';
import { datasourceService, type DatasourceType } from '@/services/datasource';

const log = logger.extend('copilot:playground');

const useStyle = createStyles(({ token, css }) => {
  return {
    layout: css`
      width: 100%;
      min-height: 100%;
      border-radius: ${token.borderRadius}px;
      display: flex;
      flex-direction: column;
      background: #fff;
      font-family: ${token.fontFamily};

      .ant-prompts {
        color: ${token.colorText};
      }
    `,
    menu: css`
      background: ${token.colorBgLayout}80;
      width: 280px;
      height: 100%;
      display: flex;
      flex-direction: column;
    `,
    conversations: css`
      padding: 0 12px;
      flex: 1;
      overflow-y: auto;
    `,
    chat: css`
      flex: 1;
      width: 100%;
      margin: 0 auto;
      box-sizing: border-box;
      display: flex;
      flex-direction: column;
      padding: ${token.paddingLG}px;
      gap: 16px;
      padding-bottom: 24px;
      background: transparent;
    `,
    messages: css`
      flex: 1;
      margin: 0 auto;
      width: 100%;
    `,
    placeholder: css`
      padding-top: 10vh;
      text-align: center;
      width: 100%;
      max-width: 800px;
      margin: 0 auto;
      display: flex;
      flex-direction: column;
      align-items: center;
    `,
    welcomeTitle: css`
      font-size: 32px;
      font-weight: 700;
      margin-bottom: 12px;
      background: linear-gradient(
        135deg,
        ${token.colorPrimary} 0%,
        ${token.colorInfo} 100%
      );
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    `,
    welcomeDesc: css`
      font-size: 16px;
      color: ${token.colorTextSecondary};
      margin-bottom: 48px;
    `,
    suggestionGrid: css`
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 16px;
      width: 100%;
    `,
    suggestionCard: css`
      background: ${token.colorBgContainer};
      border: 1px solid ${token.colorBorder};
      border-radius: 12px;
      padding: 20px;
      cursor: pointer;
      text-align: left;
      transition: all 0.3s ease;
      display: flex;
      align-items: flex-start;
      gap: 12px;
      box-shadow: ${token.boxShadowSecondary};
      height: 100%;

      &:hover {
        border-color: ${token.colorPrimary};
        transform: translateY(-2px);
        box-shadow: ${token.boxShadow};
        background: ${token.colorBgContainer};
      }
    `,
    sender: css`
      box-shadow: ${token.boxShadowSecondary};
      border-radius: 20px;
      background: ${token.colorBgElevated};
      padding: 8px 12px;
      border: 1px solid ${token.colorBorderSecondary};
      transition: all 0.3s;

      &:focus-within {
        border-color: ${token.colorPrimary};
        box-shadow: ${token.boxShadow};
        background: ${token.colorBgContainer};
      }
    `,
    senderWrapper: css`
      position: sticky;
      bottom: 0;
      z-index: 100;
      margin: 0 auto;
      width: 100%;
      padding: 0 24px 24px;
      background: #fff;
    `,
    senderToolbar: css`
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: ${token.marginSM}px;
      padding: 10px 12px;
      border: 1px solid ${token.colorBorderSecondary};
      border-radius: 14px;
      background: ${token.colorBgContainer};
      box-shadow: ${token.boxShadowSecondary};

      .ant-prompts {
        flex: 1;
        min-width: 0;
      }

      /* Make prompts compact and multi-line friendly */
      .ant-prompts-item {
        padding: 4px 10px;
        border-radius: 999px;
      }
    `,
    senderToolbarActions: css`
      display: flex;
      align-items: center;
      gap: ${token.marginXS}px;
      flex-shrink: 0;
    `,
  };
});

const Playground: React.FC = () => {
  const {
    loading,
    onPromptsItemClick,
    onSubmit,
    clearMessages,
    roles,
    prompt,
    setPrompt,
    bubbleItems,
    setDatasourceId,
  } = useChat();

  // Datasource state
  const [datasources, setDatasources] = useState<DatasourceType[]>([]);
  const [selectedDatasource, setSelectedDatasource] = useState<
    string | undefined
  >();
  const [loadingDatasources, setLoadingDatasources] = useState(false);

  // Load datasources on mount
  useEffect(() => {
    const loadDatasources = async () => {
      setLoadingDatasources(true);
      try {
        const response = await datasourceService.getDatasources({ limit: 100 });
        // Handle StandardResponse wrapper: { data: [...], success: true, message: "..." }
        const list = Array.isArray((response as any)?.data?.data)
          ? (response as any).data.data
          : Array.isArray((response as any)?.data)
            ? (response as any).data
            : [];
        setDatasources(list);

        // Find and set default datasource
        const defaultDs = list.find((ds: DatasourceType) => ds.is_default);
        if (defaultDs) {
          setSelectedDatasource(defaultDs.id);
          setDatasourceId(defaultDs.id);
        } else if (list.length > 0) {
          // If no default, use first one
          setSelectedDatasource(list[0].id);
          setDatasourceId(list[0].id);
        }
      } catch (error) {
        log('Failed to load datasources:', error);
      } finally {
        setLoadingDatasources(false);
      }
    };
    loadDatasources();
  }, []);

  const handleDatasourceChange = (value: string) => {
    setSelectedDatasource(value);
    setDatasourceId(value);
  };

  const prompts = [
    '销售量最高的前 5 个产品',
    '销售量最高的前 5 个区域',
    '前 10 名用户',
    '销售订单趋势',
  ];

  // ==================== Style ====================
  const { styles } = useStyle();
  const { token } = theme.useToken();

  const [showScrollToBottom, setShowScrollToBottom] = useState(false);

  const scrollToBottom = (behavior: ScrollBehavior = 'smooth') => {
    window.scrollTo({ top: document.body.scrollHeight, behavior });
  };

  useEffect(() => {
    const onScroll = () => {
      const distanceToBottom =
        document.body.scrollHeight - (window.innerHeight + window.scrollY);
      setShowScrollToBottom(distanceToBottom > 240);
    };

    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const handleSubmit = (nextContent: string) => {
    onSubmit(nextContent);
    // Keep the input visible and scroll the latest reply into view.
    requestAnimationFrame(() => scrollToBottom('smooth'));
  };

  // ==================== State ====================
  const senderPromptsItems = useMemo(
    () =>
      prompts.map((description, index) => ({
        key: `${index}`,
        description,
        icon: <FireOutlined style={{ color: token.colorError }} />,
      })),
    [prompts, token.colorError],
  );

  const [headerOpen, setHeaderOpen] = React.useState(false);

  const [attachedFiles, setAttachedFiles] = React.useState<
    GetProp<typeof Attachments, 'items'>
  >([]);

  const handleFileChange: GetProp<typeof Attachments, 'onChange'> = (info) =>
    setAttachedFiles(info.fileList);

  const attachmentsNode = (
    <Badge dot={attachedFiles.length > 0 && !headerOpen}>
      <Button
        type="text"
        icon={<PaperClipOutlined />}
        onClick={() => setHeaderOpen(!headerOpen)}
      />
    </Badge>
  );

  const senderHeader = (
    <Sender.Header
      title="Attachments"
      open={headerOpen}
      onOpenChange={setHeaderOpen}
      styles={{
        content: {
          padding: 0,
        },
      }}
    >
      <Attachments
        beforeUpload={() => false}
        items={attachedFiles}
        onChange={handleFileChange}
        placeholder={(type) =>
          type === 'drop'
            ? { title: 'Drop file here' }
            : {
                icon: <CloudUploadOutlined />,
                title: 'Upload files',
                description: 'Click or drag files to this area to upload',
              }
        }
      />
    </Sender.Header>
  );

  const [container, setContainer] = React.useState<HTMLDivElement | null>(null);

  return (
    <div className={styles.layout} ref={setContainer}>
      <div id="chatbi-messages" className={styles.chat}>
        <div className={styles.messages}>
          {bubbleItems.length === 0 ? (
            <div className={styles.placeholder}>
              <div className={styles.welcomeTitle}>
                Welcome to ChatBI Playground
              </div>
              <div className={styles.welcomeDesc}>
                Ask questions to generate SQL, chart visualization and more.
              </div>
              <div className={styles.suggestionGrid}>
                {prompts.map((item, index) => (
                  <div
                    key={index}
                    className={styles.suggestionCard}
                    onClick={() => {
                      setPrompt(item);
                      handleSubmit(item);
                    }}
                  >
                    <FireOutlined
                      style={{
                        fontSize: 20,
                        color: token.colorWarning,
                        marginTop: 2,
                      }}
                    />
                    <div>
                      <div style={{ fontWeight: 600, marginBottom: 4 }}>
                        Example Query {index + 1}
                      </div>
                      <div
                        style={{
                          color: token.colorTextSecondary,
                          fontSize: 13,
                        }}
                      >
                        {item}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <Bubble.List
              // @ts-ignore
              items={bubbleItems}
              roles={roles}
              className={styles.messages}
              style={{ background: 'transparent' }}
            />
          )}
        </div>
      </div>

      <div className={styles.senderWrapper}>
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          {bubbleItems.length > 0 && (
            <div className={styles.senderToolbar}>
              {!loading && prompt.trim().length === 0 ? (
                <Prompts
                  items={senderPromptsItems}
                  onItemClick={onPromptsItemClick}
                />
              ) : (
                <div style={{ flex: 1, minWidth: 0 }} />
              )}

              <div className={styles.senderToolbarActions}>
                <Select
                  size="small"
                  style={{ width: 200 }}
                  placeholder="Select datasource"
                  value={selectedDatasource}
                  onChange={handleDatasourceChange}
                  loading={loadingDatasources}
                  suffixIcon={<DatabaseOutlined />}
                  options={datasources.map((ds) => ({
                    label: ds.name,
                    value: ds.id,
                  }))}
                />
                <Button
                  onClick={clearMessages}
                  type="text"
                  size="small"
                  icon={<EllipsisOutlined />}
                >
                  Clear
                </Button>
              </div>
            </div>
          )}

          <Sender
            value={prompt}
            header={senderHeader}
            onSubmit={handleSubmit}
            onChange={setPrompt}
            prefix={attachmentsNode}
            loading={loading}
            disabled={loading}
            placeholder={
              loading
                ? '🤔 AI is thinking...'
                : '💬 Type a message to analyze your data...'
            }
            className={styles.sender}
          />

          {bubbleItems.length > 0 && showScrollToBottom && (
            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <Button
                type="default"
                size="small"
                icon={<VerticalAlignBottomOutlined />}
                onClick={() => scrollToBottom('smooth')}
              >
                Back to bottom
              </Button>
            </div>
          )}
        </Space>
      </div>
    </div>
  );
};

export default Playground;
