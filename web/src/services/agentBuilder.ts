const parse = async (res: Response) => {
  if (!res.ok) {
    throw new Error(`Request failed: ${res.status}`);
  }
  const body = await res.json();
  return body?.data;
};

export const agentBuilderService = {
  async listProfiles() {
    const res = await fetch('/api/v1/agent-builder/profiles');
    return parse(res);
  },

  async createProfile(payload: any) {
    const res = await fetch('/api/v1/agent-builder/profiles', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return parse(res);
  },

  async updateProfile(id: string, payload: any) {
    const res = await fetch(`/api/v1/agent-builder/profiles/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return parse(res);
  },

  async deleteProfile(id: string) {
    const res = await fetch(`/api/v1/agent-builder/profiles/${id}`, {
      method: 'DELETE',
    });
    return parse(res);
  },

  async listExecutionLogs(profileId: string, limit = 200) {
    const res = await fetch(
      `/api/v1/agent-builder/profiles/${profileId}/logs?limit=${limit}`,
    );
    return parse(res);
  },

  async clearExecutionLogs(profileId: string) {
    const res = await fetch(`/api/v1/agent-builder/profiles/${profileId}/logs`, {
      method: 'DELETE',
    });
    return parse(res);
  },
};
