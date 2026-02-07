import { Typography } from 'antd';
import markdownit from 'markdown-it';
import React from 'react';
import { createStyles } from 'antd-style';

const md = markdownit({
  html: true,
  breaks: true,
  linkify: true,
  typographer: true,
});

const useStyle = createStyles(({ token, css }) => ({
  markdown: css`
    font-size: 14px;
    line-height: 1.6;

    h1,
    h2,
    h3,
    h4,
    h5,
    h6 {
      margin-top: 16px;
      margin-bottom: 8px;
      font-weight: 600;
    }

    h1 {
      font-size: 24px;
    }
    h2 {
      font-size: 20px;
    }
    h3 {
      font-size: 16px;
    }

    p {
      margin-bottom: 12px;
    }

    code {
      background: ${token.colorFillTertiary};
      padding: 2px 6px;
      border-radius: 4px;
      font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
      font-size: 13px;
    }

    pre {
      background: ${token.colorBgLayout};
      padding: 12px;
      border-radius: 6px;
      overflow-x: auto;
      margin: 12px 0;

      code {
        background: none;
        padding: 0;
      }
    }

    blockquote {
      border-left: 4px solid ${token.colorPrimary};
      padding-left: 12px;
      margin: 12px 0;
      color: ${token.colorTextSecondary};
    }

    ul,
    ol {
      padding-left: 20px;
      margin-bottom: 12px;
    }

    li {
      margin-bottom: 4px;
    }

    a {
      color: ${token.colorPrimary};
      text-decoration: none;

      &:hover {
        text-decoration: underline;
      }
    }

    table {
      border-collapse: collapse;
      width: 100%;
      margin: 12px 0;

      th,
      td {
        border: 1px solid ${token.colorBorder};
        padding: 8px;
        text-align: left;
      }

      th {
        background: ${token.colorFillTertiary};
        font-weight: 600;
      }
    }

    strong {
      font-weight: 600;
      color: ${token.colorText};
    }

    em {
      font-style: italic;
    }
  `,
}));

interface MarkdownViewProps {
  content: string;
}

const MarkdownBase: React.FC<MarkdownViewProps> = ({ content }) => {
  const { styles } = useStyle();

  return (
    <Typography>
      <div
        className={styles.markdown}
        dangerouslySetInnerHTML={{ __html: md.render(content) }}
      />
    </Typography>
  );
};

export default MarkdownBase;
