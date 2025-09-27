import React, { useState, useEffect } from 'react';
import Layout from './Layout';
import { apiHelpers, stageDisplayNames, stageColors, formatCurrency, formatDate } from '../utils/api';
import { toast } from 'sonner';
import { 
  ChevronDownIcon,
  ChevronRightIcon,
  ExclamationTriangleIcon,
  DocumentArrowDownIcon
} from '@heroicons/react/24/outline';

const ProductionBoard = () => {
  const [productionBoard, setProductionBoard] = useState({});
  const [loading, setLoading] = useState(true);
  const [expandedJobs, setExpandedJobs] = useState({});

  useEffect(() => {
    loadProductionBoard();
    const interval = setInterval(loadProductionBoard, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const loadProductionBoard = async () => {
    try {
      if (loading) setLoading(true);
      const response = await apiHelpers.getProductionBoard();
      setProductionBoard(response.data?.data || {});
    } catch (error) {
      console.error('Failed to load production board:', error);
      toast.error('Failed to load production board');
    } finally {
      setLoading(false);
    }
  };

  const toggleJobExpansion = (jobId) => {
    setExpandedJobs(prev => ({
      ...prev,
      [jobId]: !prev[jobId]
    }));
  };

  const handleDownloadJobCard = async (orderId, orderNumber) => {
    try {
      const response = await apiHelpers.generateJobCard(orderId);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.download = `job_card_${orderNumber}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      toast.success('Job card downloaded successfully');
    } catch (error) {
      console.error('Failed to download job card:', error);
      toast.error('Failed to download job card');
    }
  };

  const JobCard = ({ job, stageKey }) => {
    const isExpanded = expandedJobs[job.id];
    const isOverdue = job.is_overdue;

    return (
      <div 
        className={`
          bg-gray-800 border rounded-lg p-4 transition-all duration-200 hover:shadow-lg
          ${stageColors[stageKey] || 'border-gray-600'}
          ${isOverdue ? 'border-red-500 bg-red-900/20' : ''}
        `}
        data-testid={`job-card-${job.id}`}
      >
        {/* Job Header */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center">
            {job.client_logo && (
              <img
                src={job.client_logo}
                alt={`${job.client_name} logo`}
                className="h-8 w-8 rounded object-cover mr-3"
              />
            )}
            <div>
              <h4 className="font-semibold text-white">{job.order_number}</h4>
              <p className="text-sm text-gray-400">{job.client_name}</p>
            </div>
            {isOverdue && (
              <ExclamationTriangleIcon className="h-5 w-5 text-red-400 ml-2" />
            )}
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={() => handleDownloadJobCard(job.id, job.order_number)}
              className="text-gray-400 hover:text-blue-400 transition-colors"
              title="Download Job Card"
              data-testid={`download-job-card-${job.id}`}
            >
              <DocumentArrowDownIcon className="h-5 w-5" />
            </button>
            
            <button
              onClick={() => toggleJobExpansion(job.id)}
              className="text-gray-400 hover:text-yellow-400 transition-colors"
              data-testid={`expand-job-${job.id}`}
            >
              {isExpanded ? (
                <ChevronDownIcon className="h-5 w-5" />
              ) : (
                <ChevronRightIcon className="h-5 w-5" />
              )}
            </button>
          </div>
        </div>

        {/* Job Summary */}
        <div className="space-y-1 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-400">Total:</span>
            <span className="text-yellow-400 font-medium">
              {formatCurrency(job.total_amount)}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Due:</span>
            <span className={isOverdue ? 'text-red-400' : 'text-gray-300'}>
              {formatDate(job.due_date)}
            </span>
          </div>
        </div>

        {/* Expanded Details */}
        {isExpanded && (
          <div className="mt-4 pt-4 border-t border-gray-700">
            <div className="space-y-3">
              {/* Order Items */}
              <div>
                <h5 className="font-medium text-white mb-2">Order Items:</h5>
                <div className="space-y-1">
                  {job.items.map((item, index) => (
                    <div key={index} className="flex justify-between text-sm">
                      <span className="text-gray-300">
                        {item.product_name} (x{item.quantity})
                      </span>
                      <span className="text-gray-400">
                        {formatCurrency(item.total_price)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Delivery Address */}
              {job.delivery_address && (
                <div>
                  <h5 className="font-medium text-white mb-1">Delivery:</h5>
                  <p className="text-sm text-gray-300">{job.delivery_address}</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    );
  };

  const ProductionStage = ({ stageKey, jobs, stageName }) => {
    const overdueCount = jobs.filter(job => job.is_overdue).length;
    
    return (
      <div className="flex-1 min-w-80" data-testid={`stage-${stageKey}`}>
        <div className={`bg-gray-700 rounded-t-lg p-4 border-b-4 ${stageColors[stageKey] || 'border-gray-500'}`}>
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-white">{stageName}</h3>
            <div className="flex items-center space-x-2">
              <span className="bg-gray-600 text-white text-sm px-2 py-1 rounded">
                {jobs.length}
              </span>
              {overdueCount > 0 && (
                <span className="bg-red-600 text-white text-sm px-2 py-1 rounded flex items-center">
                  <ExclamationTriangleIcon className="h-4 w-4 mr-1" />
                  {overdueCount}
                </span>
              )}
            </div>
          </div>
        </div>
        
        <div className="bg-gray-700/50 rounded-b-lg p-4 space-y-3 min-h-96 max-h-96 overflow-y-auto">
          {jobs.length > 0 ? (
            jobs.map((job) => (
              <JobCard key={job.id} job={job} stageKey={stageKey} />
            ))
          ) : (
            <p className="text-gray-400 text-center py-8">No jobs in this stage</p>
          )}
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
            <div className="flex space-x-4 overflow-x-auto">
              {[...Array(7)].map((_, i) => (
                <div key={i} className="flex-shrink-0 w-80 h-96 bg-gray-700 rounded"></div>
              ))}
            </div>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="p-8" data-testid="production-board">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Production Board</h1>
            <p className="text-gray-400">Track jobs through the manufacturing process</p>
          </div>
          <button
            onClick={loadProductionBoard}
            className="misty-button misty-button-secondary"
            data-testid="refresh-board"
          >
            Refresh
          </button>
        </div>

        {/* Production Stages */}
        <div className="flex space-x-4 overflow-x-auto pb-4">
          {Object.entries(productionBoard).map(([stageKey, jobs]) => (
            <ProductionStage
              key={stageKey}
              stageKey={stageKey}
              jobs={jobs}
              stageName={stageDisplayNames[stageKey] || stageKey}
            />
          ))}
        </div>
      </div>
    </Layout>
  );
};

export default ProductionBoard;