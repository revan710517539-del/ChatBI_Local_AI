const parse = async (res: Response) => {
  if (!res.ok) {
    throw new Error(`Request failed: ${res.status}`);
  }
  const body = await res.json();
  return body?.data;
};

export const customerInsightService = {
  async listCustomers() {
    const res = await fetch('/api/v1/customer-insight/customers');
    return parse(res);
  },

  async listSegments() {
    const res = await fetch('/api/v1/customer-insight/segments');
    return parse(res);
  },

  async getCustomer(customerId: string) {
    const res = await fetch(`/api/v1/customer-insight/customers/${customerId}`);
    return parse(res);
  },

  async getSegment(segmentId: string) {
    const res = await fetch(`/api/v1/customer-insight/segments/${segmentId}`);
    return parse(res);
  },
};
