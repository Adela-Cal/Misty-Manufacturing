import React, { useState, useEffect } from 'react';
import Layout from './Layout';
import { apiHelpers, formatCurrency } from '../utils/api';
import { toast } from 'sonner';
import { 
  ChartBarIcon,
  DocumentArrowDownIcon,
  CalendarDaysIcon,
  CubeIcon,
  CheckIcon,
  PrinterIcon
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
  const [datePreset, setDatePreset] = useState('last_30_days');
  const [customStartYear, setCustomStartYear] = useState(new Date().getFullYear());
  const [customStartMonth, setCustomStartMonth] = useState(new Date().getMonth());
  const [customEndYear, setCustomEndYear] = useState(new Date().getFullYear());
  const [customEndMonth, setCustomEndMonth] = useState(new Date().getMonth());
  const [includeOrderBreakdown, setIncludeOrderBreakdown] = useState(false);
  const [materialUsageReport, setMaterialUsageReport] = useState(null);
  const [loadingMaterialReport, setLoadingMaterialReport] = useState(false);
  
  // Product Usage Report states
  const [selectedProductClient, setSelectedProductClient] = useState('');
  const [productDatePreset, setProductDatePreset] = useState('last_30_days');
  const [productStartDate, setProductStartDate] = useState('');
  const [productEndDate, setProductEndDate] = useState('');
  const [customProductStartYear, setCustomProductStartYear] = useState(new Date().getFullYear());
  const [customProductStartMonth, setCustomProductStartMonth] = useState(new Date().getMonth());
  const [customProductEndYear, setCustomProductEndYear] = useState(new Date().getFullYear());
  const [customProductEndMonth, setCustomProductEndMonth] = useState(new Date().getMonth());
  const [includeProductOrderBreakdown, setIncludeProductOrderBreakdown] = useState(false);
  const [productUsageReport, setProductUsageReport] = useState(null);
  const [loadingProductReport, setLoadingProductReport] = useState(false);

  useEffect(() => {
    loadReportsData();
    loadMaterials();
    
    // Set default dates (last 30 days)
    const { start, end } = getDateRangeFromPreset('last_30_days');
    setStartDate(start);
    setEndDate(end);
    setProductStartDate(start);
    setProductEndDate(end);
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
  
  // Helper function to get date range based on preset
  const getDateRangeFromPreset = (preset) => {
    const now = new Date();
    let start, end;
    
    switch(preset) {
      case 'last_30_days':
        end = new Date();
        start = new Date();
        start.setDate(start.getDate() - 30);
        break;
      case 'last_90_days':
        end = new Date();
        start = new Date();
        start.setDate(start.getDate() - 90);
        break;
      case 'this_month':
        start = new Date(now.getFullYear(), now.getMonth(), 1);
        end = new Date(now.getFullYear(), now.getMonth() + 1, 0);
        break;
      case 'last_month':
        start = new Date(now.getFullYear(), now.getMonth() - 1, 1);
        end = new Date(now.getFullYear(), now.getMonth(), 0);
        break;
      case 'this_year':
        start = new Date(now.getFullYear(), 0, 1);
        end = new Date(now.getFullYear(), 11, 31);
        break;
      case 'last_year':
        start = new Date(now.getFullYear() - 1, 0, 1);
        end = new Date(now.getFullYear() - 1, 11, 31);
        break;
      case 'custom':
        start = new Date(customStartYear, customStartMonth, 1);
        end = new Date(customEndYear, customEndMonth + 1, 0);
        break;
      default:
        end = new Date();
        start = new Date();
        start.setDate(start.getDate() - 30);
    }
    
    return {
      start: start.toISOString().split('T')[0],
      end: end.toISOString().split('T')[0]
    };
  };
  
  // Update dates when preset changes
  const handlePresetChange = (preset) => {
    setDatePreset(preset);
    if (preset !== 'custom') {
      const { start, end } = getDateRangeFromPreset(preset);
      setStartDate(start);
      setEndDate(end);
    }
  };
  
  // Handle product report preset changes
  const handleProductPresetChange = (preset) => {
    setProductDatePreset(preset);
    if (preset !== 'custom') {
      const { start, end } = getDateRangeFromPreset(preset);
      setProductStartDate(start);
      setProductEndDate(end);
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
    
    // Calculate dates based on current selection
    let finalStartDate = startDate;
    let finalEndDate = endDate;
    
    if (datePreset === 'custom') {
      const { start, end } = getDateRangeFromPreset('custom');
      finalStartDate = start;
      finalEndDate = end;
      setStartDate(start);
      setEndDate(end);
    }
    
    if (!finalStartDate || !finalEndDate) {
      toast.error('Please select date range');
      return;
    }

    try {
      setLoadingMaterialReport(true);
      const response = await apiHelpers.getDetailedMaterialUsageReport(
        selectedMaterial,
        finalStartDate + 'T00:00:00Z',
        finalEndDate + 'T23:59:59Z',
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
  
  const loadProductUsageReport = async () => {
    // Calculate dates based on current selection
    let finalStartDate = productStartDate;
    let finalEndDate = productEndDate;
    
    if (productDatePreset === 'custom') {
      const start = new Date(customProductStartYear, customProductStartMonth, 1);
      const end = new Date(customProductEndYear, customProductEndMonth + 1, 0);
      finalStartDate = start.toISOString().split('T')[0];
      finalEndDate = end.toISOString().split('T')[0];
      setProductStartDate(finalStartDate);
      setProductEndDate(finalEndDate);
    }
    
    if (!finalStartDate || !finalEndDate) {
      toast.error('Please select date range');
      return;
    }

    try {
      setLoadingProductReport(true);
      const response = await apiHelpers.getDetailedProductUsageReport(
        selectedProductClient || null,
        finalStartDate + 'T00:00:00Z',
        finalEndDate + 'T23:59:59Z',
        includeProductOrderBreakdown
      );
      setProductUsageReport(response.data?.data);
      toast.success('Consumable usage report generated successfully');
    } catch (error) {
      console.error('Failed to load consumable usage report:', error);
      toast.error('Failed to load consumable usage report');
    } finally {
      setLoadingProductReport(false);
    }
  };
  
  const printMaterialUsageReport = () => {
    // Create a print-friendly window
    const printWindow = window.open('', '_blank');
    const report = materialUsageReport;
    
    if (!report) return;
    
    const htmlContent = `
      <!DOCTYPE html>
      <html>
      <head>
        <title>Material Usage Report - ${report.material_name}</title>
        <style>
          @page {
            margin: 1cm;
            size: A4;
          }
          
          body {
            font-family: Arial, sans-serif;
            color: #000;
            background: #fff;
            padding: 20px;
          }
          
          .header {
            text-align: center;
            border-bottom: 3px solid #000;
            padding-bottom: 20px;
            margin-bottom: 30px;
          }
          
          .header h1 {
            font-size: 24px;
            margin: 0 0 10px 0;
            color: #000;
          }
          
          .header h2 {
            font-size: 18px;
            margin: 0 0 5px 0;
            color: #333;
          }
          
          .header p {
            font-size: 12px;
            color: #666;
            margin: 5px 0;
          }
          
          .summary-stats {
            display: flex;
            justify-content: space-around;
            margin: 30px 0;
            padding: 20px;
            background: #f5f5f5;
            border-radius: 8px;
          }
          
          .stat-box {
            text-align: center;
          }
          
          .stat-value {
            font-size: 28px;
            font-weight: bold;
            color: #000;
          }
          
          .stat-label {
            font-size: 12px;
            color: #666;
            margin-top: 5px;
          }
          
          table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
          }
          
          th {
            background: #333;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: bold;
          }
          
          th.right {
            text-align: right;
          }
          
          th.center {
            text-align: center;
          }
          
          td {
            padding: 10px 12px;
            border-bottom: 1px solid #ddd;
          }
          
          td.right {
            text-align: right;
          }
          
          td.center {
            text-align: center;
          }
          
          tbody tr:nth-child(even) {
            background: #f9f9f9;
          }
          
          .order-breakdown {
            background: #f0f0f0;
            padding: 10px;
            margin: 5px 0;
            font-size: 11px;
          }
          
          .order-breakdown-item {
            display: flex;
            justify-content: space-between;
            padding: 3px 0;
            margin-left: 30px;
          }
          
          .total-row {
            background: #333 !important;
            color: white !important;
            font-weight: bold;
            font-size: 14px;
          }
          
          .total-row td {
            padding: 15px 12px;
          }
          
          .highlight {
            color: #d97706;
            font-weight: bold;
          }
          
          .footer {
            margin-top: 40px;
            text-align: center;
            font-size: 10px;
            color: #999;
            border-top: 1px solid #ddd;
            padding-top: 10px;
          }
          
          @media print {
            body {
              padding: 0;
            }
            
            .no-print {
              display: none;
            }
          }
        </style>
      </head>
      <body>
        <div class="header">
          <h1>Adela Merchants</h1>
          <h2>Material Usage Report by Width</h2>
          <p><strong>${report.material_name}</strong></p>
          <p>Material Code: ${report.material_code}</p>
          <p>Period: ${new Date(report.report_period.start_date).toLocaleDateString()} - ${new Date(report.report_period.end_date).toLocaleDateString()}</p>
        </div>
        
        <div class="summary-stats">
          <div class="stat-box">
            <div class="stat-value highlight">${report.grand_total_m2.toLocaleString()} m²</div>
            <div class="stat-label">Total Area Used</div>
          </div>
          <div class="stat-box">
            <div class="stat-value">${report.grand_total_length_m.toLocaleString()} m</div>
            <div class="stat-label">Total Length</div>
          </div>
          <div class="stat-box">
            <div class="stat-value">${report.total_widths_used}</div>
            <div class="stat-label">Different Widths Used</div>
          </div>
        </div>
        
        <table>
          <thead>
            <tr>
              <th>Width (mm)</th>
              <th class="right">Total Length (m)</th>
              <th class="right">Area (m²)</th>
              ${includeOrderBreakdown ? '<th class="center">Orders</th>' : ''}
            </tr>
          </thead>
          <tbody>
            ${report.usage_by_width.map(width => `
              <tr>
                <td><strong>${width.width_mm} mm</strong></td>
                <td class="right">${width.total_length_m.toLocaleString()} m</td>
                <td class="right highlight">${width.m2.toLocaleString()} m²</td>
                ${includeOrderBreakdown ? `<td class="center">${width.order_count || 0}</td>` : ''}
              </tr>
              ${includeOrderBreakdown && width.orders && width.orders.length > 0 ? `
                <tr>
                  <td colspan="${includeOrderBreakdown ? 4 : 3}" style="padding: 0;">
                    <div class="order-breakdown">
                      <strong>Order Breakdown:</strong>
                      ${width.orders.map(order => `
                        <div class="order-breakdown-item">
                          <span>${order.order_number} - ${order.client_name}</span>
                          <span>${order.length_m} m</span>
                        </div>
                      `).join('')}
                    </div>
                  </td>
                </tr>
              ` : ''}
            `).join('')}
            <tr class="total-row">
              <td>GRAND TOTAL</td>
              <td class="right">${report.grand_total_length_m.toLocaleString()} m</td>
              <td class="right">${report.grand_total_m2.toLocaleString()} m²</td>
              ${includeOrderBreakdown ? '<td></td>' : ''}
            </tr>
          </tbody>
        </table>
        
        <div class="footer">
          <p>Generated: ${new Date().toLocaleString()}</p>
          <p>Misty Manufacturing - Material Usage Report</p>
        </div>
      </body>
      </html>
    `;
    
    printWindow.document.write(htmlContent);
    printWindow.document.close();
    
    // Wait for content to load then print
    printWindow.onload = function() {
      printWindow.focus();
      printWindow.print();
    };
  };


  const printProductUsageReport = () => {
    const report = productUsageReport;
    
    if (!report) return;
    
    const printWindow = window.open('', '_blank');
    
    // Build product tables HTML
    let productsHTML = '';
    report.products.forEach(product => {
      productsHTML += `
        <div class="product-section">
          <h3>${product.product_info.product_description}</h3>
          <p class="product-meta">Code: ${product.product_info.product_code} | Client: ${product.product_info.client_name}</p>
          
          <table class="product-table">
            <thead>
              <tr>
                <th>Width (mm)</th>
                <th class="right">Total Length (m)</th>
                <th class="right">Area (m²)</th>
                ${includeProductOrderBreakdown ? '<th class="center">Orders</th>' : ''}
              </tr>
            </thead>
            <tbody>
              ${product.usage_by_width.map(width => `
                <tr>
                  <td><strong>${width.width_mm} mm</strong></td>
                  <td class="right">${width.total_length_m.toLocaleString()} m</td>
                  <td class="right highlight">${width.m2.toLocaleString()} m²</td>
                  ${includeProductOrderBreakdown ? `<td class="center">${width.order_count || 0}</td>` : ''}
                </tr>
                ${includeProductOrderBreakdown && width.orders && width.orders.length > 0 ? `
                  <tr>
                    <td colspan="${includeProductOrderBreakdown ? 4 : 3}" style="padding: 0;">
                      <div class="order-breakdown">
                        <strong>Order Breakdown:</strong>
                        ${width.orders.map(order => `
                          <div class="order-breakdown-item">
                            <span>${order.order_number} - ${order.client_name}</span>
                            <span>${order.total_length_m} m (${order.quantity} × ${order.length_per_unit}m)</span>
                          </div>
                        `).join('')}
                      </div>
                    </td>
                  </tr>
                ` : ''}
              `).join('')}
              <tr class="subtotal-row">
                <td>Product Total</td>
                <td class="right">${product.product_total_length_m.toLocaleString()} m</td>
                <td class="right highlight">${product.product_total_m2.toLocaleString()} m²</td>
                ${includeProductOrderBreakdown ? '<td></td>' : ''}
              </tr>
            </tbody>
          </table>
        </div>
      `;
    });
    
    const htmlContent = `
      <!DOCTYPE html>
      <html>
      <head>
        <title>Consumable Usage Report by Date</title>
        <style>
          @page { margin: 1cm; size: A4; }
          body { font-family: Arial, sans-serif; color: #000; background: #fff; padding: 20px; }
          .header { text-align: center; border-bottom: 3px solid #000; padding-bottom: 20px; margin-bottom: 30px; }
          .header h1 { font-size: 24px; margin: 0 0 10px 0; }
          .header h2 { font-size: 18px; margin: 0 0 5px 0; color: #333; }
          .header p { font-size: 12px; color: #666; margin: 5px 0; }
          .summary-stats { display: flex; justify-content: space-around; margin: 30px 0; padding: 20px; background: #f5f5f5; border-radius: 8px; }
          .stat-box { text-align: center; }
          .stat-value { font-size: 28px; font-weight: bold; color: #000; }
          .stat-label { font-size: 12px; color: #666; margin-top: 5px; }
          .product-section { margin: 30px 0; page-break-inside: avoid; }
          .product-section h3 { margin: 15px 0 5px 0; color: #000; border-bottom: 2px solid #333; padding-bottom: 5px; }
          .product-meta { font-size: 11px; color: #666; margin-bottom: 10px; }
          table.product-table { width: 100%; border-collapse: collapse; margin: 10px 0; }
          th { background: #555; color: white; padding: 10px; text-align: left; font-weight: bold; font-size: 11px; }
          th.right, td.right { text-align: right; }
          th.center, td.center { text-align: center; }
          td { padding: 8px 10px; border-bottom: 1px solid #ddd; font-size: 11px; }
          tbody tr:nth-child(even) { background: #f9f9f9; }
          .order-breakdown { background: #f0f0f0; padding: 8px; margin: 3px 0; font-size: 10px; }
          .order-breakdown-item { display: flex; justify-content: space-between; padding: 2px 0; margin-left: 20px; }
          .subtotal-row { background: #e0e0e0 !important; font-weight: bold; }
          .total-row { background: #333 !important; color: white !important; font-weight: bold; font-size: 13px; }
          .total-row td { padding: 12px 10px; }
          .highlight { color: #d97706; font-weight: bold; }
          .footer { margin-top: 40px; text-align: center; font-size: 10px; color: #999; border-top: 1px solid #ddd; padding-top: 10px; }
          @media print { body { padding: 0; } .no-print { display: none; } }
        </style>
      </head>
      <body>
        <div class="header">
          <h1>Adela Merchants</h1>
          <h2>Consumable Usage Report by Date</h2>
          <p>Period: ${new Date(report.report_period.start_date).toLocaleDateString()} - ${new Date(report.report_period.end_date).toLocaleDateString()}</p>
          <p style="color: #999; font-size: 10px;">Excludes: ${report.excluded_types.join(', ')}</p>
        </div>
        
        <div class="summary-stats">
          <div class="stat-box">
            <div class="stat-value highlight">${report.grand_total_m2.toLocaleString()} m²</div>
            <div class="stat-label">Total Area Used</div>
          </div>
          <div class="stat-box">
            <div class="stat-value">${report.grand_total_length_m.toLocaleString()} m</div>
            <div class="stat-label">Total Length</div>
          </div>
          <div class="stat-box">
            <div class="stat-value">${report.total_products}</div>
            <div class="stat-label">Consumables Used</div>
          </div>
        </div>
        
        ${productsHTML}
        
        <table class="product-table">
          <tbody>
            <tr class="total-row">
              <td>GRAND TOTAL (All Consumables)</td>
              <td class="right">${report.grand_total_length_m.toLocaleString()} m</td>
              <td class="right">${report.grand_total_m2.toLocaleString()} m²</td>
              ${includeProductOrderBreakdown ? '<td></td>' : ''}
            </tr>
          </tbody>
        </table>
        
        <div class="footer">
          <p>Generated: ${new Date().toLocaleString()}</p>
          <p>Misty Manufacturing - Consumable Usage Report</p>
        </div>
      </body>
      </html>
    `;
    
    printWindow.document.write(htmlContent);
    printWindow.document.close();
    
    printWindow.onload = function() {
      printWindow.focus();
      printWindow.print();
    };
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
          <div 
            className="space-y-4"
            onClick={(e) => {
              // Prevent any clicks within this card from bubbling up
              if (e.target.tagName === 'INPUT' && e.target.type === 'date') {
                e.stopPropagation();
              }
            }}
          >
            <div className="flex flex-col gap-4">
              {/* Material and Date Preset Selection */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Material Selection */}
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Material</label>
                  <select
                    className="misty-select"
                    value={selectedMaterial}
                    onChange={(e) => setSelectedMaterial(e.target.value)}
                    data-testid="material-select"
                  >
                    <option value="">Select a material...</option>
                    {materials.map((material) => (
                      <option key={material.id} value={material.id}>
                        {material.material_description || material.supplier} ({material.product_code || 'N/A'})
                      </option>
                    ))}
                  </select>
                </div>
                
                {/* Date Range Preset */}
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Date Range</label>
                  <select
                    className="misty-select"
                    value={datePreset}
                    onChange={(e) => handlePresetChange(e.target.value)}
                  >
                    <option value="last_30_days">Last 30 Days</option>
                    <option value="last_90_days">Last 90 Days</option>
                    <option value="this_month">This Month</option>
                    <option value="last_month">Last Month</option>
                    <option value="this_year">This Year</option>
                    <option value="last_year">Last Year</option>
                    <option value="custom">Custom Range</option>
                  </select>
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
              
              {/* Custom Date Range Selectors (only show when Custom is selected) */}
              {datePreset === 'custom' && (
                <div className="bg-gray-700/30 rounded-lg p-4">
                  <h4 className="text-sm font-medium text-white mb-3">Custom Date Range</h4>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {/* Start Year */}
                    <div>
                      <label className="block text-xs text-gray-400 mb-1">Start Year</label>
                      <select
                        className="misty-select text-sm"
                        value={customStartYear}
                        onChange={(e) => setCustomStartYear(parseInt(e.target.value))}
                      >
                        {Array.from({ length: 10 }, (_, i) => new Date().getFullYear() - i).map(year => (
                          <option key={year} value={year}>{year}</option>
                        ))}
                      </select>
                    </div>
                    
                    {/* Start Month */}
                    <div>
                      <label className="block text-xs text-gray-400 mb-1">Start Month</label>
                      <select
                        className="misty-select text-sm"
                        value={customStartMonth}
                        onChange={(e) => setCustomStartMonth(parseInt(e.target.value))}
                      >
                        {['January', 'February', 'March', 'April', 'May', 'June', 
                          'July', 'August', 'September', 'October', 'November', 'December'].map((month, idx) => (
                          <option key={idx} value={idx}>{month}</option>
                        ))}
                      </select>
                    </div>
                    
                    {/* End Year */}
                    <div>
                      <label className="block text-xs text-gray-400 mb-1">End Year</label>
                      <select
                        className="misty-select text-sm"
                        value={customEndYear}
                        onChange={(e) => setCustomEndYear(parseInt(e.target.value))}
                      >
                        {Array.from({ length: 10 }, (_, i) => new Date().getFullYear() - i).map(year => (
                          <option key={year} value={year}>{year}</option>
                        ))}
                      </select>
                    </div>
                    
                    {/* End Month */}
                    <div>
                      <label className="block text-xs text-gray-400 mb-1">End Month</label>
                      <select
                        className="misty-select text-sm"
                        value={customEndMonth}
                        onChange={(e) => setCustomEndMonth(parseInt(e.target.value))}
                      >
                        {['January', 'February', 'March', 'April', 'May', 'June', 
                          'July', 'August', 'September', 'October', 'November', 'December'].map((month, idx) => (
                          <option key={idx} value={idx}>{month}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                  <p className="text-xs text-gray-400 mt-2">
                    Selected range: {new Date(customStartYear, customStartMonth, 1).toLocaleDateString()} - {new Date(customEndYear, customEndMonth + 1, 0).toLocaleDateString()}
                  </p>
                </div>
              )}
              
              {/* Display selected date range */}
              {datePreset !== 'custom' && startDate && endDate && (
                <div className="text-sm text-gray-400">
                  Period: {new Date(startDate).toLocaleDateString()} - {new Date(endDate).toLocaleDateString()}
                </div>
              )}
              
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
                    <button
                      onClick={printMaterialUsageReport}
                      className="flex items-center gap-2 px-4 py-2 bg-yellow-600 hover:bg-yellow-700 text-white rounded transition-colors"
                      title="Print Report as PDF"
                    >
                      <PrinterIcon className="h-5 w-5" />
                      <span>Print Report</span>
                    </button>
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

        {/* Consumable Usage Report */}
        <ReportCard title="Consumable Usage Report by Date" icon={CubeIcon}>
          <div className="space-y-4">
            <p className="text-sm text-gray-400 mb-2">
              Tracks usage of all consumables from Products & Specifications, excluding Spiral Paper Cores and Composite Cores
            </p>
            
            <div className="flex flex-col gap-4">
              {/* Client and Date Preset Selection */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Client Selection (Optional) */}
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Client (Optional)</label>
                  <select
                    className="misty-select"
                    value={selectedProductClient}
                    onChange={(e) => setSelectedProductClient(e.target.value)}
                  >
                    <option value="">All Clients</option>
                    {clients.map((client) => (
                      <option key={client.id} value={client.id}>
                        {client.company_name}
                      </option>
                    ))}
                  </select>
                </div>
                
                {/* Date Range Preset */}
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Date Range</label>
                  <select
                    className="misty-select"
                    value={productDatePreset}
                    onChange={(e) => handleProductPresetChange(e.target.value)}
                  >
                    <option value="last_30_days">Last 30 Days</option>
                    <option value="last_90_days">Last 90 Days</option>
                    <option value="this_month">This Month</option>
                    <option value="last_month">Last Month</option>
                    <option value="this_year">This Year</option>
                    <option value="last_year">Last Year</option>
                    <option value="custom">Custom Range</option>
                  </select>
                </div>
                
                {/* Generate Button */}
                <div className="flex items-end">
                  <button
                    onClick={loadProductUsageReport}
                    disabled={loadingProductReport}
                    className="misty-button misty-button-primary w-full"
                  >
                    {loadingProductReport ? 'Loading...' : 'Generate Report'}
                  </button>
                </div>
              </div>
              
              {/* Custom Date Range Selectors */}
              {productDatePreset === 'custom' && (
                <div className="bg-gray-700/30 rounded-lg p-4">
                  <h4 className="text-sm font-medium text-white mb-3">Custom Date Range</h4>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                      <label className="block text-xs text-gray-400 mb-1">Start Year</label>
                      <select
                        className="misty-select text-sm"
                        value={customProductStartYear}
                        onChange={(e) => setCustomProductStartYear(parseInt(e.target.value))}
                      >
                        {Array.from({ length: 10 }, (_, i) => new Date().getFullYear() - i).map(year => (
                          <option key={year} value={year}>{year}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs text-gray-400 mb-1">Start Month</label>
                      <select
                        className="misty-select text-sm"
                        value={customProductStartMonth}
                        onChange={(e) => setCustomProductStartMonth(parseInt(e.target.value))}
                      >
                        {['January', 'February', 'March', 'April', 'May', 'June', 
                          'July', 'August', 'September', 'October', 'November', 'December'].map((month, idx) => (
                          <option key={idx} value={idx}>{month}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs text-gray-400 mb-1">End Year</label>
                      <select
                        className="misty-select text-sm"
                        value={customProductEndYear}
                        onChange={(e) => setCustomProductEndYear(parseInt(e.target.value))}
                      >
                        {Array.from({ length: 10 }, (_, i) => new Date().getFullYear() - i).map(year => (
                          <option key={year} value={year}>{year}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs text-gray-400 mb-1">End Month</label>
                      <select
                        className="misty-select text-sm"
                        value={customProductEndMonth}
                        onChange={(e) => setCustomProductEndMonth(parseInt(e.target.value))}
                      >
                        {['January', 'February', 'March', 'April', 'May', 'June', 
                          'July', 'August', 'September', 'October', 'November', 'December'].map((month, idx) => (
                          <option key={idx} value={idx}>{month}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                  <p className="text-xs text-gray-400 mt-2">
                    Selected range: {new Date(customProductStartYear, customProductStartMonth, 1).toLocaleDateString()} - {new Date(customProductEndYear, customProductEndMonth + 1, 0).toLocaleDateString()}
                  </p>
                </div>
              )}
              
              {/* Display selected date range */}
              {productDatePreset !== 'custom' && productStartDate && productEndDate && (
                <div className="text-sm text-gray-400">
                  Period: {new Date(productStartDate).toLocaleDateString()} - {new Date(productEndDate).toLocaleDateString()}
                </div>
              )}
              
              {/* Order Breakdown Toggle */}
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setIncludeProductOrderBreakdown(!includeProductOrderBreakdown)}
                  className={`flex items-center gap-2 px-4 py-2 rounded transition-colors ${
                    includeProductOrderBreakdown 
                      ? 'bg-yellow-600 text-white' 
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  <div className={`w-5 h-5 border-2 rounded flex items-center justify-center ${
                    includeProductOrderBreakdown ? 'border-white' : 'border-gray-400'
                  }`}>
                    {includeProductOrderBreakdown && <CheckIcon className="h-4 w-4" />}
                  </div>
                  <span>Show breakdown by order</span>
                </button>
              </div>
            </div>

            {productUsageReport && (
              <div className="mt-6 space-y-6">
                {/* Report Header */}
                <div className="border-t border-gray-700 pt-4">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h4 className="font-medium text-white text-lg mb-1">
                        Consumable Usage Report
                      </h4>
                      <p className="text-sm text-gray-400">
                        Period: {new Date(productUsageReport.report_period.start_date).toLocaleDateString()} - {new Date(productUsageReport.report_period.end_date).toLocaleDateString()}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
                        Excludes: {productUsageReport.excluded_types.join(', ')}
                      </p>
                    </div>
                    <button
                      onClick={printProductUsageReport}
                      className="flex items-center gap-2 px-4 py-2 bg-yellow-600 hover:bg-yellow-700 text-white rounded transition-colors"
                      title="Print Report as PDF"
                    >
                      <PrinterIcon className="h-5 w-5" />
                      <span>Print Report</span>
                    </button>
                  </div>
                  
                  {/* Summary Stats */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                    <div className="bg-gray-700/50 rounded-lg p-4 text-center">
                      <p className="text-2xl font-bold text-yellow-400">
                        {productUsageReport.grand_total_m2} m²
                      </p>
                      <p className="text-sm text-gray-400">Total Area Used</p>
                    </div>
                    <div className="bg-gray-700/50 rounded-lg p-4 text-center">
                      <p className="text-2xl font-bold text-green-400">
                        {productUsageReport.grand_total_length_m} m
                      </p>
                      <p className="text-sm text-gray-400">Total Length</p>
                    </div>
                    <div className="bg-gray-700/50 rounded-lg p-4 text-center">
                      <p className="text-2xl font-bold text-blue-400">
                        {productUsageReport.total_products}
                      </p>
                      <p className="text-sm text-gray-400">Consumables Used</p>
                    </div>
                  </div>

                  {/* Consumables Display */}
                  {productUsageReport.products.map((product, productIndex) => (
                    <div key={productIndex} className="mb-6 border border-gray-700 rounded-lg p-4">
                      <div className="mb-3">
                        <h5 className="font-medium text-white">{product.product_info.product_description}</h5>
                        <p className="text-xs text-gray-400">
                          Code: {product.product_info.product_code} | Client: {product.product_info.client_name}
                        </p>
                      </div>
                      
                      {/* Usage by Width Table for this Consumable */}
                      <div className="overflow-x-auto">
                        <table className="min-w-full">
                          <thead>
                            <tr className="border-b border-gray-700">
                              <th className="text-left py-2 px-3 text-gray-300 font-medium text-sm">Width (mm)</th>
                              <th className="text-right py-2 px-3 text-gray-300 font-medium text-sm">Length (m)</th>
                              <th className="text-right py-2 px-3 text-gray-300 font-medium text-sm">Area (m²)</th>
                              {includeProductOrderBreakdown && (
                                <th className="text-center py-2 px-3 text-gray-300 font-medium text-sm">Orders</th>
                              )}
                            </tr>
                          </thead>
                          <tbody>
                            {product.usage_by_width.map((width, widthIndex) => (
                              <React.Fragment key={widthIndex}>
                                <tr className="border-b border-gray-700/30 hover:bg-gray-700/20">
                                  <td className="py-2 px-3 text-white text-sm">{width.width_mm} mm</td>
                                  <td className="py-2 px-3 text-right text-gray-300 text-sm">{width.total_length_m.toLocaleString()} m</td>
                                  <td className="py-2 px-3 text-right text-yellow-400 font-medium text-sm">{width.m2.toLocaleString()} m²</td>
                                  {includeProductOrderBreakdown && (
                                    <td className="py-2 px-3 text-center text-gray-300 text-sm">{width.order_count || 0}</td>
                                  )}
                                </tr>
                                
                                {includeProductOrderBreakdown && width.orders && width.orders.length > 0 && (
                                  <tr>
                                    <td colSpan={includeProductOrderBreakdown ? 4 : 3} className="py-2 px-3 bg-gray-700/10">
                                      <div className="pl-6 space-y-1">
                                        <p className="text-xs font-medium text-gray-400 mb-1">Order Breakdown:</p>
                                        {width.orders.map((order, orderIndex) => (
                                          <div key={orderIndex} className="flex justify-between text-xs py-1">
                                            <span className="text-gray-300">
                                              {order.order_number} - {order.client_name}
                                            </span>
                                            <span className="text-gray-400">
                                              {order.total_length_m} m ({order.quantity} × {order.length_per_unit}m)
                                            </span>
                                          </div>
                                        ))}
                                      </div>
                                    </td>
                                  </tr>
                                )}
                              </React.Fragment>
                            ))}
                            
                            {/* Consumable Subtotal */}
                            <tr className="bg-gray-700/40 font-medium">
                              <td className="py-2 px-3 text-white text-sm">Consumable Total</td>
                              <td className="py-2 px-3 text-right text-white text-sm">{product.product_total_length_m.toLocaleString()} m</td>
                              <td className="py-2 px-3 text-right text-yellow-400 text-sm">{product.product_total_m2.toLocaleString()} m²</td>
                              {includeProductOrderBreakdown && <td></td>}
                            </tr>
                          </tbody>
                        </table>
                      </div>
                    </div>
                  ))}
                  
                  {/* Grand Total */}
                  <div className="bg-gray-700/50 rounded-lg p-4 mt-4">
                    <div className="flex justify-between items-center">
                      <span className="text-white font-bold">GRAND TOTAL (All Consumables)</span>
                      <div className="flex gap-8">
                        <span className="text-white font-bold">{productUsageReport.grand_total_length_m.toLocaleString()} m</span>
                        <span className="text-yellow-400 font-bold text-lg">{productUsageReport.grand_total_m2.toLocaleString()} m²</span>
                      </div>
                    </div>
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