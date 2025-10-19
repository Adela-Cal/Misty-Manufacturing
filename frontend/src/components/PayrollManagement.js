import React, { useState, useEffect } from 'react';
import Layout from './Layout';
import TimesheetEntry from './TimesheetEntry';
import { useAuth } from '../contexts/AuthContext';
import { apiHelpers, formatCurrency, formatDate } from '../utils/api';
import { toast } from 'sonner';
import {
  UserPlusIcon,
  ClockIcon,
  CalendarDaysIcon,
  BanknotesIcon,
  DocumentChartBarIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  TrashIcon,
  ArchiveBoxIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';

const PayrollManagement = () => {
  const { user, hasPermission } = useAuth();
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [employees, setEmployees] = useState([]);
  const [archivedEmployees, setArchivedEmployees] = useState([]);
  const [pendingTimesheets, setPendingTimesheets] = useState([]);
  const [pendingLeaveRequests, setPendingLeaveRequests] = useState([]);
  const [allLeaveRequests, setAllLeaveRequests] = useState([]);
  const [timesheetReminder, setTimesheetReminder] = useState(null);
  const [showEmployeeModal, setShowEmployeeModal] = useState(false);
  const [showTimesheetModal, setShowTimesheetModal] = useState(false);
  const [showLeaveRequestModal, setShowLeaveRequestModal] = useState(false);
  const [selectedEmployee, setSelectedEmployee] = useState(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [employeeToDelete, setEmployeeToDelete] = useState(null);
  const [showPermanentDeleteConfirm, setShowPermanentDeleteConfirm] = useState(false);
  const [employeeToPermanentlyDelete, setEmployeeToPermanentlyDelete] = useState(null);
  const [leaveFormData, setLeaveFormData] = useState({
    employee_id: '',
    leave_type: 'annual_leave',
    start_date: '',
    end_date: '',
    hours_requested: '',
    reason: '',
    approver_id: ''
  });

  useEffect(() => {
    loadPayrollData();
  }, []);

  const loadPayrollData = async () => {
    try {
      setLoading(true);
      
      const [employeesRes, pendingTimesheetsRes, pendingLeaveRes, reminderRes] = await Promise.all([
        hasPermission('manage_payroll') ? fetch('/api/payroll/employees', {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
        }) : Promise.resolve({ json: () => [] }),
        hasPermission('manage_payroll') ? fetch('/api/payroll/timesheets/pending', {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
        }) : Promise.resolve({ json: () => ({ data: [] }) }),
        hasPermission('manage_payroll') ? fetch('/api/payroll/leave-requests/pending', {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
        }) : Promise.resolve({ json: () => ({ data: [] }) }),
        fetch('/api/payroll/dashboard/timesheet-reminder', {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
        })
      ]);

      const employeesData = await employeesRes.json();
      const timesheetsData = await pendingTimesheetsRes.json();
      const leaveData = await pendingLeaveRes.json();
      const reminderData = await reminderRes.json();

      setEmployees(Array.isArray(employeesData) ? employeesData : []);
      setPendingTimesheets(timesheetsData.data || []);
      setPendingLeaveRequests(leaveData.data || []);
      setTimesheetReminder(reminderData.data);
      
    } catch (error) {
      console.error('Failed to load payroll data:', error);
      toast.error('Failed to load payroll data');
    } finally {
      setLoading(false);
    }
  };

  const loadArchivedEmployees = async () => {
    try {
      const response = await fetch('/api/payroll/employees/archived/list', {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setArchivedEmployees(Array.isArray(data) ? data : []);
      } else {
        toast.error('Failed to load archived employees');
      }
    } catch (error) {
      console.error('Failed to load archived employees:', error);
      toast.error('Failed to load archived employees');
    }
  };

  const handleEmployeeDelete = (employee) => {
    setEmployeeToDelete(employee);
    setShowDeleteConfirm(true);
  };

  const confirmDelete = async () => {
    if (!employeeToDelete) return;
    
    try {
      const response = await fetch(`/api/payroll/employees/${employeeToDelete.id}`, {
        method: 'DELETE',
        headers: { 
          Authorization: `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        toast.success('Employee archived successfully. Data preserved for historic review.');
        loadPayrollData();
        setShowDeleteConfirm(false);
        setEmployeeToDelete(null);
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to archive employee');
      }
    } catch (error) {
      console.error('Failed to archive employee:', error);
      toast.error('Failed to archive employee');
    }
  };

  const handleRestoreEmployee = async (employee) => {
    try {
      const response = await fetch(`/api/payroll/employees/${employee.id}/restore`, {
        method: 'POST',
        headers: { 
          Authorization: `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        toast.success('Employee restored successfully');
        loadArchivedEmployees();
        loadPayrollData();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to restore employee');
      }
    } catch (error) {
      console.error('Failed to restore employee:', error);
      toast.error('Failed to restore employee');
    }
  };

  const handlePermanentDelete = (employee) => {
    setEmployeeToPermanentlyDelete(employee);
    setShowPermanentDeleteConfirm(true);
  };

  const confirmPermanentDelete = async () => {
    if (!employeeToPermanentlyDelete) return;
    
    try {
      const response = await fetch(`/api/payroll/employees/${employeeToPermanentlyDelete.id}/permanent`, {
        method: 'DELETE',
        headers: { 
          Authorization: `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        toast.success('Employee and all associated data permanently deleted');
        loadArchivedEmployees();
        setShowPermanentDeleteConfirm(false);
        setEmployeeToPermanentlyDelete(null);
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to permanently delete employee');
      }
    } catch (error) {
      console.error('Failed to permanently delete employee:', error);
      toast.error('Failed to permanently delete employee');
    }
  };

  const loadAllLeaveRequests = async () => {
    try {
      const response = await fetch('/api/payroll/leave-requests/pending', {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setAllLeaveRequests(data.data || []);
      }
    } catch (error) {
      console.error('Failed to load leave requests:', error);
    }
  };

  const handleAddLeaveRequest = () => {
    setLeaveFormData({
      employee_id: '',
      leave_type: 'annual_leave',
      start_date: '',
      end_date: '',
      hours_requested: '',
      reason: '',
      approver_id: ''
    });
    setShowLeaveRequestModal(true);
  };

  const handleLeaveFormSubmit = async (e) => {
    e.preventDefault();
    
    try {
      const response = await fetch('/api/payroll/leave-requests', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(leaveFormData)
      });

      if (response.ok) {
        toast.success('Leave request created successfully');
        setShowLeaveRequestModal(false);
        loadAllLeaveRequests();
        loadPayrollData();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to create leave request');
      }
    } catch (error) {
      console.error('Failed to create leave request:', error);
      toast.error('Failed to create leave request');
    }
  };

  const handleApproveLeave = async (requestId) => {
    try {
      const response = await fetch(`/api/payroll/leave-requests/${requestId}/approve`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        toast.success('Leave request approved');
        loadAllLeaveRequests();
        loadPayrollData();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to approve leave request');
      }
    } catch (error) {
      console.error('Failed to approve leave request:', error);
      toast.error('Failed to approve leave request');
    }
  };

  const handleRejectLeave = async (requestId, reason) => {
    try {
      const response = await fetch(`/api/payroll/leave-requests/${requestId}/reject?rejection_reason=${encodeURIComponent(reason)}`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        toast.success('Leave request rejected');
        loadAllLeaveRequests();
        loadPayrollData();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to reject leave request');
      }
    } catch (error) {
      console.error('Failed to reject leave request:', error);
      toast.error('Failed to reject leave request');
    }
  };

  const handleEmployeeCreate = () => {
    setSelectedEmployee(null);
    setShowEmployeeModal(true);
  };

  const handleEmployeeEdit = (employee) => {
    setSelectedEmployee(employee);
    setShowEmployeeModal(true);
  };

  const handleTimesheetView = (employee) => {
    setSelectedEmployee(employee);
    setShowTimesheetModal(true);
  };

  const StatCard = ({ title, value, icon: Icon, color, action, testId }) => (
    <div 
      className={`misty-card p-6 ${color} ${
        action ? 'cursor-pointer hover:bg-gray-700 transition-colors duration-200' : ''
      }`}
      onClick={action}
      data-testid={testId}
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

  const TabButton = ({ id, label, isActive, onClick }) => (
    <button
      onClick={() => onClick(id)}
      className={`px-4 py-2 font-medium rounded-md transition-colors duration-200 ${
        isActive 
          ? 'bg-yellow-400 text-gray-900' 
          : 'text-gray-300 hover:text-yellow-400 hover:bg-gray-700'
      }`}
      data-testid={`tab-${id}`}
    >
      {label}
    </button>
  );

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
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="p-8" data-testid="payroll-management">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">
            Payroll & Leave Management
          </h1>
          <p className="text-gray-400">
            Manage employee timesheets, leave requests, and payroll processing
          </p>
        </div>

        {/* Timesheet Reminder */}
        {timesheetReminder?.show_reminder && (
          <div className="mb-8 p-4 bg-yellow-900 border border-yellow-700 rounded-lg flex items-center">
            <ExclamationTriangleIcon className="h-6 w-6 text-yellow-400 mr-3" />
            <div>
              <p className="text-yellow-100 font-medium">Timesheet Reminder</p>
              <p className="text-yellow-200 text-sm">{timesheetReminder.message}</p>
            </div>
          </div>
        )}

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard
            title="Total Employees"
            value={employees.length}
            icon={UserPlusIcon}
            color=""
            testId="total-employees-card"
          />
          
          <StatCard
            title="Pending Timesheets"
            value={pendingTimesheets.length}
            icon={ClockIcon}
            color={pendingTimesheets.length > 0 ? "border-l-4 border-orange-500" : ""}
            action={() => setActiveTab('timesheets')}
            testId="pending-timesheets-card"
          />
          
          <StatCard
            title="Leave Requests"
            value={pendingLeaveRequests.length}
            icon={CalendarDaysIcon}
            color={pendingLeaveRequests.length > 0 ? "border-l-4 border-blue-500" : ""}
            action={() => setActiveTab('leave')}
            testId="leave-requests-card"
          />
          
          <StatCard
            title="Payroll Reports"
            value="View"
            icon={DocumentChartBarIcon}
            color=""
            action={() => setActiveTab('reports')}
            testId="payroll-reports-card"
          />
        </div>

        {/* Tab Navigation */}
        <div className="mb-8">
          <div className="flex space-x-2">
            <TabButton 
              id="overview" 
              label="Overview" 
              isActive={activeTab === 'overview'} 
              onClick={setActiveTab} 
            />
            {hasPermission('manage_payroll') && (
              <>
                <TabButton 
                  id="employees" 
                  label="Employees" 
                  isActive={activeTab === 'employees'} 
                  onClick={setActiveTab} 
                />
                <TabButton 
                  id="archived" 
                  label="Archived Staff" 
                  isActive={activeTab === 'archived'} 
                  onClick={(id) => {
                    setActiveTab(id);
                    loadArchivedEmployees();
                  }} 
                />
                <TabButton 
                  id="timesheets" 
                  label="Timesheets" 
                  isActive={activeTab === 'timesheets'} 
                  onClick={setActiveTab} 
                />
                <TabButton 
                  id="leave" 
                  label="Leave Requests" 
                  isActive={activeTab === 'leave'} 
                  onClick={setActiveTab} 
                />
                <TabButton 
                  id="reports" 
                  label="Reports" 
                  isActive={activeTab === 'reports'} 
                  onClick={setActiveTab} 
                />
              </>
            )}
            <TabButton 
              id="my-timesheet" 
              label="My Timesheet" 
              isActive={activeTab === 'my-timesheet'} 
              onClick={setActiveTab} 
            />
          </div>
        </div>

        {/* Tab Content */}
        <div className="animate-fadeIn">
          {activeTab === 'overview' && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Recent Activity */}
              <div className="misty-card p-6">
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
                  <ClockIcon className="h-5 w-5 mr-2 text-yellow-400" />
                  Recent Timesheet Activity
                </h3>
                {pendingTimesheets.length > 0 ? (
                  <div className="space-y-3">
                    {pendingTimesheets.slice(0, 5).map((timesheet) => (
                      <div key={timesheet.id} className="flex items-center justify-between p-3 bg-gray-700 rounded-lg">
                        <div>
                          <p className="font-medium text-white">{timesheet.employee_name}</p>
                          <p className="text-sm text-gray-400">
                            Week {formatDate(timesheet.week_starting)} - {formatDate(timesheet.week_ending)}
                          </p>
                        </div>
                        <span className="bg-orange-600 text-white text-xs px-2 py-1 rounded">
                          Pending
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-400 text-center py-8">No pending timesheets</p>
                )}
              </div>

              {/* Leave Requests */}
              <div className="misty-card p-6">
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
                  <CalendarDaysIcon className="h-5 w-5 mr-2 text-yellow-400" />
                  Pending Leave Requests
                </h3>
                {pendingLeaveRequests.length > 0 ? (
                  <div className="space-y-3">
                    {pendingLeaveRequests.slice(0, 5).map((request) => (
                      <div key={request.id} className="flex items-center justify-between p-3 bg-gray-700 rounded-lg">
                        <div>
                          <p className="font-medium text-white">{request.employee_name}</p>
                          <p className="text-sm text-gray-400">
                            {request.leave_type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                          </p>
                          <p className="text-xs text-gray-500">
                            {formatDate(request.start_date)} - {formatDate(request.end_date)}
                          </p>
                        </div>
                        <span className="bg-blue-600 text-white text-xs px-2 py-1 rounded">
                          {request.hours_requested}h
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-400 text-center py-8">No pending leave requests</p>
                )}
              </div>
            </div>
          )}

          {activeTab === 'employees' && hasPermission('manage_payroll') && (
            <div>
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-semibold text-white">Employee Management</h3>
                <button
                  onClick={handleEmployeeCreate}
                  className="misty-button misty-button-primary flex items-center"
                  data-testid="add-employee-button"
                >
                  <UserPlusIcon className="h-5 w-5 mr-2" />
                  Add Employee
                </button>
              </div>

              {employees.length > 0 ? (
                <div className="misty-table">
                  <table className="w-full">
                    <thead>
                      <tr>
                        <th>Employee</th>
                        <th>Position</th>
                        <th>Department</th>
                        <th>Hourly Rate</th>
                        <th>Employment Type</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {employees.map((employee) => (
                        <tr key={employee.id} data-testid={`employee-row-${employee.id}`}>
                          <td>
                            <div>
                              <p className="font-medium">{employee.first_name} {employee.last_name}</p>
                              <p className="text-sm text-gray-400">{employee.employee_number}</p>
                            </div>
                          </td>
                          <td>{employee.position}</td>
                          <td>{employee.department || 'N/A'}</td>
                          <td className="font-medium text-yellow-400">
                            {formatCurrency(employee.hourly_rate)}/hr
                          </td>
                          <td>
                            <span className="text-sm bg-gray-600 px-2 py-1 rounded capitalize">
                              {employee.employment_type.replace('_', ' ')}
                            </span>
                          </td>
                          <td>
                            <div className="flex items-center space-x-2">
                              <button
                                onClick={() => handleEmployeeDelete(employee)}
                                className="text-gray-400 hover:text-red-400 transition-colors flex items-center"
                                data-testid={`delete-employee-${employee.id}`}
                              >
                                <TrashIcon className="h-4 w-4 mr-1" />
                                Delete
                              </button>
                              <button
                                onClick={() => handleTimesheetView(employee)}
                                className="text-gray-400 hover:text-blue-400 transition-colors"
                                data-testid={`view-timesheet-${employee.id}`}
                              >
                                Timesheet
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
                  <UserPlusIcon className="mx-auto h-12 w-12 text-gray-400" />
                  <h3 className="mt-2 text-sm font-medium text-gray-300">No employees</h3>
                  <p className="mt-1 text-sm text-gray-400">Get started by adding your first employee.</p>
                  <div className="mt-6">
                    <button
                      onClick={handleEmployeeCreate}
                      className="misty-button misty-button-primary"
                    >
                      <UserPlusIcon className="h-5 w-5 mr-2" />
                      Add Employee
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'archived' && hasPermission('manage_payroll') && (
            <div>
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className="text-xl font-semibold text-white flex items-center">
                    <ArchiveBoxIcon className="h-6 w-6 mr-2 text-gray-400" />
                    Archived Staff
                  </h3>
                  <p className="text-sm text-gray-400 mt-1">
                    View and restore archived employees. All historic data is preserved.
                  </p>
                </div>
              </div>

              {archivedEmployees.length > 0 ? (
                <div className="misty-table">
                  <table className="w-full">
                    <thead>
                      <tr>
                        <th>Employee</th>
                        <th>Position</th>
                        <th>Department</th>
                        <th>Hourly Rate</th>
                        <th>Employment Type</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {archivedEmployees.map((employee) => (
                        <tr key={employee.id} className="opacity-75">
                          <td>
                            <div>
                              <p className="font-medium">{employee.first_name} {employee.last_name}</p>
                              <p className="text-sm text-gray-400">{employee.employee_number}</p>
                            </div>
                          </td>
                          <td>{employee.position}</td>
                          <td>{employee.department || 'N/A'}</td>
                          <td className="font-medium text-yellow-400">
                            {formatCurrency(employee.hourly_rate)}/hr
                          </td>
                          <td>
                            <span className="text-sm bg-gray-600 px-2 py-1 rounded capitalize">
                              {employee.employment_type.replace('_', ' ')}
                            </span>
                          </td>
                          <td>
                            <div className="flex items-center space-x-2">
                              <button
                                onClick={() => handleRestoreEmployee(employee)}
                                className="text-gray-400 hover:text-green-400 transition-colors flex items-center"
                              >
                                <ArrowPathIcon className="h-4 w-4 mr-1" />
                                Restore
                              </button>
                              <button
                                onClick={() => handleTimesheetView(employee)}
                                className="text-gray-400 hover:text-blue-400 transition-colors"
                              >
                                View History
                              </button>
                              <button
                                onClick={() => handlePermanentDelete(employee)}
                                className="text-gray-400 hover:text-red-500 transition-colors flex items-center"
                              >
                                <TrashIcon className="h-4 w-4 mr-1" />
                                Delete Forever
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="text-center py-12 bg-gray-800 rounded-lg">
                  <ArchiveBoxIcon className="mx-auto h-12 w-12 text-gray-400" />
                  <h3 className="mt-2 text-sm font-medium text-gray-300">No archived employees</h3>
                  <p className="mt-1 text-sm text-gray-400">
                    Archived staff members will appear here with their historic data preserved.
                  </p>
                </div>
              )}
            </div>
          )}

          {activeTab === 'my-timesheet' && (
            <div className="misty-card p-6">
              <h3 className="text-xl font-semibold text-white mb-4">My Timesheet</h3>
              <p className="text-gray-400 mb-4">Submit your weekly timesheet here</p>
              
              <div className="text-center py-8">
                <ClockIcon className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                <p className="text-white text-lg font-medium mb-2">My Timesheet</p>
                <p className="text-gray-400 mb-6">Track your work hours and manage leave requests</p>
                <button 
                  className="misty-button misty-button-primary"
                  onClick={() => setShowTimesheetModal(true)}
                >
                  Open Current Week Timesheet
                </button>
              </div>
            </div>
          )}

          {activeTab === 'timesheets' && hasPermission('manage_payroll') && (
            <div className="misty-card p-6">
              <h3 className="text-xl font-semibold text-white mb-4">Pending Timesheets</h3>
              <p className="text-gray-400 mb-4">Review and approve employee timesheets</p>
              
              <div className="text-center py-8">
                <CheckCircleIcon className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                <p className="text-gray-400">Timesheet approval interface will be implemented here</p>
              </div>
            </div>
          )}

          {activeTab === 'leave' && hasPermission('manage_payroll') && (
            <div>
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className="text-xl font-semibold text-white flex items-center">
                    <CalendarDaysIcon className="h-6 w-6 mr-2 text-yellow-400" />
                    Leave Requests Management
                  </h3>
                  <p className="text-sm text-gray-400 mt-1">
                    Create and manage employee leave requests
                  </p>
                </div>
                <button
                  onClick={() => {
                    loadAllLeaveRequests();
                    handleAddLeaveRequest();
                  }}
                  className="misty-button misty-button-primary flex items-center"
                >
                  <UserPlusIcon className="h-4 w-4 mr-2" />
                  Add Leave Request
                </button>
              </div>

              {allLeaveRequests.length > 0 ? (
                <div className="misty-table">
                  <table className="w-full">
                    <thead>
                      <tr>
                        <th>Employee</th>
                        <th>Leave Type</th>
                        <th>Dates</th>
                        <th>Hours</th>
                        <th>Reason</th>
                        <th>Status</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {allLeaveRequests.map((request) => (
                        <tr key={request.id}>
                          <td>
                            <p className="font-medium">{request.employee_name}</p>
                          </td>
                          <td>
                            <span className="text-sm bg-blue-900 px-2 py-1 rounded capitalize">
                              {request.leave_type.replace('_', ' ')}
                            </span>
                          </td>
                          <td className="text-sm">
                            <p>{new Date(request.start_date).toLocaleDateString()}</p>
                            <p className="text-gray-400">to {new Date(request.end_date).toLocaleDateString()}</p>
                          </td>
                          <td className="font-medium text-yellow-400">
                            {request.hours_requested}h
                          </td>
                          <td className="text-sm text-gray-400">
                            {request.reason || 'No reason provided'}
                          </td>
                          <td>
                            <span className={`text-sm px-2 py-1 rounded ${
                              request.status === 'pending' ? 'bg-yellow-900 text-yellow-200' :
                              request.status === 'approved' ? 'bg-green-900 text-green-200' :
                              'bg-red-900 text-red-200'
                            }`}>
                              {request.status}
                            </span>
                          </td>
                          <td>
                            {request.status === 'pending' && (
                              <div className="flex items-center space-x-2">
                                <button
                                  onClick={() => handleApproveLeave(request.id)}
                                  className="text-green-400 hover:text-green-300 transition-colors text-sm"
                                >
                                  Approve
                                </button>
                                <button
                                  onClick={() => {
                                    const reason = prompt('Reason for rejection:');
                                    if (reason) handleRejectLeave(request.id, reason);
                                  }}
                                  className="text-red-400 hover:text-red-300 transition-colors text-sm"
                                >
                                  Reject
                                </button>
                              </div>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="text-center py-12 bg-gray-800 rounded-lg">
                  <CalendarDaysIcon className="mx-auto h-12 w-12 text-gray-400" />
                  <h3 className="mt-2 text-sm font-medium text-gray-300">No leave requests</h3>
                  <p className="mt-1 text-sm text-gray-400">
                    Click "Add Leave Request" to create a new leave request for an employee.
                  </p>
                </div>
              )}
            </div>
          )}

          {activeTab === 'reports' && hasPermission('manage_payroll') && (
            <div className="misty-card p-6">
              <h3 className="text-xl font-semibold text-white mb-4">Payroll Reports</h3>
              <p className="text-gray-400 mb-4">Generate payroll summaries and leave balance reports</p>
              
              <div className="text-center py-8">
                <BanknotesIcon className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                <p className="text-gray-400">Payroll reporting interface will be implemented here</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Employee Modal Placeholder */}
      {showEmployeeModal && (
        <div className="modal-overlay">
          <div className="modal-content max-w-4xl">
            <div className="p-6">
              <h2 className="text-xl font-bold text-white mb-4">
                {selectedEmployee ? 'Edit Employee' : 'Add New Employee'}
              </h2>
              <p className="text-gray-400 mb-4">Employee form will be implemented here</p>
              <div className="flex justify-end space-x-3">
                <button
                  onClick={() => setShowEmployeeModal(false)}
                  className="misty-button misty-button-secondary"
                >
                  Cancel
                </button>
                <button className="misty-button misty-button-primary">
                  {selectedEmployee ? 'Update' : 'Create'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Timesheet Modal */}
      {showTimesheetModal && (
        <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && setShowTimesheetModal(false)}>
          <div className="modal-content max-w-6xl max-h-[90vh] overflow-y-auto">
            <TimesheetEntry
              employeeId={selectedEmployee?.id || user?.id || user?.user_id || user?.sub}
              onClose={() => setShowTimesheetModal(false)}
              isManager={user?.role === 'admin' || user?.role === 'manager'}
            />
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && setShowDeleteConfirm(false)}>
          <div className="modal-content max-w-md">
            <div className="p-6">
              <div className="flex items-center mb-4">
                <div className="flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-red-900 bg-opacity-30">
                  <TrashIcon className="h-6 w-6 text-red-400" />
                </div>
                <div className="ml-4">
                  <h3 className="text-lg font-medium text-white">Archive Employee</h3>
                  <p className="text-sm text-gray-400">This action can be reversed</p>
                </div>
              </div>
              
              <div className="mb-6">
                <p className="text-gray-300 mb-2">
                  Are you sure you want to archive <span className="font-semibold text-white">
                    {employeeToDelete?.first_name} {employeeToDelete?.last_name}
                  </span>?
                </p>
                <div className="bg-blue-900 bg-opacity-30 border border-blue-500 border-opacity-30 rounded-lg p-3 mt-3">
                  <p className="text-sm text-blue-200">
                    <CheckCircleIcon className="h-4 w-4 inline mr-1" />
                    All historic data will be preserved including:
                  </p>
                  <ul className="text-xs text-blue-300 mt-2 ml-6 space-y-1">
                    <li>• Timesheets and attendance records</li>
                    <li>• Leave requests and balances</li>
                    <li>• Payroll history</li>
                    <li>• Employment details</li>
                  </ul>
                  <p className="text-xs text-blue-300 mt-2">
                    You can restore this employee from the "Archived Staff" tab at any time.
                  </p>
                </div>
              </div>

              <div className="flex justify-end space-x-3">
                <button
                  onClick={() => {
                    setShowDeleteConfirm(false);
                    setEmployeeToDelete(null);
                  }}
                  className="misty-button misty-button-secondary"
                >
                  Cancel
                </button>
                <button
                  onClick={confirmDelete}
                  className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors duration-200 flex items-center"
                >
                  <TrashIcon className="h-4 w-4 mr-2" />
                  Archive Employee
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Permanent Delete Confirmation Modal */}
      {showPermanentDeleteConfirm && (
        <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && setShowPermanentDeleteConfirm(false)}>
          <div className="modal-content max-w-md">
            <div className="p-6">
              <div className="flex items-center mb-4">
                <div className="flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-red-900">
                  <ExclamationTriangleIcon className="h-7 w-7 text-red-300" />
                </div>
                <div className="ml-4">
                  <h3 className="text-lg font-medium text-white">Permanent Delete</h3>
                  <p className="text-sm text-red-400 font-semibold">This action CANNOT be reversed!</p>
                </div>
              </div>
              
              <div className="mb-6">
                <p className="text-gray-300 mb-3">
                  Are you absolutely sure you want to <span className="text-red-400 font-semibold">permanently delete</span> all data for{' '}
                  <span className="font-semibold text-white">
                    {employeeToPermanentlyDelete?.first_name} {employeeToPermanentlyDelete?.last_name}
                  </span>?
                </p>
                
                <div className="bg-red-900 bg-opacity-30 border border-red-500 rounded-lg p-4 mb-3">
                  <p className="text-sm text-red-200 font-semibold mb-2 flex items-center">
                    <ExclamationTriangleIcon className="h-5 w-5 inline mr-2" />
                    WARNING: All data will be permanently deleted:
                  </p>
                  <ul className="text-xs text-red-300 ml-6 space-y-1">
                    <li>• Employee profile and personal information</li>
                    <li>• All timesheets and attendance records</li>
                    <li>• All leave requests and history</li>
                    <li>• Complete payroll history</li>
                    <li>• All employment records</li>
                  </ul>
                </div>

                <div className="bg-gray-800 border border-gray-600 rounded-lg p-3">
                  <p className="text-xs text-gray-300">
                    <strong className="text-white">Note:</strong> This action should only be used for compliance reasons 
                    or when absolutely certain data should not be retained. Consider archiving instead if you may 
                    need this information in the future.
                  </p>
                </div>
              </div>

              <div className="flex justify-end space-x-3">
                <button
                  onClick={() => {
                    setShowPermanentDeleteConfirm(false);
                    setEmployeeToPermanentlyDelete(null);
                  }}
                  className="misty-button misty-button-secondary"
                >
                  Cancel
                </button>
                <button
                  onClick={confirmPermanentDelete}
                  className="px-4 py-2 bg-red-700 text-white rounded-md hover:bg-red-800 transition-colors duration-200 flex items-center font-semibold"
                >
                  <TrashIcon className="h-4 w-4 mr-2" />
                  Delete Permanently
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </Layout>
  );
};

export default PayrollManagement;