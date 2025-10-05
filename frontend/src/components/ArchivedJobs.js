import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import Layout from './Layout';
import JobCard from './JobCard';
import { apiHelpers } from '../utils/api';
import { toast } from 'sonner';
import { 
  ClipboardDocumentListIcon,
  FunnelIcon,
  CalendarDaysIcon,
  ArrowLeftIcon,
  EyeIcon
} from '@heroicons/react/24/outline';

const ArchivedJobs = () => {
  const { clientId } = useParams();
  const [client, setClient] = useState(null);
  const [archivedJobs, setArchivedJobs] = useState([]);
  const [jobCards, setJobCards] = useState([]);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState('jobs'); // 'jobs' or 'job-cards'
  const [selectedDateRange, setSelectedDateRange] = useState('all');
  const [selectedProcess, setSelectedProcess] = useState('all');
  const [showJobCard, setShowJobCard] = useState(false);
  const [selectedJobCard, setSelectedJobCard] = useState({ jobId: null, stage: null, orderId: null });

  useEffect(() => {
    if (clientId) {
      loadClientData();
      loadArchivedJobs();
      loadJobCards();
    }
  }, [clientId]);

  const loadClientData = async () => {
    try {
      const response = await apiHelpers.getClient(clientId);
      setClient(response.data);
    } catch (error) {
      console.error('Failed to load client data:', error);
      toast.error('Failed to load client data');
    }
  };

  const loadArchivedJobs = async () => {
    try {
      setLoading(true);
      // This would need to be implemented in the backend
      const response = await apiHelpers.getClientArchivedJobs(clientId);
      setArchivedJobs(response.data);
    } catch (error) {
      console.error('Failed to load archived jobs:', error);
      // For now, use mock data
      setArchivedJobs([
        {
          id: 1,
          order_number: 'ORD-2024-001',
          product_code: 'PC-100-50',
          quantity: 1000,
          completed_date: '2024-01-15',
          total_production_time: 240,
          status: 'completed'
        },
        {
          id: 2,
          order_number: 'ORD-2024-005',
          product_code: 'PC-120-75',
          quantity: 500,
          completed_date: '2024-01-20',
          total_production_time: 180,
          status: 'completed'
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const loadJobCards = async () => {
    try {
      // This would need to be implemented in the backend
      const response = await apiHelpers.getClientJobCards(clientId);
      setJobCards(response.data);
    } catch (error) {
      console.error('Failed to load job cards:', error);
      // For now, use mock data
      setJobCards([
        {
          id: 1,
          job_id: 1,
          order_id: 1,
          order_number: 'ORD-2024-001',
          process_stage: 'paper_slitting',
          generated_date: '2024-01-15T08:00:00Z',
          machine_used: 'Slitter A1',
          operator: 'John Smith',
          setup_time: 45,
          run_time: 120,
          total_time: 165
        },
        {
          id: 2,
          job_id: 1,
          order_id: 1,
          order_number: 'ORD-2024-001',
          process_stage: 'winding',
          generated_date: '2024-01-15T11:00:00Z',
          machine_used: 'Winder X1',
          operator: 'Jane Doe',
          setup_time: 30,
          run_time: 75,
          total_time: 105
        }
      ]);
    }
  };

  const handleViewJobCard = (jobId, stage, orderId) => {
    setSelectedJobCard({ jobId, stage, orderId });
    setShowJobCard(true);
  };

  const handleCloseJobCard = () => {
    setShowJobCard(false);
    setSelectedJobCard({ jobId: null, stage: null, orderId: null });
  };

  const getFilteredJobs = () => {
    let filtered = archivedJobs;

    if (selectedDateRange !== 'all') {
      const now = new Date();
      let cutoffDate;
      
      switch (selectedDateRange) {
        case 'week':
          cutoffDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
          break;
        case 'month':
          cutoffDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
          break;
        case 'quarter':
          cutoffDate = new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000);
          break;
        default:
          cutoffDate = new Date(0);
      }

      filtered = filtered.filter(job => new Date(job.completed_date) >= cutoffDate);
    }

    return filtered;
  };

  const getFilteredJobCards = () => {
    let filtered = jobCards;

    if (selectedProcess !== 'all') {
      filtered = filtered.filter(card => card.process_stage === selectedProcess);
    }

    if (selectedDateRange !== 'all') {
      const now = new Date();
      let cutoffDate;
      
      switch (selectedDateRange) {
        case 'week':
          cutoffDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
          break;
        case 'month':
          cutoffDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
          break;
        case 'quarter':
          cutoffDate = new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000);
          break;
        default:
          cutoffDate = new Date(0);
      }

      filtered = filtered.filter(card => new Date(card.generated_date) >= cutoffDate);
    }

    return filtered;
  };

  const getProcessDisplayName = (stage) => {
    const names = {
      paper_slitting: 'Paper Slitting',
      winding: 'Core Winder',
      finishing: 'Cutting/Indexing',
      delivery: 'Packing/Delivery'
    };
    return names[stage] || stage;
  };

  if (loading) {
    return (
      <Layout>
        <div className="p-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-yellow-400 mx-auto"></div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="p-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center">
            <button
              onClick={() => window.history.back()}
              className="text-gray-400 hover:text-white mr-4 p-2"
              title="Go back"
            >
              <ArrowLeftIcon className="h-5 w-5" />
            </button>
            <div>
              <h1 className="text-3xl font-bold text-white mb-2">
                Archived Jobs - {client?.company_name}
              </h1>
              <p className="text-gray-400">
                View completed jobs and historic production job cards
              </p>
            </div>
          </div>

          {/* View Toggle */}
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setView('jobs')}
              className={`px-4 py-2 rounded-md transition-colors ${
                view === 'jobs'
                  ? 'bg-yellow-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              Archived Jobs
            </button>
            <button
              onClick={() => setView('job-cards')}
              className={`px-4 py-2 rounded-md transition-colors ${
                view === 'job-cards'
                  ? 'bg-yellow-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              Historic Job Cards
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="mb-6 flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <FunnelIcon className="h-5 w-5 text-gray-400" />
            <span className="text-sm text-gray-300">Filters:</span>
          </div>

          <select
            value={selectedDateRange}
            onChange={(e) => setSelectedDateRange(e.target.value)}
            className="misty-select"
          >
            <option value="all">All Time</option>
            <option value="week">Last Week</option>
            <option value="month">Last Month</option>
            <option value="quarter">Last Quarter</option>
          </select>

          {view === 'job-cards' && (
            <select
              value={selectedProcess}
              onChange={(e) => setSelectedProcess(e.target.value)}
              className="misty-select"
            >
              <option value="all">All Processes</option>
              <option value="paper_slitting">Paper Slitting</option>
              <option value="winding">Winding</option>
              <option value="finishing">Cutting/Indexing</option>
              <option value="delivery">Packing/Delivery</option>
            </select>
          )}
        </div>

        {/* Content */}
        {view === 'jobs' ? (
          /* Archived Jobs View */
          <div className="space-y-4">
            {getFilteredJobs().length > 0 ? (
              getFilteredJobs().map((job) => (
                <div key={job.id} className="misty-card p-6">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-4">
                        <div>
                          <h3 className="text-lg font-semibold text-white">
                            {job.order_number}
                          </h3>
                          <p className="text-sm text-gray-400">
                            Product: {job.product_code}
                          </p>
                        </div>
                        
                        <div className="text-center">
                          <div className="text-xl font-bold text-yellow-400">
                            {job.quantity?.toLocaleString()}
                          </div>
                          <div className="text-xs text-gray-400">units</div>
                        </div>

                        <div className="text-center">
                          <div className="text-lg font-medium text-white">
                            {Math.round(job.total_production_time / 60)}h {job.total_production_time % 60}m
                          </div>
                          <div className="text-xs text-gray-400">total time</div>
                        </div>

                        <div className="text-center">
                          <div className="text-sm font-medium text-white">
                            {new Date(job.completed_date).toLocaleDateString()}
                          </div>
                          <div className="text-xs text-gray-400">completed</div>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center space-x-2">
                      <span className="px-3 py-1 bg-green-600 text-white text-xs rounded-full">
                        {job.status}
                      </span>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-12">
                <ClipboardDocumentListIcon className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-300">No archived jobs found</h3>
                <p className="mt-1 text-sm text-gray-400">
                  Jobs will appear here once they are completed and archived.
                </p>
              </div>
            )}
          </div>
        ) : (
          /* Historic Job Cards View */
          <div className="space-y-4">
            {getFilteredJobCards().length > 0 ? (
              getFilteredJobCards().map((card) => (
                <div key={card.id} className="misty-card p-6">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-6">
                        <div>
                          <h3 className="text-lg font-semibold text-white">
                            {card.order_number}
                          </h3>
                          <p className="text-sm text-gray-400">
                            {getProcessDisplayName(card.process_stage)}
                          </p>
                        </div>
                        
                        <div className="text-center">
                          <div className="text-lg font-medium text-white">
                            {card.machine_used}
                          </div>
                          <div className="text-xs text-gray-400">machine</div>
                        </div>

                        <div className="text-center">
                          <div className="text-lg font-medium text-white">
                            {card.operator}
                          </div>
                          <div className="text-xs text-gray-400">operator</div>
                        </div>

                        <div className="text-center">
                          <div className="text-lg font-medium text-yellow-400">
                            {Math.round(card.total_time / 60)}h {card.total_time % 60}m
                          </div>
                          <div className="text-xs text-gray-400">
                            Setup: {card.setup_time}m | Run: {card.run_time}m
                          </div>
                        </div>

                        <div className="text-center">
                          <div className="text-sm font-medium text-white">
                            {new Date(card.generated_date).toLocaleDateString()}
                          </div>
                          <div className="text-xs text-gray-400">
                            {new Date(card.generated_date).toLocaleTimeString()}
                          </div>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => handleViewJobCard(card.job_id, card.process_stage, card.order_id)}
                        className="text-gray-400 hover:text-purple-400 transition-colors p-2"
                        title="View Job Card"
                      >
                        <EyeIcon className="h-5 w-5" />
                      </button>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-12">
                <ClipboardDocumentListIcon className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-300">No job cards found</h3>
                <p className="mt-1 text-sm text-gray-400">
                  Historic job cards will appear here as jobs are processed.
                </p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Interactive Job Card Modal */}
      {showJobCard && (
        <JobCard
          jobId={selectedJobCard.jobId}
          stage={selectedJobCard.stage}
          orderId={selectedJobCard.orderId}
          onClose={handleCloseJobCard}
        />
      )}
    </Layout>
  );
};

export default ArchivedJobs;