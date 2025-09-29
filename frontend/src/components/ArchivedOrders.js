import React, { useState, useEffect } from 'react';
import { XMarkIcon, MagnifyingGlassIcon, DocumentArrowDownIcon, FunnelIcon } from '@heroicons/react/24/outline';
import { getClientArchivedOrders, downloadExcelReport } from '../utils/api';
import { toast } from 'sonner';

// Report field options for Fast Report
const REPORT_FIELDS = [
  { id: 'order_number', label: 'Order Number', checked: true },
  { id: 'client_name', label: 'Client Name', checked: true },
  { id: 'purchase_order_number', label: 'Purchase Order Number', checked: false },
  { id: 'created_at', label: 'Order Date', checked: true },
  { id: 'completed_at', label: 'Completion Date', checked: true },
  { id: 'due_date', label: 'Due Date', checked: false },
  { id: 'subtotal', label: 'Subtotal', checked: true },
  { id: 'gst', label: 'GST', checked: false },
  { id: 'total_amount', label: 'Total Amount', checked: true },
  { id: 'delivery_address', label: 'Delivery Address', checked: false },
  { id: 'product_names', label: 'Products', checked: true },
  { id: 'product_quantities', label: 'Product Quantities', checked: false },
  { id: 'notes', label: 'Notes', checked: false },
  { id: 'runtime_estimate', label: 'Runtime Estimate', checked: false }
];

const TIME_PERIODS = [
  { id: 'current_month', label: 'Current Month' },
  { id: 'last_month', label: 'Last Month' },
  { id: 'last_3_months', label: 'Last 3 Months' },
  { id: 'last_6_months', label: 'Last 6 Months' },
  { id: 'last_9_months', label: 'Last 9 Months' },
  { id: 'last_year', label: 'Last Year' },
  { id: 'current_quarter', label: 'Current Quarter' },
  { id: 'last_quarter', label: 'Last Quarter' },
  { id: 'current_financial_year', label: 'Current Financial Year' },
  { id: 'last_financial_year', label: 'Last Financial Year' },
  { id: 'year_to_date', label: 'Year to Date' },
  { id: 'custom_range', label: 'Custom Date Range' }
];

