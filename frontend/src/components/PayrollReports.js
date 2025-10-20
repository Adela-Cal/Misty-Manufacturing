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
  BuildingLibraryIcon
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
      const response = await fetch('/api/payroll/reports/payslips', {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      if (response.ok) {
        const result = await response.json();
        setPayslips(result.data || []);
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
      const response = await fetch(`/api/payroll/reports/payslip/${timesheetId}`, {
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
      let url = '/api/payroll/reports/timesheets?';
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
      const response = await fetch('/api/payroll/leave-adjustments', {
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

  const downloadPayslip = (payslip) => {
    const data = payslip.payslip_data;
    const content = `
PAYSLIP
================================================================
${data.employee.name} - ${data.employee.employee_number}
${data.employee.position} - ${data.employee.department}

PAY PERIOD: ${data.pay_period.week_start} to ${data.pay_period.week_end}
================================================================

HOURS WORKED:
  Regular Hours:    ${data.hours.regular_hours} @ $${data.hours.hourly_rate}/hr
  Overtime Hours:   ${data.hours.overtime_hours} @ $${(data.hours.hourly_rate * 1.5).toFixed(2)}/hr

EARNINGS:
  Regular Pay:      $${data.earnings.regular_pay.toFixed(2)}
  Overtime Pay:     $${data.earnings.overtime_pay.toFixed(2)}
  Gross Pay:        $${data.earnings.gross_pay.toFixed(2)}

DEDUCTIONS:
  Tax Withheld:     $${data.deductions.tax_withheld.toFixed(2)}
  Superannuation:   $${data.deductions.superannuation.toFixed(2)}

NET PAY:            $${data.net_pay.toFixed(2)}

YEAR TO DATE:
  Gross Pay:        $${data.year_to_date.gross_pay.toFixed(2)}
  Tax Withheld:     $${data.year_to_date.tax_withheld.toFixed(2)}
  Superannuation:   $${data.year_to_date.superannuation.toFixed(2)}
  Net Pay:          $${data.year_to_date.net_pay.toFixed(2)}

PAYMENT DETAILS:
  BSB:              ${data.bank_details.bsb}
  Account Number:   ${data.bank_details.account_number}
  Super Fund:       ${data.bank_details.superannuation_fund}
  TFN:              ${data.employee.tax_file_number}

Generated: ${new Date(data.generated_at).toLocaleString()}
================================================================
    `;

    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `payslip_${data.employee.employee_number}_${data.pay_period.week_start}.txt`;
    a.click();
    URL.revokeObjectURL(url);
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
          Timesheets
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
                          <button
                            onClick={() => downloadPayslip(payslip)}
                            className="text-blue-400 hover:text-blue-300 flex items-center text-sm"
                          >
                            <ArrowDownTrayIcon className="h-4 w-4 mr-1" />
                            Download
                          </button>
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

      {/* Timesheets Report Tab */}
      {activeReportTab === 'timesheets' && (
        <div>
          <h3 className="text-xl font-semibold text-white mb-4">Timesheet Report</h3>
          
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
                            toast.info('Bank details management coming soon');
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
    </div>
  );
};

export default PayrollReports;
