import React, { useState, useEffect } from 'react';
import { toast } from 'sonner';
import {
  DocumentChartBarIcon,
  BanknotesIcon,
  ClockIcon,
  CalendarDaysIcon,
  ArrowDownTrayIcon,
  PencilIcon,
  CheckCircleIcon,
  BuildingLibraryIcon,
  EyeIcon
} from '@heroicons/react/24/outline';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';

const PayrollReports = () => {
  const [activeReportTab, setActiveReportTab] = useState('payslips');
  const [employees, setEmployees] = useState([]);
  const [payslips, setPayslips] = useState([]);
  const [timesheets, setTimesheets] = useState([]);
  const [timesheetSummary, setTimesheetSummary] = useState(null);
  const [selectedEmployee, setSelectedEmployee] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [loading, setLoading] = useState(false);
  const [showLeaveAdjustment, setShowLeaveAdjustment] = useState(false);
  const [selectedEmployeeForAdjustment, setSelectedEmployeeForAdjustment] = useState(null);
  const [adjustmentFormData, setAdjustmentFormData] = useState({
    leave_type: 'annual_leave',
    adjustment_hours: '',
    reason: ''
  });
  const [showBankDetailsModal, setShowBankDetailsModal] = useState(false);
  const [selectedEmployeeForBank, setSelectedEmployeeForBank] = useState(null);
  const [bankDetailsFormData, setBankDetailsFormData] = useState({
    bank_account_bsb: '',
    bank_account_number: '',
    tax_file_number: '',
    superannuation_fund: ''
  });
  const [showPayslipModal, setShowPayslipModal] = useState(false);
  const [selectedPayslip, setSelectedPayslip] = useState(null);

  useEffect(() => {
    loadEmployees();
    if (activeReportTab === 'payslips') {
      loadPayslips();
    }
  }, [activeReportTab]);

  const loadEmployees = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/payroll/employees`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      if (response.ok) {
        const data = await response.json();
        setEmployees(Array.isArray(data) ? data : []);
      }
    } catch (error) {
      console.error('Failed to load employees:', error);
    }
  };

  const loadPayslips = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${BACKEND_URL}/api/payroll/reports/payslips`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      if (response.ok) {
        const result = await response.json();
        let filteredPayslips = result.data || [];
        
        // Apply employee filter
        if (selectedEmployee) {
          filteredPayslips = filteredPayslips.filter(p => p.employee_id === selectedEmployee);
        }
        
        // Apply date filters
        if (startDate || endDate) {
          filteredPayslips = filteredPayslips.filter(p => {
            const payDate = new Date(p.payslip_data.pay_period.week_start);
            const start = startDate ? new Date(startDate) : null;
            const end = endDate ? new Date(endDate) : null;
            
            if (start && payDate < start) return false;
            if (end && payDate > end) return false;
            return true;
          });
        }
        
        setPayslips(filteredPayslips);
      }
    } catch (error) {
      toast.error('Failed to load payslips');
    } finally {
      setLoading(false);
    }
  };

  const generatePayslip = async (timesheetId) => {
    try {
      setLoading(true);
      const response = await fetch(`${BACKEND_URL}/api/payroll/reports/payslip/${timesheetId}`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      if (response.ok) {
        const result = await response.json();
        toast.success('Payslip generated successfully');
        loadPayslips();
        return result.data;
      } else {
        toast.error('Failed to generate payslip');
      }
    } catch (error) {
      toast.error('Failed to generate payslip');
    } finally {
      setLoading(false);
    }
  };

  const loadTimesheetReport = async () => {
    try {
      setLoading(true);
      let url = `${BACKEND_URL}/api/payroll/reports/timesheets?`;
      if (selectedEmployee) url += `employee_id=${selectedEmployee}&`;
      if (startDate) url += `start_date=${startDate}&`;
      if (endDate) url += `end_date=${endDate}&`;

      const response = await fetch(url, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      
      if (response.ok) {
        const result = await response.json();
        setTimesheets(result.data || []);
        setTimesheetSummary(result.summary || null);
      } else {
        toast.error('Failed to load timesheet report');
      }
    } catch (error) {
      toast.error('Failed to load timesheet report');
    } finally {
      setLoading(false);
    }
  };

  const handleLeaveAdjustment = async (e) => {
    e.preventDefault();
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/payroll/leave-adjustments`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          employee_id: selectedEmployeeForAdjustment.id,
          ...adjustmentFormData
        })
      });

      if (response.ok) {
        const result = await response.json();
        toast.success(result.message);
        setShowLeaveAdjustment(false);
        loadEmployees();
        setAdjustmentFormData({
          leave_type: 'annual_leave',
          adjustment_hours: '',
          reason: ''
        });
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to adjust leave');
      }
    } catch (error) {
      toast.error('Failed to adjust leave');
    }
  };

  const handleBankDetailsSubmit = async (e) => {
    e.preventDefault();
    
    if (!bankDetailsFormData.bank_account_bsb || !bankDetailsFormData.bank_account_number) {
      toast.error('BSB and Account Number are required');
      return;
    }
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/payroll/employees/${selectedEmployeeForBank.id}/bank-details?bank_account_bsb=${encodeURIComponent(bankDetailsFormData.bank_account_bsb)}&bank_account_number=${encodeURIComponent(bankDetailsFormData.bank_account_number)}&tax_file_number=${encodeURIComponent(bankDetailsFormData.tax_file_number || '')}&superannuation_fund=${encodeURIComponent(bankDetailsFormData.superannuation_fund || '')}`, {
        method: 'PUT',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        toast.success('Bank details updated successfully');
        setShowBankDetailsModal(false);
        setBankDetailsFormData({
          bank_account_bsb: '',
          bank_account_number: '',
          tax_file_number: '',
          superannuation_fund: ''
        });
        loadEmployees();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to update bank details');
      }
    } catch (error) {
      console.error('Failed to update bank details:', error);
      toast.error('Failed to update bank details');
    }
  };

  const downloadPayslip = async (payslip) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/payroll/reports/payslip/${payslip.id}/pdf`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      
      if (response.ok) {
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `payslip_${payslip.payslip_data.employee.employee_number}_${payslip.payslip_data.pay_period.week_start}.pdf`;
        a.click();
        URL.revokeObjectURL(url);
        toast.success('Payslip downloaded successfully');
      } else {
        toast.error('Failed to download payslip');
      }
    } catch (error) {
      console.error('Error downloading payslip:', error);
      toast.error('Failed to download payslip');
    }
  };

  const viewPayslip = (payslip) => {
    setSelectedPayslip(payslip);
    setShowPayslipModal(true);
  };

  return (
    <div>
      {/* Sub-Tab Navigation */}
      <div className="flex space-x-4 mb-6 border-b border-gray-600">
        <button
          onClick={() => setActiveReportTab('payslips')}
          className={`px-4 py-2 font-medium transition-colors ${
            activeReportTab === 'payslips'
              ? 'text-yellow-400 border-b-2 border-yellow-400'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          <BanknotesIcon className="h-5 w-5 inline mr-2" />
          Pay Slips
        </button>
        <button
          onClick={() => setActiveReportTab('timesheets')}
          className={`px-4 py-2 font-medium transition-colors ${
            activeReportTab === 'timesheets'
              ? 'text-yellow-400 border-b-2 border-yellow-400'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          <ClockIcon className="h-5 w-5 inline mr-2" />
          Approved Timesheets
        </button>
        <button
          onClick={() => setActiveReportTab('leave')}
          className={`px-4 py-2 font-medium transition-colors ${
            activeReportTab === 'leave'
              ? 'text-yellow-400 border-b-2 border-yellow-400'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          <CalendarDaysIcon className="h-5 w-5 inline mr-2" />
          Leave Entitlements
        </button>
        <button
          onClick={() => setActiveReportTab('bank-details')}
          className={`px-4 py-2 font-medium transition-colors ${
            activeReportTab === 'bank-details'
              ? 'text-yellow-400 border-b-2 border-yellow-400'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          <BuildingLibraryIcon className="h-5 w-5 inline mr-2" />
          Bank Details
        </button>
      </div>

      {/* Pay Slips Tab */}
      {activeReportTab === 'payslips' && (
        <div>
          <h3 className="text-xl font-semibold text-white mb-4">Historic Pay Slips</h3>
          <p className="text-sm text-gray-400 mb-6">
            View and download all generated payslips from approved timesheets
          </p>

          {/* Filters - Same as Approved Timesheets */}
          <div className="bg-gray-800 rounded-lg p-4 mb-6">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Employee
                </label>
                <select
                  value={selectedEmployee}
                  onChange={(e) => setSelectedEmployee(e.target.value)}
                  className="misty-select w-full"
                >
                  <option value="">All Employees</option>
                  {employees.map((emp) => (
                    <option key={emp.id} value={emp.id}>
                      {emp.first_name} {emp.last_name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  From Date
                </label>
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="misty-input w-full"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  To Date
                </label>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="misty-input w-full"
                />
              </div>
              <div className="flex items-end">
                <button
                  onClick={loadPayslips}
                  className="misty-button misty-button-primary w-full"
                >
                  Filter Payslips
                </button>
              </div>
            </div>
          </div>

          {loading ? (
            <p className="text-gray-400 text-center py-8">Loading payslips...</p>
          ) : payslips.length > 0 ? (
            <div className="misty-table">
              <table className="w-full">
                <thead>
                  <tr>
                    <th>Employee</th>
                    <th>Pay Period</th>
                    <th>Hours</th>
                    <th>Gross Pay</th>
                    <th>Net Pay</th>
                    <th>Generated</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {payslips.map((payslip) => {
                    const data = payslip.payslip_data;
                    return (
                      <tr key={payslip.id}>
                        <td>
                          <p className="font-medium">{data.employee.name}</p>
                          <p className="text-sm text-gray-400">{data.employee.employee_number}</p>
                        </td>
                        <td className="text-sm">
                          <p>{data.pay_period.week_start}</p>
                          <p className="text-gray-400">to {data.pay_period.week_end}</p>
                        </td>
                        <td>
                          <p>{data.hours.regular_hours}h regular</p>
                          <p className="text-sm text-gray-400">{data.hours.overtime_hours}h overtime</p>
                        </td>
                        <td className="font-medium text-green-400">
                          ${data.earnings.gross_pay.toFixed(2)}
                        </td>
                        <td className="font-medium text-yellow-400">
                          ${data.net_pay.toFixed(2)}
                        </td>
                        <td className="text-sm text-gray-400">
                          {new Date(data.generated_at).toLocaleDateString()}
                        </td>
                        <td>
                          <div className="flex items-center space-x-2">
                            <button
                              onClick={() => viewPayslip(payslip)}
                              className="text-blue-400 hover:text-blue-300 flex items-center text-sm"
                              title="View Payslip"
                            >
                              <EyeIcon className="h-4 w-4 mr-1" />
                              View
                            </button>
                            <button
                              onClick={() => downloadPayslip(payslip)}
                              className="text-green-400 hover:text-green-300 flex items-center text-sm"
                              title="Download Payslip"
                            >
                              <ArrowDownTrayIcon className="h-4 w-4 mr-1" />
                              Download
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
              <BanknotesIcon className="mx-auto h-12 w-12 text-gray-400" />
              <p className="mt-2 text-sm text-gray-300">No payslips generated yet</p>
              <p className="text-xs text-gray-500">Payslips are automatically generated from approved timesheets</p>
            </div>
          )}
        </div>
      )}

      {/* Approved Timesheets Report Tab */}
      {activeReportTab === 'timesheets' && (
        <div>
          <div className="mb-4">
            <h3 className="text-xl font-semibold text-white">Approved Timesheets Report</h3>
            <p className="text-sm text-gray-400 mt-1">View all approved timesheets archived against employees who entered them</p>
          </div>
          
          {/* Filters */}
          <div className="bg-gray-800 rounded-lg p-4 mb-6">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Employee
                </label>
                <select
                  value={selectedEmployee}
                  onChange={(e) => setSelectedEmployee(e.target.value)}
                  className="misty-select w-full"
                >
                  <option value="">All Employees</option>
                  {employees.map((emp) => (
                    <option key={emp.id} value={emp.id}>
                      {emp.first_name} {emp.last_name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  From Date
                </label>
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="misty-input w-full"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  To Date
                </label>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="misty-input w-full"
                />
              </div>
              <div className="flex items-end">
                <button
                  onClick={loadTimesheetReport}
                  className="misty-button misty-button-primary w-full"
                >
                  Generate Report
                </button>
              </div>
            </div>
          </div>

          {/* Summary */}
          {timesheetSummary && (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-blue-900 bg-opacity-20 border border-blue-500 border-opacity-30 rounded-lg p-4">
                <p className="text-sm text-gray-400">Total Timesheets</p>
                <p className="text-2xl font-bold text-white">{timesheetSummary.total_timesheets}</p>
              </div>
              <div className="bg-green-900 bg-opacity-20 border border-green-500 border-opacity-30 rounded-lg p-4">
                <p className="text-sm text-gray-400">Regular Hours</p>
                <p className="text-2xl font-bold text-white">{timesheetSummary.total_regular_hours}h</p>
              </div>
              <div className="bg-yellow-900 bg-opacity-20 border border-yellow-500 border-opacity-30 rounded-lg p-4">
                <p className="text-sm text-gray-400">Overtime Hours</p>
                <p className="text-2xl font-bold text-white">{timesheetSummary.total_overtime_hours}h</p>
              </div>
              <div className="bg-purple-900 bg-opacity-20 border border-purple-500 border-opacity-30 rounded-lg p-4">
                <p className="text-sm text-gray-400">Total Hours</p>
                <p className="text-2xl font-bold text-white">{timesheetSummary.total_hours}h</p>
              </div>
            </div>
          )}

          {/* Timesheets Table */}
          {loading ? (
            <p className="text-gray-400 text-center py-8">Loading timesheets...</p>
          ) : timesheets.length > 0 ? (
            <div className="misty-table">
              <table className="w-full">
                <thead>
                  <tr>
                    <th>Employee</th>
                    <th>Week</th>
                    <th>Regular Hours</th>
                    <th>Overtime Hours</th>
                    <th>Status</th>
                    <th>Approver</th>
                  </tr>
                </thead>
                <tbody>
                  {timesheets.map((timesheet) => (
                    <tr key={timesheet.id}>
                      <td>
                        <p className="font-medium">{timesheet.employee_name}</p>
                      </td>
                      <td className="text-sm">
                        <p>{timesheet.week_start}</p>
                        <p className="text-gray-400">to {timesheet.week_end}</p>
                      </td>
                      <td className="font-medium text-green-400">
                        {timesheet.total_regular_hours || 0}h
                      </td>
                      <td className="font-medium text-yellow-400">
                        {timesheet.total_overtime_hours || 0}h
                      </td>
                      <td>
                        <span className={`text-sm px-2 py-1 rounded ${
                          timesheet.status === 'approved' ? 'bg-green-900 text-green-200' :
                          timesheet.status === 'submitted' ? 'bg-yellow-900 text-yellow-200' :
                          'bg-gray-700 text-gray-300'
                        }`}>
                          {timesheet.status}
                        </span>
                      </td>
                      <td className="text-sm text-gray-400">
                        {timesheet.approver_name || 'N/A'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-12 bg-gray-800 rounded-lg">
              <ClockIcon className="mx-auto h-12 w-12 text-gray-400" />
              <p className="mt-2 text-sm text-gray-300">No timesheets found</p>
              <p className="text-xs text-gray-500">Select filters and click Generate Report</p>
            </div>
          )}
        </div>
      )}

      {/* Leave Entitlements Tab */}
      {activeReportTab === 'leave' && (
        <div>
          <h3 className="text-xl font-semibold text-white mb-4">Leave Entitlements</h3>
          <p className="text-sm text-gray-400 mb-6">
            View and manage employee leave balances
          </p>

          {employees.length > 0 ? (
            <div className="misty-table">
              <table className="w-full">
                <thead>
                  <tr>
                    <th>Employee</th>
                    <th>Annual Leave</th>
                    <th>Sick Leave</th>
                    <th>Personal Leave</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {employees.map((employee) => (
                    <tr key={employee.id}>
                      <td>
                        <p className="font-medium">{employee.first_name} {employee.last_name}</p>
                        <p className="text-sm text-gray-400">{employee.employee_number}</p>
                      </td>
                      <td className="font-medium text-blue-400">
                        {employee.annual_leave_balance || 0}h / {employee.annual_leave_entitlement}h
                      </td>
                      <td className="font-medium text-green-400">
                        {employee.sick_leave_balance || 0}h / {employee.sick_leave_entitlement}h
                      </td>
                      <td className="font-medium text-yellow-400">
                        {employee.personal_leave_balance || 0}h / {employee.personal_leave_entitlement}h
                      </td>
                      <td>
                        <button
                          onClick={() => {
                            setSelectedEmployeeForAdjustment(employee);
                            setShowLeaveAdjustment(true);
                          }}
                          className="text-yellow-400 hover:text-yellow-300 flex items-center text-sm"
                        >
                          <PencilIcon className="h-4 w-4 mr-1" />
                          Adjust
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-gray-400 text-center py-8">No employees found</p>
          )}
        </div>
      )}

      {/* Bank Details Tab */}
      {activeReportTab === 'bank-details' && (
        <div>
          <h3 className="text-xl font-semibold text-white mb-4">Employee Bank Details</h3>
          <p className="text-sm text-gray-400 mb-6">
            Manage employee banking information for payroll processing
          </p>

          {employees.length > 0 ? (
            <div className="misty-table">
              <table className="w-full">
                <thead>
                  <tr>
                    <th>Employee</th>
                    <th>Bank Name</th>
                    <th>BSB</th>
                    <th>Account Number</th>
                    <th>Super Fund</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {employees.map((employee) => (
                    <tr key={employee.id}>
                      <td>
                        <p className="font-medium">{employee.first_name} {employee.last_name}</p>
                        <p className="text-sm text-gray-400">{employee.employee_number}</p>
                      </td>
                      <td className="text-sm">
                        {employee.bank_name || <span className="text-gray-500">Not set</span>}
                      </td>
                      <td className="font-mono text-sm">
                        {employee.bsb || <span className="text-gray-500">Not set</span>}
                      </td>
                      <td className="font-mono text-sm">
                        {employee.account_number ? 
                          `****${employee.account_number.slice(-4)}` : 
                          <span className="text-gray-500">Not set</span>
                        }
                      </td>
                      <td className="text-sm">
                        {employee.superannuation_fund || <span className="text-gray-500">Not set</span>}
                      </td>
                      <td>
                        <button
                          onClick={() => {
                            setSelectedEmployeeForBank(employee);
                            setBankDetailsFormData({
                              bank_account_bsb: employee.bank_account_bsb || '',
                              bank_account_number: employee.bank_account_number || '',
                              tax_file_number: employee.tax_file_number || '',
                              superannuation_fund: employee.superannuation_fund || ''
                            });
                            setShowBankDetailsModal(true);
                          }}
                          className="text-yellow-400 hover:text-yellow-300 flex items-center text-sm"
                        >
                          <PencilIcon className="h-4 w-4 mr-1" />
                          Edit
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-12 bg-gray-800 rounded-lg">
              <BuildingLibraryIcon className="mx-auto h-12 w-12 text-gray-400" />
              <p className="mt-2 text-sm text-gray-300">No employees found</p>
              <p className="text-xs text-gray-500">Employee bank details will appear here</p>
            </div>
          )}
        </div>
      )}

      {/* Leave Adjustment Modal */}
      {showLeaveAdjustment && (
        <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && setShowLeaveAdjustment(false)}>
          <div className="modal-content max-w-md">
            <div className="p-6">
              <h3 className="text-xl font-semibold text-white mb-4">
                Adjust Leave Balance
              </h3>
              <p className="text-sm text-gray-400 mb-6">
                Employee: {selectedEmployeeForAdjustment?.first_name} {selectedEmployeeForAdjustment?.last_name}
              </p>

              <form onSubmit={handleLeaveAdjustment} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Leave Type
                  </label>
                  <select
                    value={adjustmentFormData.leave_type}
                    onChange={(e) => setAdjustmentFormData({...adjustmentFormData, leave_type: e.target.value})}
                    className="misty-select w-full"
                    required
                  >
                    <option value="annual_leave">Annual Leave</option>
                    <option value="sick_leave">Sick Leave</option>
                    <option value="personal_leave">Personal Leave</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Adjustment Hours (+ to add, - to deduct)
                  </label>
                  <input
                    type="number"
                    step="0.5"
                    value={adjustmentFormData.adjustment_hours}
                    onChange={(e) => setAdjustmentFormData({...adjustmentFormData, adjustment_hours: e.target.value})}
                    className="misty-input w-full"
                    placeholder="e.g., 8 or -4"
                    required
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Use positive numbers to add leave, negative to deduct
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Reason <span className="text-red-400">*</span>
                  </label>
                  <textarea
                    value={adjustmentFormData.reason}
                    onChange={(e) => setAdjustmentFormData({...adjustmentFormData, reason: e.target.value})}
                    className="misty-textarea w-full"
                    rows={3}
                    placeholder="Enter reason for this adjustment..."
                    required
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Required for audit trail and record keeping
                  </p>
                </div>

                <div className="flex justify-end space-x-3 pt-4 border-t border-gray-600">
                  <button
                    type="button"
                    onClick={() => setShowLeaveAdjustment(false)}
                    className="misty-button misty-button-secondary"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="misty-button misty-button-primary"
                  >
                    Apply Adjustment
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Bank Details Modal */}
      {showBankDetailsModal && selectedEmployeeForBank && (
        <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && setShowBankDetailsModal(false)}>
          <div className="modal-content max-w-lg">
            <div className="p-6">
              <h3 className="text-xl font-semibold text-white mb-4">
                Edit Bank Details
              </h3>
              <p className="text-sm text-gray-400 mb-6">
                Employee: {selectedEmployeeForBank.first_name} {selectedEmployeeForBank.last_name} ({selectedEmployeeForBank.employee_number})
              </p>

              <form onSubmit={handleBankDetailsSubmit} className="space-y-4">
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
                    Save Bank Details
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Payslip View Modal */}
      {showPayslipModal && selectedPayslip && (
        <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && setShowPayslipModal(false)}>
          <div className="modal-content max-w-4xl">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-2xl font-bold text-yellow-400">Payslip</h3>
                <button
                  onClick={() => setShowPayslipModal(false)}
                  className="text-gray-400 hover:text-white"
                >
                  ✕
                </button>
              </div>

              {/* Payslip Content */}
              <div className="bg-gray-800 rounded-lg p-6 space-y-6">
                {/* Employee Details */}
                <div className="border-b border-gray-600 pb-4">
                  <h4 className="text-xl font-semibold text-white mb-2">
                    {selectedPayslip.payslip_data.employee.name}
                  </h4>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <p className="text-gray-400">Employee Number: <span className="text-white">{selectedPayslip.payslip_data.employee.employee_number}</span></p>
                    <p className="text-gray-400">Position: <span className="text-white">{selectedPayslip.payslip_data.employee.position}</span></p>
                    <p className="text-gray-400">Department: <span className="text-white">{selectedPayslip.payslip_data.employee.department}</span></p>
                    <p className="text-gray-400">TFN: <span className="text-white">{selectedPayslip.payslip_data.employee.tax_file_number}</span></p>
                  </div>
                </div>

                {/* Pay Period */}
                <div className="border-b border-gray-600 pb-4">
                  <h5 className="text-lg font-semibold text-yellow-400 mb-2">Pay Period</h5>
                  <p className="text-white">
                    {selectedPayslip.payslip_data.pay_period.week_start} to {selectedPayslip.payslip_data.pay_period.week_end}
                  </p>
                </div>

                {/* Hours Worked */}
                <div className="border-b border-gray-600 pb-4">
                  <h5 className="text-lg font-semibold text-yellow-400 mb-2">Hours Worked</h5>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <p className="text-gray-400">Regular Hours: <span className="text-white">{selectedPayslip.payslip_data.hours.regular_hours}h @ ${selectedPayslip.payslip_data.hours.hourly_rate}/hr</span></p>
                    <p className="text-gray-400">Overtime Hours: <span className="text-white">{selectedPayslip.payslip_data.hours.overtime_hours}h @ ${(selectedPayslip.payslip_data.hours.hourly_rate * 1.5).toFixed(2)}/hr</span></p>
                  </div>
                </div>

                {/* Earnings */}
                <div className="border-b border-gray-600 pb-4">
                  <h5 className="text-lg font-semibold text-yellow-400 mb-2">Earnings</h5>
                  <div className="space-y-1 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-400">Regular Pay:</span>
                      <span className="text-white">${selectedPayslip.payslip_data.earnings.regular_pay.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Overtime Pay:</span>
                      <span className="text-white">${selectedPayslip.payslip_data.earnings.overtime_pay.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between font-semibold text-lg border-t border-gray-700 pt-2 mt-2">
                      <span className="text-green-400">Gross Pay:</span>
                      <span className="text-green-400">${selectedPayslip.payslip_data.earnings.gross_pay.toFixed(2)}</span>
                    </div>
                  </div>
                </div>

                {/* Deductions */}
                <div className="border-b border-gray-600 pb-4">
                  <h5 className="text-lg font-semibold text-yellow-400 mb-2">Deductions</h5>
                  <div className="space-y-1 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-400">Tax Withheld:</span>
                      <span className="text-white">${selectedPayslip.payslip_data.deductions.tax_withheld.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Superannuation:</span>
                      <span className="text-white">${selectedPayslip.payslip_data.deductions.superannuation.toFixed(2)}</span>
                    </div>
                  </div>
                </div>

                {/* Net Pay */}
                <div className="border-b border-gray-600 pb-4">
                  <div className="flex justify-between items-center">
                    <h5 className="text-xl font-bold text-yellow-400">NET PAY:</h5>
                    <span className="text-3xl font-bold text-yellow-400">${selectedPayslip.payslip_data.net_pay.toFixed(2)}</span>
                  </div>
                </div>

                {/* Year to Date */}
                <div className="border-b border-gray-600 pb-4">
                  <h5 className="text-lg font-semibold text-yellow-400 mb-2">Year to Date</h5>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <p className="text-gray-400">Gross Pay: <span className="text-white">${selectedPayslip.payslip_data.year_to_date.gross_pay.toFixed(2)}</span></p>
                    <p className="text-gray-400">Tax Withheld: <span className="text-white">${selectedPayslip.payslip_data.year_to_date.tax_withheld.toFixed(2)}</span></p>
                    <p className="text-gray-400">Superannuation: <span className="text-white">${selectedPayslip.payslip_data.year_to_date.superannuation.toFixed(2)}</span></p>
                    <p className="text-gray-400">Net Pay: <span className="text-white">${selectedPayslip.payslip_data.year_to_date.net_pay.toFixed(2)}</span></p>
                  </div>
                </div>

                {/* Payment Details */}
                <div>
                  <h5 className="text-lg font-semibold text-yellow-400 mb-2">Payment Details</h5>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <p className="text-gray-400">BSB: <span className="text-white">{selectedPayslip.payslip_data.bank_details.bsb}</span></p>
                    <p className="text-gray-400">Account Number: <span className="text-white">{selectedPayslip.payslip_data.bank_details.account_number}</span></p>
                    <p className="text-gray-400" style={{gridColumn: 'span 2'}}>Super Fund: <span className="text-white">{selectedPayslip.payslip_data.bank_details.superannuation_fund}</span></p>
                  </div>
                  <p className="text-xs text-gray-500 mt-4">
                    Generated: {new Date(selectedPayslip.payslip_data.generated_at).toLocaleString()}
                  </p>
                </div>
              </div>

              {/* Modal Actions */}
              <div className="flex justify-end space-x-3 mt-6">
                <button
                  onClick={() => downloadPayslip(selectedPayslip)}
                  className="misty-button misty-button-primary flex items-center"
                >
                  <ArrowDownTrayIcon className="h-4 w-4 mr-2" />
                  Download PDF
                </button>
                <button
                  onClick={() => setShowPayslipModal(false)}
                  className="misty-button misty-button-secondary"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PayrollReports;
