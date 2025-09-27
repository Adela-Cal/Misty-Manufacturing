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
  MagnifyingGlassIcon
} from '@heroicons/react/24/outline';

const Invoicing = () => {
  const [activeTab, setActiveTab] = useState('live-jobs');
  const [liveJobs, setLiveJobs] = useState([]);
  const [archivedJobs, setArchivedJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedJob, setSelectedJob] = useState(null);
  const [showInvoiceModal, setShowInvoiceModal] = useState(false);
  const [invoiceType, setInvoiceType] = useState('full');
  const [reportMonth, setReportMonth] = useState(new Date().getMonth() + 1);
  const [reportYear, setReportYear] = useState(new Date().getFullYear());

  useEffect(() => {
    loadData();
  }, [activeTab]);

  const loadData = async () => {
    setLoading(true);
    try {
      if (activeTab === 'live-jobs') {
        const response = await apiHelpers.getLiveJobs();
        setLiveJobs(response.data.data || []);
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
    setShowInvoiceModal(true);
  };

  const generateInvoice = async () => {
    if (!selectedJob) return;

    try {
      const invoiceData = {
        invoice_type: invoiceType,
        items: selectedJob.items,
        subtotal: selectedJob.subtotal,
        gst: selectedJob.gst,
        total_amount: selectedJob.total_amount,
        due_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
      };

      const response = await apiHelpers.generateJobInvoice(selectedJob.id, invoiceData);
      
      toast.success(`Invoice ${response.data.invoice_number} generated successfully`);
      
      // Show download prompt instead of automatic download
      toast.success(
        <div>
          <p>📄 Documents ready for download:</p>
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
        { duration: 10000 }
      );
      
      setShowInvoiceModal(false);
      setSelectedJob(null);
      loadData(); // Refresh data
    } catch (error) {
      console.error('Failed to generate invoice:', error);
      toast.error('Failed to generate invoice');
    }
  };

  const downloadInvoice = async (jobId, orderNumber) => {
    try {
      const response = await apiHelpers.generateInvoice(jobId);
      
      // Ensure we have the right response type
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      
      const link = document.createElement('a');
      link.href = url;
      link.download = `invoice_${orderNumber}.pdf`;
      link.target = '_blank'; // Add target blank
      document.body.appendChild(link);
      
      // Use a small delay to ensure the link is ready
      setTimeout(() => {
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
        toast.success(`📄 Invoice ${orderNumber} downloaded`);
      }, 100);
      
    } catch (error) {
      console.error('Failed to download invoice:', error);
      toast.error('Failed to download invoice');
    }
  };

  const downloadPackingSlip = async (jobId, orderNumber) => {
    try {
      const response = await apiHelpers.generatePackingList(jobId);
      
      // Ensure we have the right response type
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      
      const link = document.createElement('a');
      link.href = url;
      link.download = `packing_slip_${orderNumber}.pdf`;
      link.target = '_blank'; // Add target blank
      document.body.appendChild(link);
      
      // Use a small delay to ensure the link is ready
      setTimeout(() => {
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
        toast.success(`📦 Packing Slip ${orderNumber} downloaded`);
      }, 100);
      
    } catch (error) {
      console.error('Failed to download packing slip:', error);
      toast.error('Failed to download packing slip');
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
          <div>
            <button
              onClick={testPdfDownload}
              className="bg-red-600 hover:bg-red-700 px-4 py-2 rounded text-white text-sm"
            >
              🔧 Test PDF Download
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="mb-6">
          <div className="border-b border-gray-700">
            <nav className="-mb-px flex space-x-8">
              {[
                { key: 'live-jobs', label: 'Live Jobs', icon: ClipboardDocumentListIcon },
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
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search jobs..."
                className="misty-input pl-10 w-full max-w-md"
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
                            <button
                              onClick={() => downloadInvoice(job.id, job.order_number)}
                              className="text-gray-400 hover:text-yellow-400 transition-colors"
                              title="Download Invoice PDF"
                            >
                              <DocumentArrowDownIcon className="h-4 w-4" />
                            </button>
                            <button
                              onClick={() => downloadPackingSlip(job.id, job.order_number)}
                              className="text-gray-400 hover:text-green-400 transition-colors"
                              title="Download Packing Slip"
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
                <ClipboardDocumentListIcon className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-300">No jobs ready for invoicing</h3>
                <p className="mt-1 text-sm text-gray-400">
                  Jobs will appear here when they reach the delivery stage.
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
                    onClick={generateInvoice}
                    className="misty-button misty-button-primary"
                  >
                    Generate Invoice
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