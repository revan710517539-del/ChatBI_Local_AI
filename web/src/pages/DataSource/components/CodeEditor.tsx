import React, { useRef, useEffect } from 'react';
import Editor, { OnMount } from '@monaco-editor/react';
import { useTheme } from 'antd-style';
import type { editor } from 'monaco-editor';
import { Space, Button, Tooltip, message } from 'antd';
import {
  FormatPainterOutlined,
  ClearOutlined,
  PlayCircleOutlined,
} from '@ant-design/icons';
import { format } from 'sql-formatter';

type CodeEditorProps = {
  value: string;
  onChange: (value: string) => void;
  language?: string;
  height?: string | number;
  width?: string;
  onExecute?: () => void;
  schema?: any; // Schema for autocomplete suggestions
};

const CodeEditor: React.FC<CodeEditorProps> = ({
  value,
  onChange,
  language = 'sql',
  height = 200,
  width = '100%',
  onExecute,
  schema,
}) => {
  const theme = useTheme();
  const editorRef = useRef<editor.IStandaloneCodeEditor | null>(null);
  const monacoRef = useRef<typeof import('monaco-editor') | null>(null);

  const handleEditorChange = (value: string | undefined) => {
    onChange(value || '');
  };

  const handleFormat = () => {
    if (!value) return;
    try {
      const formatted = format(value, {
        language: 'postgresql',
        uppercase: true,
      });
      onChange(formatted);
      message.success('SQL formatted');
    } catch (error) {
      console.error('Failed to format SQL:', error);
      message.error('Format failed: ' + (error as Error).message);
    }
  };

  const handleClear = () => {
    onChange('');
  };

  const handleEditorDidMount: OnMount = (editor, monaco) => {
    editorRef.current = editor;
    // monacoRef.current = monaco;  // Type compatibility issue with different monaco imports

    // Setup keyboard shortcuts
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, () => {
      if (onExecute) {
        onExecute();
      }
    });

    // Enable autocomplete for SQL
    if (language === 'sql' && schema) {
      // Register SQL keywords and schema-based suggestions
      monaco.languages.registerCompletionItemProvider('sql', {
        provideCompletionItems: (model, position) => {
          const suggestions: any[] = [];

          // SQL keywords
          const keywords = [
            'SELECT',
            'FROM',
            'WHERE',
            'JOIN',
            'INNER JOIN',
            'LEFT JOIN',
            'RIGHT JOIN',
            'ON',
            'GROUP BY',
            'HAVING',
            'ORDER BY',
            'LIMIT',
            'OFFSET',
            'INSERT',
            'UPDATE',
            'DELETE',
            'CREATE',
            'DROP',
            'ALTER',
            'AND',
            'OR',
            'NOT',
            'IN',
            'LIKE',
            'BETWEEN',
            'AS',
            'DISTINCT',
            'COUNT',
            'SUM',
            'AVG',
            'MIN',
            'MAX',
          ];

          keywords.forEach((keyword) => {
            suggestions.push({
              label: keyword,
              kind: monaco.languages.CompletionItemKind.Keyword,
              insertText: keyword,
              documentation: `SQL keyword: ${keyword}`,
            });
          });

          // Add table names from schema
          if (schema && schema.tables) {
            schema.tables.forEach((table: any) => {
              suggestions.push({
                label: table.name,
                kind: monaco.languages.CompletionItemKind.Class,
                insertText: table.name,
                documentation: `Table: ${table.name}`,
                detail: 'Table',
              });

              // Add columns
              if (table.columns) {
                table.columns.forEach((column: any) => {
                  suggestions.push({
                    label: `${table.name}.${column.name}`,
                    kind: monaco.languages.CompletionItemKind.Field,
                    insertText: `${table.name}.${column.name}`,
                    documentation: `${column.type}${
                      column.primary_key ? ' (Primary Key)' : ''
                    }`,
                    detail: column.type,
                  });
                });
              }
            });
          }

          return { suggestions };
        },
      });
    }

    // Set editor focus
    editor.focus();
  };

  return (
    <div
      style={{
        position: 'relative',
        border: `1px solid ${theme.colorBorder}`,
        borderRadius: theme.borderRadius,
        height: height,
        minHeight: 200,
      }}
    >
      <div
        style={{
          position: 'absolute',
          top: 8,
          right: 24,
          zIndex: 10,
        }}
      >
        <Space size="small">
          {onExecute && (
            <Tooltip title="Run Query (Cmd/Ctrl + Enter)">
              <Button
                size="small"
                type="primary"
                icon={<PlayCircleOutlined />}
                onClick={onExecute}
              >
                Run
              </Button>
            </Tooltip>
          )}
          <Tooltip title="Format SQL">
            <Button
              size="small"
              icon={<FormatPainterOutlined />}
              onClick={handleFormat}
            />
          </Tooltip>
          <Tooltip title="Clear">
            <Button
              size="small"
              icon={<ClearOutlined />}
              onClick={handleClear}
            />
          </Tooltip>
        </Space>
      </div>
      <Editor
        height="100%"
        width={width}
        language={language}
        value={value}
        onChange={handleEditorChange}
        onMount={handleEditorDidMount}
        theme={theme.isDarkMode ? 'vs-dark' : 'light'}
        options={{
          minimap: { enabled: false },
          fontSize: 14,
          scrollBeyondLastLine: false,
          lineNumbers: 'on',
          scrollBeyondLastLine: false,
          automaticLayout: true,
          wordWrap: 'on',
          formatOnPaste: true,
          formatOnType: true,
          suggestOnTriggerCharacters: true,
          quickSuggestions: true,
          tabSize: 2,
          renderWhitespace: 'selection',
          folding: true,
          lineDecorationsWidth: 10,
          lineNumbersMinChars: 3,
        }}
      />
    </div>
  );
};

export default CodeEditor;
