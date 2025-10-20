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
  PrinterIcon,
  UserIcon,
  ExclamationTriangleIcon,
  ClipboardDocumentListIcon,
  DocumentChartBarIcon,
  CurrencyDollarIcon,
  ChevronDownIcon,
  ChevronUpIcon
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
  
  // Projected Order Analysis states
  const [selectedProjectionClient, setSelectedProjectionClient] = useState('');
  const [projectionDatePreset, setProjectionDatePreset] = useState('last_90_days');
  const [projectionStartDate, setProjectionStartDate] = useState('');
  const [projectionEndDate, setProjectionEndDate] = useState('');
  const [customProjectionStartYear, setCustomProjectionStartYear] = useState(new Date().getFullYear());
  const [customProjectionStartMonth, setCustomProjectionStartMonth] = useState(new Date().getMonth());
  const [customProjectionEndYear, setCustomProjectionEndYear] = useState(new Date().getFullYear());
  const [customProjectionEndMonth, setCustomProjectionEndMonth] = useState(new Date().getMonth());
  const [projectionReport, setProjectionReport] = useState(null);
  const [loadingProjectionReport, setLoadingProjectionReport] = useState(false);
  const [expandedMaterials, setExpandedMaterials] = useState({});
  const [expandedCustomers, setExpandedCustomers] = useState({});
  
  // Job Card Performance Report states
  const [jobCardSearchTerm, setJobCardSearchTerm] = useState('');
  const [jobCardSearchType, setJobCardSearchType] = useState('customer'); // customer, invoice, product
  const [jobCardResults, setJobCardResults] = useState([]);
  const [loadingJobCards, setLoadingJobCards] = useState(false);
  const [selectedOrderJobCards, setSelectedOrderJobCards] = useState(null);
  const [showJobCardsModal, setShowJobCardsModal] = useState(false);
  const [editingJobCard, setEditingJobCard] = useState(null);
  const [selectedProjectionPeriod, setSelectedProjectionPeriod] = useState('3_months');
  
  // Modal states for each report type
  const [showMaterialUsageModal, setShowMaterialUsageModal] = useState(false);
  const [showConsumableUsageModal, setShowConsumableUsageModal] = useState(false);
  const [showProjectionModal, setShowProjectionModal] = useState(false);
  const [showOutstandingJobsModal, setShowOutstandingJobsModal] = useState(false);
  const [showLateDeliveriesModal, setShowLateDeliveriesModal] = useState(false);
  const [showCustomerReportModal, setShowCustomerReportModal] = useState(false);
  const [showJobPerformanceModal, setShowJobPerformanceModal] = useState(false);
  
  // Job Performance Report states
  const [jobPerformanceStartDate, setJobPerformanceStartDate] = useState('');
  const [jobPerformanceEndDate, setJobPerformanceEndDate] = useState('');
  const [jobPerformanceDatePreset, setJobPerformanceDatePreset] = useState('last_30_days');
  const [customJobPerformanceStartYear, setCustomJobPerformanceStartYear] = useState(new Date().getFullYear());
  const [customJobPerformanceStartMonth, setCustomJobPerformanceStartMonth] = useState(new Date().getMonth());
  const [customJobPerformanceEndYear, setCustomJobPerformanceEndYear] = useState(new Date().getFullYear());
  const [customJobPerformanceEndMonth, setCustomJobPerformanceEndMonth] = useState(new Date().getMonth());
  const [jobPerformanceReport, setJobPerformanceReport] = useState(null);
  const [loadingJobPerformance, setLoadingJobPerformance] = useState(false);
  const [expandedJobDetails, setExpandedJobDetails] = useState({});
  const [showJobTypeBreakdown, setShowJobTypeBreakdown] = useState(false);
  const [showClientPerformance, setShowClientPerformance] = useState(false);

  // Profitability Report states
  const [showProfitabilityModal, setShowProfitabilityModal] = useState(false);
  const [profitabilityMode, setProfitabilityMode] = useState('all'); // 'all' or 'filtered'
  const [selectedProfitClients, setSelectedProfitClients] = useState([]); // Multiple clients
  const [selectedProfitProducts, setSelectedProfitProducts] = useState([]); // Multiple products
  const [clientProducts, setClientProducts] = useState([]); // All client products
  const [profitabilityStartDate, setProfitabilityStartDate] = useState('');
  const [profitabilityEndDate, setProfitabilityEndDate] = useState('');
  const [profitabilityDatePreset, setProfitabilityDatePreset] = useState('last_30_days');
  const [profitThreshold, setProfitThreshold] = useState(0);
  const [profitabilityReport, setProfitabilityReport] = useState(null);
  const [loadingProfitability, setLoadingProfitability] = useState(false);
  const [completedOrders, setCompletedOrders] = useState([]);
  const [expandedMaterialDetails, setExpandedMaterialDetails] = useState({});

  useEffect(() => {
    loadReportsData();
    loadMaterials();
    
    // Set default dates (last 30 days)
    const { start, end } = getDateRangeFromPreset('last_30_days');
    setStartDate(start);
    setEndDate(end);
    setProductStartDate(start);
    setProductEndDate(end);
    setJobPerformanceStartDate(start);
    setJobPerformanceEndDate(end);
    setProfitabilityStartDate(start);
    setProfitabilityEndDate(end);
    
    // Set default projection dates (last 90 days for better analysis)
    const projectionDates = getDateRangeFromPreset('last_90_days');
    setProjectionStartDate(projectionDates.start);
    setProjectionEndDate(projectionDates.end);
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
  
  // Handle projection report preset changes
  const handleProjectionPresetChange = (preset) => {
    setProjectionDatePreset(preset);
    if (preset !== 'custom') {
      const { start, end } = getDateRangeFromPreset(preset);
      setProjectionStartDate(start);
      setProjectionEndDate(end);
    }
  };
  
  const loadProjectionReport = async () => {
    // Calculate dates based on current selection
    let finalStartDate = projectionStartDate;
    let finalEndDate = projectionEndDate;
    
    if (projectionDatePreset === 'custom') {
      const start = new Date(customProjectionStartYear, customProjectionStartMonth, 1);
      const end = new Date(customProjectionEndYear, customProjectionEndMonth + 1, 0);
      finalStartDate = start.toISOString().split('T')[0];
      finalEndDate = end.toISOString().split('T')[0];
      setProjectionStartDate(finalStartDate);
      setProjectionEndDate(finalEndDate);
    }
    
    if (!finalStartDate || !finalEndDate) {
      toast.error('Please select date range');
      return;
    }

    try {
      setLoadingProjectionReport(true);
      const response = await apiHelpers.getProjectedOrderAnalysis(
        selectedProjectionClient || null,
        finalStartDate + 'T00:00:00Z',
        finalEndDate + 'T23:59:59Z'
      );
      setProjectionReport(response.data?.data);
      toast.success('Projected order analysis generated successfully');
    } catch (error) {
      console.error('Failed to load projection report:', error);
      toast.error('Failed to load projection report');
    } finally {
      setLoadingProjectionReport(false);
    }
  };
  
  const toggleMaterialsView = (productId) => {
    setExpandedMaterials(prev => ({
      ...prev,
      [productId]: !prev[productId]
    }));
  };
  
  const toggleCustomersView = (productId) => {
    setExpandedCustomers(prev => ({
      ...prev,
      [productId]: !prev[productId]
    }));
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
  

  const loadJobPerformanceReport = async () => {
    // Calculate dates based on current selection
    let finalStartDate = jobPerformanceStartDate;
    let finalEndDate = jobPerformanceEndDate;
    
    if (jobPerformanceDatePreset === 'custom') {
      const start = new Date(customJobPerformanceStartYear, customJobPerformanceStartMonth, 1);
      const end = new Date(customJobPerformanceEndYear, customJobPerformanceEndMonth + 1, 0);
      finalStartDate = start.toISOString().split('T')[0];
      finalEndDate = end.toISOString().split('T')[0];
      setJobPerformanceStartDate(finalStartDate);
      setJobPerformanceEndDate(finalEndDate);
    }
    
    if (!finalStartDate || !finalEndDate) {
      toast.error('Please select date range');
      return;
    }

    try {
      setLoadingJobPerformance(true);
      const response = await apiHelpers.getJobCardPerformance(
        finalStartDate + 'T00:00:00Z',
        finalEndDate + 'T23:59:59Z'
      );
      setJobPerformanceReport(response.data?.data);
      toast.success('Job card performance report generated successfully');
    } catch (error) {
      console.error('Failed to load job performance report:', error);
      toast.error('Failed to load job performance report');
    } finally {
      setLoadingJobPerformance(false);
    }
  };
  
  const exportJobPerformanceCSV = async () => {
    if (!jobPerformanceReport) {
      toast.error('Please generate the report first');
      return;
    }

    try {
      const response = await apiHelpers.exportJobCardPerformanceCSV(
        jobPerformanceStartDate + 'T00:00:00Z',
        jobPerformanceEndDate + 'T23:59:59Z'
      );
      
      // Create blob and download
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `job_card_performance_${new Date().toISOString().split('T')[0]}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      toast.success('CSV exported successfully');
    } catch (error) {
      console.error('Failed to export CSV:', error);
      toast.error('Failed to export CSV');
    }
  };
  
  const loadProfitabilityReport = async () => {
    try {
      setLoadingProfitability(true);
      
      // Build request based on mode
      const requestData = {
        profit_threshold: profitThreshold
      };
      
      if (profitabilityMode === 'all') {
        // All jobs mode - get all completed/archived jobs
        // Use date range for filtering
        let finalStartDate = profitabilityStartDate;
        let finalEndDate = profitabilityEndDate;
        
        if (finalStartDate && finalEndDate) {
          requestData.start_date = finalStartDate + 'T00:00:00Z';
          requestData.end_date = finalEndDate + 'T23:59:59Z';
        }
      } else if (profitabilityMode === 'filtered') {
        // Filtered mode - use client and product filters
        
        // Multiple clients filter
        if (selectedProfitClients.length > 0) {
          requestData.client_ids = selectedProfitClients;
        }
        
        // Multiple products filter
        if (selectedProfitProducts.length > 0) {
          requestData.product_ids = selectedProfitProducts;
        }
        
        // Date range
        let finalStartDate = profitabilityStartDate;
        let finalEndDate = profitabilityEndDate;
        
        if (profitabilityDatePreset !== 'all_time' && (!finalStartDate || !finalEndDate)) {
          toast.error('Please select date range');
          return;
        }
        
        if (finalStartDate && finalEndDate) {
          requestData.start_date = finalStartDate + 'T00:00:00Z';
          requestData.end_date = finalEndDate + 'T23:59:59Z';
        }
      }
      
      const response = await fetch('/api/reports/profitability', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
      });
      
      if (response.ok) {
        const data = await response.json();
        setProfitabilityReport(data.data);
        toast.success(data.message);
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to generate profitability report');
      }
    } catch (error) {
      console.error('Failed to load profitability report:', error);
      toast.error('Failed to load profitability report');
    } finally {
      setLoadingProfitability(false);
    }
  };
  
  const loadCompletedOrders = async () => {
    try {
      const response = await apiHelpers.getOrders();
      const completed = response.data.filter(order => 
        order.status === 'completed' || order.current_stage === 'cleared'
      );
      setCompletedOrders(completed);
    } catch (error) {
      console.error('Failed to load completed orders:', error);
    }
  };
  
  const loadClientProducts = async () => {
    try {
      // Load all client products from all clients
      const clientsResponse = await apiHelpers.getClients();
      const allClients = clientsResponse.data;
      
      let allProducts = [];
      
      // Fetch products for each client
      for (const client of allClients) {
        try {
          const response = await fetch(`/api/clients/${client.id}/catalog`, {
            headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
          });
          if (response.ok) {
            const products = await response.json();
            // Add client name to each product for display
            const productsWithClient = products.map(p => ({
              ...p,
              client_name: client.name || client.company_name
            }));
            allProducts = [...allProducts, ...productsWithClient];
          }
        } catch (error) {
          console.error(`Failed to load products for client ${client.id}:`, error);
        }
      }
      
      setClientProducts(allProducts);
      console.log(`Loaded ${allProducts.length} products from ${allClients.length} clients`);
    } catch (error) {
      console.error('Failed to load client products:', error);
      toast.error('Failed to load client products');
    }
  };
  
  const toggleMaterialDetails = (orderId) => {
    setExpandedMaterialDetails(prev => ({
      ...prev,
      [orderId]: !prev[orderId]
    }));
  };
  
  const toggleJobDetails = (jobId) => {
    setExpandedJobDetails(prev => ({
      ...prev,
      [jobId]: !prev[jobId]
    }));
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

  const searchJobCards = async () => {
    // Trim whitespace and check if empty
    const trimmedSearch = jobCardSearchTerm.trim();
    
    if (!trimmedSearch) {
      toast.error('Please enter a search term or click "Search All"');
      return;
    }

    try {
      setLoadingJobCards(true);
      const params = {};
      
      if (jobCardSearchType === 'customer') {
        params.customer = trimmedSearch;
      } else if (jobCardSearchType === 'invoice') {
        params.invoice_number = trimmedSearch;
      } else if (jobCardSearchType === 'product') {
        params.product = trimmedSearch;
      }
      
      const response = await apiHelpers.searchJobCards(params);
      setJobCardResults(response.data?.data || []);
      
      if (response.data?.data?.length === 0) {
        toast.info('No job cards found for this search');
      } else {
        toast.success(`Found ${response.data?.data?.length} orders with job cards`);
      }
    } catch (error) {
      console.error('Failed to search job cards:', error);
      toast.error('Failed to search job cards');
    } finally {
      setLoadingJobCards(false);
    }
  };

  const searchAllJobCards = async () => {
    try {
      setLoadingJobCards(true);
      
      // Search without any parameters to get all job cards
      const response = await apiHelpers.searchJobCards({});
      setJobCardResults(response.data?.data || []);
      
      if (response.data?.data?.length === 0) {
        toast.info('No job cards found');
      } else {
        toast.success(`Found ${response.data?.data?.length} orders with job cards`);
      }
    } catch (error) {
      console.error('Failed to search job cards:', error);
      toast.error('Failed to search job cards');
    } finally {
      setLoadingJobCards(false);
    }
  };

  const viewOrderJobCards = async (orderData) => {
    setSelectedOrderJobCards(orderData);
    setShowJobCardsModal(true);
  };

  const updateJobCard = async (jobCardId, updates) => {
    try {
      await apiHelpers.updateJobCard(jobCardId, updates);
      toast.success('Job card updated successfully');
      
      // Refresh the job cards for this order
      const response = await apiHelpers.getJobCardsByOrder(selectedOrderJobCards.order_id);
      const updatedJobCards = response.data?.data || [];
      setSelectedOrderJobCards({
        ...selectedOrderJobCards,
        job_cards: updatedJobCards
      });
    } catch (error) {
      console.error('Failed to update job card:', error);
      toast.error('Failed to update job card');
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


  const ReportTile = ({ title, description, icon: Icon, onClick }) => {
    return (
      <div 
        className="misty-card p-6 cursor-pointer hover:bg-gray-700/50 transition-all duration-200 hover:scale-105 hover:shadow-xl border-2 border-gray-700 hover:border-yellow-500"
        onDoubleClick={onClick}
        title="Double-click to open"
      >
        <div className="flex flex-col items-center text-center h-full justify-center">
          <Icon className="h-12 w-12 text-yellow-400 mb-4" />
          <h3 className="text-lg font-semibold text-white mb-2">{title}</h3>
          <p className="text-sm text-gray-400">{description}</p>
          <p className="text-xs text-gray-500 mt-3 italic">Double-click to open</p>
        </div>
      </div>
    );
  };
  
  const ReportModal = ({ isOpen, onClose, title, children }) => {
    if (!isOpen) return null;
    
    return (
      <div 
        className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4"
        onClick={(e) => {
          if (e.target === e.currentTarget) onClose();
        }}
      >
        <div className="bg-gray-800 rounded-lg shadow-2xl max-w-6xl w-full max-h-[90vh] overflow-hidden border-2 border-gray-700">
          <div className="bg-gray-900 px-6 py-4 border-b border-gray-700 flex justify-between items-center">
            <h2 className="text-2xl font-bold text-white">{title}</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white transition-colors text-2xl font-bold"
            >
              ×
            </button>
          </div>
          <div className="p-6 overflow-y-auto max-h-[calc(90vh-80px)]">
            {children}
          </div>
        </div>
      </div>
    );
  };

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
      <div className="p-6">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-white">Reports Dashboard</h2>
          <p className="text-sm text-gray-400">Double-click any report to open</p>
        </div>
        
        {/* Report Tiles Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-6">
          <ReportTile
            title="Material Usage Report"
            description="Track raw material usage by width across selected time periods"
            icon={CubeIcon}
            onClick={() => setShowMaterialUsageModal(true)}
          />
          
          <ReportTile
            title="Consumable Usage Report"
            description="Analyze consumable product usage excluding cores, with order breakdowns"
            icon={CubeIcon}
            onClick={() => setShowConsumableUsageModal(true)}
          />
          
          <ReportTile
            title="Projected Order Analysis"
            description="Forecast future orders for 3, 6, 9, and 12 months with material requirements"
            icon={ChartBarIcon}
            onClick={() => setShowProjectionModal(true)}
          />
          
          <ReportTile
            title="Outstanding Jobs"
            description="View all active jobs currently in production"
            icon={ClipboardDocumentListIcon}
            onClick={() => setShowOutstandingJobsModal(true)}
          />
          
          <ReportTile
            title="Late Deliveries"
            description="Track overdue orders and jobs that missed their delivery dates"
            icon={ExclamationTriangleIcon}
            onClick={() => setShowLateDeliveriesModal(true)}
          />
          
          <ReportTile
            title="Customer Annual Report"
            description="Comprehensive yearly analysis of customer orders and spending"
            icon={UserIcon}
            onClick={() => setShowCustomerReportModal(true)}
          />
          
          <ReportTile
            title="Job Card Performance"
            description="Track time spent on each job and stock produced with averages"
            icon={ClipboardDocumentListIcon}
            onClick={() => setShowJobPerformanceModal(true)}
          />
          
          <ReportTile
            title="Profitability Report"
            description="Calculate Gross Profit and Net Profit for completed jobs"
            icon={CurrencyDollarIcon}
            onClick={() => {
              setShowProfitabilityModal(true);
              loadCompletedOrders();
              loadClientProducts();
            }}
          />
        </div>

        {/* Report Modals */}
        <ReportModal
          isOpen={showMaterialUsageModal}
          onClose={() => setShowMaterialUsageModal(false)}
          title="Material Usage Report by Width"
        >
          <div className="space-y-4">
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
        </ReportModal>

        <ReportModal
          isOpen={showConsumableUsageModal}
          onClose={() => setShowConsumableUsageModal(false)}
          title="Consumable Usage Report by Date"
        >
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
                                
                                {/* Order Breakdown */}
                                {includeProductOrderBreakdown && width.orders && width.orders.length > 0 && (
                                  <tr>
                                    <td colSpan={includeProductOrderBreakdown ? 4 : 3} className="py-2 px-3 bg-gray-700/20">
                                      <div className="pl-8 space-y-1">
                                        <p className="text-sm font-medium text-gray-400 mb-2">Order Breakdown:</p>
                                        {width.orders.map((order, orderIndex) => (
                                          <div key={orderIndex} className="flex justify-between text-sm py-1">
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
                            <tr className="bg-gray-700/30 font-bold">
                              <td className="py-3 px-3 text-white">Product Total</td>
                              <td className="py-3 px-3 text-right text-white">{product.product_total_length_m.toLocaleString()} m</td>
                              <td className="py-3 px-3 text-right text-yellow-400">{product.product_total_m2.toLocaleString()} m²</td>
                              {includeProductOrderBreakdown && <td></td>}
                            </tr>
                          </tbody>
                        </table>
                      </div>
                    </div>
                  ))}
                  
                  {/* Grand Total */}
                  <div className="border-t-2 border-gray-600 pt-4">
                    <div className="bg-gray-700/50 rounded-lg p-4">
                      <div className="flex justify-between items-center">
                        <span className="text-lg font-bold text-white">GRAND TOTAL (All Consumables)</span>
                        <div className="text-right">
                          <div className="text-lg font-bold text-yellow-400">{productUsageReport.grand_total_m2} m²</div>
                          <div className="text-sm text-gray-400">{productUsageReport.grand_total_length_m} m</div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </ReportModal>

        <ReportModal
          isOpen={showProjectionModal}
          onClose={() => setShowProjectionModal(false)}
          title="Projected Order Analysis"
        >
          <div className="space-y-4">
            <p className="text-sm text-gray-400 mb-2">
              Analyze all orders (including orders on hand) and project future requirements for 3, 6, 9, and 12 months with material breakdown
            </p>
            
            <div className="flex flex-col gap-4">
              {/* Client and Date Preset Selection */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Client Selection (Optional) */}
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Client (Optional)</label>
                  <select
                    className="misty-select"
                    value={selectedProjectionClient}
                    onChange={(e) => setSelectedProjectionClient(e.target.value)}
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
                  <label className="block text-sm text-gray-400 mb-1">Historical Period</label>
                  <select
                    className="misty-select"
                    value={projectionDatePreset}
                    onChange={(e) => handleProjectionPresetChange(e.target.value)}
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
                    onClick={loadProjectionReport}
                    disabled={loadingProjectionReport}
                    className="misty-button misty-button-primary w-full"
                  >
                    {loadingProjectionReport ? 'Loading...' : 'Generate Analysis'}
                  </button>
                </div>
              </div>
              
              {/* Custom Date Range Selectors */}
              {projectionDatePreset === 'custom' && (
                <div className="bg-gray-700/30 rounded-lg p-4">
                  <h4 className="text-sm font-medium text-white mb-3">Custom Historical Period</h4>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                      <label className="block text-xs text-gray-400 mb-1">Start Year</label>
                      <select
                        className="misty-select text-sm"
                        value={customProjectionStartYear}
                        onChange={(e) => setCustomProjectionStartYear(parseInt(e.target.value))}
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
                        value={customProjectionStartMonth}
                        onChange={(e) => setCustomProjectionStartMonth(parseInt(e.target.value))}
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
                        value={customProjectionEndYear}
                        onChange={(e) => setCustomProjectionEndYear(parseInt(e.target.value))}
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
                        value={customProjectionEndMonth}
                        onChange={(e) => setCustomProjectionEndMonth(parseInt(e.target.value))}
                      >
                        {['January', 'February', 'March', 'April', 'May', 'June', 
                          'July', 'August', 'September', 'October', 'November', 'December'].map((month, idx) => (
                          <option key={idx} value={idx}>{month}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                  <p className="text-xs text-gray-400 mt-2">
                    Selected range: {new Date(customProjectionStartYear, customProjectionStartMonth, 1).toLocaleDateString()} - {new Date(customProjectionEndYear, customProjectionEndMonth + 1, 0).toLocaleDateString()}
                  </p>
                </div>
              )}
              
              {/* Display selected date range */}
              {projectionDatePreset !== 'custom' && projectionStartDate && projectionEndDate && (
                <div className="text-sm text-gray-400">
                  Historical Period: {new Date(projectionStartDate).toLocaleDateString()} - {new Date(projectionEndDate).toLocaleDateString()}
                </div>
              )}
            </div>

            {projectionReport && projectionReport.report_period && (
              <div className="mt-6 space-y-6">
                {/* Report Header */}
                <div className="border-t border-gray-700 pt-4">
                  <div className="mb-4">
                    <h4 className="font-medium text-white text-lg mb-1">
                      Projected Order Analysis
                    </h4>
                    <p className="text-sm text-gray-400">
                      Based on historical period: {new Date(projectionReport.report_period.start_date).toLocaleDateString()} - {new Date(projectionReport.report_period.end_date).toLocaleDateString()}
                    </p>
                  </div>
                  
                  {/* Projection Period Selector */}
                  <div className="mb-6">
                    <label className="block text-sm text-gray-400 mb-2">View Projections For:</label>
                    <div className="flex flex-wrap gap-2">
                      {['3_months', '6_months', '9_months', '12_months'].map((period) => (
                        <button
                          key={period}
                          onClick={() => setSelectedProjectionPeriod(period)}
                          className={`px-4 py-2 rounded transition-colors ${
                            selectedProjectionPeriod === period
                              ? 'bg-yellow-600 text-white'
                              : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                          }`}
                        >
                          {period.replace('_', ' ').replace('months', 'Months')}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Summary Stats */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                    <div className="bg-gray-700/50 rounded-lg p-4 text-center">
                      <p className="text-2xl font-bold text-yellow-400">
                        {projectionReport.summary[selectedProjectionPeriod]?.total_projected_orders || 0}
                      </p>
                      <p className="text-sm text-gray-400">Projected Orders</p>
                    </div>
                    <div className="bg-gray-700/50 rounded-lg p-4 text-center">
                      <p className="text-2xl font-bold text-green-400">
                        {projectionReport.summary[selectedProjectionPeriod]?.total_projected_material_cost ? formatCurrency(projectionReport.summary[selectedProjectionPeriod].total_projected_material_cost) : '$0'}
                      </p>
                      <p className="text-sm text-gray-400">Projected Material Cost</p>
                    </div>
                    <div className="bg-gray-700/50 rounded-lg p-4 text-center">
                      <p className="text-2xl font-bold text-blue-400">
                        {projectionReport.products?.length || 0}
                      </p>
                      <p className="text-sm text-gray-400">Products Analyzed</p>
                    </div>
                  </div>

                  {/* Products List */}
                  <div className="space-y-4">
                    {projectionReport.products.map((product, index) => {
                      const projectedQty = product.projections[selectedProjectionPeriod];
                      const materialReqs = product.material_requirements[selectedProjectionPeriod];
                      const isExpanded = expandedMaterials[product.product_info.product_id];
                      
                      return (
                        <div key={index} className="border border-gray-700 rounded-lg p-4 bg-gray-800/50">
                          <div className="flex justify-between items-start mb-3">
                            <div className="flex-1">
                              <h5 className="font-medium text-white text-lg">
                                {product.product_info.product_description}
                              </h5>
                              <p className="text-xs text-gray-400">
                                Code: {product.product_info.product_code} | Client: {product.product_info.client_name}
                              </p>
                            </div>
                            <div className="text-right">
                              <div className="text-xl font-bold text-yellow-400">
                                {projectedQty} units
                              </div>
                              <div className="text-sm text-gray-400">
                                Projected for {selectedProjectionPeriod.replace('_', ' ')}
                              </div>
                            </div>
                          </div>
                          
                          <div className="grid grid-cols-2 gap-4 mb-4">
                            <div className="text-center bg-gray-700/30 rounded p-3">
                              <p className="text-lg font-bold text-green-400">
                                {product.historical_data.total_orders}
                              </p>
                              <p className="text-xs text-gray-400">Historical Orders</p>
                            </div>
                            <div className="text-center bg-gray-700/30 rounded p-3">
                              <p className="text-lg font-bold text-blue-400">
                                {product.historical_data.avg_monthly_orders}
                              </p>
                              <p className="text-xs text-gray-400">Avg Monthly Orders</p>
                            </div>
                          </div>
                          
                          {/* Material Requirements Toggle */}
                          <div className="flex justify-between items-center mb-3">
                            <button
                              onClick={() => toggleMaterialsView(product.product_info.product_id)}
                              className="flex items-center gap-2 text-sm text-yellow-400 hover:text-yellow-300"
                            >
                              <span>{isExpanded ? '▼' : '▶'}</span>
                              <span>Material Requirements ({materialReqs?.length || 0} materials)</span>
                            </button>
                            <button
                              onClick={() => toggleCustomersView(product.product_info.product_id)}
                              className="flex items-center gap-2 text-sm text-blue-400 hover:text-blue-300"
                            >
                              <span>{expandedCustomers[product.product_info.product_id] ? '▼' : '▶'}</span>
                              <span>Customer Breakdown</span>
                            </button>
                          </div>
                          
                          {/* Material Requirements */}
                          {isExpanded && materialReqs && (
                            <div className="mt-4 border-t border-gray-700 pt-4">
                              <h6 className="text-xs text-gray-400 mb-3">
                                Formula: Volume = π × core_length × (outer_radius² − inner_radius²); Mass = Volume × Density; Area = Volume ÷ Thickness
                              </h6>
                              <div className="space-y-3">
                                {materialReqs.map((mat, matIndex) => {
                                  if (mat.is_total) {
                                    return (
                                      <div key={matIndex} className="bg-yellow-900/20 border border-yellow-600 rounded-lg p-4">
                                        <div className="text-sm font-bold text-white mb-2">TOTALS FOR CORE</div>
                                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                                          <div>
                                            <p className="text-gray-400">Outer Diameter</p>
                                            <p className="text-white font-medium">{mat.outer_diameter_mm}mm</p>
                                          </div>
                                          <div>
                                            <p className="text-gray-400">Total Mass</p>
                                            <p className="text-green-400 font-medium">{mat.total_paper_mass_kg}kg</p>
                                          </div>
                                          <div>
                                            <p className="text-gray-400">Total Area</p>
                                            <p className="text-blue-400 font-medium">{mat.total_paper_area_m2}m²</p>
                                          </div>
                                          {mat.total_strip_length_m && (
                                            <div>
                                              <p className="text-gray-400">Total Strip Length</p>
                                              <p className="text-purple-400 font-medium">{mat.total_strip_length_m?.toLocaleString()}m</p>
                                            </div>
                                          )}
                                          {mat.total_cost > 0 && (
                                            <div>
                                              <p className="text-gray-400">Total Cost</p>
                                              <p className="text-yellow-400 font-bold text-lg">${mat.total_cost?.toLocaleString()}</p>
                                            </div>
                                          )}
                                        </div>
                                      </div>
                                    );
                                  }
                                  
                                  return (
                                    <div key={matIndex} className="bg-gray-800/50 border border-gray-700 rounded-lg p-4">
                                      <div className="flex justify-between items-start gap-4">
                                        <div className="flex-1">
                                          <div className="mb-2">
                                            <p className="text-sm font-medium text-white">{mat.material_name}</p>
                                            <p className="text-xs text-blue-400">{mat.layer_type}</p>
                                          </div>
                                          <div className="text-xs text-gray-400 space-y-1">
                                            <div className="grid grid-cols-2 gap-2">
                                              <div>
                                                <span className="text-gray-500">Width:</span> {mat.width_mm}mm
                                              </div>
                                              <div>
                                                <span className="text-gray-500">Thickness:</span> {mat.thickness_mm}mm
                                              </div>
                                              <div>
                                                <span className="text-gray-500">GSM:</span> {mat.gsm}
                                              </div>
                                              <div>
                                                <span className="text-gray-500">Layers:</span> {mat.num_layers}
                                              </div>
                                            </div>
                                            <div className="mt-2 text-xs">
                                              <div className="text-purple-400">
                                                Radius: {mat.stream_inner_radius_mm}mm → {mat.stream_outer_radius_mm}mm
                                              </div>
                                              <div className="text-blue-400">
                                                Density: {mat.density_kg_m3} kg/m³ | Volume: {mat.volume_m3_per_core} m³
                                              </div>
                                            </div>
                                            {mat.cost_per_meter > 0 && mat.total_meters_needed > 0 && (
                                              <div className="text-yellow-400 mt-1">
                                                ${mat.cost_per_meter}/m × {mat.total_meters_needed?.toLocaleString()}m = ${mat.total_cost?.toLocaleString()}
                                              </div>
                                            )}
                                          </div>
                                        </div>
                                        <div className="text-right">
                                          <div className="space-y-1">
                                            <div>
                                              <div className="text-lg font-bold text-yellow-400">
                                                {mat.total_meters_needed?.toLocaleString()}m
                                              </div>
                                              <div className="text-xs text-gray-400">
                                                ({mat.meters_per_core}m/core)
                                              </div>
                                            </div>
                                            <div>
                                              <div className="text-sm font-medium text-green-400">
                                                {mat.total_mass_kg?.toLocaleString()}kg
                                              </div>
                                              <div className="text-xs text-gray-400">
                                                ({mat.mass_kg_per_core}kg/core)
                                              </div>
                                            </div>
                                            {mat.total_cost > 0 && (
                                              <div className="text-lg font-bold text-green-400 mt-2">
                                                ${mat.total_cost?.toLocaleString()}
                                              </div>
                                            )}
                                          </div>
                                        </div>
                                      </div>
                                    </div>
                                  );
                                })}
                              </div>
                            </div>
                          )}
                          
                          {/* Customer Breakdown */}
                          {expandedCustomers[product.product_info.product_id] && (
                            <div className="mt-4 border-t border-gray-700 pt-4">
                              <h6 className="text-sm font-medium text-white mb-3">
                                Customer Breakdown for {selectedProjectionPeriod.replace('_', ' ')}
                              </h6>
                              {product.customer_projections && Object.keys(product.customer_projections).length > 0 ? (
                                <div className="space-y-2">
                                  {Object.entries(product.customer_projections).map(([customerName, customerData], custIndex) => {
                                    const projectedQty = customerData[selectedProjectionPeriod];
                                    
                                    return (
                                      <div key={custIndex} className="bg-gray-700/40 rounded p-3">
                                        <div className="flex justify-between items-start mb-2">
                                          <div className="flex-1">
                                            <p className="text-sm font-medium text-white">
                                              {customerName}
                                            </p>
                                            <p className="text-xs text-gray-400">
                                              Historical: {customerData.historical_total} units ({customerData.order_count} orders)
                                            </p>
                                          </div>
                                          <div className="text-right">
                                            <div className="text-lg font-bold text-yellow-400">
                                              {projectedQty} units
                                            </div>
                                            <div className="text-xs text-gray-400">
                                              Projected
                                            </div>
                                          </div>
                                        </div>
                                        
                                        {/* Projections for all periods */}
                                        <div className="mt-4 bg-gray-700/20 rounded p-3">
                                          <p className="text-xs font-medium text-gray-400 mb-2">All Projection Periods:</p>
                                          <div className="grid grid-cols-4 gap-2 text-xs">
                                            <div className="text-center">
                                              <div className="text-yellow-400 font-medium">{customerData['3_months']}</div>
                                              <div className="text-gray-500">3 months</div>
                                            </div>
                                            <div className="text-center">
                                              <div className="text-yellow-400 font-medium">{customerData['6_months']}</div>
                                              <div className="text-gray-500">6 months</div>
                                            </div>
                                            <div className="text-center">
                                              <div className="text-yellow-400 font-medium">{customerData['9_months']}</div>
                                              <div className="text-gray-500">9 months</div>
                                            </div>
                                            <div className="text-center">
                                              <div className="text-yellow-400 font-medium">{customerData['12_months']}</div>
                                              <div className="text-gray-500">12 months</div>
                                            </div>
                                          </div>
                                        </div>
                                      </div>
                                    );
                                  })}
                                </div>
                              ) : (
                                <p className="text-sm text-gray-400">No customer breakdown available</p>
                              )}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            )}
          </div>
        </ReportModal>

        <ReportModal
          isOpen={showOutstandingJobsModal}
          onClose={() => setShowOutstandingJobsModal(false)}
          title="Outstanding Jobs Report"
        >
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
        </ReportModal>

        <ReportModal
          isOpen={showLateDeliveriesModal}
          onClose={() => setShowLateDeliveriesModal(false)}
          title="Late Deliveries Report"
        >
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
        </ReportModal>

        <ReportModal
          isOpen={showCustomerReportModal}
          onClose={() => setShowCustomerReportModal(false)}
          title="Customer Annual Report"
        >
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
        </ReportModal>

        
        {/* Job Card Performance Report Modal */}
        <ReportModal
          isOpen={showJobPerformanceModal}
          onClose={() => setShowJobPerformanceModal(false)}
          title="Job Card Performance Report"
        >
          <div className="space-y-4">
            {/* Search Interface */}
            <div className="border border-gray-700 rounded-lg p-4 bg-gray-800/50">
              <h4 className="text-sm text-gray-300 mb-3">Search Job Cards</h4>
              <div className="grid grid-cols-5 gap-3">
                <select
                  className="misty-select"
                  value={jobCardSearchType}
                  onChange={(e) => setJobCardSearchType(e.target.value)}
                >
                  <option value="customer">Customer</option>
                  <option value="invoice">Invoice Number</option>
                  <option value="product">Product</option>
                </select>
                
                <input
                  type="text"
                  className="misty-input col-span-2"
                  placeholder={`Enter ${jobCardSearchType}...`}
                  value={jobCardSearchTerm}
                  onChange={(e) => setJobCardSearchTerm(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && jobCardSearchTerm.trim() && searchJobCards()}
                />
                
                <button
                  onClick={searchJobCards}
                  disabled={loadingJobCards || !jobCardSearchTerm.trim()}
                  className="misty-button misty-button-primary"
                >
                  {loadingJobCards ? 'Searching...' : 'Search'}
                </button>
                
                <button
                  onClick={searchAllJobCards}
                  disabled={loadingJobCards}
                  className="misty-button misty-button-secondary"
                >
                  {loadingJobCards ? 'Loading...' : 'Search All'}
                </button>
              </div>
            </div>

            {/* Search Results */}
            {jobCardResults.length > 0 && (
              <div className="space-y-3">
                <h4 className="text-sm text-gray-300">
                  Found {jobCardResults.length} order(s) with completed job cards
                </h4>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {jobCardResults.map((orderGroup) => (
                    <div
                      key={orderGroup.order_id}
                      onDoubleClick={() => viewOrderJobCards(orderGroup)}
                      className="border border-gray-700 rounded-lg p-4 cursor-pointer hover:bg-gray-700 transition-colors"
                    >
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <h3 className="text-white font-semibold">
                            {orderGroup.order_number} - {orderGroup.client_name}
                          </h3>
                          {orderGroup.invoice_number && (
                            <p className="text-sm text-yellow-400">
                              Invoice: {orderGroup.invoice_number}
                            </p>
                          )}
                        </div>
                        <span className="bg-green-900 text-green-200 px-3 py-1 rounded-full text-sm">
                          {orderGroup.job_cards.length} Job Card{orderGroup.job_cards.length !== 1 ? 's' : ''}
                        </span>
                      </div>
                      
                      <div className="text-sm text-gray-400">
                        <p className="mb-1">
                          <span className="font-medium">Stages Completed:</span>{' '}
                          {orderGroup.job_cards
                            .map(card => card.stage.replace(/_/g, ' ').toUpperCase())
                            .join(' → ')}
                        </p>
                        <p className="text-xs text-gray-500 mt-2">
                          Double-click to view and edit job cards
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Empty State */}
            {!loadingJobCards && jobCardResults.length === 0 && jobCardSearchTerm && (
              <div className="text-center py-8">
                <DocumentChartBarIcon className="mx-auto h-12 w-12 text-gray-600 mb-3" />
                <p className="text-gray-400">No job cards found for this search</p>
                <p className="text-sm text-gray-500 mt-1">Try a different search term</p>
              </div>
            )}

            {/* Instructions */}
            {!jobCardSearchTerm && (
              <div className="text-center py-8">
                <DocumentChartBarIcon className="mx-auto h-12 w-12 text-gray-600 mb-3" />
                <p className="text-gray-400">Search for job cards by customer, invoice number, or product</p>
                <p className="text-sm text-gray-500 mt-1">Results are grouped by order number</p>
              </div>
            )}
          </div>
        </ReportModal>

        {/* Job Cards Viewing/Editing Modal */}
        {showJobCardsModal && selectedOrderJobCards && (
          <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && setShowJobCardsModal(false)}>
            <div className="modal-content max-w-6xl max-h-[90vh] overflow-y-auto">
              <div className="p-6">
                {/* Header */}
                <div className="flex items-center justify-between mb-6 border-b border-gray-700 pb-4">
                  <div>
                    <h3 className="text-xl font-semibold text-white">
                      {selectedOrderJobCards.order_number} - Job Cards
                    </h3>
                    <p className="text-sm text-gray-400">
                      {selectedOrderJobCards.client_name}
                      {selectedOrderJobCards.invoice_number && (
                        <span className="ml-2 text-yellow-400">
                          • Invoice: {selectedOrderJobCards.invoice_number}
                        </span>
                      )}
                    </p>
                  </div>
                  <button
                    onClick={() => setShowJobCardsModal(false)}
                    className="text-gray-400 hover:text-white text-2xl"
                  >
                    ×
                  </button>
                </div>

                {/* Job Cards List */}
                <div className="space-y-4">
                  {selectedOrderJobCards.job_cards.map((card, index) => (
                    <div key={card.id} className="border border-gray-700 rounded-lg p-5 bg-gray-800/50">
                      {/* Card Header */}
                      <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-3">
                          <span className="bg-purple-900 text-purple-200 px-3 py-1 rounded-full text-sm font-medium">
                            Stage {index + 1}
                          </span>
                          <h4 className="text-lg font-semibold text-white">
                            {card.stage.replace(/_/g, ' ').toUpperCase()}
                          </h4>
                        </div>
                        <button
                          onClick={() => setEditingJobCard(card)}
                          className="misty-button misty-button-secondary text-sm"
                        >
                          Edit
                        </button>
                      </div>

                      {/* Card Details Grid */}
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div>
                          <p className="text-xs text-gray-400 mb-1">Machine</p>
                          <p className="text-white font-medium">{card.machine || 'N/A'}</p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-400 mb-1">Start Time</p>
                          <p className="text-white font-medium">
                            {card.job_start_time ? new Date(card.job_start_time).toLocaleString() : 'N/A'}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-400 mb-1">End Time</p>
                          <p className="text-white font-medium">
                            {card.job_end_time ? new Date(card.job_end_time).toLocaleString() : 'N/A'}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-400 mb-1">Runtime</p>
                          <p className="text-green-400 font-bold">
                            {Math.floor((card.actual_run_time_minutes || 0) / 60)}h{' '}
                            {(card.actual_run_time_minutes || 0) % 60}m
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-400 mb-1">Finished Quantity</p>
                          <p className="text-white font-medium">{card.finished_quantity || 0}</p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-400 mb-1">Master Cores</p>
                          <p className="text-white font-medium">{card.master_cores || 0}</p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-400 mb-1">Completed By</p>
                          <p className="text-white font-medium">{card.completed_by || 'Unknown'}</p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-400 mb-1">Completed At</p>
                          <p className="text-white font-medium">
                            {card.completed_at ? new Date(card.completed_at).toLocaleDateString() : 'N/A'}
                          </p>
                        </div>
                      </div>

                      {/* Setup Notes */}
                      {card.setup_notes && (
                        <div className="mt-4 pt-4 border-t border-gray-700">
                          <p className="text-xs text-gray-400 mb-2">Setup Notes:</p>
                          <p className="text-sm text-gray-300">{card.setup_notes}</p>
                        </div>
                      )}

                      {/* Additional Production */}
                      {card.additional_production && card.additional_production.length > 0 && (
                        <div className="mt-4 pt-4 border-t border-gray-700">
                          <p className="text-xs text-gray-400 mb-2">Additional Production:</p>
                          <div className="space-y-1">
                            {card.additional_production.map((prod, idx) => (
                              <p key={idx} className="text-sm text-gray-300">
                                • {prod.description}: {prod.quantity}
                              </p>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>

                {/* Footer */}
                <div className="flex justify-end mt-6 pt-4 border-t border-gray-700">
                  <button
                    onClick={() => setShowJobCardsModal(false)}
                    className="misty-button misty-button-secondary"
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Edit Job Card Modal */}
        {editingJobCard && (
          <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && setEditingJobCard(null)}>
            <div className="modal-content max-w-2xl">
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-white">
                    Edit Job Card - {editingJobCard.stage.replace(/_/g, ' ').toUpperCase()}
                  </h3>
                  <button
                    onClick={() => setEditingJobCard(null)}
                    className="text-gray-400 hover:text-white text-2xl"
                  >
                    ×
                  </button>
                </div>

                <form onSubmit={(e) => {
                  e.preventDefault();
                  const formData = new FormData(e.target);
                  const updates = {
                    machine: formData.get('machine'),
                    setup_notes: formData.get('setup_notes'),
                    finished_quantity: parseInt(formData.get('finished_quantity')),
                    master_cores: parseInt(formData.get('master_cores'))
                  };
                  updateJobCard(editingJobCard.id, updates);
                  setEditingJobCard(null);
                }}>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm text-gray-400 mb-1">Machine</label>
                      <input
                        type="text"
                        name="machine"
                        className="misty-input"
                        defaultValue={editingJobCard.machine}
                      />
                    </div>
                    <div>
                      <label className="block text-sm text-gray-400 mb-1">Finished Quantity</label>
                      <input
                        type="number"
                        name="finished_quantity"
                        className="misty-input"
                        defaultValue={editingJobCard.finished_quantity}
                      />
                    </div>
                    <div>
                      <label className="block text-sm text-gray-400 mb-1">Master Cores</label>
                      <input
                        type="number"
                        name="master_cores"
                        className="misty-input"
                        defaultValue={editingJobCard.master_cores}
                      />
                    </div>
                    <div>
                      <label className="block text-sm text-gray-400 mb-1">Setup Notes</label>
                      <textarea
                        name="setup_notes"
                        rows="3"
                        className="misty-input"
                        defaultValue={editingJobCard.setup_notes}
                      />
                    </div>
                  </div>

                  <div className="flex justify-end gap-3 mt-6">
                    <button
                      type="button"
                      onClick={() => setEditingJobCard(null)}
                      className="misty-button misty-button-secondary"
                    >
                      Cancel
                    </button>
                    <button type="submit" className="misty-button misty-button-primary">
                      Save Changes
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        )}

        {/* Profitability Report Modal */}
        <ReportModal
          isOpen={showProfitabilityModal}
          onClose={() => setShowProfitabilityModal(false)}
          title="Profitability Report - GP & NP Analysis"
        >
          <div className="space-y-6">
            {/* Mode Selection */}
            <div>
              <label className="block text-sm text-gray-400 mb-2">Analysis Mode</label>
              <div className="flex gap-4">
                <label className="flex items-center">
                  <input
                    type="radio"
                    value="all"
                    checked={profitabilityMode === 'all'}
                    onChange={(e) => setProfitabilityMode(e.target.value)}
                    className="mr-2"
                  />
                  <span className="text-white">All Jobs (All Clients)</span>
                </label>
                <label className="flex items-center">
                  <input
                    type="radio"
                    value="filtered"
                    checked={profitabilityMode === 'filtered'}
                    onChange={(e) => setProfitabilityMode(e.target.value)}
                    className="mr-2"
                  />
                  <span className="text-white">Filtered (Select Clients & Products)</span>
                </label>
              </div>
            </div>

            {/* All Jobs Mode - Simple Date Range */}
            {profitabilityMode === 'all' && (
              <div className="bg-blue-900 bg-opacity-20 border border-blue-500 border-opacity-30 rounded-lg p-4">
                <p className="text-blue-300 text-sm mb-3">
                  📊 This will analyze ALL completed/archived jobs from ALL clients
                </p>
                <div>
                  <label className="block text-sm text-gray-400 mb-2">Date Range (Optional)</label>
                  <select
                    className="misty-select w-full"
                    value={profitabilityDatePreset}
                    onChange={(e) => {
                      const preset = e.target.value;
                      setProfitabilityDatePreset(preset);
                      if (preset !== 'all_time') {
                        const { start, end } = getDateRangeFromPreset(preset);
                        setProfitabilityStartDate(start);
                        setProfitabilityEndDate(end);
                      }
                    }}
                  >
                    <option value="last_7_days">Last 7 Days</option>
                    <option value="last_30_days">Last 30 Days</option>
                    <option value="last_90_days">Last 90 Days</option>
                    <option value="this_year">This Year</option>
                    <option value="all_time">All Time</option>
                  </select>
                </div>
              </div>
            )}

            {/* Filtered Mode - Multiple Clients & Products */}
            {profitabilityMode === 'filtered' && (
              <div className="space-y-4">
                <div className="bg-yellow-900 bg-opacity-20 border border-yellow-500 border-opacity-30 rounded-lg p-4">
                  <p className="text-yellow-300 text-sm">
                    🔍 Select specific clients and/or products to analyze
                  </p>
                </div>

                {/* Multiple Clients Selection */}
                <div>
                  <label className="block text-sm text-gray-400 mb-2">
                    Select Clients (Hold Ctrl/Cmd for multiple)
                  </label>
                  {clients.length > 0 && (
                    <div className="text-gray-400 text-xs mb-2">
                      {clients.length} client(s) available | {selectedProfitClients.length} selected
                    </div>
                  )}
                  <select
                    multiple
                    className="misty-select w-full h-32"
                    value={selectedProfitClients}
                    onChange={(e) => {
                      const selected = Array.from(e.target.selectedOptions, option => option.value);
                      setSelectedProfitClients(selected);
                    }}
                  >
                    {clients.map(client => (
                      <option key={client.id} value={client.id}>
                        {client.name}
                      </option>
                    ))}
                  </select>
                  <p className="text-xs text-gray-500 mt-1">
                    Leave empty to include all clients
                  </p>
                </div>

                {/* Multiple Products Selection */}
                <div>
                  <label className="block text-sm text-gray-400 mb-2">
                    Select Products (Hold Ctrl/Cmd for multiple)
                  </label>
                  {clientProducts.length > 0 && (
                    <div className="text-gray-400 text-xs mb-2">
                      {clientProducts.length} product(s) available | {selectedProfitProducts.length} selected
                    </div>
                  )}
                  <select
                    multiple
                    className="misty-select w-full h-32"
                    value={selectedProfitProducts}
                    onChange={(e) => {
                      const selected = Array.from(e.target.selectedOptions, option => option.value);
                      setSelectedProfitProducts(selected);
                    }}
                  >
                    {clientProducts.map(product => (
                      <option key={product.id} value={product.id}>
                        {product.product_name} ({product.client_name})
                      </option>
                    ))}
                  </select>
                  <p className="text-xs text-gray-500 mt-1">
                    Leave empty to include all products
                  </p>
                </div>

                {/* Date Range for Filtered Mode */}
                <div>
                  <label className="block text-sm text-gray-400 mb-2">Date Range</label>
                  <select
                    className="misty-select w-full"
                    value={profitabilityDatePreset}
                    onChange={(e) => {
                      const preset = e.target.value;
                      setProfitabilityDatePreset(preset);
                      if (preset !== 'all_time') {
                        const { start, end } = getDateRangeFromPreset(preset);
                        setProfitabilityStartDate(start);
                        setProfitabilityEndDate(end);
                      }
                    }}
                  >
                    <option value="last_7_days">Last 7 Days</option>
                    <option value="last_30_days">Last 30 Days</option>
                    <option value="last_90_days">Last 90 Days</option>
                    <option value="this_year">This Year</option>
                    <option value="all_time">All Time</option>
                  </select>
                </div>
              </div>
            )}

            {/* Profit Threshold */}
            <div>
              <label className="block text-sm text-gray-400 mb-2">
                Profit Warning Threshold (%)
              </label>
              <input
                type="number"
                step="1"
                value={profitThreshold}
                onChange={(e) => setProfitThreshold(parseFloat(e.target.value))}
                className="misty-input w-full md:w-64"
                placeholder="e.g., 10"
              />
              <p className="text-xs text-gray-500 mt-1">
                Jobs below this Net Profit % will be highlighted in red
              </p>
            </div>

            {/* Generate Button */}
            <button
              onClick={loadProfitabilityReport}
              disabled={loadingProfitability}
              className="misty-button misty-button-primary w-full md:w-auto"
            >
              {loadingProfitability ? 'Generating...' : '📊 Generate Profitability Report'}
            </button>

            {/* Results */}
            {profitabilityReport && (
              <div className="space-y-6 mt-6">
                {/* Summary Cards */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-gray-700 rounded-lg p-4">
                    <p className="text-sm text-gray-400">Total Jobs</p>
                    <p className="text-2xl font-bold text-white">{profitabilityReport.summary.total_jobs}</p>
                  </div>
                  <div className="bg-gray-700 rounded-lg p-4">
                    <p className="text-sm text-gray-400">Total Revenue</p>
                    <p className="text-2xl font-bold text-green-400">
                      ${profitabilityReport.summary.total_revenue.toLocaleString()}
                    </p>
                  </div>
                  <div className="bg-gray-700 rounded-lg p-4">
                    <p className="text-sm text-gray-400">Avg GP %</p>
                    <p className="text-2xl font-bold text-blue-400">
                      {profitabilityReport.summary.average_gp_percentage.toFixed(1)}%
                    </p>
                  </div>
                  <div className="bg-gray-700 rounded-lg p-4">
                    <p className="text-sm text-gray-400">Avg NP %</p>
                    <p className="text-2xl font-bold text-yellow-400">
                      {profitabilityReport.summary.average_np_percentage.toFixed(1)}%
                    </p>
                  </div>
                </div>

                {profitabilityReport.summary.jobs_below_threshold > 0 && (
                  <div className="bg-red-900 bg-opacity-30 border border-red-500 rounded-lg p-4">
                    <p className="text-red-400 font-medium">
                      ⚠️ Alert: {profitabilityReport.summary.jobs_below_threshold} job(s) below profit threshold!
                    </p>
                  </div>
                )}

                {/* Detailed Table */}
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-700">
                      <tr>
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-300 uppercase">Job</th>
                        <th className="px-3 py-2 text-right text-xs font-medium text-gray-300 uppercase">Revenue</th>
                        <th className="px-3 py-2 text-right text-xs font-medium text-gray-300 uppercase">Material</th>
                        <th className="px-3 py-2 text-right text-xs font-medium text-gray-300 uppercase">Labour</th>
                        <th className="px-3 py-2 text-right text-xs font-medium text-gray-300 uppercase">Machine</th>
                        <th className="px-3 py-2 text-right text-xs font-medium text-gray-300 uppercase">GP</th>
                        <th className="px-3 py-2 text-right text-xs font-medium text-gray-300 uppercase">GP %</th>
                        <th className="px-3 py-2 text-right text-xs font-medium text-gray-300 uppercase">NP</th>
                        <th className="px-3 py-2 text-right text-xs font-medium text-gray-300 uppercase">NP %</th>
                      </tr>
                    </thead>
                    <tbody className="bg-gray-800 divide-y divide-gray-700">
                      {profitabilityReport.profitability_data.map((job, index) => (
                        <tr key={index} className={job.alert_low_profit ? 'bg-red-900 bg-opacity-20' : ''}>
                          <td className="px-3 py-3 text-sm">
                            <div className="text-white font-medium">{job.order_number}</div>
                            <div className="text-gray-400 text-xs">{job.client_name}</div>
                          </td>
                          <td className="px-3 py-3 text-sm text-right text-white">
                            ${job.job_revenue.toLocaleString()}
                          </td>
                          <td className="px-3 py-3 text-sm text-right text-gray-300">
                            ${job.material_cost.toLocaleString()}
                          </td>
                          <td className="px-3 py-3 text-sm text-right text-gray-300">
                            ${job.labour_cost.toLocaleString()}
                          </td>
                          <td className="px-3 py-3 text-sm text-right text-gray-300">
                            ${job.machine_cost.toLocaleString()}
                          </td>
                          <td className="px-3 py-3 text-sm text-right font-medium text-blue-400">
                            ${job.gross_profit.toLocaleString()}
                          </td>
                          <td className="px-3 py-3 text-sm text-right font-medium text-blue-400">
                            {job.gp_percentage.toFixed(1)}%
                          </td>
                          <td className={`px-3 py-3 text-sm text-right font-medium ${job.alert_low_profit ? 'text-red-400' : 'text-green-400'}`}>
                            ${job.net_profit.toLocaleString()}
                          </td>
                          <td className={`px-3 py-3 text-sm text-right font-medium ${job.alert_low_profit ? 'text-red-400' : 'text-green-400'}`}>
                            {job.np_percentage.toFixed(1)}%
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        </ReportModal>

      </div>
    </Layout>
  );
};

export default Reports;
