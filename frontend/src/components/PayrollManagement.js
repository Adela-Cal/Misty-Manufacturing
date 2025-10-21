import React, { useState, useEffect } from 'react';
import Layout from './Layout';
import TimesheetEntry from './TimesheetEntry';
import PayrollReports from './PayrollReports';
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
  ArrowPathIcon,
  BuildingLibraryIcon,
  EyeIcon
} from '@heroicons/react/24/outline';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';

const PayrollManagement = () => {
  const { user, hasPermission } = useAuth();
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [employees, setEmployees] = useState([]);
  const [archivedEmployees, setArchivedEmployees] = useState([]);
  const [pendingTimesheets, setPendingTimesheets] = useState([]);
  const [pendingLeaveRequests, setPendingLeaveRequests] = useState([]);
  const [allLeaveRequests, setAllLeaveRequests] = useState([]);
  const [archivedLeaveRequests, setArchivedLeaveRequests] = useState([]);
  const [leaveCalendarEvents, setLeaveCalendarEvents] = useState([]);
  const [leaveReminders, setLeaveReminders] = useState([]);
  const [showArchivedLeave, setShowArchivedLeave] = useState(false);
  const [showLeaveCalendar, setShowLeaveCalendar] = useState(false);
  const [timesheetReminder, setTimesheetReminder] = useState(null);
  const [showEmployeeModal, setShowEmployeeModal] = useState(false);
  const [showTimesheetModal, setShowTimesheetModal] = useState(false);
  const [showLeaveRequestModal, setShowLeaveRequestModal] = useState(false);
  const [selectedEmployee, setSelectedEmployee] = useState(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [employeeToDelete, setEmployeeToDelete] = useState(null);
  const [showPermanentDeleteConfirm, setShowPermanentDeleteConfirm] = useState(false);
  const [employeeToPermanentlyDelete, setEmployeeToPermanentlyDelete] = useState(null);
  const [showBankDetailsModal, setShowBankDetailsModal] = useState(false);
  const [approvingTimesheet, setApprovingTimesheet] = useState(null);
  const [bankDetailsFormData, setBankDetailsFormData] = useState({
    bank_account_bsb: '',
    bank_account_number: '',
    tax_file_number: '',
    superannuation_fund: ''
  });
  const [leaveFormData, setLeaveFormData] = useState({
    employee_id: '',
    leave_type: 'annual_leave',
    start_date: '',
    end_date: '',
    hours_requested: '',
    reason: '',
    approver_id: ''
  });

  // Calculate business days between two dates (excluding weekends)
  const calculateBusinessDays = (startDate, endDate) => {
    if (!startDate || !endDate) return 0;
    
    const start = new Date(startDate);
    const end = new Date(endDate);
    
    if (end < start) return 0;
    
    let businessDays = 0;
    const currentDate = new Date(start);
    
    while (currentDate <= end) {
      const dayOfWeek = currentDate.getDay();
      // 0 = Sunday, 6 = Saturday
      if (dayOfWeek !== 0 && dayOfWeek !== 6) {
        businessDays++;
      }
      currentDate.setDate(currentDate.getDate() + 1);
    }
    
    return businessDays;
  };

  // Auto-calculate hours when dates change
  const handleDateChange = (field, value) => {
    const newFormData = { ...leaveFormData, [field]: value };
    
    // If both dates are set, calculate hours
    if (newFormData.start_date && newFormData.end_date) {
      const businessDays = calculateBusinessDays(newFormData.start_date, newFormData.end_date);
      // Assuming 8 hours per work day
      const calculatedHours = businessDays * 8;
      newFormData.hours_requested = calculatedHours.toString();
    }
    
    setLeaveFormData(newFormData);
  };

  useEffect(() => {
    loadPayrollData();
    loadLeaveReminders(); // Load leave reminders on mount (for login notifications)
  }, []);

  const loadPayrollData = async () => {
    try {
      setLoading(true);
      
      const [employeesRes, pendingTimesheetsRes, pendingLeaveRes, reminderRes] = await Promise.all([
        hasPermission('manage_payroll') ? fetch(`${BACKEND_URL}/api/payroll/employees`, {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
        }) : Promise.resolve({ json: () => [] }),
        hasPermission('manage_payroll') ? fetch(`${BACKEND_URL}/api/payroll/timesheets/pending`, {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
        }) : Promise.resolve({ json: () => ({ data: [] }) }),
        hasPermission('manage_payroll') ? fetch(`${BACKEND_URL}/api/payroll/leave-requests/pending`, {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
        }) : Promise.resolve({ json: () => ({ data: [] }) }),
        fetch(`${BACKEND_URL}/api/payroll/dashboard/timesheet-reminder`, {
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

  const loadArchivedLeaveRequests = async () => {
    try {
      const response = await fetch('/api/payroll/leave-requests/archived', {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setArchivedLeaveRequests(data.data || []);
      }
    } catch (error) {
      console.error('Failed to load archived leave requests:', error);
    }
  };

  const loadLeaveCalendar = async () => {
    try {
      const response = await fetch('/api/payroll/leave-requests/calendar', {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setLeaveCalendarEvents(data.data || []);
      }
    } catch (error) {
      console.error('Failed to load leave calendar:', error);
      toast.error('Failed to load leave calendar');
    }
  };

  const loadLeaveReminders = async () => {
    try {
      const response = await fetch('/api/payroll/leave-requests/reminders', {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setLeaveReminders(data.data || []);
      }
    } catch (error) {
      console.error('Failed to load leave reminders:', error);
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
      // Prepare data with proper type conversions
      const submitData = {
        employee_id: leaveFormData.employee_id,
        leave_type: leaveFormData.leave_type,
        start_date: leaveFormData.start_date,
        end_date: leaveFormData.end_date,
        hours_requested: parseFloat(leaveFormData.hours_requested),
        reason: leaveFormData.reason || null,
        approver_id: leaveFormData.approver_id || null
      };

      const response = await fetch('/api/payroll/leave-requests', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(submitData)
      });

      if (response.ok) {
        toast.success('Leave request created successfully');
        setShowLeaveRequestModal(false);
        loadAllLeaveRequests();
        loadPayrollData();
      } else {
        const error = await response.json();
        // Handle Pydantic validation errors
        if (error.detail) {
          if (Array.isArray(error.detail)) {
            // Pydantic validation error array
            const errorMessages = error.detail.map(err => err.msg || JSON.stringify(err)).join(', ');
            toast.error(errorMessages);
          } else if (typeof error.detail === 'string') {
            toast.error(error.detail);
          } else {
            toast.error('Validation error occurred');
          }
        } else {
          toast.error('Failed to create leave request');
        }
      }
    } catch (error) {
      console.error('Failed to create leave request:', error);
      toast.error('Failed to create leave request');
    }
  };

  const handleBankDetailsSubmit = async (e) => {
    e.preventDefault();
    
    try {
      const response = await fetch(`/api/payroll/employees/${selectedEmployee.id}/bank-details?bank_account_bsb=${encodeURIComponent(bankDetailsFormData.bank_account_bsb)}&bank_account_number=${encodeURIComponent(bankDetailsFormData.bank_account_number)}&tax_file_number=${encodeURIComponent(bankDetailsFormData.tax_file_number || '')}&superannuation_fund=${encodeURIComponent(bankDetailsFormData.superannuation_fund || '')}`, {
        method: 'PUT',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        toast.success('Bank details updated successfully');
        setShowBankDetailsModal(false);
        loadPayrollData();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to update bank details');
      }
    } catch (error) {
      console.error('Failed to update bank details:', error);
      toast.error('Failed to update bank details');
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

  const handleCancelLeave = async (requestId) => {
    if (!window.confirm('Are you sure you want to cancel this approved leave? The hours will be restored to the employee.')) {
      return;
    }
    
    try {
      const response = await fetch(`/api/payroll/leave-requests/${requestId}/cancel`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const result = await response.json();
        toast.success(result.message || 'Leave cancelled and hours restored');
        loadLeaveCalendar();
        loadPayrollData();
        loadAllLeaveRequests();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to cancel leave');
      }
    } catch (error) {
      console.error('Failed to cancel leave:', error);
      toast.error('Failed to cancel leave');
    }
  };

  const handleApproveTimesheet = async (timesheetId) => {
    if (!window.confirm('Are you sure you want to approve this timesheet and calculate pay?')) {
      return;
    }
    
    try {
      setApprovingTimesheet(timesheetId);
      
      const response = await fetch(`${BACKEND_URL}/api/payroll/timesheets/${timesheetId}/approve`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const result = await response.json();
        const payData = result.data || {};
        toast.success(`Timesheet approved! Gross pay: $${payData.gross_pay?.toFixed(2) || '0.00'}, Net pay: $${payData.net_pay?.toFixed(2) || '0.00'}`);
        loadPayrollData(); // Reload to update pending timesheets
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to approve timesheet');
      }
    } catch (error) {
      console.error('Failed to approve timesheet:', error);
      toast.error('Failed to approve timesheet');
    } finally {
      setApprovingTimesheet(null);
    }
  };

  const handleViewTimesheet = (timesheet) => {
    // Set a minimal employee object with just the id for TimesheetEntry
    // TimesheetEntry will load the full employee details if needed
    setSelectedEmployee({ id: timesheet.employee_id });
    setShowTimesheetModal(true);
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
            <div>
              <h3 className="text-xl font-semibold text-white mb-6">Payroll Dashboard</h3>
              
              {/* Leave Reminders Section for Managers */}
              {hasPermission('manage_payroll') && leaveReminders.length > 0 && (
                <div className="bg-yellow-900 bg-opacity-20 border border-yellow-500 border-opacity-50 rounded-lg p-4 mb-6">
                  <div className="flex items-center mb-3">
                    <ExclamationTriangleIcon className="h-6 w-6 text-yellow-400 mr-2" />
                    <h4 className="text-lg font-semibold text-white">Upcoming Leave Reminders</h4>
                  </div>
                  <div className="space-y-2">
                    {leaveReminders.map((reminder) => (
                      <div key={reminder.id} className="bg-gray-800 rounded p-3 flex items-center justify-between">
                        <div>
                          <p className="text-white font-medium">{reminder.message}</p>
                          <p className="text-sm text-gray-400">
                            {reminder.employee_number} - {reminder.department} | 
                            {new Date(reminder.start_date).toLocaleDateString()} to {new Date(reminder.end_date).toLocaleDateString()} | 
                            {reminder.hours_requested}h
                          </p>
                        </div>
                        <span className={`px-3 py-1 rounded text-sm font-medium ${
                          reminder.reminder_type === '1_day' 
                            ? 'bg-red-900 text-red-200' 
                            : 'bg-yellow-900 text-yellow-200'
                        }`}>
                          {reminder.reminder_type === '1_day' ? 'Tomorrow' : 'In 7 days'}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

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
            </div>
          )}

          {activeTab === 'employees' && hasPermission('manage_payroll') && (
            <div>
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className="text-xl font-semibold text-white">Employee Management</h3>
                  <p className="text-sm text-gray-400 mt-1">
                    {employees.length} active employees synced from Staff & Security
                  </p>
                </div>
                <div className="flex space-x-3">
                  <button
                    onClick={async () => {
                      try {
                        const response = await fetch('/api/payroll/employees/sync', {
                          method: 'POST',
                          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
                        });
                        if (response.ok) {
                          const result = await response.json();
                          toast.success(result.message || 'Employees synced successfully');
                          loadPayrollData();
                        } else {
                          toast.error('Failed to sync employees');
                        }
                      } catch (error) {
                        toast.error('Failed to sync employees');
                      }
                    }}
                    className="misty-button misty-button-secondary flex items-center"
                  >
                    <ArrowPathIcon className="h-5 w-5 mr-2" />
                    Sync from Staff & Security
                  </button>
                  <button
                    onClick={handleEmployeeCreate}
                    className="misty-button misty-button-primary flex items-center"
                    data-testid="add-employee-button"
                  >
                    <UserPlusIcon className="h-5 w-5 mr-2" />
                    Add Employee
                  </button>
                </div>
              </div>

              {/* Info box about sync */}
              <div className="bg-blue-900 bg-opacity-20 border border-blue-500 border-opacity-30 rounded-lg p-4 mb-6">
                <div className="flex items-start">
                  <div className="flex-shrink-0">
                    <CheckCircleIcon className="h-5 w-5 text-blue-400 mt-0.5" />
                  </div>
                  <div className="ml-3">
                    <p className="text-sm text-blue-200">
                      <strong>Auto-Sync Enabled:</strong> All active users from Staff & Security automatically appear here.
                    </p>
                    <p className="text-xs text-blue-300 mt-1">
                      Missing someone? Check that they are marked as "Active" in Staff & Security, or click "Sync from Staff & Security" to manually refresh.
                    </p>
                  </div>
                </div>
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
                              <button
                                onClick={() => {
                                  setSelectedEmployee(employee);
                                  setBankDetailsFormData({
                                    bank_account_bsb: employee.bank_account_bsb || '',
                                    bank_account_number: employee.bank_account_number || '',
                                    tax_file_number: employee.tax_file_number || '',
                                    superannuation_fund: employee.superannuation_fund || ''
                                  });
                                  setShowBankDetailsModal(true);
                                }}
                                className="text-gray-400 hover:text-green-400 transition-colors flex items-center"
                                data-testid={`bank-details-${employee.id}`}
                              >
                                <BuildingLibraryIcon className="h-4 w-4 mr-1" />
                                Bank
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
              
              {pendingTimesheets.length > 0 ? (
                <div className="misty-table">
                  <table className="w-full">
                    <thead>
                      <tr>
                        <th>Employee</th>
                        <th>Week</th>
                        <th>Regular Hours</th>
                        <th>Overtime Hours</th>
                        <th>Total Hours</th>
                        <th>Status</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {pendingTimesheets.map((timesheet) => {
                        const regularHours = timesheet.total_regular_hours || 0;
                        const overtimeHours = timesheet.total_overtime_hours || 0;
                        const totalHours = regularHours + overtimeHours;
                        
                        return (
                          <tr key={timesheet.id}>
                            <td>
                              <p className="font-medium">{timesheet.employee_name || 'Unknown'}</p>
                              <p className="text-sm text-gray-400">{timesheet.employee_number || 'N/A'}</p>
                            </td>
                            <td className="text-sm">
                              <p>{timesheet.week_starting || timesheet.week_start}</p>
                              <p className="text-gray-400">to {timesheet.week_ending || timesheet.week_end}</p>
                            </td>
                            <td className="font-medium text-green-400">{regularHours.toFixed(1)}h</td>
                            <td className="font-medium text-yellow-400">{overtimeHours.toFixed(1)}h</td>
                            <td className="font-bold text-white">{totalHours.toFixed(1)}h</td>
                            <td>
                              <span className="text-sm px-2 py-1 rounded bg-yellow-900 text-yellow-200">
                                {timesheet.status || 'submitted'}
                              </span>
                            </td>
                            <td>
                              <div className="flex space-x-2">
                                <button
                                  onClick={() => handleApproveTimesheet(timesheet.id)}
                                  className="text-green-400 hover:text-green-300 flex items-center text-sm"
                                  disabled={approvingTimesheet === timesheet.id}
                                >
                                  <CheckCircleIcon className="h-4 w-4 mr-1" />
                                  {approvingTimesheet === timesheet.id ? 'Approving...' : 'Approve'}
                                </button>
                                <button
                                  onClick={() => handleViewTimesheet(timesheet)}
                                  className="text-blue-400 hover:text-blue-300 flex items-center text-sm"
                                >
                                  <EyeIcon className="h-4 w-4 mr-1" />
                                  View
                                </button>
                              </div>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="text-center py-12 bg-gray-800 rounded-lg">
                  <CheckCircleIcon className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                  <p className="text-gray-300">No pending timesheets</p>
                  <p className="text-sm text-gray-500">Submitted timesheets will appear here for approval</p>
                </div>
              )}
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
                <div className="flex space-x-3">
                  <button
                    onClick={() => {
                      loadLeaveCalendar();
                      setShowLeaveCalendar(true);
                    }}
                    className="misty-button misty-button-secondary flex items-center"
                  >
                    <CalendarDaysIcon className="h-4 w-4 mr-2" />
                    Leave Calendar
                  </button>
                  <button
                    onClick={() => {
                      loadArchivedLeaveRequests();
                      setShowArchivedLeave(true);
                    }}
                    className="misty-button misty-button-secondary flex items-center"
                  >
                    <ArchiveBoxIcon className="h-4 w-4 mr-2" />
                    Archived Leave
                  </button>
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
            <PayrollReports />
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

      {/* Leave Request Modal */}
      {showLeaveRequestModal && (
        <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && setShowLeaveRequestModal(false)}>
          <div className="modal-content max-w-2xl">
            <div className="p-6">
              <h3 className="text-xl font-semibold text-white mb-6 flex items-center">
                <CalendarDaysIcon className="h-6 w-6 mr-2 text-yellow-400" />
                Add Leave Request
              </h3>

              <form onSubmit={handleLeaveFormSubmit} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  {/* Employee Selection */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Employee <span className="text-red-400">*</span>
                    </label>
                    <select
                      value={leaveFormData.employee_id}
                      onChange={(e) => setLeaveFormData({...leaveFormData, employee_id: e.target.value})}
                      className="misty-select w-full"
                      required
                    >
                      <option value="">Select employee...</option>
                      {employees.map((emp) => (
                        <option key={emp.id} value={emp.id}>
                          {emp.first_name} {emp.last_name} - {emp.employee_number}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Leave Type */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Leave Type <span className="text-red-400">*</span>
                    </label>
                    <select
                      value={leaveFormData.leave_type}
                      onChange={(e) => setLeaveFormData({...leaveFormData, leave_type: e.target.value})}
                      className="misty-select w-full"
                      required
                    >
                      <option value="annual_leave">Annual Leave</option>
                      <option value="sick_leave">Sick Leave</option>
                      <option value="personal_leave">Personal Leave</option>
                      <option value="unpaid_leave">Unpaid Leave</option>
                    </select>
                  </div>

                  {/* Start Date */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Start Date <span className="text-red-400">*</span>
                    </label>
                    <input
                      type="date"
                      value={leaveFormData.start_date}
                      onChange={(e) => handleDateChange('start_date', e.target.value)}
                      className="misty-input w-full"
                      required
                    />
                  </div>

                  {/* End Date */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      End Date <span className="text-red-400">*</span>
                    </label>
                    <input
                      type="date"
                      value={leaveFormData.end_date}
                      onChange={(e) => handleDateChange('end_date', e.target.value)}
                      className="misty-input w-full"
                      min={leaveFormData.start_date}
                      required
                    />
                  </div>

                  {/* Hours Requested */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Hours Requested <span className="text-red-400">*</span>
                    </label>
                    <input
                      type="number"
                      step="0.5"
                      min="0"
                      value={leaveFormData.hours_requested}
                      onChange={(e) => setLeaveFormData({...leaveFormData, hours_requested: e.target.value})}
                      className="misty-input w-full"
                      placeholder="Auto-calculated from dates"
                      required
                    />
                    {leaveFormData.start_date && leaveFormData.end_date && (
                      <p className="text-xs text-blue-400 mt-1">
                        ℹ️ {calculateBusinessDays(leaveFormData.start_date, leaveFormData.end_date)} business days 
                        (excludes weekends) × 8 hours = {leaveFormData.hours_requested || 0} hours
                      </p>
                    )}
                    <p className="text-xs text-gray-500 mt-1">
                      You can manually adjust this value if needed
                    </p>
                  </div>

                  {/* Approver Selection */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Assign Approver <span className="text-gray-500 text-xs">(Optional)</span>
                    </label>
                    <select
                      value={leaveFormData.approver_id}
                      onChange={(e) => setLeaveFormData({...leaveFormData, approver_id: e.target.value})}
                      className="misty-select w-full"
                    >
                      <option value="">No specific approver</option>
                      {employees.filter(emp => 
                        emp.position && (
                          emp.position.toLowerCase().includes('manager') || 
                          emp.position.toLowerCase().includes('admin') ||
                          emp.position.toLowerCase().includes('supervisor')
                        )
                      ).map((emp) => (
                        <option key={emp.id} value={emp.id}>
                          {emp.first_name} {emp.last_name} - {emp.position}
                        </option>
                      ))}
                    </select>
                    <p className="text-xs text-gray-500 mt-1">
                      Leave request will appear in this person's approval queue
                    </p>
                  </div>
                </div>

                {/* Reason */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Reason <span className="text-gray-500 text-xs">(Optional)</span>
                  </label>
                  <textarea
                    value={leaveFormData.reason}
                    onChange={(e) => setLeaveFormData({...leaveFormData, reason: e.target.value})}
                    className="misty-textarea w-full"
                    rows={3}
                    placeholder="Enter reason for leave request..."
                  />
                </div>

                {/* Actions */}
                <div className="flex justify-end space-x-3 pt-4 border-t border-gray-600">
                  <button
                    type="button"
                    onClick={() => setShowLeaveRequestModal(false)}
                    className="misty-button misty-button-secondary"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="misty-button misty-button-primary"
                  >
                    Create Leave Request
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Bank Details Modal */}
      {showBankDetailsModal && (
        <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && setShowBankDetailsModal(false)}>
          <div className="modal-content max-w-lg">
            <div className="p-6">
              <h3 className="text-xl font-semibold text-white mb-4 flex items-center">
                <BuildingLibraryIcon className="h-6 w-6 mr-2 text-green-400" />
                Update Bank Details
              </h3>
              <p className="text-sm text-gray-400 mb-6">
                Employee: {selectedEmployee?.first_name} {selectedEmployee?.last_name}
              </p>

              <form onSubmit={handleBankDetailsSubmit} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      BSB <span className="text-red-400">*</span>
                    </label>
                    <input
                      type="text"
                      value={bankDetailsFormData.bank_account_bsb}
                      onChange={(e) => setBankDetailsFormData({...bankDetailsFormData, bank_account_bsb: e.target.value})}
                      className="misty-input w-full font-mono"
                      placeholder="123-456"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Account Number <span className="text-red-400">*</span>
                    </label>
                    <input
                      type="text"
                      value={bankDetailsFormData.bank_account_number}
                      onChange={(e) => setBankDetailsFormData({...bankDetailsFormData, bank_account_number: e.target.value})}
                      className="misty-input w-full font-mono"
                      placeholder="12345678"
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Tax File Number (TFN)
                  </label>
                  <input
                    type="text"
                    value={bankDetailsFormData.tax_file_number}
                    onChange={(e) => setBankDetailsFormData({...bankDetailsFormData, tax_file_number: e.target.value})}
                    className="misty-input w-full font-mono"
                    placeholder="123 456 789"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Superannuation Fund
                  </label>
                  <input
                    type="text"
                    value={bankDetailsFormData.superannuation_fund}
                    onChange={(e) => setBankDetailsFormData({...bankDetailsFormData, superannuation_fund: e.target.value})}
                    className="misty-input w-full"
                    placeholder="e.g., AustralianSuper"
                  />
                </div>

                <div className="bg-blue-900 bg-opacity-20 border border-blue-500 border-opacity-30 rounded-lg p-3">
                  <p className="text-xs text-blue-200">
                    <CheckCircleIcon className="h-4 w-4 inline mr-1" />
                    This information is securely stored and used for payroll processing only.
                  </p>
                </div>

                <div className="flex justify-end space-x-3 pt-4 border-t border-gray-600">
                  <button
                    type="button"
                    onClick={() => setShowBankDetailsModal(false)}
                    className="misty-button misty-button-secondary"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="misty-button misty-button-primary"
                  >
                    Update Details
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Archived Leave Requests Modal */}
      {showArchivedLeave && (
        <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && setShowArchivedLeave(false)}>
          <div className="modal-content max-w-6xl max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-semibold text-white flex items-center">
                  <ArchiveBoxIcon className="h-6 w-6 mr-2 text-gray-400" />
                  Archived Leave Requests
                </h3>
                <button
                  onClick={() => setShowArchivedLeave(false)}
                  className="text-gray-400 hover:text-white"
                >
                  ✕
                </button>
              </div>
              <p className="text-sm text-gray-400 mb-6">
                Viewing all approved and declined leave requests
              </p>

              {archivedLeaveRequests.length > 0 ? (
                <div className="misty-table">
                  <table className="w-full">
                    <thead>
                      <tr>
                        <th>Employee</th>
                        <th>Leave Type</th>
                        <th>Dates</th>
                        <th>Hours</th>
                        <th>Status</th>
                        <th>Approver</th>
                        <th>Reason</th>
                      </tr>
                    </thead>
                    <tbody>
                      {archivedLeaveRequests.map((request) => (
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
                          <td>
                            <span className={`text-sm px-2 py-1 rounded ${
                              request.status === 'approved' ? 'bg-green-900 text-green-200' :
                              'bg-red-900 text-red-200'
                            }`}>
                              {request.status}
                            </span>
                          </td>
                          <td className="text-sm text-gray-400">
                            {request.approver_name || 'N/A'}
                          </td>
                          <td className="text-sm text-gray-400 max-w-xs truncate">
                            {request.reason || 'No reason provided'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="text-center py-12 bg-gray-800 rounded-lg">
                  <ArchiveBoxIcon className="mx-auto h-12 w-12 text-gray-400" />
                  <p className="mt-2 text-sm text-gray-300">No archived leave requests</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Leave Calendar Modal */}
      {showLeaveCalendar && (
        <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && setShowLeaveCalendar(false)}>
          <div className="modal-content max-w-6xl max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-semibold text-white flex items-center">
                  <CalendarDaysIcon className="h-6 w-6 mr-2 text-blue-400" />
                  Upcoming Approved Leave Calendar
                </h3>
                <button
                  onClick={() => setShowLeaveCalendar(false)}
                  className="text-gray-400 hover:text-white"
                >
                  ✕
                </button>
              </div>
              <p className="text-sm text-gray-400 mb-6">
                Showing all upcoming approved leave from today onwards
              </p>

              {leaveCalendarEvents.length > 0 ? (
                <div className="space-y-4">
                  {leaveCalendarEvents.map((event) => {
                    const startDate = new Date(event.start_date);
                    const endDate = new Date(event.end_date);
                    const daysUntil = Math.ceil((startDate - new Date()) / (1000 * 60 * 60 * 24));
                    
                    return (
                      <div key={event.id} className="bg-gray-800 rounded-lg p-4 border-l-4 border-blue-500">
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <div className="flex items-center space-x-3 mb-2">
                              <h4 className="text-lg font-semibold text-white">{event.employee_name}</h4>
                              <span className="text-sm bg-blue-900 px-2 py-1 rounded capitalize">
                                {event.leave_type.replace('_', ' ')}
                              </span>
                              {daysUntil <= 7 && (
                                <span className="text-xs bg-yellow-900 text-yellow-200 px-2 py-1 rounded">
                                  {daysUntil === 0 ? 'Today' : daysUntil === 1 ? 'Tomorrow' : `In ${daysUntil} days`}
                                </span>
                              )}
                            </div>
                            <div className="text-sm text-gray-400">
                              <p>{event.employee_number} - {event.department}</p>
                              <p className="mt-1">
                                <span className="font-medium text-white">
                                  {startDate.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' })}
                                </span>
                                <span className="mx-2">→</span>
                                <span className="font-medium text-white">
                                  {endDate.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' })}
                                </span>
                              </p>
                              <p className="mt-1">{event.hours_requested} hours</p>
                              {event.reason && (
                                <p className="mt-2 text-xs italic">"{event.reason}"</p>
                              )}
                            </div>
                          </div>
                          <div className="text-right flex flex-col items-end">
                            <div className="text-3xl font-bold text-blue-400 mb-2">
                              {startDate.getDate()}
                            </div>
                            <div className="text-sm text-gray-400 mb-3">
                              {startDate.toLocaleDateString('en-US', { month: 'short' })}
                            </div>
                            <button
                              onClick={() => handleCancelLeave(event.id)}
                              className="text-xs text-red-400 hover:text-red-300 transition-colors"
                            >
                              Cancel Leave
                            </button>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="text-center py-12 bg-gray-800 rounded-lg">
                  <CalendarDaysIcon className="mx-auto h-12 w-12 text-gray-400" />
                  <p className="mt-2 text-sm text-gray-300">No upcoming approved leave</p>
                </div>
              )}
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