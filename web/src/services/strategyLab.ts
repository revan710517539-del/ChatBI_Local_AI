const parse = async (res: Response) => {
  if (!res.ok) {
    throw new Error(`Request failed: ${res.status}`);
  }
  const body = await res.json();
  return body?.data;
};

export const strategyLabService = {
  async getSummary() {
    const res = await fetch('/api/v1/strategy-lab/summary');
    return parse(res);
  },

  async listExperiments(limit = 100) {
    const res = await fetch(`/api/v1/strategy-lab/experiments?limit=${limit}`);
    return parse(res);
  },

  async getExperiment(id: string) {
    const res = await fetch(`/api/v1/strategy-lab/experiments/${id}`);
    return parse(res);
  },

  async getExperimentTrend(id: string) {
    const res = await fetch(`/api/v1/strategy-lab/experiments/${id}/trend`);
    return parse(res);
  },

  async createFromStrategy(payload: {
    strategy_id: string;
    name?: string;
    sample_size_control?: number;
    sample_size_treatment?: number;
    duration_days?: number;
  }) {
    const res = await fetch('/api/v1/strategy-lab/experiments/from-strategy', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return parse(res);
  },

  async updateStatus(id: string, status: string) {
    const res = await fetch(`/api/v1/strategy-lab/experiments/${id}/status`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status }),
    });
    return parse(res);
  },
};
