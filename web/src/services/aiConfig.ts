export type SceneType = 'dashboard' | 'data_discuss';

export type LLMSource = {
  id: string;
  name: string;
  provider: string;
  base_url: string;
  model: string;
  api_key?: string;
  description?: string;
  is_default: boolean;
  enabled: boolean;
  capability?: string;
};

export type RuntimeStatus = {
  active_runtime_model?: string | null;
  running_models?: string[];
  local_models?: string[];
  model_capabilities?: Record<string, string>;
};

const parse = async (res: Response) => {
  if (!res.ok) {
    throw new Error(`Request failed: ${res.status}`);
  }
  const body = await res.json();
  return body?.data;
};

export const aiConfigService = {
  async listLLMSources(): Promise<LLMSource[]> {
    const res = await fetch('/api/v1/ai-config/llm-sources');
    return parse(res);
  },

  async createLLMSource(payload: Partial<LLMSource>) {
    const res = await fetch('/api/v1/ai-config/llm-sources', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return parse(res);
  },

  async updateLLMSource(id: string, payload: Partial<LLMSource>) {
    const res = await fetch(`/api/v1/ai-config/llm-sources/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return parse(res);
  },

  async deleteLLMSource(id: string) {
    const res = await fetch(`/api/v1/ai-config/llm-sources/${id}`, {
      method: 'DELETE',
    });
    return parse(res);
  },

  async listPrompts(): Promise<Record<SceneType, string>> {
    const res = await fetch('/api/v1/ai-config/prompts');
    return parse(res);
  },

  async updatePrompt(scene: SceneType, prompt: string) {
    const res = await fetch('/api/v1/ai-config/prompts', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scene, prompt }),
    });
    return parse(res);
  },

  async listSceneBindings(): Promise<Record<SceneType, string>> {
    const res = await fetch('/api/v1/ai-config/scene-llm-binding');
    return parse(res);
  },

  async updateSceneBinding(scene: SceneType, llmSourceId: string) {
    const res = await fetch('/api/v1/ai-config/scene-llm-binding', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scene, llm_source_id: llmSourceId }),
    });
    return parse(res);
  },

  async getRuntimeStatus() {
    const res = await fetch('/api/v1/ai-config/runtime/status');
    return parse(res) as Promise<RuntimeStatus>;
  },

  async activateRuntimeModel(capability: string) {
    const res = await fetch(`/api/v1/ai-config/runtime/activate/${capability}`, {
      method: 'POST',
    });
    return parse(res);
  },

  async getCapabilityModels() {
    const res = await fetch('/api/v1/ai-config/runtime/capabilities');
    return parse(res) as Promise<Record<string, string>>;
  },

  async updateCapabilityModel(capability: string, model: string) {
    const res = await fetch('/api/v1/ai-config/runtime/capabilities', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ capability, model }),
    });
    return parse(res);
  },

  async analyzeVision(prompt: string, image: File) {
    const fd = new FormData();
    fd.append('prompt', prompt);
    fd.append('image', image);
    const res = await fetch('/api/v1/ai-config/vision/analyze', {
      method: 'POST',
      body: fd,
    });
    return parse(res);
  },

  async analyzeTable(prompt: string, tableText: string) {
    const res = await fetch('/api/v1/ai-config/table/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt, table_text: tableText }),
    });
    return parse(res);
  },

  async listRagDocs() {
    const res = await fetch('/api/v1/ai-config/rag/documents');
    return parse(res);
  },

  async uploadRagDoc(file: File) {
    const fd = new FormData();
    fd.append('file', file);
    const res = await fetch('/api/v1/ai-config/rag/documents', {
      method: 'POST',
      body: fd,
    });
    return parse(res);
  },

  async deleteRagDoc(filename: string) {
    const res = await fetch(
      `/api/v1/ai-config/rag/documents/${encodeURIComponent(filename)}`,
      { method: 'DELETE' },
    );
    return parse(res);
  },

  async syncRagVectors() {
    const res = await fetch('/api/v1/ai-config/rag/sync', {
      method: 'POST',
    });
    return parse(res);
  },

  async listDatasourcePresets() {
    const res = await fetch('/api/v1/ai-config/datasource-presets');
    return parse(res);
  },

  async quickCreateMysqlDatasource() {
    const res = await fetch('/api/v1/ai-config/datasource/quick-create/mysql', {
      method: 'POST',
    });
    return parse(res);
  },

  async quickCreateExcelDatasource() {
    const res = await fetch('/api/v1/ai-config/datasource/quick-create/excel', {
      method: 'POST',
    });
    return parse(res);
  },
};
