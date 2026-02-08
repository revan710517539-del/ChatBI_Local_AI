const parse = async (res: Response) => {
  if (!res.ok) {
    throw new Error(`Request failed: ${res.status}`);
  }
  const body = await res.json();
  return body?.data;
};

export const mcpSkillService = {
  async listMcpServers() {
    const res = await fetch('/api/v1/mcp-skill/mcp-servers');
    return parse(res);
  },

  async updateMcpServer(id: string, payload: any) {
    const res = await fetch(`/api/v1/mcp-skill/mcp-servers/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return parse(res);
  },

  async listSkills() {
    const res = await fetch('/api/v1/mcp-skill/skills');
    return parse(res);
  },

  async updateSkill(id: string, payload: any) {
    const res = await fetch(`/api/v1/mcp-skill/skills/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return parse(res);
  },

  async getEmailConfig() {
    const res = await fetch('/api/v1/mcp-skill/email-config');
    return parse(res);
  },

  async updateEmailConfig(payload: any) {
    const res = await fetch('/api/v1/mcp-skill/email-config', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return parse(res);
  },

  async listStrategies(limit = 100) {
    const res = await fetch(`/api/v1/mcp-skill/strategies?limit=${limit}`);
    return parse(res);
  },

  async generateStrategy(payload: any) {
    const res = await fetch('/api/v1/mcp-skill/strategies/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return parse(res);
  },

  async sendStrategyEmail(strategyId: string) {
    const res = await fetch(`/api/v1/mcp-skill/strategies/${strategyId}/send-email`, {
      method: 'POST',
    });
    return parse(res);
  },

  async approveStrategy(strategyId: string, replyText = 'AGREE', execute = true) {
    const res = await fetch(`/api/v1/mcp-skill/strategies/${strategyId}/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reply_text: replyText, execute }),
    });
    return parse(res);
  },

  async refineStrategy(strategyId: string, discussion: string, operator = 'human') {
    const res = await fetch(`/api/v1/mcp-skill/strategies/${strategyId}/refine`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ discussion, operator }),
    });
    return parse(res);
  },
};
