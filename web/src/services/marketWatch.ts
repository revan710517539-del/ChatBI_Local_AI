const parse = async (res: Response) => {
  if (!res.ok) {
    throw new Error(`Request failed: ${res.status}`);
  }
  const body = await res.json();
  return body?.data;
};

export const marketWatchService = {
  async listSources() {
    const res = await fetch('/api/v1/market-watch/sources');
    return parse(res);
  },

  async getSnapshot(limit = 8, forceRefresh = false) {
    const res = await fetch(
      `/api/v1/market-watch/snapshot?limit=${limit}&force_refresh=${forceRefresh}`,
    );
    return parse(res);
  },

  async getAnalysis(limit = 8, forceRefresh = false) {
    const res = await fetch(
      `/api/v1/market-watch/analysis?limit=${limit}&force_refresh=${forceRefresh}`,
    );
    return parse(res);
  },

  async refresh(limit = 8) {
    const res = await fetch(`/api/v1/market-watch/refresh?limit=${limit}`, {
      method: 'POST',
    });
    return parse(res);
  },
};
