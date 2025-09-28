import React, { useState, useEffect } from 'react';
import Layout from './Layout';
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
  CheckCircleIcon
} from '@heroicons/react/24/outline';

const PayrollManagement = () => {
  const { user, hasPermission } = useAuth();
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [employees, setEmployees] = useState([]);
  const [pendingTimesheets, setPendingTimesheets] = useState([]);
  const [pendingLeaveRequests, setPendingLeaveRequests] = useState([]);
  const [timesheetReminder, setTimesheetReminder] = useState(null);
  const [showEmployeeModal, setShowEmployeeModal] = useState(false);
  const [showTimesheetModal, setShowTimesheetModal] = useState(false);
  const [selectedEmployee, setSelectedEmployee] = useState(null);

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
                                onClick={() => handleEmployeeEdit(employee)}
                                className="text-gray-400 hover:text-yellow-400 transition-colors"
                                data-testid={`edit-employee-${employee.id}`}
                              >
                                Edit
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
            <div className="misty-card p-6">
              <h3 className="text-xl font-semibold text-white mb-4">Leave Requests</h3>
              <p className="text-gray-400 mb-4">Manage employee leave requests and approvals</p>
              
              <div className="text-center py-8">
                <CalendarDaysIcon className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                <p className="text-gray-400">Leave request management will be implemented here</p>
              </div>
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

      {/* Timesheet Modal Placeholder */}
      {showTimesheetModal && selectedEmployee && (
        <div className="modal-overlay">
          <div className="modal-content max-w-6xl">
            <div className="p-6">
              <h2 className="text-xl font-bold text-white mb-4">
                Timesheet - {selectedEmployee.first_name} {selectedEmployee.last_name}
              </h2>
              <p className="text-gray-400 mb-4">Timesheet interface will be implemented here</p>
              <div className="flex justify-end space-x-3">
                <button
                  onClick={() => setShowTimesheetModal(false)}
                  className="misty-button misty-button-secondary"
                >
                  Close
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