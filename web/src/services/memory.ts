const parse = async (res: Response) => {
  if (!res.ok) {
    throw new Error(`Request failed: ${res.status}`);
  }
  const body = await res.json();
  return body?.data;
};

export const memoryService = {
  async getSettings() {
    const res = await fetch('/api/v1/memory/settings');
    return parse(res);
  },

  async updateSettings(payload: Record<string, any>) {
    const res = await fetch('/api/v1/memory/settings', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return parse(res);
  },

  async listEvents(params?: { limit?: number; scene?: string; event_type?: string }) {
    const q = new URLSearchParams();
    if (params?.limit) q.set('limit', String(params.limit));
    if (params?.scene) q.set('scene', params.scene);
    if (params?.event_type) q.set('event_type', params.event_type);
    const suffix = q.toString() ? `?${q.toString()}` : '';
    const res = await fetch(`/api/v1/memory/events${suffix}`);
    return parse(res);
  },

  async recordEvent(payload: Record<string, any>) {
    const res = await fetch('/api/v1/memory/events', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return parse(res);
  },

  async search(query: string, limit = 20, scene?: string) {
    const res = await fetch('/api/v1/memory/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, limit, scene }),
    });
    return parse(res);
  },
};
