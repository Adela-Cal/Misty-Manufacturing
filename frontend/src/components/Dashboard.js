import React, { useState, useEffect } from 'react';
import Layout from './Layout';
import { useAuth } from '../contexts/AuthContext';
import { apiHelpers, formatCurrency, formatDate, stageDisplayNames } from '../utils/api';
import { toast } from 'sonner';
import {
  ClipboardDocumentListIcon,
  UsersIcon,
  Cog8ToothIcon,
  ExclamationTriangleIcon,
  CalendarDaysIcon,
  ClockIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';

const Dashboard = () => {
  const { user, hasPermission } = useAuth();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    totalOrders: 0,
    totalClients: 0,
    overdueJobs: 0,
    jobsDueToday: 0,
    jobsDueThisWeek: 0,
    recentOrders: []
  });
  const [productionBoard, setProductionBoard] = useState({});
  const [modalOpen, setModalOpen] = useState(null);
  const [modalData, setModalData] = useState([]);
  const [modalLoading, setModalLoading] = useState(false);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      
      const [ordersRes, clientsRes, boardRes, reportsRes] = await Promise.all([
        apiHelpers.getOrders(),
        hasPermission('manage_clients') ? apiHelpers.getClients() : Promise.resolve({ data: [] }),
        hasPermission('update_production') ? apiHelpers.getProductionBoard() : Promise.resolve({ data: { data: {} } }),
        hasPermission('view_reports') ? apiHelpers.getOutstandingJobsReport() : Promise.resolve({ data: { data: {} } })
      ]);

      const orders = ordersRes.data;
      const clients = clientsRes.data;
      const board = boardRes.data?.data || {};
      const reports = reportsRes.data?.data || {};

      // Calculate recent orders (last 5)
      const recentOrders = orders.slice(0, 5);

      setStats({
        totalOrders: orders.length,
        totalClients: clients.length,
        overdueJobs: reports.overdue_jobs || 0,
        jobsDueToday: reports.jobs_due_today || 0,
        jobsDueThisWeek: reports.jobs_due_this_week || 0,
        recentOrders
      });

      setProductionBoard(board);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const handleCardDoubleClick = async (cardType) => {
    setModalOpen(cardType);
    setModalLoading(true);
    setModalData([]);
    
    try {
      let data = [];
      
      switch (cardType) {
        case 'totalOrders':
          const ordersRes = await apiHelpers.getOrders();
          data = ordersRes.data.map(order => ({
            id: order.id,
            orderNumber: order.order_number,
            clientName: order.client_name,
            dateCreated: formatDate(order.created_at),
            status: order.current_stage || 'N/A',
            dueDate: order.due_date ? formatDate(order.due_date) : 'N/A',
            totalAmount: formatCurrency(order.total_amount)
          }));
          break;
          
        case 'totalClients':
          const clientsRes = await apiHelpers.getClients();
          data = clientsRes.data.map(client => ({
            id: client.id,
            name: client.name,
            contactPerson: client.contact_person || 'N/A',
            email: client.email || 'N/A',
            phone: client.phone || 'N/A',
            totalOrders: stats.recentOrders.filter(o => o.client_name === client.name).length
          }));
          break;
          
        case 'overdueJobs':
          const boardRes = await apiHelpers.getProductionBoard();
          const board = boardRes.data?.data || {};
          data = [];
          Object.entries(board).forEach(([stage, jobs]) => {
            jobs.forEach(job => {
              if (job.is_overdue) {
                const dueDate = new Date(job.due_date);
                const today = new Date();
                const daysOverdue = Math.floor((today - dueDate) / (1000 * 60 * 60 * 24));
                data.push({
                  id: job.order_id,
                  jobNumber: job.order_number,
                  clientName: job.client_name,
                  dueDate: formatDate(job.due_date),
                  daysOverdue: daysOverdue,
                  status: stageDisplayNames[job.current_stage] || job.current_stage
                });
              }
            });
          });
          break;
          
        case 'dueToday':
          const boardTodayRes = await apiHelpers.getProductionBoard();
          const boardToday = boardTodayRes.data?.data || {};
          const today = new Date().toISOString().split('T')[0];
          data = [];
          Object.entries(boardToday).forEach(([stage, jobs]) => {
            jobs.forEach(job => {
              if (job.due_date && job.due_date.split('T')[0] === today) {
                data.push({
                  id: job.order_id,
                  jobNumber: job.order_number,
                  clientName: job.client_name,
                  jobType: stageDisplayNames[job.current_stage] || job.current_stage,
                  dueDate: formatDate(job.due_date),
                  status: stageDisplayNames[job.current_stage] || job.current_stage
                });
              }
            });
          });
          break;
          
        case 'dueThisWeek':
          const boardWeekRes = await apiHelpers.getProductionBoard();
          const boardWeek = boardWeekRes.data?.data || {};
          const todayDate = new Date();
          const weekFromNow = new Date(todayDate.getTime() + 7 * 24 * 60 * 60 * 1000);
          data = [];
          Object.entries(boardWeek).forEach(([stage, jobs]) => {
            jobs.forEach(job => {
              if (job.due_date) {
                const dueDate = new Date(job.due_date);
                if (dueDate >= todayDate && dueDate <= weekFromNow) {
                  const daysUntilDue = Math.ceil((dueDate - todayDate) / (1000 * 60 * 60 * 24));
                  data.push({
                    id: job.order_id,
                    jobNumber: job.order_number,
                    clientName: job.client_name,
                    jobType: stageDisplayNames[job.current_stage] || job.current_stage,
                    dueDate: formatDate(job.due_date),
                    daysUntilDue: daysUntilDue,
                    status: stageDisplayNames[job.current_stage] || job.current_stage
                  });
                }
              }
            });
          });
          break;
      }
      
      setModalData(data);
    } catch (error) {
      console.error('Failed to load modal data:', error);
      toast.error('Failed to load detailed information');
    } finally {
      setModalLoading(false);
    }
  };

  const StatCard = ({ title, value, icon: Icon, color, testId, cardType }) => (
    <div 
      className={`misty-card p-6 ${color} cursor-pointer hover:bg-gray-700 transition-colors duration-200`} 
      data-testid={testId}
      onDoubleClick={() => handleCardDoubleClick(cardType)}
    >
      <div className="flex items-center">
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-300">{title}</p>
          <p className="text-2xl font-bold text-white">{value}</p>
        </div>
        <Icon className="h-8 w-8 text-yellow-400" />
      </div>
    </div>
  );

  const ProductionStageCard = ({ stage, jobs, stageKey }) => {
    const stageColors = {
      order_entered: 'border-blue-500',
      pending_material: 'border-orange-500',
      paper_slitting: 'border-purple-500',
      winding: 'border-indigo-500',
      finishing: 'border-green-500',
      delivery: 'border-teal-500',
      invoicing: 'border-yellow-500'
    };

    return (
      <div className={`misty-card p-4 border-l-4 ${stageColors[stageKey] || 'border-gray-500'}`}>
        <h4 className="font-medium text-gray-200 mb-2">{stage}</h4>
        <p className="text-2xl font-bold text-white">{jobs.length}</p>
        {jobs.length > 0 && (
          <p className="text-xs text-gray-400 mt-1">
            {jobs.filter(job => job.is_overdue).length} overdue
          </p>
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <Layout>
        <div className="p-8">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-700 rounded w-1/4 mb-8"></div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="h-24 bg-gray-700 rounded"></div>
              ))}
            </div>
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
      <div className="p-8" data-testid="dashboard">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">
            Welcome back, {user?.full_name}
          </h1>
          <p className="text-gray-400">
            Here's what's happening with your manufacturing operations today.
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-8">
          <StatCard
            title="Total Orders"
            value={stats.totalOrders}
            icon={ClipboardDocumentListIcon}
            color=""
            testId="total-orders-card"
          />
          
          {hasPermission('manage_clients') && (
            <StatCard
              title="Total Clients"
              value={stats.totalClients}
              icon={UsersIcon}
              color=""
              testId="total-clients-card"
            />
          )}
          
          <StatCard
            title="Overdue Jobs"
            value={stats.overdueJobs}
            icon={ExclamationTriangleIcon}
            color={stats.overdueJobs > 0 ? "border-l-4 border-red-500" : ""}
            testId="overdue-jobs-card"
          />
          
          <StatCard
            title="Due Today"
            value={stats.jobsDueToday}
            icon={CalendarDaysIcon}
            color={stats.jobsDueToday > 0 ? "border-l-4 border-yellow-500" : ""}
            testId="due-today-card"
          />
          
          <StatCard
            title="Due This Week"
            value={stats.jobsDueThisWeek}
            icon={ClockIcon}
            color=""
            testId="due-week-card"
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Production Overview */}
          {hasPermission('update_production') && (
            <div className="misty-card p-6">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
                <Cog8ToothIcon className="h-5 w-5 mr-2 text-yellow-400" />
                Production Overview
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {Object.entries(productionBoard).map(([stageKey, jobs]) => (
                  <ProductionStageCard
                    key={stageKey}
                    stage={stageDisplayNames[stageKey] || stageKey}
                    jobs={jobs}
                    stageKey={stageKey}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Recent Orders */}
          <div className="misty-card p-6">
            <h3 className="text-lg font-semibold text-white mb-4">
              Recent Orders
            </h3>
            {stats.recentOrders.length > 0 ? (
              <div className="space-y-3">
                {stats.recentOrders.map((order) => (
                  <div key={order.id} className="flex items-center justify-between p-3 bg-gray-700 rounded-lg">
                    <div className="flex-1">
                      <p className="font-medium text-white">{order.order_number}</p>
                      <p className="text-sm text-gray-400">{order.client_name}</p>
                    </div>
                    <div className="text-right">
                      <p className="font-medium text-yellow-400">
                        {formatCurrency(order.total_amount)}
                      </p>
                      <p className="text-xs text-gray-400">
                        {formatDate(order.created_at)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-400 text-center py-8">No recent orders</p>
            )}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="mt-8">
          <h3 className="text-lg font-semibold text-white mb-4">Quick Actions</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {hasPermission('create_orders') && (
              <button className="misty-card p-4 hover:bg-gray-700 transition-colors duration-200 text-left">
                <h4 className="font-medium text-white mb-2">Create New Order</h4>
                <p className="text-sm text-gray-400">Start a new manufacturing order</p>
              </button>
            )}
            
            {hasPermission('manage_clients') && (
              <button className="misty-card p-4 hover:bg-gray-700 transition-colors duration-200 text-left">
                <h4 className="font-medium text-white mb-2">Add New Client</h4>
                <p className="text-sm text-gray-400">Register a new customer</p>
              </button>
            )}
            
            {hasPermission('view_reports') && (
              <button className="misty-card p-4 hover:bg-gray-700 transition-colors duration-200 text-left">
                <h4 className="font-medium text-white mb-2">View Reports</h4>
                <p className="text-sm text-gray-400">Access performance analytics</p>
              </button>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default Dashboard;