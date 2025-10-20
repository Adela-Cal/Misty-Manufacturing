import React, { useState, useEffect } from 'react';
import Layout from './Layout';
import JobCard from './JobCard';
import { apiHelpers, stageDisplayNames, stageColors, formatCurrency, formatDate } from '../utils/api';
import { toast } from 'sonner';
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';
import { 
  ChevronDownIcon,
  ChevronRightIcon,
  ExclamationTriangleIcon,
  DocumentArrowDownIcon,
  BookOpenIcon,
  ChevronLeftIcon,
  ArrowRightIcon,
  ArrowLeftIcon,
  UserIcon,
  ClipboardDocumentListIcon,
  ClockIcon
} from '@heroicons/react/24/outline';

// Custom Jumping Man Icon Component
const JumpingManIcon = ({ className = "h-5 w-5" }) => (
  <svg 
    className={className} 
    viewBox="0 0 24 24" 
    fill="none" 
    stroke="currentColor" 
    strokeWidth="2"
  >
    {/* Head */}
    <circle cx="12" cy="5" r="2" />
    {/* Body */}
    <path d="M12 7v6" />
    {/* Arms - raised up for jumping motion */}
    <path d="M8 9l4-2 4 2" />
    {/* Legs - spread for jumping motion */}
    <path d="M9 17l3-4 3 4" />
    <path d="M10 21v-2" />
    <path d="M14 21v-2" />
  </svg>
);

