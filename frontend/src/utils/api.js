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
  deleteClient: (id) => api.delete(`/clients/${id}`),
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
  getProducts: () => api.get('/products'),
  getClientProducts: (clientId) => api.get(`/clients/${clientId}/products`),
  createProduct: (data) => api.post('/products', data),
  updateProduct: (id, data) => api.put(`/products/${id}`, data),
  getProduct: (id) => api.get(`/products/${id}`),
  
  // Materials
  getMaterials: () => api.get('/materials'),
  createMaterial: (data) => api.post('/materials', data),
  updateMaterial: (id, data) => api.put(`/materials/${id}`, data),
  getMaterial: (id) => api.get(`/materials/${id}`),
  deleteMaterial: (id) => api.delete(`/materials/${id}`),
  
  // Suppliers  
  getSuppliers: () => api.get('/suppliers'),
  createSupplier: (data) => api.post('/suppliers', data),
  updateSupplier: (id, data) => api.put(`/suppliers/${id}`, data),
  getSupplier: (id) => api.get(`/suppliers/${id}`),
  deleteSupplier: (id) => api.delete(`/suppliers/${id}`),
  
  // Product Specifications
  getProductSpecifications: () => api.get('/product-specifications'),
  createProductSpecification: (data) => api.post('/product-specifications', data),
  updateProductSpecification: (id, data) => api.put(`/product-specifications/${id}`, data),
  getProductSpecification: (id) => api.get(`/product-specifications/${id}`),
  deleteProductSpecification: (id) => api.delete(`/product-specifications/${id}`),
  syncProductSpecToClientProducts: (specId) => api.post('/sync/product-spec-to-client-products', null, { params: { spec_id: specId } }),
  syncClientProductToSpec: (clientId, productId) => api.post('/sync/client-product-to-spec', null, { params: { client_id: clientId, product_id: productId } }),
  
  // Calculators
  calculateMaterialConsumptionByClient: (data) => api.post('/calculators/material-consumption-by-client', data),
  calculateMaterialPermutation: (data) => api.post('/calculators/material-permutation', data),
  calculateSpiralCoreConsumption: (data) => api.post('/calculators/spiral-core-consumption', data),
  
  // Stocktake
  getCurrentStocktake: () => api.get('/stocktake/current'),
  createStocktake: (data) => api.post('/stocktake', data),
  updateStocktakeEntry: (stocktakeId, data) => api.put(`/stocktake/${stocktakeId}/entry`, data),
  completeStocktake: (stocktakeId) => api.post(`/stocktake/${stocktakeId}/complete`),
  
  // Client Product Catalogue
  getClientCatalogue: (clientId) => api.get(`/clients/${clientId}/catalog`),
  getClientProduct: (clientId, productId) => api.get(`/clients/${clientId}/catalog/${productId}`),
  createClientProduct: (clientId, data) => api.post(`/clients/${clientId}/catalog`, data),
  updateClientProduct: (clientId, productId, data) => api.put(`/clients/${clientId}/catalog/${productId}`, data),
  getClientProduct: (clientId, productId) => api.get(`/clients/${clientId}/catalog/${productId}`),
  deleteClientProduct: (clientId, productId) => api.delete(`/clients/${clientId}/catalog/${productId}`),
  copyClientProduct: (clientId, productId, targetClientId) => api.post(`/clients/${clientId}/catalog/${productId}/copy-to/${targetClientId}`),
  
  // Orders
  getOrders: (statusFilter) => api.get('/orders', { params: { status_filter: statusFilter } }),
  createOrder: (data) => api.post('/orders', data),
  getOrder: (id) => api.get(`/orders/${id}`),
  deleteOrder: (id) => api.delete(`/orders/${id}`),
  updateOrder: (id, data) => api.put(`/orders/${id}`, data),
  updateOrderStage: (id, data) => api.put(`/orders/${id}/stage`, data),
  
  // Job Specifications
  createJobSpecification: (data) => api.post('/job-specifications', data),
  getJobSpecificationByOrder: (orderId) => api.get(`/orders/${orderId}/job-specification`),
  
  // Production Board
  getProductionBoard: () => api.get('/production/board'),
  getProductionLogs: (orderId) => api.get(`/production/logs/${orderId}`),
  moveOrderStage: (orderId, data) => api.post(`/production/move-stage/${orderId}`, data),
  jumpToStage: (orderId, data) => api.post(`/production/jump-stage/${orderId}`, data),
  reorderJobs: (data) => api.put('/orders/reorder', data),
  getMaterialsStatus: (orderId) => api.get(`/production/materials-status/${orderId}`),
  updateMaterialsStatus: (orderId, data) => api.put(`/production/materials-status/${orderId}`, data),
  updateOrderItemStatus: (orderId, data) => api.put(`/production/order-item-status/${orderId}`, data),
  
  // Jobs
  getJob: (jobId) => api.get(`/jobs/${jobId}`),
  getClientArchivedJobs: (clientId) => api.get(`/clients/${clientId}/archived-jobs`),
  getClientJobCards: (clientId) => api.get(`/clients/${clientId}/job-cards`),
  
  // Reports
  getOutstandingJobsReport: () => api.get('/reports/outstanding-jobs'),
  getLateDeliveriesReport: () => api.get('/reports/late-deliveries'),
  getCustomerAnnualReport: (clientId, year) => api.get(`/reports/customer-annual/${clientId}`, { params: { year } }),
  getDetailedMaterialUsageReport: (materialId, startDate, endDate, includeOrderBreakdown) => 
    api.get('/stock/reports/material-usage-detailed', { 
      params: { 
        material_id: materialId, 
        start_date: startDate, 
        end_date: endDate,
        include_order_breakdown: includeOrderBreakdown
      } 
    }),
  getDetailedProductUsageReport: (clientId, startDate, endDate, includeOrderBreakdown) => 
    api.get('/stock/reports/product-usage-detailed', { 
      params: { 
        client_id: clientId, 
        start_date: startDate, 
        end_date: endDate,
        include_order_breakdown: includeOrderBreakdown
      } 
    }),
  getProjectedOrderAnalysis: (clientId, startDate, endDate) => 
    api.get('/stock/reports/projected-order-analysis', { 
      params: { 
        client_id: clientId, 
        start_date: startDate, 
        end_date: endDate
      } 
    }),
  getJobCardPerformance: (startDate, endDate) => 
    api.get('/stock/reports/job-card-performance', { 
      params: { 
        start_date: startDate, 
        end_date: endDate
      } 
    }),
  exportJobCardPerformanceCSV: (startDate, endDate) => 
    api.get('/stock/reports/job-card-performance/export-csv', { 
      params: { 
        start_date: startDate, 
        end_date: endDate
      },
      responseType: 'blob'
    }),
  
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
  
  // Accounting Transactions
  getAccountingTransactions: () => api.get('/invoicing/accounting-transactions'),
  completeAccountingTransaction: (jobId) => api.post(`/invoicing/complete-transaction/${jobId}`),
  exportDraftedInvoicesCSV: () => api.get('/invoicing/export-drafted-csv', { responseType: 'blob' }),
  
  // Xero Integration
  checkXeroConnection: () => api.get('/xero/status'),
  getXeroAuthUrl: () => api.get('/xero/auth/url'),
  handleXeroCallback: (data) => {
    // Use direct route to bypass /api routing issues
    return axios.post(`${BACKEND_URL}/xero-auth-callback`, data, {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    });
  },
  disconnectXero: () => api.delete('/xero/disconnect'),
  getNextXeroInvoiceNumber: () => api.get('/xero/next-invoice-number'),
  createXeroDraftInvoice: (invoiceData) => api.post('/xero/create-draft-invoice', invoiceData),
  getXeroAccountCodes: () => api.get('/xero/account-codes'),
  getXeroTaxRates: () => api.get('/xero/tax-rates'),
  
  // User Management
  getUsers: () => api.get('/users'),
  createUser: (userData) => api.post('/users', userData),
  getUser: (userId) => api.get(`/users/${userId}`),
  updateUser: (userId, userData) => api.put(`/users/${userId}`, userData),
  deleteUser: (userId) => api.delete(`/users/${userId}`),
  changePassword: (passwordData) => api.post('/users/change-password', passwordData),
  
  // Machinery Rates
  getMachineryRates: () => api.get('/machinery-rates'),
  createMachineryRate: (data) => api.post('/machinery-rates', data),
  getMachineryRate: (id) => api.get(`/machinery-rates/${id}`),
  updateMachineryRate: (id, data) => api.put(`/machinery-rates/${id}`, data),
  deleteMachineryRate: (id) => api.delete(`/machinery-rates/${id}`),

  // Stock Management System
  // Raw Substrates
  getRawSubstrates: (clientId = null) => api.get(`/stock/raw-substrates${clientId ? `?client_id=${clientId}` : ''}`),
  createRawSubstrate: (data) => api.post('/stock/raw-substrates', data),
  updateRawSubstrate: (id, data) => api.put(`/stock/raw-substrates/${id}`, data),
  deleteRawSubstrate: (id) => api.delete(`/stock/raw-substrates/${id}`),

  // Raw Materials Stock
  getRawMaterialsStock: () => api.get('/stock/raw-materials'),
  createRawMaterialStock: (data) => api.post('/stock/raw-materials', data),
  updateRawMaterialStock: (id, data) => api.put(`/stock/raw-materials/${id}`, data),
  deleteRawMaterialStock: (id) => api.delete(`/stock/raw-materials/${id}`),

  // Stock Movements
  getStockMovements: (stockId) => api.get(`/stock/movements/${stockId}`),

  // Stock Alerts
  getStockAlerts: () => api.get('/stock/alerts'),
  acknowledgeStockAlert: (id, data) => api.post(`/stock/alerts/${id}/acknowledge`, data),
  checkLowStock: () => api.post('/stock/check-low-stock'),

  // Slit Width Management
  getSlitWidthsByMaterial: (materialId) => api.get(`/slit-widths/material/${materialId}`),
  createSlitWidth: (data) => api.post('/slit-widths', data),
  updateSlitWidth: (slitWidthId, data) => api.put(`/slit-widths/${slitWidthId}`, data),
  deleteSlitWidth: (slitWidthId) => api.delete(`/slit-widths/${slitWidthId}`),
  checkSlitWidthAvailability: (materialId, widthMm, quantityMeters) => 
    api.get(`/slit-widths/check-availability?material_id=${materialId}&required_width_mm=${widthMm}&required_quantity_meters=${quantityMeters}`),
  allocateSlitWidth: (allocationData) => api.post('/slit-widths/allocate', allocationData),
  getSlitWidthAllocations: (orderId) => api.get(`/slit-widths/allocations/${orderId}`),

  // Label Designer
  getLabelTemplates: () => api.get('/label-templates'),
  getLabelTemplate: (templateId) => api.get(`/label-templates/${templateId}`),
  createLabelTemplate: (data) => api.post('/label-templates', data),
  updateLabelTemplate: (templateId, data) => api.put(`/label-templates/${templateId}`, data),
  deleteLabelTemplate: (templateId) => api.delete(`/label-templates/${templateId}`),
  
  // Printing
  getPrinters: () => api.get('/printers'),
  printLabel: (data) => api.post('/print-label', data),

  // Generic GET/POST/PUT methods for flexibility
  get: (url) => api.get(url),
  post: (url, data) => api.post(url, data),
  put: (url, data) => api.put(url, data),
  delete: (url) => api.delete(url),
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