const ArchivedOrders = ({ client, onClose }) => {
  const [archivedOrders, setArchivedOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showFilters, setShowFilters] = useState(false);
  const [showFastReport, setShowFastReport] = useState(false);
  const [generatingReport, setGeneratingReport] = useState(false);
  
  // Filter states
  const [filters, setFilters] = useState({
    date_from: '',
    date_to: '',
    search_query: ''
  });

  // Fast Report states
  const [reportConfig, setReportConfig] = useState({
    time_period: 'last_3_months',
    date_from: '',
    date_to: '',
    selected_fields: REPORT_FIELDS.filter(field => field.checked).map(field => field.id),
    product_filter: '',
    report_title: ''
  });

  useEffect(() => {
    loadArchivedOrders();
  }, [client.id]);

  const loadArchivedOrders = async () => {
    try {
      setLoading(true);
      const response = await getClientArchivedOrders(client.id, filters);
      setArchivedOrders(response.data.data || []);
    } catch (error) {
      console.error('Failed to load archived orders:', error);
      toast.error('Failed to load archived orders');
      setArchivedOrders([]);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (field, value) => {
    setFilters(prev => ({ ...prev, [field]: value }));
  };

  const applyFilters = () => {
    loadArchivedOrders();
    setShowFilters(false);
  };

  const clearFilters = () => {
    setFilters({
      date_from: '',
      date_to: '',
      search_query: ''
    });
    // Reload without filters
    setTimeout(() => {
      loadArchivedOrders();
    }, 100);
  };

  const handleReportConfigChange = (field, value) => {
    setReportConfig(prev => ({ ...prev, [field]: value }));
  };

  const toggleReportField = (fieldId) => {
    setReportConfig(prev => ({
      ...prev,
      selected_fields: prev.selected_fields.includes(fieldId)
        ? prev.selected_fields.filter(id => id !== fieldId)
        : [...prev.selected_fields, fieldId]
    }));
  };

  const generateReport = async () => {
    if (reportConfig.selected_fields.length === 0) {
      toast.error('Please select at least one field for the report');
      return;
    }

    try {
      setGeneratingReport(true);

      const reportData = {
        client_id: client.id,
        time_period: reportConfig.time_period,
        selected_fields: reportConfig.selected_fields,
        report_title: reportConfig.report_title || `${client.company_name} - Archived Orders Report`
      };

      // Add custom date range if selected
      if (reportConfig.time_period === 'custom_range') {
        if (!reportConfig.date_from || !reportConfig.date_to) {
          toast.error('Please select both start and end dates for custom range');
          return;
        }
        reportData.date_from = reportConfig.date_from;
        reportData.date_to = reportConfig.date_to;
      }

      // Add product filter if specified
      if (reportConfig.product_filter.trim()) {
        reportData.product_filter = reportConfig.product_filter.trim();
      }

      const result = await downloadExcelReport(client.id, reportData);
      
      toast.success(`Report generated successfully: ${result.filename}`);
      setShowFastReport(false);
    } catch (error) {
      console.error('Failed to generate report:', error);
      const message = error.response?.data?.detail || 'Failed to generate report';
      toast.error(message);
    } finally {
      setGeneratingReport(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString();
  };

  const formatCurrency = (amount) => {
    return `$${Number(amount || 0).toFixed(2)}`;
  };

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal-content max-w-7xl max-h-[90vh] overflow-hidden flex flex-col">
        
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-600">
          <div>
            <h2 className="text-2xl font-bold text-white">Archived Orders</h2>
            <p className="text-gray-300">{client.company_name}</p>
          </div>
          <div className="flex space-x-3">
            <button
              onClick={() => setShowFastReport(true)}
              className="misty-button misty-button-primary flex items-center"
            >
              <DocumentArrowDownIcon className="h-4 w-4 mr-2" />
              Fast Report
            </button>
            <button
              onClick={() => setShowFilters(true)}
              className="misty-button misty-button-secondary flex items-center"
            >
              <FunnelIcon className="h-4 w-4 mr-2" />
              Filters
            </button>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white transition-colors"
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>
        </div>

        {/* Search Bar */}
        <div className="p-6 border-b border-gray-600">
          <div className="relative">
            <MagnifyingGlassIcon className="absolute left-4 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search orders by number, products, or PO number..."
              value={filters.search_query}
              onChange={(e) => handleFilterChange('search_query', e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && applyFilters()}
              className="misty-input pl-12 w-full"
            />
          </div>
          
          {/* Active Filters Display */}
          {(filters.date_from || filters.date_to || filters.search_query) && (
            <div className="flex items-center space-x-2 mt-3">
              <span className="text-sm text-gray-300">Active filters:</span>
              {filters.date_from && (
                <span className="px-2 py-1 bg-yellow-900 text-yellow-100 rounded text-sm">
                  From: {filters.date_from}
                </span>
              )}
              {filters.date_to && (
                <span className="px-2 py-1 bg-yellow-900 text-yellow-100 rounded text-sm">
                  To: {filters.date_to}
                </span>
              )}
              {filters.search_query && (
                <span className="px-2 py-1 bg-yellow-900 text-yellow-100 rounded text-sm">
                  Search: "{filters.search_query}"
                </span>
              )}
              <button
                onClick={clearFilters}
                className="text-red-400 hover:text-red-300 text-sm underline"
              >
                Clear all
              </button>
            </div>
          )}
        </div>

        {/* Orders List */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-yellow-400"></div>
              <span className="ml-3 text-white">Loading archived orders...</span>
            </div>
          ) : archivedOrders.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-400 text-lg">No archived orders found</p>
              {(filters.date_from || filters.date_to || filters.search_query) && (
                <p className="text-sm text-gray-500 mt-2">Try adjusting your filters</p>
              )}
            </div>
          ) : (
            <div className="space-y-4">
              {archivedOrders.map((order) => (
                <div key={order.id} className="misty-card p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-4 mb-2">
                        <h3 className="text-lg font-semibold text-white">
                          {order.order_number}
                        </h3>
                        {order.purchase_order_number && (
                          <span className="px-2 py-1 bg-blue-900 text-blue-100 rounded text-sm">
                            PO: {order.purchase_order_number}
                          </span>
                        )}
                        <span className="px-2 py-1 bg-green-900 text-green-100 rounded text-sm">
                          ARCHIVED
                        </span>
                      </div>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div>
                          <span className="text-gray-400">Order Date:</span>
                          <span className="text-white ml-2">{formatDate(order.created_at)}</span>
                        </div>
                        <div>
                          <span className="text-gray-400">Completed:</span>
                          <span className="text-white ml-2">{formatDate(order.completed_at)}</span>
                        </div>
                        <div>
                          <span className="text-gray-400">Due Date:</span>
                          <span className="text-white ml-2">{formatDate(order.due_date)}</span>
                        </div>
                        <div>
                          <span className="text-gray-400">Total:</span>
                          <span className="text-yellow-400 ml-2 font-semibold">
                            {formatCurrency(order.total_amount)}
                          </span>
                        </div>
                      </div>
                      <div className="mt-2">
                        <span className="text-gray-400 text-sm">Products:</span>
                        <span className="text-white ml-2 text-sm">
                          {order.items.map(item => item.product_name).join(', ')}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Filters Modal */}
      {showFilters && (
        <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && setShowFilters(false)}>
          <div className="modal-content max-w-md">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white">Filter Options</h3>
                <button
                  onClick={() => setShowFilters(false)}
                  className="text-gray-400 hover:text-white transition-colors"
                >
                  <XMarkIcon className="h-5 w-5" />
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Date From
                  </label>
                  <input
                    type="date"
                    value={filters.date_from}
                    onChange={(e) => handleFilterChange('date_from', e.target.value)}
                    className="misty-input w-full"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Date To
                  </label>
                  <input
                    type="date"
                    value={filters.date_to}
                    onChange={(e) => handleFilterChange('date_to', e.target.value)}
                    className="misty-input w-full"
                  />
                </div>
              </div>

              <div className="flex justify-end space-x-3 mt-6">
                <button
                  onClick={() => setShowFilters(false)}
                  className="misty-button misty-button-secondary"
                >
                  Cancel
                </button>
                <button
                  onClick={applyFilters}
                  className="misty-button misty-button-primary"
                >
                  Apply Filters
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Fast Report Modal */}
      {showFastReport && (
        <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && setShowFastReport(false)}>
          <div className="modal-content max-w-4xl max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-semibold text-white">Generate Fast Report</h3>
                <button
                  onClick={() => setShowFastReport(false)}
                  className="text-gray-400 hover:text-white transition-colors"
                >
                  <XMarkIcon className="h-5 w-5" />
                </button>
              </div>

              <div className="space-y-6">
                {/* Report Title */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Report Title
                  </label>
                  <input
                    type="text"
                    value={reportConfig.report_title}
                    onChange={(e) => handleReportConfigChange('report_title', e.target.value)}
                    placeholder={`${client.company_name} - Archived Orders Report`}
                    className="misty-input w-full"
                  />
                </div>

                {/* Time Period */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Time Period
                  </label>
                  <select
                    value={reportConfig.time_period}
                    onChange={(e) => handleReportConfigChange('time_period', e.target.value)}
                    className="misty-select w-full"
                  >
                    {TIME_PERIODS.map(period => (
                      <option key={period.id} value={period.id}>
                        {period.label}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Custom Date Range */}
                {reportConfig.time_period === 'custom_range' && (
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-1">
                        Start Date
                      </label>
                      <input
                        type="date"
                        value={reportConfig.date_from}
                        onChange={(e) => handleReportConfigChange('date_from', e.target.value)}
                        className="misty-input w-full"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-1">
                        End Date
                      </label>
                      <input
                        type="date"
                        value={reportConfig.date_to}
                        onChange={(e) => handleReportConfigChange('date_to', e.target.value)}
                        className="misty-input w-full"
                      />
                    </div>
                  </div>
                )}

                {/* Product Filter */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Product Filter (Optional)
                  </label>
                  <input
                    type="text"
                    value={reportConfig.product_filter}
                    onChange={(e) => handleReportConfigChange('product_filter', e.target.value)}
                    placeholder="Filter by product name (leave empty for all products)"
                    className="misty-input w-full"
                  />
                </div>

                {/* Report Fields */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-3">
                    Select Fields to Include
                  </label>
                  <div className="grid grid-cols-2 gap-3 max-h-64 overflow-y-auto">
                    {REPORT_FIELDS.map(field => (
                      <label key={field.id} className="flex items-center space-x-2 text-sm">
                        <input
                          type="checkbox"
                          checked={reportConfig.selected_fields.includes(field.id)}
                          onChange={() => toggleReportField(field.id)}
                          className="rounded border-gray-600 bg-gray-700 text-yellow-400 focus:ring-yellow-400"
                        />
                        <span className="text-gray-300">{field.label}</span>
                      </label>
                    ))}
                  </div>
                </div>
              </div>

              <div className="flex justify-end space-x-3 mt-6">
                <button
                  onClick={() => setShowFastReport(false)}
                  className="misty-button misty-button-secondary"
                  disabled={generatingReport}
                >
                  Cancel
                </button>
                <button
                  onClick={generateReport}
                  className="misty-button misty-button-primary"
                  disabled={generatingReport}
                >
                  {generatingReport ? (
                    <div className="flex items-center">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-900 mr-2"></div>
                      Generating...
                    </div>
                  ) : (
                    <>
                      <DocumentArrowDownIcon className="h-4 w-4 mr-2" />
                      Generate Excel Report
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ArchivedOrders;