const ProductionBoard = () => {
  const [productionBoard, setProductionBoard] = useState({});
  const [loading, setLoading] = useState(true);
  const [expandedJobs, setExpandedJobs] = useState({});
  const [showJumpModal, setShowJumpModal] = useState(false);
  const [jumpJobData, setJumpJobData] = useState({ jobId: null, currentStage: null, stages: [] });
  const [showJobCard, setShowJobCard] = useState(false);
  const [selectedJobCard, setSelectedJobCard] = useState({ jobId: null, stage: null, orderId: null });

  useEffect(() => {
    loadProductionBoard();
    
    const interval = setInterval(() => {
      // Only refresh if no job card is currently open
      if (!showJobCard) {
        console.log('Auto-refreshing production board (no job card open)');
        loadProductionBoard();
      } else {
        console.log('Skipping auto-refresh (job card is open)');
      }
    }, 30000); // Check every 30 seconds
    
    return () => clearInterval(interval);
  }, [showJobCard]);

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

  const openJumpModal = (jobId, currentStage) => {
    const availableStages = getAvailableStages(currentStage);
    setJumpJobData({ jobId, currentStage, stages: availableStages });
    setShowJumpModal(true);
  };

  const jumpToStage = async (targetStage) => {
    try {
      await apiHelpers.jumpToStage(jumpJobData.jobId, { target_stage: targetStage });
      toast.success(`Job jumped to ${stageDisplayNames[targetStage]}`);
      setShowJumpModal(false);
      loadProductionBoard(); // Reload to show updated position
    } catch (error) {
      console.error('Failed to jump job to stage:', error);
      if (error.response?.data?.detail) {
        toast.error(error.response.data.detail);
      } else {
        toast.error('Failed to jump job to stage');
      }
    }
  };

  // Get available stages for jumping (excluding current stage)
  const getAvailableStages = (currentStage) => {
    const allStages = Object.keys(stageDisplayNames);
    return allStages.filter(stage => stage !== currentStage);
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


  const handleDragEnd = async (result) => {
    const { source, destination, draggableId } = result;

    // Dropped outside the list
    if (!destination) {
      return;
    }

    // Dropped in the same position
    if (
      source.droppableId === destination.droppableId &&
      source.index === destination.index
    ) {
      return;
    }

    const stageKey = source.droppableId;
    const jobs = [...productionBoard[stageKey]];

    // Reorder the jobs array
    const [removed] = jobs.splice(source.index, 1);
    jobs.splice(destination.index, 0, removed);

    // Update local state immediately for smooth UI
    setProductionBoard(prev => ({
      ...prev,
      [stageKey]: jobs
    }));

    // Send update to backend
    try {
      const jobOrder = jobs.map(job => job.id);
      await apiHelpers.reorderJobs({
        stage: stageKey,
        job_order: jobOrder
      });
      toast.success('Job order updated successfully');
    } catch (error) {
      console.error('Failed to reorder jobs:', error);
      toast.error('Failed to save job order');
      // Revert on error
      loadProductionBoard();
    }
  };


  const handleOpenJobCard = (jobId, stage, orderId) => {
    console.log('Opening job card:', { jobId, stage, orderId });
    
    if (!jobId || !stage) {
      toast.error('Missing job information for job card');
      console.error('Missing required parameters:', { jobId, stage, orderId });
      return;
    }
    
    // Use jobId as orderId if orderId is not provided
    const finalOrderId = orderId || jobId;
    
    console.log('Job card opening with:', { jobId, stage, orderId: finalOrderId });
    setSelectedJobCard({ jobId, stage, orderId: finalOrderId });
    setShowJobCard(true);
  };

  const handleCloseJobCard = () => {
    setShowJobCard(false);
    setSelectedJobCard({ jobId: null, stage: null, orderId: null });
    
    // Refresh production board when job card is closed to catch up on any updates
    setTimeout(() => {
      console.log('Refreshing production board after job card closed');
      loadProductionBoard();
    }, 500);
  };

  const handleJobStarted = () => {
    console.log('Job started - refreshing production board');
    loadProductionBoard();
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
    // Removed Australia map functionality as requested
    return { x: 60, y: 60 };
  };

  const getJobStartStatus = (job, currentStage) => {
    // Check if the job has been started for the CURRENT stage
    if (job.stage_start_times && job.stage_start_times[currentStage]) {
      return 'started';
    }
    return 'not_started';
  };

  const JobStartStatusIcon = ({ status }) => (
    <ClockIcon 
      className={`h-5 w-5 ${
        status === 'started' 
          ? 'text-green-500 animate-pulse' 
          : 'text-red-500'
      }`}
    />
  );

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

  // Removed AustraliaMap component as requested

  const JobTile = ({ job, stageKey, isDragging = false }) => {
    const isExpanded = expandedJobs[job.id];
    const isOverdue = job.is_overdue;
    const materialsStatus = getMaterialsStatus(job);
    const jobStartStatus = getJobStartStatus(job);

    return (
      <div 
        className={`
          relative bg-gray-800 border rounded-lg p-3 transition-all duration-200 hover:shadow-lg overflow-hidden cursor-move
          ${stageColors[stageKey] || 'border-gray-600'}
          ${isOverdue ? 'border-red-500 bg-red-900/20' : ''}
          ${isDragging ? 'shadow-2xl ring-2 ring-yellow-400' : ''}
        `}
        data-testid={`job-card-${job.id}`}
      >
        {/* Job Header */}
        <div className="mb-2 relative z-10">
          <div className="flex items-center mb-1">
            <div className="flex-1 min-w-0">
              <h4 className="font-semibold text-white text-sm truncate">{job.order_number}</h4>
            </div>
            {isOverdue && (
              <ExclamationTriangleIcon className="h-4 w-4 text-red-400 ml-1 flex-shrink-0" />
            )}
          </div>
          <p className="text-xs text-gray-400 truncate">{job.client_name}</p>
          
          <div className="flex items-center justify-between mt-2 flex-wrap gap-1">
            {/* Job Start Status */}
            <button
              onClick={(e) => e.stopPropagation()}
              className="cursor-default"
              title={`Job ${jobStartStatus === 'started' ? 'Started' : 'Not Started'}`}
            >
              <JobStartStatusIcon status={jobStartStatus} />
            </button>
            
            {/* Order Items */}
            <button
              onClick={() => toggleJobExpansion(job.id)}
              className="text-gray-400 hover:text-yellow-400 transition-colors"
              title="View Order Items"
              data-testid={`expand-job-${job.id}`}
            >
              <BookOpenIcon className="h-4 w-4" />
            </button>
            
            {/* Jump to Stage */}
            <button
              onClick={(e) => {
                e.stopPropagation();
                openJumpModal(job.id, stageKey);
              }}
              className="text-gray-400 hover:text-green-400 transition-colors"
              title="Jump to Stage"
              data-testid={`jump-stage-${job.id}`}
            >
              <JumpingManIcon className="h-4 w-4" />
            </button>
            
            {/* Interactive Job Card */}
            <button
              onClick={() => handleOpenJobCard(job.id, stageKey, job.order_id || job.id)}
              className="text-gray-400 hover:text-purple-400 transition-colors"
              title="View Job Card"
              data-testid={`view-job-card-${job.id}`}
            >
              <ClipboardDocumentListIcon className="h-4 w-4" />
            </button>

            <button
              onClick={() => handleDownloadJobCard(job.id, job.order_number)}
              className="text-gray-400 hover:text-blue-400 transition-colors"
              title="Download"
              data-testid={`download-job-card-${job.id}`}
            >
              <DocumentArrowDownIcon className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Job Summary */}
        <div className="space-y-1 text-xs mt-2 relative z-10">
          <div className="flex justify-between">
            <span className="text-gray-400">Runtime:</span>
            <span className="text-yellow-400 font-medium truncate ml-1">
              {job.runtime || '2-3d'}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Due:</span>
            <span className={`truncate ml-1 ${isOverdue ? 'text-red-400' : 'text-gray-300'}`}>
              {formatDate(job.due_date)}
            </span>
          </div>
        </div>

        {/* Navigation Arrows */}
        <div className="flex justify-between mt-2 pt-2 border-t border-gray-700 relative z-10">
          <button
            onClick={() => moveJobStage(job.id, stageKey, 'backward')}
            className="text-gray-400 hover:text-yellow-400 transition-colors"
            title="Move to Previous Stage"
          >
            <ArrowLeftIcon className="h-5 w-5" />
          </button>
          
          <button
            onClick={() => moveJobStage(job.id, stageKey, 'forward')}
            className="text-gray-400 hover:text-yellow-400 transition-colors"
            title="Move to Next Stage"
          >
            <ArrowRightIcon className="h-5 w-5" />
          </button>
        </div>

        {/* Expanded Details */}
        {isExpanded && (
          <div className="mt-4 pt-4 border-t border-gray-700 relative z-10">
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
        
        <Droppable droppableId={stageKey} direction="horizontal">
          {(provided, snapshot) => (
            <div
              ref={provided.innerRef}
              {...provided.droppableProps}
              className={`bg-gray-700/30 rounded-b-lg p-4 min-h-32 transition-colors ${
                snapshot.isDraggingOver ? 'bg-gray-600/50 border-2 border-yellow-400' : ''
              }`}
            >
              {jobs.length > 0 ? (
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6 gap-3">
                  {jobs.map((job, index) => (
                    <Draggable key={job.id} draggableId={job.id} index={index}>
                      {(provided, snapshot) => (
                        <div
                          ref={provided.innerRef}
                          {...provided.draggableProps}
                          {...provided.dragHandleProps}
                          className={snapshot.isDragging ? 'opacity-75 rotate-2' : ''}
                        >
                          <JobTile job={job} stageKey={stageKey} isDragging={snapshot.isDragging} />
                        </div>
                      )}
                    </Draggable>
                  ))}
                  {provided.placeholder}
                </div>
              ) : (
                <p className="text-gray-400 text-center py-8">No jobs in this stage</p>
              )}
            </div>
          )}
        </Droppable>
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

        {/* Production Stages - Row Layout with Drag & Drop */}
        <DragDropContext onDragEnd={handleDragEnd}>
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
        </DragDropContext>
      </div>

      {/* Interactive Job Card Modal */}
      {showJobCard && (
        <JobCard
          jobId={selectedJobCard.jobId}
          stage={selectedJobCard.stage}
          orderId={selectedJobCard.orderId}
          onClose={handleCloseJobCard}
          onJobStarted={handleJobStarted}
        />
      )}

      {/* Jump to Stage Modal */}
      {showJumpModal && (
        <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && setShowJumpModal(false)}>
          <div className="modal-content max-w-md">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-white">Jump to Stage</h3>
                  <p className="text-sm text-gray-400">
                    Select a stage to jump this job to
                  </p>
                </div>
                <button
                  onClick={() => setShowJumpModal(false)}
                  className="text-gray-400 hover:text-white text-2xl"
                >
                  ×
                </button>
              </div>

              <div className="mb-6">
                <p className="text-sm text-gray-400 mb-4">
                  Current Stage: <span className="text-white font-medium">{stageDisplayNames[jumpJobData.currentStage]}</span>
                </p>
                
                {jumpJobData.stages.length > 0 ? (
                  <div className="space-y-2">
                    {jumpJobData.stages.map((stage) => (
                      <button
                        key={stage}
                        onClick={() => jumpToStage(stage)}
                        className="w-full text-left px-4 py-3 bg-gray-800 hover:bg-gray-700 border border-gray-600 rounded-lg transition-colors text-white"
                      >
                        <div className="flex items-center justify-between">
                          <span>Jump to {stageDisplayNames[stage]}</span>
                          <svg className="h-5 w-5 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                          </svg>
                        </div>
                      </button>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-400 text-sm py-4 text-center">No other stages available</p>
                )}
              </div>

              <div className="flex justify-end">
                <button
                  onClick={() => setShowJumpModal(false)}
                  className="misty-button misty-button-secondary"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </Layout>
  );
};


export default ProductionBoard;