// ============= ARCHIVED ORDERS API =============

// Get archived orders for a client
export const getClientArchivedOrders = async (clientId, filters = {}) => {
  const params = new URLSearchParams();
  if (filters.date_from) params.append('date_from', filters.date_from);
  if (filters.date_to) params.append('date_to', filters.date_to);
  if (filters.search_query) params.append('search_query', filters.search_query);
  
  const queryString = params.toString();
  const url = queryString ? 
    `/clients/${clientId}/archived-orders?${queryString}` : 
    `/clients/${clientId}/archived-orders`;
    
  return api.get(url);
};

// Generate Fast Report for archived orders
export const generateFastReport = async (clientId, reportData) => {
  return api.post(`/clients/${clientId}/archived-orders/fast-report`, reportData, {
    responseType: 'blob' // Important for file downloads
  });
};

// Helper function to download Excel file
export const downloadExcelReport = async (clientId, reportData) => {
  try {
    const response = await generateFastReport(clientId, reportData);
    
    // Create blob link to download
    const blob = new Blob([response.data], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    });
    
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    
    // Extract filename from response headers if available
    const contentDisposition = response.headers['content-disposition'];
    let filename = 'archived_orders_report.xlsx';
    
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename="?([^"]*)"?/);
      if (filenameMatch) {
        filename = filenameMatch[1];
      }
    }
    
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
    
    return { success: true, filename };
  } catch (error) {
    console.error('Error downloading Excel report:', error);
    throw error;
  }
};