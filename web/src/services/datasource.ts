import { client } from './client';
import { paths } from './api-schema';
import type { components } from './api-schema';

// Define TypeScript types based on API paths
type DataSourceResponse =
  paths['/api/v1/datasources/{datasource_id}']['get']['responses']['200']['content']['application/json'];
type DataSourceListResponse =
  paths['/api/v1/datasources']['get']['responses']['200']['content']['application/json'];
type DataSourceCreateRequest =
  paths['/api/v1/datasources']['post']['requestBody']['content']['application/json'];
type DataSourceUpdateRequest =
  paths['/api/v1/datasources/{datasource_id}']['put']['requestBody']['content']['application/json'];
type DataSourceTestConnectionRequest =
  paths['/api/v1/datasources/test-connection']['post']['requestBody']['content']['application/json'];
type QueryResponse =
  paths['/api/v1/datasources/{datasource_id}/query']['post']['responses']['200']['content']['application/json'];
type SchemaResponse =
  paths['/api/v1/datasources/{datasource_id}/schema']['get']['responses']['200']['content']['application/json'];

// Export more precise types for component use
export type DatasourceType = components['schemas']['DataSourceResponse'];
export type QueryResultType = components['schemas']['QueryResult'];
export type SchemaMetadataType = components['schemas']['SchemaMetadata'];

/**
 * Datasource service providing methods for interacting with datasource API endpoints
 */
export const datasourceService = {
  /**
   * Get a paginated list of datasources
   * @param params - Pagination parameters and filters
   * @returns List of datasources
   */
  async getDatasources(params?: {
    skip?: number;
    limit?: number;
    type?: string;
    status?: string;
  }): Promise<DataSourceListResponse> {
    try {
      const response = await client.GET('/api/v1/datasources', {
        params: {
          query: (params as any) || { skip: 0, limit: 100 },
        },
      });
      return response.data as DataSourceListResponse;
    } catch (error) {
      console.error('Failed to fetch datasources:', error);
      throw error;
    }
  },

  /**
   * Get a datasource by ID
   * @param id - Datasource ID
   * @returns Datasource details
   */
  async getDatasource(id: string): Promise<DatasourceType> {
    try {
      const response = await client.GET('/api/v1/datasources/{datasource_id}', {
        params: {
          path: { datasource_id: id },
        },
      });
      // Extract the actual datasource from StandardResponse wrapper
      const data = response.data as any;
      return (data?.data || data) as DatasourceType;
    } catch (error) {
      console.error(`Failed to fetch datasource ${id}:`, error);
      throw error;
    }
  },

  /**
   * Create a new datasource
   * @param data - Datasource creation data
   * @returns Created datasource
   */
  async createDatasource(
    data: DataSourceCreateRequest,
  ): Promise<DataSourceResponse> {
    try {
      const response = await client.POST('/api/v1/datasources', {
        body: data,
      });
      // Extract from StandardResponse wrapper
      const result = response.data as any;
      return (result?.data || result) as DataSourceResponse;
    } catch (error) {
      console.error('Failed to create datasource:', error);
      throw error;
    }
  },

  /**
   * Update an existing datasource
   * @param id - Datasource ID
   * @param data - Datasource update data
   * @returns Updated datasource
   */
  async updateDatasource(
    id: string,
    data: DataSourceUpdateRequest,
  ): Promise<DataSourceResponse> {
    try {
      const response = await client.PUT('/api/v1/datasources/{datasource_id}', {
        params: {
          path: { datasource_id: id },
        },
        body: data,
      });
      // Extract from StandardResponse wrapper
      const result = response.data as any;
      return (result?.data || result) as DataSourceResponse;
    } catch (error) {
      console.error(`Failed to update datasource ${id}:`, error);
      throw error;
    }
  },

  /**
   * Delete a datasource
   * @param id - Datasource ID
   * @returns Deletion status
   */
  async deleteDatasource(id: string): Promise<void> {
    try {
      await client.DELETE('/api/v1/datasources/{datasource_id}', {
        params: {
          path: { datasource_id: id },
        },
      });
      return;
    } catch (error) {
      console.error(`Failed to delete datasource ${id}:`, error);
      throw error;
    }
  },

  /**
   * Test connection to a datasource
   * @param data - Connection details to test
   * @returns Connection status
   */
  async testConnection(
    data: DataSourceTestConnectionRequest,
  ): Promise<{ status: string; message?: string }> {
    try {
      const response = await client.POST(
        '/api/v1/datasources/test-connection',
        {
          body: data,
        },
      );
      // Extract from StandardResponse wrapper
      const result = response.data as any;
      const testResult = result?.data || result;
      return {
        status: testResult?.success ? 'success' : 'error',
        message: testResult?.message || 'Test completed',
      };
    } catch (error) {
      console.error('Connection test failed:', error);
      throw error;
    }
  },

  /**
   * Execute a SQL query against a datasource
   * @param id - Datasource ID
   * @param query - SQL query string
   * @param timeout - Query timeout in seconds
   * @param maxRows - Maximum number of rows to return
   * @returns Query results
   */
  async executeQuery(
    id: string,
    query: string,
    timeout = 30,
    maxRows = 1000,
  ): Promise<QueryResultType> {
    try {
      const response = await client.POST(
        '/api/v1/datasources/{datasource_id}/query',
        {
          params: {
            path: { datasource_id: id },
          },
          body: {
            sql: query,
            timeout,
            max_rows: maxRows,
          },
        },
      );
      // Extract from StandardResponse wrapper
      const result = response.data as any;
      return (result?.data || result) as QueryResultType;
    } catch (error) {
      console.error(`Failed to execute query on datasource ${id}:`, error);
      throw error;
    }
  },

  /**
   * Get schema metadata for a datasource
   * @param id - Datasource ID
   * @returns Database schema information
   */
  async getDatabaseSchema(id: string): Promise<SchemaMetadataType> {
    try {
      const response = await client.GET(
        '/api/v1/datasources/{datasource_id}/schema',
        {
          params: {
            path: { datasource_id: id },
          },
        },
      );
      // Extract from StandardResponse wrapper
      const result = response.data as any;
      return (result?.data || result) as SchemaMetadataType;
    } catch (error) {
      console.error(`Failed to fetch schema for datasource ${id}:`, error);
      throw error;
    }
  },
};

// Export individual functions for backward compatibility
export const {
  getDatasources,
  getDatasource,
  createDatasource,
  updateDatasource,
  deleteDatasource,
  testConnection,
  executeQuery,
  getDatabaseSchema,
} = datasourceService;
