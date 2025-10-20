import React, { useState, useEffect } from 'react';
import Layout from './Layout';
import { apiHelpers } from '../utils/api';
import { toast } from 'sonner';
import { 
  DocumentArrowDownIcon,
  EyeIcon,
  CalendarDaysIcon,
  CurrencyDollarIcon,
  ClipboardDocumentListIcon,
  MagnifyingGlassIcon,
  CubeIcon,
  BanknotesIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';

const Invoicing = () => {
  const [activeTab, setActiveTab] = useState('live-jobs');
  const [liveJobs, setLiveJobs] = useState([]);
  const [archivedJobs, setArchivedJobs] = useState([]);
  const [accountingTransactions, setAccountingTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedJob, setSelectedJob] = useState(null);
  const [showInvoiceModal, setShowInvoiceModal] = useState(false);
  const [showPartSupplyModal, setShowPartSupplyModal] = useState(false);
  const [invoiceType, setInvoiceType] = useState('full');
  const [partialItems, setPartialItems] = useState([]);
  const [reportMonth, setReportMonth] = useState(new Date().getMonth() + 1);
  const [reportYear, setReportYear] = useState(new Date().getFullYear());
  const [xeroConnected, setXeroConnected] = useState(false);
  const [checkingXeroStatus, setCheckingXeroStatus] = useState(false);

  useEffect(() => {
    loadData();
    checkXeroConnectionStatus();
  }, [activeTab]);

  const checkXeroConnectionStatus = async () => {
    try {
      setCheckingXeroStatus(true);
      const response = await apiHelpers.checkXeroConnection();
      setXeroConnected(response.data.connected);
    } catch (error) {
      console.error('Failed to check Xero status:', error);
      setXeroConnected(false);
    } finally {
      setCheckingXeroStatus(false);
    }
  };

  const handleXeroConnect = async () => {
    try {
      const response = await apiHelpers.getXeroAuthUrl();
      const { auth_url } = response.data;
      
      // Open Xero OAuth in a new window
      const authWindow = window.open(
        auth_url,
        'xero-auth',
        'width=600,height=700,scrollbars=yes,resizable=yes'
      );

      // Listen for messages from the popup
      const messageHandler = async (event) => {
        if (event.data.type === 'xero-auth-success') {
          window.removeEventListener('message', messageHandler);
          
          try {
            // Handle the callback with the parent window's authentication
            const callbackResponse = await apiHelpers.handleXeroCallback({
              code: event.data.code,
              state: event.data.state
            });
            
            setXeroConnected(true);
            toast.success('Successfully connected to Xero!');
            checkXeroConnectionStatus(); // Refresh status
          } catch (error) {
            console.error('Failed to complete Xero connection:', error);
            toast.error(`Failed to complete Xero connection: ${error.message}`);
          }
        } else if (event.data.type === 'xero-auth-error') {
          window.removeEventListener('message', messageHandler);
          toast.error(`Xero connection failed: ${event.data.error}`);
        }
      };

      window.addEventListener('message', messageHandler);

      // Also listen for the OAuth callback (fallback)
      const checkClosed = setInterval(() => {
        if (authWindow.closed) {
          clearInterval(checkClosed);
          window.removeEventListener('message', messageHandler);
          // Check connection status after auth window closes
          setTimeout(() => {
            checkXeroConnectionStatus();
          }, 1000);
        }
      }, 1000);

    } catch (error) {
      console.error('Failed to initiate Xero connection:', error);
      toast.error('Failed to connect to Xero');
    }
  };

  const handleXeroDisconnect = async () => {
    try {
      await apiHelpers.disconnectXero();
      setXeroConnected(false);
      toast.success('Disconnected from Xero');
    } catch (error) {
      console.error('Failed to disconnect from Xero:', error);
      toast.error('Failed to disconnect from Xero');
    }
  };

  const loadData = async () => {
    setLoading(true);
    try {
      if (activeTab === 'live-jobs') {
        const response = await apiHelpers.getLiveJobs();
        setLiveJobs(response.data.data || []);
      } else if (activeTab === 'accounting-transactions') {
        const response = await apiHelpers.getAccountingTransactions();
        setAccountingTransactions(response.data.data || []);
      } else if (activeTab === 'archived') {
        const response = await apiHelpers.getArchivedJobs(reportMonth, reportYear);
        setArchivedJobs(response.data.data || []);
      }
    } catch (error) {
      console.error('Failed to load data:', error);
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const handleInvoiceJob = (job) => {
    setSelectedJob(job);
    // Initialize partial items with zero quantities
    if (job.items && Array.isArray(job.items)) {
      const initialPartialItems = job.items.map(item => ({
        ...item,
        invoice_quantity: 0,
        original_quantity: item.quantity || 0
      }));
      setPartialItems(initialPartialItems);
    }
    setShowInvoiceModal(true);
  };

  const handlePartSupplyNext = () => {
    setShowInvoiceModal(false);
    setShowPartSupplyModal(true);
  };

  const updatePartialItemQuantity = (index, quantity) => {
    const newPartialItems = [...partialItems];
    newPartialItems[index].invoice_quantity = Math.min(
      Math.max(0, quantity), 
      newPartialItems[index].original_quantity
    );
    setPartialItems(newPartialItems);
  };

  const generateInvoice = async () => {
    if (!selectedJob) return;

    try {
      let invoiceData;
      
      if (invoiceType === 'partial') {
        // Validate at least one item selected
        const selectedItems = partialItems.filter(item => item.invoice_quantity > 0);
        if (selectedItems.length === 0) {
          toast.error('Please select at least one item to invoice');
          return;
        }
        
        // Calculate subtotal for selected items
        const subtotal = selectedItems.reduce((sum, item) => {
          return sum + (item.unit_price * item.invoice_quantity);
        }, 0);
        const gst = subtotal * 0.1; // 10% GST
        const total_amount = subtotal + gst;
        
        invoiceData = {
          invoice_type: invoiceType,
          items: selectedItems.map(item => ({
            ...item,
            quantity: item.invoice_quantity // Use invoice quantity
          })),
          subtotal: subtotal,
          gst: gst,
          total_amount: total_amount,
          due_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
        };
      } else {
        // Full invoice
        invoiceData = {
          invoice_type: invoiceType,
          items: selectedJob.items,
          subtotal: selectedJob.subtotal,
          gst: selectedJob.gst,
          total_amount: selectedJob.total_amount,
          due_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
        };
      }

      const response = await apiHelpers.generateJobInvoice(selectedJob.id, invoiceData);
      
      // Show success message with Xero integration info
      toast.success(
        <div>
          <p>📄 Invoice {response.data.invoice_number} generated successfully!</p>
          <p className="text-sm text-gray-300">Job moved to Accounting Transactions tab</p>
          {xeroConnected && (
            <p className="text-sm text-green-300">✅ Xero draft created automatically</p>
          )}
          <div className="mt-2 space-x-2">
            <button 
              onClick={() => downloadInvoice(selectedJob.id, selectedJob.order_number)}
              className="bg-yellow-600 hover:bg-yellow-700 px-3 py-1 rounded text-xs text-white"
            >
              📄 Invoice PDF
            </button>
            <button 
              onClick={() => downloadPackingSlip(selectedJob.id, selectedJob.order_number)}
              className="bg-green-600 hover:bg-green-700 px-3 py-1 rounded text-xs text-white"
            >
              📦 Packing Slip
            </button>
          </div>
        </div>,
        { duration: 8000 }
      );
      
      setShowInvoiceModal(false);
      setShowPartSupplyModal(false);
      setSelectedJob(null);
      loadData(); // Refresh data
    } catch (error) {
      console.error('Failed to generate invoice:', error);
      toast.error('Failed to generate invoice');
    }
  };

  const completeAccountingTransaction = async (job) => {
    try {
      await apiHelpers.completeAccountingTransaction(job.id);
      toast.success(`Job ${job.order_number} completed and archived successfully`);
      loadData(); // Refresh data
    } catch (error) {
      console.error('Failed to complete accounting transaction:', error);
      toast.error('Failed to complete transaction');
    }
  };

  const exportDraftedInvoicesToCSV = async () => {
    try {
      // Try server-side CSV export first
      try {
        const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/invoicing/export-drafted-csv`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json'
          }
        });
        
        if (response.ok) {
          const blob = await response.blob();
          const url = window.URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = url;
          
          const today = new Date();
          const dateStr = today.toISOString().split('T')[0];
          link.download = `drafted_invoices_${dateStr}.csv`;
          
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          window.URL.revokeObjectURL(url);
          
          toast.success('Drafted invoices exported successfully!');
          return;
        }
      } catch (serverError) {
        console.log('Server-side export failed, falling back to client-side:', serverError);
      }
      
      // Fallback to client-side generation
      if (accountingTransactions.length === 0) {
        toast.info('No drafted invoices to export. Switch to "Accounting Transactions" tab first to load data.');
        return;
      }
      
      // Generate CSV content client-side using loaded data
      const csvContent = generateCSVContent(accountingTransactions);
      
      // Create blob and download
      const blob = new Blob([csvContent], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      
      // Generate filename with current date
      const today = new Date();
      const dateStr = today.toISOString().split('T')[0];
      link.download = `drafted_invoices_${dateStr}.csv`;
      
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      toast.success(`Drafted invoices exported successfully! (${accountingTransactions.length} transactions)`);
    } catch (error) {
      console.error('Failed to export CSV:', error);
      toast.error('Failed to export drafted invoices: ' + error.message);
    }
  };

  const generateCSVContent = (transactions) => {
    // CSV Headers based on Xero import format
    const headers = [
      "ContactName", "EmailAddress", "POAddressLine1", "POAddressLine2", 
      "POAddressLine3", "POAddressLine4", "POCity", "PORegion", 
      "POPostalCode", "POCountry", "InvoiceNumber", "Reference", 
      "InvoiceDate", "DueDate", "InventoryItemCode", "Description", 
      "Quantity", "UnitAmount", "Discount", "AccountCode", "TaxType", 
      "TrackingName1", "TrackingOption1", "TrackingName2", "TrackingOption2", 
      "Currency", "BrandingTheme"
    ];
    
    const csvRows = [];
    csvRows.push(headers.join(','));
    
    // Process each transaction
    transactions.forEach(transaction => {
      const client_name = transaction.client_name || 'Unknown Client';
      const client_email = transaction.client_email || '';
      const invoice_number = transaction.invoice_number || `INV-${transaction.order_number}`;
      
      // Format dates (DD/MM/YYYY)
      const invoice_date = transaction.invoice_date 
        ? new Date(transaction.invoice_date).toLocaleDateString('en-AU')
        : new Date().toLocaleDateString('en-AU');
      
      const due_date_obj = transaction.invoice_date 
        ? new Date(new Date(transaction.invoice_date).getTime() + 30 * 24 * 60 * 60 * 1000)
        : new Date(Date.now() + 30 * 24 * 60 * 60 * 1000);
      const due_date = due_date_obj.toLocaleDateString('en-AU');
      
      // Process items
      const items = transaction.items || [];
      if (items.length === 0) {
        // Create single line if no items
        items.push({
          description: `Services for Order ${transaction.order_number}`,
          quantity: 1,
          unit_price: transaction.total_amount || 0
        });
      }
      
      items.forEach(item => {
        const description = `${item.product_name || item.description || 'Product'} - ${item.specifications || ''}`.replace(' - ', ' ').trim();
        
        const row = [
          `"${client_name}"`, // ContactName
          `"${client_email}"`, // EmailAddress
          '""', '""', '""', '""', '""', '""', '""', '""', // Address fields
          `"${invoice_number}"`, // InvoiceNumber
          `"${transaction.order_number}"`, // Reference
          `"${invoice_date}"`, // InvoiceDate
          `"${due_date}"`, // DueDate
          `"${item.product_code || ''}"`, // InventoryItemCode
          `"${description}"`, // Description
          `"${item.quantity || 1}"`, // Quantity
          `"${item.unit_price || item.price || 0}"`, // UnitAmount
          `"${item.discount_percent || ''}"`, // Discount
          '"200"', // AccountCode
          '"OUTPUT"', // TaxType
          '""', '""', '""', '""', // Tracking fields
          '"AUD"', // Currency
          '""' // BrandingTheme
        ];
        
        csvRows.push(row.join(','));
      });
    });
    
    return csvRows.join('\n');
  };

  const downloadInvoice = async (jobId, orderNumber) => {
    try {
      // Use fetch instead of axios for blob handling
      const token = localStorage.getItem('token');
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/documents/invoice/${jobId}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const blob = await response.blob();
      console.log('Invoice blob size:', blob.size, 'type:', blob.type);
      
      if (blob.size === 0) {
        throw new Error('Received empty PDF');
      }

      const url = window.URL.createObjectURL(blob);
      
      // Try download first
      const link = document.createElement('a');
      link.href = url;
      link.download = `invoice_${orderNumber}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      // Also open in new tab as backup
      setTimeout(() => {
        window.open(url, '_blank');
        window.URL.revokeObjectURL(url);
        toast.success(`📄 Invoice ${orderNumber} ready for download`);
      }, 500);
      
    } catch (error) {
      console.error('Failed to download invoice:', error);
      toast.error(`Failed to download invoice: ${error.message}`);
    }
  };

  const downloadPackingSlip = async (jobId, orderNumber) => {
    try {
      // Use fetch instead of axios for blob handling
      const token = localStorage.getItem('token');
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/documents/packing-list/${jobId}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const blob = await response.blob();
      console.log('Packing slip blob size:', blob.size, 'type:', blob.type);
      
      if (blob.size === 0) {
        throw new Error('Received empty PDF');
      }

      const url = window.URL.createObjectURL(blob);
      
      // Try download first
      const link = document.createElement('a');
      link.href = url;
      link.download = `packing_slip_${orderNumber}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      // Also open in new tab as backup
      setTimeout(() => {
        window.open(url, '_blank');
        window.URL.revokeObjectURL(url);
        toast.success(`📦 Packing Slip ${orderNumber} ready for download`);
      }, 500);
      
    } catch (error) {
      console.error('Failed to download packing slip:', error);
      toast.error(`Failed to download packing slip: ${error.message}`);
    }
  };

  const filteredLiveJobs = liveJobs.filter(job => 
    job.order_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    job.client_name?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const filteredArchivedJobs = archivedJobs.filter(job => 
    job.order_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    job.client_name?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-AU', {
      style: 'currency',
      currency: 'AUD',
    }).format(amount);
  };

  const formatDate = (date) => {
    return new Intl.DateTimeFormat('en-AU').format(new Date(date));
  };

  const testPdfDownload = async () => {
    try {
      // First try: Direct browser navigation (forces download)
      const downloadUrl = `${process.env.REACT_APP_BACKEND_URL}/api/debug/test-pdf`;
      
      // Create a temporary iframe for download
      const iframe = document.createElement('iframe');
      iframe.style.display = 'none';
      iframe.src = downloadUrl;
      document.body.appendChild(iframe);
      
      // Also try the blob method
      const response = await fetch(downloadUrl);
      if (response.ok) {
        const blob = await response.blob();
        
        // Multiple download attempts
        const url = URL.createObjectURL(blob);
        
        // Method 1: Hidden link click
        const a = document.createElement('a');
        a.href = url;
        a.download = 'test.pdf';
        a.style.display = 'none';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        
        // Method 2: Force navigation
        setTimeout(() => {
          window.location.href = url;
        }, 500);
        
        // Cleanup
        setTimeout(() => {
          document.body.removeChild(iframe);
          URL.revokeObjectURL(url);
        }, 2000);
        
        toast.success('PDF download initiated - check Downloads folder or adjust Chrome settings if needed');
      }
    } catch (error) {
      console.error('Download failed:', error);
      toast.error(`Download failed: ${error.message}`);
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="p-8">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-700 rounded w-1/4 mb-8"></div>
            <div className="space-y-4">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="h-16 bg-gray-700 rounded"></div>
              ))}
            </div>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="p-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Invoicing & Job Closure</h1>
            <p className="text-gray-400">Generate invoices and manage completed jobs</p>
          </div>
          <div className="flex items-center space-x-4">
            {/* Xero Connection Status */}
            <div className="flex items-center space-x-3">
              <div className="flex items-center space-x-2">
                <div className={`h-3 w-3 rounded-full ${xeroConnected ? 'bg-green-400' : 'bg-red-400'}`}></div>
                <span className="text-sm text-gray-300">
                  Xero {xeroConnected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
              
              {xeroConnected ? (
                <button
                  onClick={handleXeroDisconnect}
                  className="misty-button misty-button-danger text-xs px-3 py-1"
                >
                  Disconnect Xero
                </button>
              ) : (
                <button
                  onClick={handleXeroConnect}
                  disabled={checkingXeroStatus}
                  className="misty-button misty-button-primary text-xs px-3 py-1"
                >
                  {checkingXeroStatus ? 'Connecting...' : 'Connect to Xero'}
                </button>
              )}
              
              {/* Export CSV Button */}
              <button
                onClick={exportDraftedInvoicesToCSV}
                className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg text-sm transition-colors flex items-center space-x-2"
                title={accountingTransactions.length === 0 ? "Switch to 'Accounting Transactions' tab first to load data" : "Export drafted invoices to CSV"}
              >
                <DocumentArrowDownIcon className="h-4 w-4" />
                <span>Export Drafts .CSV</span>
                {accountingTransactions.length > 0 && (
                  <span className="bg-green-800 text-xs px-2 py-1 rounded-full">
                    {accountingTransactions.length}
                  </span>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="mb-6">
          <div className="border-b border-gray-700">
            <nav className="-mb-px flex space-x-8">
              {[
                { key: 'live-jobs', label: 'Live Jobs', icon: ClipboardDocumentListIcon },
                { key: 'accounting-transactions', label: 'Accounting Transactions', icon: BanknotesIcon },
                { key: 'archived', label: 'Archived Jobs', icon: DocumentArrowDownIcon },
                { key: 'reports', label: 'Monthly Reports', icon: CalendarDaysIcon }
              ].map((tab) => (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key)}
                  className={`
                    flex items-center py-2 px-1 border-b-2 font-medium text-sm transition-colors
                    ${activeTab === tab.key
                      ? 'border-yellow-400 text-yellow-400'
                      : 'border-transparent text-gray-400 hover:text-gray-300 hover:border-gray-300'
                    }
                  `}
                >
                  <tab.icon className="h-5 w-5 mr-2" />
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* Search */}
        {activeTab !== 'reports' && (
          <div className="mb-6">
            <div className="relative">
              <MagnifyingGlassIcon className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search jobs..."
                className="misty-input pl-12 w-full max-w-md"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
          </div>
        )}

        {/* Live Jobs Tab */}
        {activeTab === 'live-jobs' && (
          <div>
            <h2 className="text-xl font-semibold text-white mb-4">Jobs Ready for Invoicing</h2>
            
            {filteredLiveJobs.length > 0 ? (
              <div className="misty-table">
                <table className="w-full">
                  <thead>
                    <tr>
                      <th>Order #</th>
                      <th>Client</th>
                      <th>Amount</th>
                      <th>Due Date</th>
                      <th>Payment Terms</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredLiveJobs.map((job) => (
                      <tr key={job.id}>
                        <td className="font-medium">{job.order_number}</td>
                        <td>{job.client_name}</td>
                        <td className="font-medium text-yellow-400">
                          {formatCurrency(job.total_amount)}
                        </td>
                        <td>{formatDate(job.due_date)}</td>
                        <td className="text-sm text-gray-300">
                          {job.client_payment_terms || 'Net 30 days'}
                        </td>
                        <td>
                          <div className="flex items-center space-x-2">
                            <button
                              onClick={() => handleInvoiceJob(job)}
                              className="misty-button misty-button-primary text-xs px-3 py-1"
                              title="Generate Invoice"
                            >
                              <CurrencyDollarIcon className="h-4 w-4 mr-1" />
                              Invoice
                            </button>
                            <a
                              href={`${process.env.REACT_APP_BACKEND_URL}/api/documents/invoice/${job.id}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-gray-400 hover:text-yellow-400 transition-colors"
                              title="Download Invoice PDF (right-click to save)"
                              onClick={() => toast.success('Invoice PDF opened - right-click to save if needed')}
                            >
                              <DocumentArrowDownIcon className="h-4 w-4" />
                            </a>
                            <a
                              href={`${process.env.REACT_APP_BACKEND_URL}/api/documents/packing-list/${job.id}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-gray-400 hover:text-green-400 transition-colors"
                              title="Download Packing Slip PDF (right-click to save)"
                              onClick={() => toast.success('Packing Slip PDF opened - right-click to save if needed')}
                            >
                              <CubeIcon className="h-4 w-4" />
                            </a>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-12">
                <ClipboardDocumentListIcon className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-300">No jobs ready for invoicing</h3>
                <p className="mt-1 text-sm text-gray-400">
                  Jobs will appear here when they reach the delivery stage.
                </p>
              </div>
            )}
          </div>
        )}

        {/* Accounting Transactions Tab */}
        {activeTab === 'accounting-transactions' && (
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-white">Accounting Transactions</h2>
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search transactions..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="misty-input w-64"
                  />
                </div>
              </div>
            </div>

            {accountingTransactions.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-700">
                  <thead className="bg-gray-800">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                        Order
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                        Client
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                        Total Amount
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                        Invoice Date
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-gray-900 divide-y divide-gray-700">
                    {accountingTransactions
                      .filter(job => 
                        job.client_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                        job.order_number?.toLowerCase().includes(searchTerm.toLowerCase())
                      )
                      .map((job) => (
                      <tr key={job.id} className="hover:bg-gray-800">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-white">{job.order_number}</div>
                          <div className="text-sm text-gray-400">ID: {job.id}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-white">{job.client_name}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-yellow-100 text-yellow-800">
                            Status: Draft
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-white">
                          ${job.total_amount?.toFixed(2)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                          {job.invoice_date ? new Date(job.invoice_date).toLocaleDateString('en-AU') : 'Not set'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <button
                            onClick={() => completeAccountingTransaction(job)}
                            className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg text-sm transition-colors flex items-center space-x-2"
                          >
                            <CheckCircleIcon className="h-4 w-4" />
                            <span>Completed</span>
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-12">
                <BanknotesIcon className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-300">No accounting transactions</h3>
                <p className="mt-1 text-sm text-gray-400">
                  Invoiced jobs will appear here for final processing.
                </p>
              </div>
            )}
          </div>
        )}

        {/* Archived Jobs Tab */}
        {activeTab === 'archived' && (
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-white">Archived Jobs</h2>
              
              <div className="flex items-center space-x-4">
                <select
                  value={reportMonth}
                  onChange={(e) => setReportMonth(parseInt(e.target.value))}
                  className="misty-select"
                >
                  {[...Array(12)].map((_, i) => (
                    <option key={i} value={i + 1}>
                      {new Date(2024, i).toLocaleString('en-AU', { month: 'long' })}
                    </option>
                  ))}
                </select>
                <select
                  value={reportYear}
                  onChange={(e) => setReportYear(parseInt(e.target.value))}
                  className="misty-select"
                >
                  {[2023, 2024, 2025].map(year => (
                    <option key={year} value={year}>{year}</option>
                  ))}
                </select>
                <button
                  onClick={loadData}
                  className="misty-button misty-button-secondary"
                >
                  Filter
                </button>
              </div>
            </div>

            {filteredArchivedJobs.length > 0 ? (
              <div className="misty-table">
                <table className="w-full">
                  <thead>
                    <tr>
                      <th>Order #</th>
                      <th>Invoice #</th>
                      <th>Client</th>
                      <th>Amount</th>
                      <th>Invoice Date</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredArchivedJobs.map((job) => (
                      <tr key={job.id}>
                        <td className="font-medium">{job.order_number}</td>
                        <td className="text-yellow-400">{job.invoice_number}</td>
                        <td>{job.client_name}</td>
                        <td className="font-medium text-green-400">
                          {formatCurrency(job.total_amount)}
                        </td>
                        <td>{job.invoice_date ? formatDate(job.invoice_date) : 'N/A'}</td>
                        <td>
                          <div className="flex items-center space-x-2">
                            <button
                              onClick={() => downloadInvoice(job.id, job.order_number)}
                              className="text-gray-400 hover:text-yellow-400 transition-colors"
                              title="Download Invoice"
                            >
                              <DocumentArrowDownIcon className="h-4 w-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-12">
                <DocumentArrowDownIcon className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-300">No archived jobs found</h3>
                <p className="mt-1 text-sm text-gray-400">
                  Select a different month/year or check back after invoicing some jobs.
                </p>
              </div>
            )}
          </div>
        )}

        {/* Reports Tab */}
        {activeTab === 'reports' && (
          <div>
            <h2 className="text-xl font-semibold text-white mb-4">Monthly Reports</h2>
            <div className="text-center py-12 text-gray-400">
              <CalendarDaysIcon className="mx-auto h-12 w-12 mb-4" />
              <p>Monthly reporting feature coming soon...</p>
              <p className="text-sm mt-2">This will show detailed reports of jobs completed and invoiced each month.</p>
            </div>
          </div>
        )}

        {/* Invoice Generation Modal */}
        {showInvoiceModal && selectedJob && (
          <div className="modal-overlay">
            <div className="modal-content max-w-lg">
              <div className="p-6">
                <h3 className="text-xl font-bold text-white mb-4">
                  Generate Invoice - {selectedJob.order_number}
                </h3>
                
                <div className="mb-4">
                  <p className="text-gray-300 mb-2">
                    <strong>Client:</strong> {selectedJob.client_name}
                  </p>
                  <p className="text-gray-300 mb-2">
                    <strong>Total Amount:</strong> {formatCurrency(selectedJob.total_amount)}
                  </p>
                  <p className="text-gray-300 mb-4">
                    <strong>Payment Terms:</strong> {selectedJob.client_payment_terms || 'Net 30 days'}
                  </p>
                </div>

                <div className="mb-6">
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Invoice Type
                  </label>
                  <div className="space-y-2">
                    <label className="flex items-center">
                      <input
                        type="radio"
                        value="full"
                        checked={invoiceType === 'full'}
                        onChange={(e) => setInvoiceType(e.target.value)}
                        className="form-radio h-4 w-4 text-yellow-400"
                      />
                      <span className="ml-2 text-gray-300">Full Invoice</span>
                    </label>
                    <label className="flex items-center">
                      <input
                        type="radio"
                        value="partial"
                        checked={invoiceType === 'partial'}
                        onChange={(e) => setInvoiceType(e.target.value)}
                        className="form-radio h-4 w-4 text-yellow-400"
                      />
                      <span className="ml-2 text-gray-300">Part Supply</span>
                    </label>
                  </div>
                </div>

                <div className="flex justify-end space-x-3">
                  <button
                    onClick={() => setShowInvoiceModal(false)}
                    className="misty-button misty-button-secondary"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={() => {
                      if (invoiceType === 'partial') {
                        handlePartSupplyNext();
                      } else {
                        generateInvoice();
                      }
                    }}
                    className="misty-button misty-button-primary"
                  >
                    {invoiceType === 'partial' ? 'Next: Select Items' : 'Generate Invoice'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default Invoicing;