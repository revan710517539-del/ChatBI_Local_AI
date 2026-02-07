const parse = async (res: Response) => {
  if (!res.ok) {
    throw new Error(`Request failed: ${res.status}`);
  }
  const body = await res.json();
  return body?.data;
};

export const dashboardService = {
  async getLoanKpis(datasourceId?: string) {
    const q = datasourceId ? `?datasource_id=${encodeURIComponent(datasourceId)}` : '';
    const res = await fetch(`/api/v1/dashboard/loan-kpis${q}`);
    return parse(res);
  },

  async getIndicatorDefinitions() {
    const res = await fetch('/api/v1/dashboard/indicator-definitions');
    return parse(res);
  },
};
