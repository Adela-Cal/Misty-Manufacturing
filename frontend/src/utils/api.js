import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

export const api = axios.create({
  baseURL: `${BACKEND_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for adding auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for handling errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// API helper functions
export const apiHelpers = {
  // Authentication
  login: (credentials) => api.post('/auth/login', credentials),
  getCurrentUser: () => api.get('/auth/me'),
  
  // Clients
  getClients: () => api.get('/clients'),
  createClient: (data) => api.post('/clients', data),
  updateClient: (id, data) => api.put(`/clients/${id}`, data),
  getClient: (id) => api.get(`/clients/${id}`),
  uploadClientLogo: (id, file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post(`/clients/${id}/logo`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
  
  // Products
  getClientProducts: (clientId) => api.get(`/clients/${clientId}/products`),
  createProduct: (data) => api.post('/products', data),
  updateProduct: (id, data) => api.put(`/products/${id}`, data),
  getProduct: (id) => api.get(`/products/${id}`),
  
  // Orders
  getOrders: (statusFilter) => api.get('/orders', { params: { status_filter: statusFilter } }),
  createOrder: (data) => api.post('/orders', data),
  getOrder: (id) => api.get(`/orders/${id}`),
  updateOrder: (id, data) => api.put(`/orders/${id}`, data),
  updateOrderStage: (id, data) => api.put(`/orders/${id}/stage`, data),
  
  // Job Specifications
  createJobSpecification: (data) => api.post('/job-specifications', data),
  getJobSpecificationByOrder: (orderId) => api.get(`/orders/${orderId}/job-specification`),
  
  // Production Board
  getProductionBoard: () => api.get('/production/board'),
  getProductionLogs: (orderId) => api.get(`/production/logs/${orderId}`),
  
  // Reports
  getOutstandingJobsReport: () => api.get('/reports/outstanding-jobs'),
  getLateDeliveriesReport: () => api.get('/reports/late-deliveries'),
  getCustomerAnnualReport: (clientId, year) => api.get(`/reports/customer-annual/${clientId}`, { params: { year } }),
  
  // Documents
  generateAcknowledgment: (orderId) => api.get(`/documents/acknowledgment/${orderId}`, { responseType: 'blob' }),
  generateJobCard: (orderId) => api.get(`/documents/job-card/${orderId}`, { responseType: 'blob' }),
  generatePackingList: (orderId) => api.get(`/documents/packing-list/${orderId}`, { responseType: 'blob' }),
  generateInvoice: (orderId) => api.get(`/documents/invoice/${orderId}`, { responseType: 'blob' }),
  
  // Invoicing
  getLiveJobs: () => api.get('/invoicing/live-jobs'),
  getArchivedJobs: (month, year) => api.get('/invoicing/archived-jobs', { params: { month, year } }),
  generateJobInvoice: (jobId, invoiceData) => api.post(`/invoicing/generate/${jobId}`, invoiceData),
  getMonthlyReport: (month, year) => api.get('/invoicing/monthly-report', { params: { month, year } }),
};

// File download helper
export const downloadFile = (blob, filename) => {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
};

// Format currency
export const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-AU', {
    style: 'currency',
    currency: 'AUD',
  }).format(amount);
};

// Format date
export const formatDate = (date) => {
  return new Intl.DateTimeFormat('en-AU', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  }).format(new Date(date));
};

// Format date for input
export const formatDateForInput = (date) => {
  return new Date(date).toISOString().split('T')[0];
};

// Production stage display names
export const stageDisplayNames = {
  order_entered: 'Order Entered',
  pending_material: 'Pending Material',
  paper_slitting: 'Paper Slitting',
  winding: 'Winding',
  finishing: 'Finishing',
  delivery: 'Delivery',
  invoicing: 'Invoicing',
  cleared: 'Cleared'
};

// Stage colors
export const stageColors = {
  order_entered: 'bg-blue-900 border-blue-700',
  pending_material: 'bg-orange-900 border-orange-700',
  paper_slitting: 'bg-purple-900 border-purple-700',
  winding: 'bg-indigo-900 border-indigo-700',
  finishing: 'bg-green-900 border-green-700',
  delivery: 'bg-teal-900 border-teal-700',
  invoicing: 'bg-yellow-900 border-yellow-700'
};

// User role display names
export const roleDisplayNames = {
  admin: 'Administrator',
  production_manager: 'Production Manager',
  sales: 'Sales',
  production_team: 'Production Team'
};