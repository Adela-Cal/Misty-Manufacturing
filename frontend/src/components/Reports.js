import React, { useState, useEffect } from 'react';
import Layout from './Layout';
import { apiHelpers, formatCurrency } from '../utils/api';
import { toast } from 'sonner';
import { 
  ChartBarIcon,
  DocumentArrowDownIcon,
  CalendarDaysIcon,
  CubeIcon,
  CheckIcon
} from '@heroicons/react/24/outline';

const Reports = () => {
  const [loading, setLoading] = useState(true);
  const [outstandingJobs, setOutstandingJobs] = useState(null);
  const [lateDeliveries, setLateDeliveries] = useState(null);
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const [clients, setClients] = useState([]);
  const [selectedClient, setSelectedClient] = useState('');
  const [customerReport, setCustomerReport] = useState(null);
  
  // Material Usage Report states
  const [materials, setMaterials] = useState([]);
  const [selectedMaterial, setSelectedMaterial] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [includeOrderBreakdown, setIncludeOrderBreakdown] = useState(false);
  const [materialUsageReport, setMaterialUsageReport] = useState(null);
  const [loadingMaterialReport, setLoadingMaterialReport] = useState(false);

  useEffect(() => {
    loadReportsData();
    loadMaterials();
    
    // Set default dates (last 30 days)
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - 30);
    setEndDate(end.toISOString().split('T')[0]);
    setStartDate(start.toISOString().split('T')[0]);
  }, []);

  const loadReportsData = async () => {
    try {
      setLoading(true);
      const [outstandingRes, lateRes, clientsRes] = await Promise.all([
        apiHelpers.getOutstandingJobsReport(),
        apiHelpers.getLateDeliveriesReport(),
        apiHelpers.getClients()
      ]);
      
      setOutstandingJobs(outstandingRes.data?.data);
      setLateDeliveries(lateRes.data?.data);
      setClients(clientsRes.data);
    } catch (error) {
      console.error('Failed to load reports data:', error);
      toast.error('Failed to load reports data');
    } finally {
      setLoading(false);
    }
  };
  
  const loadMaterials = async () => {
    try {
      const response = await apiHelpers.getMaterials();
      setMaterials(response.data || []);
    } catch (error) {
      console.error('Failed to load materials:', error);
      toast.error('Failed to load materials');
    }
  };

  const loadCustomerReport = async () => {
    if (!selectedClient) {
      toast.error('Please select a client');
      return;
    }

    try {
      const response = await apiHelpers.getCustomerAnnualReport(selectedClient, selectedYear);
      setCustomerReport(response.data?.data);
      toast.success('Customer report loaded successfully');
    } catch (error) {
      console.error('Failed to load customer report:', error);
      toast.error('Failed to load customer report');
    }
  };
  
  const loadMaterialUsageReport = async () => {
    if (!selectedMaterial) {
      toast.error('Please select a material');
      return;
    }
    
    if (!startDate || !endDate) {
      toast.error('Please select date range');
      return;
    }

    try {
      setLoadingMaterialReport(true);
      const response = await apiHelpers.getDetailedMaterialUsageReport(
        selectedMaterial,
        startDate + 'T00:00:00Z',
        endDate + 'T23:59:59Z',
        includeOrderBreakdown
      );
      setMaterialUsageReport(response.data?.data);
      toast.success('Material usage report generated successfully');
    } catch (error) {
      console.error('Failed to load material usage report:', error);
      toast.error('Failed to load material usage report');
    } finally {
      setLoadingMaterialReport(false);
    }
  };

  const ReportCard = ({ title, children, icon: Icon }) => (
    <div className="misty-card p-6">
      <div className="flex items-center mb-4">
        <Icon className="h-6 w-6 text-yellow-400 mr-2" />
        <h3 className="text-lg font-semibold text-white">{title}</h3>
      </div>
      {children}
    </div>
  );

  if (loading) {
    return (
      <Layout>
        <div className="p-8">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-700 rounded w-1/4 mb-8"></div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <div className="h-64 bg-gray-700 rounded"></div>
              <div className="h-64 bg-gray-700 rounded"></div>
            </div>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="p-8" data-testid="reports">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">Reports & Analytics</h1>
          <p className="text-gray-400">Track performance and generate business insights</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Outstanding Jobs Report */}
          <ReportCard title="Outstanding Jobs" icon={ChartBarIcon}>
            {outstandingJobs ? (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center">
                    <p className="text-2xl font-bold text-yellow-400">{outstandingJobs.total_jobs}</p>
                    <p className="text-sm text-gray-400">Total Jobs</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-red-400">{outstandingJobs.overdue_jobs}</p>
                    <p className="text-sm text-gray-400">Overdue</p>
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center">
                    <p className="text-xl font-bold text-orange-400">{outstandingJobs.jobs_due_today}</p>
                    <p className="text-sm text-gray-400">Due Today</p>
                  </div>
                  <div className="text-center">
                    <p className="text-xl font-bold text-blue-400">{outstandingJobs.jobs_due_this_week}</p>
                    <p className="text-sm text-gray-400">Due This Week</p>
                  </div>
                </div>

                <div>
                  <h4 className="font-medium text-white mb-2">Jobs by Stage:</h4>
                  <div className="space-y-1">
                    {Object.entries(outstandingJobs.jobs_by_stage || {}).map(([stage, count]) => (
                      <div key={stage} className="flex justify-between text-sm">
                        <span className="text-gray-300 capitalize">{stage.replace('_', ' ')}</span>
                        <span className="text-gray-400">{count}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-gray-400">No data available</p>
            )}
          </ReportCard>

          {/* Late Deliveries Report */}
          <ReportCard title="Late Deliveries" icon={DocumentArrowDownIcon}>
            {lateDeliveries ? (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center">
                    <p className="text-2xl font-bold text-red-400">{lateDeliveries.total_late_deliveries}</p>
                    <p className="text-sm text-gray-400">Late Deliveries</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-orange-400">{lateDeliveries.average_delay_days?.toFixed(1) || 0}</p>
                    <p className="text-sm text-gray-400">Avg Delay (days)</p>
                  </div>
                </div>

                {Object.keys(lateDeliveries.late_deliveries_by_client || {}).length > 0 && (
                  <div>
                    <h4 className="font-medium text-white mb-2">Late Deliveries by Client:</h4>
                    <div className="space-y-1">
                      {Object.entries(lateDeliveries.late_deliveries_by_client).map(([client, count]) => (
                        <div key={client} className="flex justify-between text-sm">
                          <span className="text-gray-300">{client}</span>
                          <span className="text-red-400">{count}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-gray-400">No data available</p>
            )}
          </ReportCard>
        </div>

        {/* Customer Annual Report */}
        <ReportCard title="Customer Annual Report" icon={CalendarDaysIcon}>
          <div className="space-y-4">
            <div className="flex flex-col sm:flex-row gap-4">
              <select
                className="misty-select flex-1"
                value={selectedClient}
                onChange={(e) => setSelectedClient(e.target.value)}
                data-testid="client-select"
              >
                <option value="">Select a client...</option>
                {clients.map((client) => (
                  <option key={client.id} value={client.id}>
                    {client.company_name}
                  </option>
                ))}
              </select>
              
              <select
                className="misty-select"
                value={selectedYear}
                onChange={(e) => setSelectedYear(parseInt(e.target.value))}
                data-testid="year-select"
              >
                {[...Array(5)].map((_, i) => {
                  const year = new Date().getFullYear() - i;
                  return (
                    <option key={year} value={year}>
                      {year}
                    </option>
                  );
                })}
              </select>
              
              <button
                onClick={loadCustomerReport}
                className="misty-button misty-button-primary"
                data-testid="generate-customer-report"
              >
                Generate Report
              </button>
            </div>

            {customerReport && (
              <div className="mt-6 space-y-4">
                <div className="border-t border-gray-700 pt-4">
                  <h4 className="font-medium text-white mb-3">
                    {customerReport.client_name} - {customerReport.year} Report
                  </h4>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                    <div className="text-center">
                      <p className="text-xl font-bold text-yellow-400">{customerReport.total_orders}</p>
                      <p className="text-sm text-gray-400">Total Orders</p>
                    </div>
                    <div className="text-center">
                      <p className="text-xl font-bold text-green-400">
                        {formatCurrency(customerReport.total_revenue)}
                      </p>
                      <p className="text-sm text-gray-400">Total Revenue</p>
                    </div>
                    <div className="text-center">
                      <p className="text-xl font-bold text-blue-400">
                        {formatCurrency(customerReport.average_order_value)}
                      </p>
                      <p className="text-sm text-gray-400">Avg Order Value</p>
                    </div>
                  </div>

                  <div className="text-center">
                    <p className="text-lg font-bold text-teal-400">
                      {customerReport.on_time_delivery_rate?.toFixed(1) || 0}%
                    </p>
                    <p className="text-sm text-gray-400">On-Time Delivery Rate</p>
                  </div>

                  {customerReport.top_products && customerReport.top_products.length > 0 && (
                    <div className="mt-4">
                      <h5 className="font-medium text-white mb-2">Top Products:</h5>
                      <div className="space-y-1">
                        {customerReport.top_products.slice(0, 5).map((product, index) => (
                          <div key={index} className="flex justify-between text-sm">
                            <span className="text-gray-300">{product.product}</span>
                            <span className="text-yellow-400">
                              {formatCurrency(product.revenue)}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </ReportCard>

        {/* Material Usage Report */}
        <ReportCard title="Material Usage Report by Width" icon={CubeIcon}>
          <div className="space-y-4">
            <div className="flex flex-col gap-4">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {/* Material Selection */}
                <select
                  className="misty-select"
                  value={selectedMaterial}
                  onChange={(e) => setSelectedMaterial(e.target.value)}
                  data-testid="material-select"
                >
                  <option value="">Select a material...</option>
                  {materials.map((material) => (
                    <option key={material.id} value={material.id}>
                      {material.material_name} ({material.material_code || 'N/A'})
                    </option>
                  ))}
                </select>
                
                {/* Start Date */}
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Start Date</label>
                  <input
                    type="date"
                    className="misty-input"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    data-testid="start-date"
                  />
                </div>
                
                {/* End Date */}
                <div>
                  <label className="block text-sm text-gray-400 mb-1">End Date</label>
                  <input
                    type="date"
                    className="misty-input"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    data-testid="end-date"
                  />
                </div>
                
                {/* Generate Button */}
                <div className="flex items-end">
                  <button
                    onClick={loadMaterialUsageReport}
                    disabled={loadingMaterialReport}
                    className="misty-button misty-button-primary w-full"
                    data-testid="generate-material-report"
                  >
                    {loadingMaterialReport ? 'Loading...' : 'Generate Report'}
                  </button>
                </div>
              </div>
              
              {/* Order Breakdown Toggle */}
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setIncludeOrderBreakdown(!includeOrderBreakdown)}
                  className={`flex items-center gap-2 px-4 py-2 rounded transition-colors ${
                    includeOrderBreakdown 
                      ? 'bg-yellow-600 text-white' 
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  <div className={`w-5 h-5 border-2 rounded flex items-center justify-center ${
                    includeOrderBreakdown ? 'border-white' : 'border-gray-400'
                  }`}>
                    {includeOrderBreakdown && <CheckIcon className="h-4 w-4" />}
                  </div>
                  <span>Show breakdown by order</span>
                </button>
              </div>
            </div>

            {materialUsageReport && (
              <div className="mt-6 space-y-6">
                {/* Report Header */}
                <div className="border-t border-gray-700 pt-4">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h4 className="font-medium text-white text-lg mb-1">
                        {materialUsageReport.material_name}
                      </h4>
                      <p className="text-sm text-gray-400">
                        Code: {materialUsageReport.material_code} | 
                        Period: {new Date(materialUsageReport.report_period.start_date).toLocaleDateString()} - {new Date(materialUsageReport.report_period.end_date).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  
                  {/* Summary Stats */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                    <div className="bg-gray-700/50 rounded-lg p-4 text-center">
                      <p className="text-2xl font-bold text-yellow-400">
                        {materialUsageReport.grand_total_m2} m²
                      </p>
                      <p className="text-sm text-gray-400">Total Area Used</p>
                    </div>
                    <div className="bg-gray-700/50 rounded-lg p-4 text-center">
                      <p className="text-2xl font-bold text-green-400">
                        {materialUsageReport.grand_total_length_m} m
                      </p>
                      <p className="text-sm text-gray-400">Total Length</p>
                    </div>
                    <div className="bg-gray-700/50 rounded-lg p-4 text-center">
                      <p className="text-2xl font-bold text-blue-400">
                        {materialUsageReport.total_widths_used}
                      </p>
                      <p className="text-sm text-gray-400">Different Widths Used</p>
                    </div>
                  </div>

                  {/* Usage by Width Table */}
                  <div className="overflow-x-auto">
                    <table className="min-w-full">
                      <thead>
                        <tr className="border-b border-gray-700">
                          <th className="text-left py-3 px-4 text-gray-300 font-medium">Width (mm)</th>
                          <th className="text-right py-3 px-4 text-gray-300 font-medium">Total Length (m)</th>
                          <th className="text-right py-3 px-4 text-gray-300 font-medium">Area (m²)</th>
                          {includeOrderBreakdown && (
                            <th className="text-center py-3 px-4 text-gray-300 font-medium">Orders</th>
                          )}
                        </tr>
                      </thead>
                      <tbody>
                        {materialUsageReport.usage_by_width.map((width, index) => (
                          <React.Fragment key={index}>
                            <tr className="border-b border-gray-700/50 hover:bg-gray-700/30">
                              <td className="py-3 px-4 text-white font-medium">{width.width_mm} mm</td>
                              <td className="py-3 px-4 text-right text-gray-300">{width.total_length_m.toLocaleString()} m</td>
                              <td className="py-3 px-4 text-right text-yellow-400 font-medium">{width.m2.toLocaleString()} m²</td>
                              {includeOrderBreakdown && (
                                <td className="py-3 px-4 text-center text-gray-300">{width.order_count || 0}</td>
                              )}
                            </tr>
                            
                            {/* Order Breakdown */}
                            {includeOrderBreakdown && width.orders && width.orders.length > 0 && (
                              <tr>
                                <td colSpan={includeOrderBreakdown ? 4 : 3} className="py-2 px-4 bg-gray-700/20">
                                  <div className="pl-8 space-y-1">
                                    <p className="text-sm font-medium text-gray-400 mb-2">Order Breakdown:</p>
                                    {width.orders.map((order, orderIndex) => (
                                      <div key={orderIndex} className="flex justify-between text-sm py-1">
                                        <span className="text-gray-300">
                                          {order.order_number} - {order.client_name}
                                        </span>
                                        <span className="text-gray-400">
                                          {order.length_m} m
                                        </span>
                                      </div>
                                    ))}
                                  </div>
                                </td>
                              </tr>
                            )}
                          </React.Fragment>
                        ))}
                        
                        {/* Grand Total Row */}
                        <tr className="bg-gray-700/50 font-bold">
                          <td className="py-4 px-4 text-white">GRAND TOTAL</td>
                          <td className="py-4 px-4 text-right text-white">
                            {materialUsageReport.grand_total_length_m.toLocaleString()} m
                          </td>
                          <td className="py-4 px-4 text-right text-yellow-400 text-lg">
                            {materialUsageReport.grand_total_m2.toLocaleString()} m²
                          </td>
                          {includeOrderBreakdown && <td></td>}
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}
          </div>
        </ReportCard>
      </div>
    </Layout>
  );
};

export default Reports;