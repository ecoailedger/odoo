/**
 * RPC Service
 * Handles communication with the backend API
 */

class RPCService {
    constructor(baseUrl = '') {
        this.baseUrl = baseUrl;
        this.requestQueue = [];
        this.processing = false;
        this.token = null;
        this.sessionId = null;
    }

    /**
     * Set authentication token
     */
    setToken(token) {
        this.token = token;
        if (token) {
            localStorage.setItem('auth_token', token);
        } else {
            localStorage.removeItem('auth_token');
        }
    }

    /**
     * Get authentication token
     */
    getToken() {
        if (!this.token) {
            this.token = localStorage.getItem('auth_token');
        }
        return this.token;
    }

    /**
     * Get authentication headers
     */
    getHeaders() {
        const headers = {
            'Content-Type': 'application/json',
        };

        const token = this.getToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        return headers;
    }

    /**
     * Make HTTP request
     */
    async request(url, options = {}) {
        const fullUrl = this.baseUrl + url;
        const defaultOptions = {
            headers: this.getHeaders(),
        };

        const response = await fetch(fullUrl, { ...defaultOptions, ...options });

        // Handle authentication errors
        if (response.status === 401) {
            this.setToken(null);
            window.dispatchEvent(new CustomEvent('auth:required'));
            throw new Error('Authentication required');
        }

        // Handle other errors
        if (!response.ok) {
            const error = await response.json().catch(() => ({ message: response.statusText }));
            throw new Error(error.message || error.error?.message || 'Request failed');
        }

        return response.json();
    }

    /**
     * JSON-RPC call
     */
    async jsonrpc(method, params = {}) {
        const payload = {
            jsonrpc: '2.0',
            method: method,
            params: params,
            id: Date.now(),
        };

        const response = await this.request('/jsonrpc', {
            method: 'POST',
            body: JSON.stringify(payload),
        });

        if (response.error) {
            throw new Error(response.error.message || 'RPC error');
        }

        return response.result;
    }

    /**
     * Call model method
     */
    async call(model, method, args = [], kwargs = {}) {
        return this.jsonrpc('call', {
            model,
            method,
            args,
            kwargs,
        });
    }

    /**
     * Search records
     */
    async search(model, domain = [], options = {}) {
        const { limit = 80, offset = 0, order = null, fields = null } = options;

        return this.call(model, 'search_read', [domain], {
            fields,
            limit,
            offset,
            order,
        });
    }

    /**
     * Read records by IDs
     */
    async read(model, ids, fields = null) {
        return this.call(model, 'read', [ids], { fields });
    }

    /**
     * Create record
     */
    async create(model, values) {
        return this.call(model, 'create', [values]);
    }

    /**
     * Update records
     */
    async write(model, ids, values) {
        return this.call(model, 'write', [ids, values]);
    }

    /**
     * Delete records
     */
    async unlink(model, ids) {
        return this.call(model, 'unlink', [ids]);
    }

    /**
     * REST API - List records
     */
    async restList(model, params = {}) {
        const query = new URLSearchParams();

        if (params.domain) {
            query.append('domain', JSON.stringify(params.domain));
        }
        if (params.fields) {
            query.append('fields', Array.isArray(params.fields) ? params.fields.join(',') : params.fields);
        }
        if (params.limit) {
            query.append('limit', params.limit);
        }
        if (params.offset) {
            query.append('offset', params.offset);
        }
        if (params.order) {
            query.append('order', params.order);
        }

        const url = `/api/v1/${model}?${query.toString()}`;
        const response = await this.request(url);
        return response.data;
    }

    /**
     * REST API - Get single record
     */
    async restGet(model, id, fields = null) {
        const query = fields ? `?fields=${Array.isArray(fields) ? fields.join(',') : fields}` : '';
        const url = `/api/v1/${model}/${id}${query}`;
        const response = await this.request(url);
        return response.data;
    }

    /**
     * REST API - Create record
     */
    async restCreate(model, values) {
        const url = `/api/v1/${model}`;
        const response = await this.request(url, {
            method: 'POST',
            body: JSON.stringify({ values }),
        });
        return response.data;
    }

    /**
     * REST API - Update record
     */
    async restUpdate(model, id, values) {
        const url = `/api/v1/${model}/${id}`;
        const response = await this.request(url, {
            method: 'PUT',
            body: JSON.stringify({ values }),
        });
        return response.data;
    }

    /**
     * REST API - Delete record
     */
    async restDelete(model, id) {
        const url = `/api/v1/${model}/${id}`;
        await this.request(url, { method: 'DELETE' });
        return true;
    }

    /**
     * Batch RPC calls
     */
    async batch(calls) {
        const requests = calls.map((call, index) => ({
            jsonrpc: '2.0',
            method: 'call',
            params: {
                model: call.model,
                method: call.method,
                args: call.args || [],
                kwargs: call.kwargs || {},
            },
            id: index,
        }));

        const response = await this.request('/jsonrpc/batch', {
            method: 'POST',
            body: JSON.stringify(requests),
        });

        return response.map(r => {
            if (r.error) {
                throw new Error(r.error.message || 'RPC error');
            }
            return r.result;
        });
    }
}

// Export singleton instance
const rpc = new RPCService();

// Make available globally
window.rpc = rpc;

export default rpc;
