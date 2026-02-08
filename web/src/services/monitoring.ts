const parse = async (res: Response) => {
  if (!res.ok) {
    throw new Error(`Request failed: ${res.status}`);
  }
  const body = await res.json();
  return body?.data;
};

export const monitoringService = {
  async getRuleConfig() {
    const res = await fetch('/api/v1/monitoring/rule-config');
    return parse(res);
  },

  async updateRuleConfig(rules: any[]) {
    const res = await fetch('/api/v1/monitoring/rule-config', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ rules }),
    });
    return parse(res);
  },

  async getDiagnosisConfig() {
    const res = await fetch('/api/v1/monitoring/diagnosis-config');
    return parse(res);
  },

  async updateDiagnosisConfig(payload: any) {
    const res = await fetch('/api/v1/monitoring/diagnosis-config', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return parse(res);
  },

  async getEmailConfig() {
    const res = await fetch('/api/v1/monitoring/email-config');
    return parse(res);
  },

  async updateEmailConfig(payload: any) {
    const res = await fetch('/api/v1/monitoring/email-config', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return parse(res);
  },

  async getSnapshot() {
    const res = await fetch('/api/v1/monitoring/snapshot');
    return parse(res);
  },

  async checkAlerts(sendEmail = true) {
    const res = await fetch('/api/v1/monitoring/alerts/check', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ send_email: sendEmail }),
    });
    return parse(res);
  },

  async listAlerts(limit = 200, status?: string) {
    const suffix = status
      ? `?limit=${limit}&status=${encodeURIComponent(status)}`
      : `?limit=${limit}`;
    const res = await fetch(`/api/v1/monitoring/alerts${suffix}`);
    return parse(res);
  },

  async ackAlert(alertId: string, note?: string) {
    const res = await fetch(`/api/v1/monitoring/alerts/${alertId}/ack`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ note }),
    });
    return parse(res);
  },

  async resendAlertEmail(alertId: string) {
    const res = await fetch(`/api/v1/monitoring/alerts/${alertId}/send-email`, {
      method: 'POST',
    });
    return parse(res);
  },
};
