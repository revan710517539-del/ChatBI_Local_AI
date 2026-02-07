import { logger } from '@/utils/logger';
import { create } from 'zustand';
import { createJSONStorage, persist } from 'zustand/middleware';

const log = logger.extend('ChatStore');

type ChatStore = {
  prompt: string;
  chatType: string;
  messages: Chat.IMessage[];
  visualizing: boolean;
  autoVisualize: boolean;
  autoVizType: string;
  datasourceId: string | undefined;
  llmSourceId: string | undefined;
  agentProfileId: string | undefined;
  scene: 'dashboard' | 'data_discuss';

  setMessages: (messages: Chat.IMessage[]) => void;
  setPrompt: (prompt: string) => void;
  clearMessages: () => void;
  setChatType: (chatType: string) => void;
  setAutoVisualize: (autoVisualize: boolean) => void;
  setVisualizing: (visualizing: boolean) => void;
  setAutoVizType: (autoVizType: string) => void;
  addMessage: (messages: Chat.IMessage[]) => void;
  setDatasourceId: (datasourceId: string | undefined) => void;
  setLlmSourceId: (llmSourceId: string | undefined) => void;
  setAgentProfileId: (agentProfileId: string | undefined) => void;
  setScene: (scene: 'dashboard' | 'data_discuss') => void;
};

const useChatDbStore = create(
  persist<ChatStore>(
    (set) => ({
      prompt: '',
      messages: [],
      chatType: 'chat',
      autoVisualize: true,
      visualizing: false,
      autoVizType: 'ava',
      datasourceId: undefined,
      llmSourceId: undefined,
      agentProfileId: undefined,
      scene: 'data_discuss',

      setAutoVizType: (autoVizType: string) => {
        set(() => {
          return {
            autoVizType,
          };
        });
      },
      setVisualizing: (visualizing: boolean) => {
        set(() => {
          return {
            visualizing,
          };
        });
      },
      setAutoVisualize: (autoVisualize: boolean) => {
        set(() => {
          return {
            autoVisualize,
          };
        });
      },
      setChatType: (chatType: string) => {
        set(() => {
          return {
            chatType,
          };
        });
      },
      clearMessages: () => {
        set(() => {
          return {
            messages: [],
          };
        });
      },
      setMessages: (messages: Chat.IMessage[]) => {
        log('setMessages', messages);
        set((state) => {
          return {
            messages: [...state.messages, ...messages],
          };
        });
      },
      addMessage: (messages: Chat.IMessage[]) => {
        log('addMessage', messages);
        set((state) => {
          return {
            messages: [...state.messages, ...messages],
          };
        });
      },
      setPrompt: (prompt: string) => {
        set(() => {
          return {
            prompt,
          };
        });
      },
      setDatasourceId: (datasourceId: string | undefined) => {
        set(() => {
          return {
            datasourceId,
          };
        });
      },
      setLlmSourceId: (llmSourceId: string | undefined) => {
        set(() => ({ llmSourceId }));
      },
      setAgentProfileId: (agentProfileId: string | undefined) => {
        set(() => ({ agentProfileId }));
      },
      setScene: (scene: 'dashboard' | 'data_discuss') => {
        set(() => ({ scene }));
      },
    }),
    {
      name: 'chat-db-storage',
      storage: createJSONStorage(() => localStorage),
    },
  ),
);

export default useChatDbStore;
