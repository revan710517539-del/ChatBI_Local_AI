import type { components } from '../api-schema';
import { client } from '../client';

const unwrapError = (error: any, fallback: string) => {
  return (
    error?.message ||
    error?.detail ||
    error?.error ||
    error?.data?.message ||
    error?.data?.detail ||
    error?.response?.message ||
    fallback
  );
};

export async function analyze(
  question: string,
  datasourceId?: string,
  visualize = true,
  scene: 'dashboard' | 'data_discuss' = 'data_discuss',
  llmSourceId?: string,
  agentProfileId?: string,
) {
  const {
    data, // only present if 2XX response
    error, // only present if 4XX or 5XX response
  } = await client.POST('/api/v1/chat/', {
    body: {
      question,
      visualize,
      datasource_id: datasourceId,
      scene,
      llm_source_id: llmSourceId,
      agent_profile_id: agentProfileId,
    },
  });

  if (error) {
    throw new Error(unwrapError(error, 'Failed to analyze question'));
  }

  return data;
}

export async function generateSql(question: string, visualize = false) {
  const {
    data, // only present if 2XX response
    error, // only present if 4XX or 5XX response
  } = await client.POST('/api/v1/chat/generate_sql', {
    body: {
      question,
      visualize,
    },
  });

  if (error) {
    throw new Error(unwrapError(error, 'Failed to generate SQL'));
  }

  return data;
}

export async function runSql(
  id: string,
  sql: string,
  timeout: number | null = 30,
  max_rows: number | null = 1000,
) {
  const {
    data, // only present if 2XX response
    error, // only present if 4XX or 5XX response
  } = await client.POST('/api/v1/chat/run_sql', {
    body: {
      id,
      sql,
      timeout,
      max_rows,
    },
  });

  if (error) {
    throw new Error(unwrapError(error, 'Failed to execute SQL query'));
  }

  return data;
}

export async function generateVisualize(id: string, question: string) {
  const {
    data, // only present if 2XX response
    error, // only present if 4XX or 5XX response
  } = await client.POST('/api/v1/chat/generate_visualize', {
    body: {
      id,
      question,
      visualize: true,
    },
  });

  if (error) {
    throw error;
  }

  return data as components['schemas']['CommonResponse'];
}
