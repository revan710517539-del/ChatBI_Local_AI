const parse = async (res: Response) => {
  if (!res.ok) {
    throw new Error(`Request failed: ${res.status}`);
  }
  const body = await res.json();
  return body?.data;
};

export const planningService = {
  async listRules() {
    const res = await fetch('/api/v1/planning/rules');
    return parse(res);
  },

  async updateRules(rules: any[]) {
    const res = await fetch('/api/v1/planning/rules', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ rules }),
    });
    return parse(res);
  },

  async listChains() {
    const res = await fetch('/api/v1/planning/chains');
    return parse(res);
  },

  async updateChains(chains: any[]) {
    const res = await fetch('/api/v1/planning/chains', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ chains }),
    });
    return parse(res);
  },

  async buildPlan(question: string, scene = 'data_discuss', loanType?: string) {
    const res = await fetch('/api/v1/planning/plan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, scene, loan_type: loanType }),
    });
    return parse(res);
  },

  async listPlanHistory(limit = 100) {
    const res = await fetch(`/api/v1/planning/plans?limit=${limit}`);
    return parse(res);
  },

  async startExecution(payload: {
    plan_id?: string;
    question?: string;
    scene?: string;
    loan_type?: string;
    auto_start?: boolean;
  }) {
    const res = await fetch('/api/v1/planning/executions/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return parse(res);
  },

  async listExecutions(limit = 100) {
    const res = await fetch(`/api/v1/planning/executions?limit=${limit}`);
    return parse(res);
  },

  async getExecution(executionId: string) {
    const res = await fetch(`/api/v1/planning/executions/${executionId}`);
    return parse(res);
  },

  async taskAction(
    executionId: string,
    taskId: string,
    action: 'start' | 'complete' | 'fail' | 'retry' | 'skip',
    note?: string,
  ) {
    const res = await fetch(`/api/v1/planning/executions/${executionId}/task-action`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ task_id: taskId, action, note }),
    });
    return parse(res);
  },

  async tickExecution(executionId: string) {
    const res = await fetch(`/api/v1/planning/executions/${executionId}/tick`, {
      method: 'POST',
    });
    return parse(res);
  },

  async runExecution(executionId: string, maxSteps = 20) {
    const res = await fetch(`/api/v1/planning/executions/${executionId}/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ max_steps: maxSteps }),
    });
    return parse(res);
  },

  async listExecutionLogs(limit = 200, executionId?: string) {
    const suffix = executionId
      ? `?limit=${limit}&execution_id=${encodeURIComponent(executionId)}`
      : `?limit=${limit}`;
    const res = await fetch(`/api/v1/planning/execution${suffix}`);
    return parse(res);
  },
};
