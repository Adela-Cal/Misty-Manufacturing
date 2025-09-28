import React, { useState, useEffect } from 'react';
import Layout from './Layout';
import { apiHelpers, stageDisplayNames, stageColors, formatCurrency, formatDate } from '../utils/api';
import { toast } from 'sonner';
import { 
  ChevronDownIcon,
  ChevronRightIcon,
  ExclamationTriangleIcon,
  DocumentArrowDownIcon,
  BookOpenIcon,
  ChevronLeftIcon,
  ArrowRightIcon,
  ArrowLeftIcon
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

  const moveJobStage = async (jobId, currentStage, direction) => {
    try {
      await apiHelpers.moveOrderStage(jobId, { direction });
      toast.success(`Job moved ${direction}`);
      loadProductionBoard(); // Refresh the board
    } catch (error) {
      console.error('Failed to move job stage:', error);
      if (error.response?.data?.detail) {
        toast.error(error.response.data.detail);
      } else {
        toast.error('Failed to move job stage');
      }
    }
  };

  const getMaterialsStatus = (job) => {
    return job.materials_ready ? 'ready' : 'pending';
  };

  const toggleMaterialsModal = async (jobId) => {
    try {
      const response = await apiHelpers.getMaterialsStatus(jobId);
      // TODO: Open modal to show/edit materials checklist
      toast.info('Materials modal feature coming soon');
    } catch (error) {
      console.error('Failed to load materials status:', error);
      toast.error('Failed to load materials status');
    }
  };

  const toggleOrderItemStatus = async (jobId, itemIndex, currentStatus) => {
    try {
      await apiHelpers.updateOrderItemStatus(jobId, {
        item_index: itemIndex,
        is_completed: !currentStatus
      });
      toast.success('Item status updated');
      loadProductionBoard(); // Refresh to show updated status
    } catch (error) {
      console.error('Failed to update item status:', error);
      toast.error('Failed to update item status');
    }
  };

  const getDeliveryLocationDot = (deliveryAddress) => {
    // Simple mapping of states/cities to approximate coordinates on Australia map
    // These are rough percentages for positioning on a 200x150 SVG map
    const locationMap = {
      'NSW': { x: 75, y: 60 },
      'VIC': { x: 70, y: 80 },
      'QLD': { x: 80, y: 40 },
      'SA': { x: 55, y: 70 },
      'WA': { x: 20, y: 50 },
      'TAS': { x: 70, y: 95 },
      'NT': { x: 55, y: 25 },
      'ACT': { x: 75, y: 65 },
      // Major cities
      'Sydney': { x: 78, y: 58 },
      'Melbourne': { x: 70, y: 78 },
      'Brisbane': { x: 82, y: 38 },
      'Perth': { x: 18, y: 52 },
      'Adelaide': { x: 58, y: 68 },
      'Darwin': { x: 55, y: 15 },
      'Hobart': { x: 70, y: 92 },
      'Canberra': { x: 76, y: 62 }
    };

    if (!deliveryAddress) return { x: 60, y: 60 }; // Default center

    const address = deliveryAddress.toUpperCase();
    
    // Try to find state or city match
    for (const [location, coords] of Object.entries(locationMap)) {
      if (address.includes(location.toUpperCase())) {
        return coords;
      }
    }
    
    // Default to center if no match
    return { x: 60, y: 60 };
  };

  const HexagonIcon = ({ status }) => (
    <svg 
      width="20" 
      height="20" 
      viewBox="0 0 24 24" 
      className={`${status === 'ready' ? 'text-green-500' : 'text-red-500'}`}
    >
      <path 
        fill="currentColor" 
        d="M17.5 3.5L22 12l-4.5 8.5h-11L2 12l4.5-8.5h11z"
      />
    </svg>
  );

  const AustraliaMap = ({ deliveryAddress }) => {
    const location = getDeliveryLocationDot(deliveryAddress);
    
    return (
      <div className="relative" title={`Delivery: ${deliveryAddress || 'Unknown'}`}>
        <svg width="60" height="45" viewBox="0 0 200 150" className="text-gray-400">
          {/* Simplified Australia outline */}
          <path 
            fill="none" 
            stroke="currentColor" 
            strokeWidth="2"
            d="M30,40 L50,20 L80,15 L120,20 L150,25 L170,40 L180,60 L175,80 L170,100 L160,120 L140,130 L100,135 L70,130 L50,125 L35,110 L25,90 L20,70 L25,50 Z"
          />
          {/* Tasmania */}
          <path 
            fill="none" 
            stroke="currentColor" 
            strokeWidth="2"
            d="M125,130 L135,125 L140,135 L130,140 Z"
          />
          {/* Delivery location dot */}
          <circle 
            cx={location.x * 2} 
            cy={location.y * 1.5} 
            r="3" 
            fill="red" 
            className="animate-pulse"
          />
        </svg>
      </div>
    );
  };

  const JobCard = ({ job, stageKey }) => {
    const isExpanded = expandedJobs[job.id];
    const isOverdue = job.is_overdue;
    const materialsStatus = getMaterialsStatus(job);

    return (
      <div 
        className={`
          bg-gray-800 border rounded-lg p-4 transition-all duration-200 hover:shadow-lg mb-3
          ${stageColors[stageKey] || 'border-gray-600'}
          ${isOverdue ? 'border-red-500 bg-red-900/20' : ''}
        `}
        data-testid={`job-card-${job.id}`}
      >
        {/* Job Header */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center flex-1">
            {job.client_logo && (
              <img
                src={job.client_logo}
                alt={`${job.client_name} logo`}
                className="h-8 w-8 rounded object-cover mr-3"
              />
            )}
            <div className="flex-1">
              <h4 className="font-semibold text-white">{job.order_number}</h4>
              <p className="text-sm text-gray-400">{job.client_name}</p>
            </div>
            
            {/* Australia Map */}
            <div className="mx-3">
              <AustraliaMap deliveryAddress={job.delivery_address} />
            </div>
            
            {isOverdue && (
              <ExclamationTriangleIcon className="h-5 w-5 text-red-400 ml-2" />
            )}
          </div>
          
          <div className="flex items-center space-x-2">
            {/* Materials Status Hexagon */}
            <button
              onClick={() => toggleMaterialsModal(job.id)}
              className="text-gray-400 hover:text-yellow-400 transition-colors"
              title={`Materials ${materialsStatus === 'ready' ? 'Ready' : 'Pending'}`}
            >
              <HexagonIcon status={materialsStatus} />
            </button>
            
            {/* Book Icon for Order Items */}
            <button
              onClick={() => toggleJobExpansion(job.id)}
              className="text-gray-400 hover:text-yellow-400 transition-colors"
              title="View Order Items"
              data-testid={`expand-job-${job.id}`}
            >
              <BookOpenIcon className="h-5 w-5" />
            </button>
            
            <button
              onClick={() => handleDownloadJobCard(job.id, job.order_number)}
              className="text-gray-400 hover:text-blue-400 transition-colors"
              title="Download Job Card"
              data-testid={`download-job-card-${job.id}`}
            >
              <DocumentArrowDownIcon className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Job Summary */}
        <div className="space-y-1 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-400">Runtime:</span>
            <span className="text-yellow-400 font-medium">
              {job.runtime || '2-3 days'}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Due:</span>
            <span className={isOverdue ? 'text-red-400' : 'text-gray-300'}>
              {formatDate(job.due_date)}
            </span>
          </div>
        </div>

        {/* Navigation Arrows */}
        <div className="flex justify-between mt-3">
          <button
            onClick={() => moveJobStage(job.id, stageKey, 'backward')}
            className="text-gray-400 hover:text-yellow-400 transition-colors"
            title="Move to Previous Stage"
          >
            <ArrowLeftIcon className="h-6 w-6 font-bold" />
          </button>
          
          <button
            onClick={() => moveJobStage(job.id, stageKey, 'forward')}
            className="text-gray-400 hover:text-yellow-400 transition-colors"
            title="Move to Next Stage"
          >
            <ArrowRightIcon className="h-6 w-6 font-bold" />
          </button>
        </div>

        {/* Expanded Details */}
        {isExpanded && (
          <div className="mt-4 pt-4 border-t border-gray-700">
            <div className="space-y-3">
              {/* Order Items with checkboxes */}
              <div>
                <h5 className="font-medium text-white mb-2">Order Items:</h5>
                <div className="space-y-2">
                  {job.items.map((item, index) => (
                    <div key={index} className="flex items-center justify-between text-sm">
                      <div className="flex items-center">
                        <input
                          type="checkbox"
                          checked={item.is_completed || false}
                          onChange={() => toggleOrderItemStatus(job.id, index, item.is_completed)}
                          className="mr-2 rounded bg-gray-700 border-gray-600"
                        />
                        <span className={`${item.is_completed ? 'line-through text-gray-500' : 'text-gray-300'}`}>
                          {item.product_name} (x{item.quantity})
                        </span>
                      </div>
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
      <div className="mb-6" data-testid={`stage-${stageKey}`}>
        <div className={`bg-gray-700 rounded-t-lg p-4 border-l-4 ${stageColors[stageKey] || 'border-gray-500'}`}>
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-white text-lg">{stageName}</h3>
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
        
        <div className="bg-gray-700/30 rounded-b-lg p-4 min-h-32">
          {jobs.length > 0 ? (
            <div className="space-y-0">
              {jobs.map((job) => (
                <JobCard key={job.id} job={job} stageKey={stageKey} />
              ))}
            </div>
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
            <div className="space-y-4">
              {[...Array(7)].map((_, i) => (
                <div key={i} className="h-32 bg-gray-700 rounded"></div>
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

        {/* Production Stages - Row Layout */}
        <div className="space-y-4 pb-4">
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