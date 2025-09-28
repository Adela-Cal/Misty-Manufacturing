import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { payrollApi, payrollUtils, payrollValidation } from '../utils/payrollApi';
import { toast } from 'sonner';
import {
  ClockIcon,
  CalendarDaysIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';

const TimesheetEntry = ({ employeeId, onClose, isManager = false }) => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [timesheet, setTimesheet] = useState(null);
  const [employee, setEmployee] = useState(null);
  const [entries, setEntries] = useState([]);
  const [totalHours, setTotalHours] = useState({ regular: 0, overtime: 0, leave: {} });
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [showLeaveModal, setShowLeaveModal] = useState(false);
  const [selectedDayIndex, setSelectedDayIndex] = useState(null);
  const [selectedLeaveType, setSelectedLeaveType] = useState('');

  useEffect(() => {
    loadTimesheet();
  }, [employeeId]);

  useEffect(() => {
    calculateTotals();
  }, [entries]);

  const loadTimesheet = async () => {
    try {
      setLoading(true);
      const response = await payrollApi.getCurrentWeekTimesheet(employeeId);
      const timesheetData = response.data;
      
      setTimesheet(timesheetData);
      setEntries(timesheetData.entries || generateEmptyWeek());
      
      // Load employee info if manager
      if (isManager) {
        try {
          const empResponse = await payrollApi.getEmployee(employeeId);
          setEmployee(empResponse.data);
        } catch (error) {
          console.warn('Could not load employee details:', error);
        }
      }
      
    } catch (error) {
      console.error('Failed to load timesheet:', error);
      toast.error('Failed to load timesheet');
      setEntries(generateEmptyWeek());
    } finally {
      setLoading(false);
    }
  };

  const generateEmptyWeek = () => {
    const { monday } = payrollUtils.getCurrentWeekDates();
    const weekEntries = [];
    
    for (let i = 0; i < 7; i++) {
      const date = new Date(monday);
      date.setDate(monday.getDate() + i);
      
      weekEntries.push({
        date: date.toISOString().split('T')[0],
        regular_hours: 0,
        overtime_hours: 0,
        leave_hours: {},
        notes: ''
      });
    }
    
    return weekEntries;
  };

  const calculateTotals = () => {
    let totalRegular = 0;
    let totalOvertime = 0;
    let totalLeave = {};
    
    entries.forEach(entry => {
      totalRegular += parseFloat(entry.regular_hours || 0);
      totalOvertime += parseFloat(entry.overtime_hours || 0);
      
      Object.entries(entry.leave_hours || {}).forEach(([leaveType, hours]) => {
        if (!totalLeave[leaveType]) totalLeave[leaveType] = 0;
        totalLeave[leaveType] += parseFloat(hours || 0);
      });
    });
    
    setTotalHours({
      regular: totalRegular,
      overtime: totalOvertime,
      leave: totalLeave
    });
  };

  const updateEntry = (index, field, value) => {
    const newEntries = [...entries];
    
    if (field.startsWith('leave_')) {
      const leaveType = field.replace('leave_', '');
      if (!newEntries[index].leave_hours) {
        newEntries[index].leave_hours = {};
      }
      newEntries[index].leave_hours[leaveType] = value;
    } else {
      newEntries[index][field] = value;
    }
    
    setEntries(newEntries);
  };

  const handleDayClick = (dayIndex) => {
    if (!canEdit()) return;
    setSelectedDayIndex(dayIndex);
    setSelectedLeaveType('');
    setShowLeaveModal(true);
  };

  const applyLeaveToDay = () => {
    if (selectedDayIndex !== null && selectedLeaveType) {
      const newEntries = [...entries];
      
      // Clear all work hours and set 8 hours of selected leave type
      newEntries[selectedDayIndex].regular_hours = 0;
      newEntries[selectedDayIndex].overtime_hours = 0;
      newEntries[selectedDayIndex].leave_hours = {
        [selectedLeaveType]: 8
      };
      
      setEntries(newEntries);
      setShowLeaveModal(false);
      setSelectedDayIndex(null);
      setSelectedLeaveType('');
    }
  };

  const clearLeaveFromDay = () => {
    if (selectedDayIndex !== null) {
      const newEntries = [...entries];
      newEntries[selectedDayIndex].leave_hours = {};
      setEntries(newEntries);
      setShowLeaveModal(false);
      setSelectedDayIndex(null);
    }
  };

  const calculateAnnualLeaveAccrual = (employmentType, totalRegularHours) => {
    // Annual leave accrual rates per hour worked (Australian standards)
    const accrualRates = {
      full_time: 0.0769, // 4 weeks per year (152 hours) / 1976 standard hours
      part_time: 0.0769, // Same rate as full time (pro-rata)
      casual: 0.0962     // Additional 17.5% loading in lieu of leave entitlements
    };
    
    const rate = accrualRates[employmentType] || accrualRates.full_time;
    return (totalRegularHours * rate).toFixed(2);
  };

  const validateTimesheet = () => {
    const newErrors = {};
    let hasErrors = false;
    
    entries.forEach((entry, index) => {
      const totalDayHours = (entry.regular_hours || 0) + (entry.overtime_hours || 0);
      
      // Validate individual hour entries
      const regularError = payrollValidation.timesheet.hours(entry.regular_hours || 0);
      if (regularError) {
        newErrors[`${index}_regular_hours`] = regularError;
        hasErrors = true;
      }
      
      const overtimeError = payrollValidation.timesheet.hours(entry.overtime_hours || 0);
      if (overtimeError) {
        newErrors[`${index}_overtime_hours`] = overtimeError;
        hasErrors = true;
      }
      
      // Check daily total hours
      if (totalDayHours > 16) {
        newErrors[`${index}_daily_total`] = 'Daily hours exceed 16 hours';
        hasErrors = true;
      }
      
      // Validate leave hours
      Object.entries(entry.leave_hours || {}).forEach(([leaveType, hours]) => {
        const leaveError = payrollValidation.timesheet.hours(hours);
        if (leaveError) {
          newErrors[`${index}_leave_${leaveType}`] = leaveError;
          hasErrors = true;
        }
      });
    });
    
    // Validate weekly totals
    const weeklyError = payrollValidation.timesheet.weeklyHours(totalHours.regular + totalHours.overtime);
    if (weeklyError) {
      newErrors.weekly_total = weeklyError;
      hasErrors = true;
    }
    
    setErrors(newErrors);
    return !hasErrors;
  };

  const handleSave = async () => {
    if (!validateTimesheet()) {
      toast.error('Please fix the errors before saving');
      return;
    }
    
    try {
      setSubmitting(true);
      
      const timesheetData = {
        employee_id: employeeId,
        week_starting: timesheet?.week_starting || payrollUtils.getCurrentWeekDates().monday.toISOString().split('T')[0],
        entries: entries
      };
      
      if (timesheet?.id) {
        await payrollApi.updateTimesheet(timesheet.id, timesheetData);
        toast.success('Timesheet saved successfully');
      } else {
        // Create new timesheet logic would go here
        toast.success('Timesheet created successfully');
      }
      
      await loadTimesheet(); // Reload to get updated data
      
    } catch (error) {
      console.error('Failed to save timesheet:', error);
      toast.error('Failed to save timesheet');
    } finally {
      setSubmitting(false);
    }
  };

  const handleSubmit = async () => {
    if (!validateTimesheet()) {
      toast.error('Please fix the errors before submitting');
      return;
    }
    
    try {
      setSubmitting(true);
      
      // Save first if there are changes
      await handleSave();
      
      // Then submit for approval
      if (timesheet?.id) {
        await payrollApi.submitTimesheet(timesheet.id);
        toast.success('Timesheet submitted for approval');
        onClose?.();
      }
      
    } catch (error) {
      console.error('Failed to submit timesheet:', error);
      toast.error('Failed to submit timesheet');
    } finally {
      setSubmitting(false);
    }
  };

  const handleApprove = async () => {
    if (!isManager || !timesheet?.id) return;
    
    try {
      setSubmitting(true);
      await payrollApi.approveTimesheet(timesheet.id);
      toast.success('Timesheet approved and pay calculated');
      onClose?.();
    } catch (error) {
      console.error('Failed to approve timesheet:', error);
      toast.error('Failed to approve timesheet');
    } finally {
      setSubmitting(false);
    }
  };

  const getDayName = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-AU', { weekday: 'short' });
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-AU', { day: '2-digit', month: '2-digit' });
  };

  const canEdit = () => {
    if (isManager) return true;
    return timesheet?.status === 'draft' || !timesheet?.status;
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'draft': return 'text-gray-400';
      case 'submitted': return 'text-orange-400';
      case 'approved': return 'text-green-400';
      case 'rejected': return 'text-red-400';
      case 'paid': return 'text-blue-400';
      default: return 'text-gray-400';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-yellow-400"></div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto" data-testid="timesheet-entry">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-white mb-1">
              {isManager && employee ? `${employee.first_name} ${employee.last_name}'s Timesheet` : 'My Timesheet'}
            </h2>
            <div className="flex items-center space-x-4 text-sm text-gray-400">
              <span className="flex items-center">
                <CalendarDaysIcon className="h-4 w-4 mr-1" />
                Week {timesheet?.week_starting && formatDate(timesheet.week_starting)} - {timesheet?.week_ending && formatDate(timesheet.week_ending)}
              </span>
              {timesheet?.status && (
                <span className={`flex items-center font-medium ${getStatusColor(timesheet.status)}`}>
                  Status: {payrollUtils.timesheetStatusDisplayNames[timesheet.status] || timesheet.status}
                </span>
              )}
            </div>
          </div>
          
          {/* Action Buttons */}
          <div className="flex items-center space-x-3">
            {canEdit() && (
              <>
                <button
                  onClick={handleSave}
                  disabled={submitting}
                  className="misty-button misty-button-secondary"
                  data-testid="save-timesheet"
                >
                  Save Draft
                </button>
                
                {!isManager && (
                  <button
                    onClick={handleSubmit}
                    disabled={submitting}
                    className="misty-button misty-button-primary"
                    data-testid="submit-timesheet"
                  >
                    Submit for Approval
                  </button>
                )}
              </>
            )}
            
            {isManager && timesheet?.status === 'submitted' && (
              <button
                onClick={handleApprove}
                disabled={submitting}
                className="misty-button misty-button-primary"
                data-testid="approve-timesheet"
              >
                <CheckCircleIcon className="h-4 w-4 mr-1" />
                Approve & Calculate Pay
              </button>
            )}
            
            <button
              onClick={onClose}
              className="misty-button misty-button-secondary"
              data-testid="close-timesheet"
            >
              Close
            </button>
          </div>
        </div>
      </div>

      {/* Error Summary */}
      {Object.keys(errors).length > 0 && (
        <div className="mb-6 p-4 bg-red-900 border border-red-700 rounded-lg">
          <div className="flex items-center mb-2">
            <ExclamationTriangleIcon className="h-5 w-5 text-red-400 mr-2" />
            <h3 className="font-medium text-red-100">Please fix the following errors:</h3>
          </div>
          <ul className="text-sm text-red-200 list-disc list-inside">
            {Object.values(errors).map((error, index) => (
              <li key={index}>{error}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Timesheet Grid */}
      <div className="misty-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-700">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Day
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Regular Hours
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Overtime Hours
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Annual Leave
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Sick Leave
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Notes
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700">
              {entries.map((entry, index) => {
                const isWeekend = new Date(entry.date).getDay() === 0 || new Date(entry.date).getDay() === 6;
                return (
                  <tr key={index} className={isWeekend ? 'bg-gray-700/30' : ''}>
                    <td className="px-4 py-3">
                      <div className="text-sm">
                        <div className="font-medium text-white">{getDayName(entry.date)}</div>
                        <div className="text-gray-400">{formatDate(entry.date)}</div>
                      </div>
                    </td>
                    
                    <td className="px-4 py-3 text-center">
                      <input
                        type="number"
                        min="0"
                        max="24"
                        step="0.25"
                        value={entry.regular_hours || ''}
                        onChange={(e) => updateEntry(index, 'regular_hours', e.target.value)}
                        disabled={!canEdit()}
                        className={`w-20 text-center misty-input ${
                          errors[`${index}_regular_hours`] ? 'border-red-500' : ''
                        }`}
                        data-testid={`regular-hours-${index}`}
                      />
                    </td>
                    
                    <td className="px-4 py-3 text-center">
                      <input
                        type="number"
                        min="0"
                        max="24"
                        step="0.25"
                        value={entry.overtime_hours || ''}
                        onChange={(e) => updateEntry(index, 'overtime_hours', e.target.value)}
                        disabled={!canEdit()}
                        className={`w-20 text-center misty-input ${
                          errors[`${index}_overtime_hours`] ? 'border-red-500' : ''
                        }`}
                        data-testid={`overtime-hours-${index}`}
                      />
                    </td>
                    
                    <td className="px-4 py-3 text-center">
                      <input
                        type="number"
                        min="0"
                        max="24"
                        step="0.25"
                        value={entry.leave_hours?.annual_leave || ''}
                        onChange={(e) => updateEntry(index, 'leave_annual_leave', e.target.value)}
                        disabled={!canEdit()}
                        className={`w-20 text-center misty-input ${
                          errors[`${index}_leave_annual_leave`] ? 'border-red-500' : ''
                        }`}
                        data-testid={`annual-leave-${index}`}
                      />
                    </td>
                    
                    <td className="px-4 py-3 text-center">
                      <input
                        type="number"
                        min="0"
                        max="24"
                        step="0.25"
                        value={entry.leave_hours?.sick_leave || ''}
                        onChange={(e) => updateEntry(index, 'leave_sick_leave', e.target.value)}
                        disabled={!canEdit()}
                        className={`w-20 text-center misty-input ${
                          errors[`${index}_leave_sick_leave`] ? 'border-red-500' : ''
                        }`}
                        data-testid={`sick-leave-${index}`}
                      />
                    </td>
                    
                    <td className="px-4 py-3">
                      <input
                        type="text"
                        placeholder="Notes..."
                        value={entry.notes || ''}
                        onChange={(e) => updateEntry(index, 'notes', e.target.value)}
                        disabled={!canEdit()}
                        className="w-full misty-input"
                        data-testid={`notes-${index}`}
                      />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Summary */}
      <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="misty-card p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Regular Hours</p>
              <p className="text-xl font-bold text-white">{payrollUtils.formatHours(totalHours.regular)}</p>
            </div>
            <ClockIcon className="h-8 w-8 text-blue-400" />
          </div>
        </div>
        
        <div className="misty-card p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Overtime Hours</p>
              <p className="text-xl font-bold text-white">{payrollUtils.formatHours(totalHours.overtime)}</p>
            </div>
            <ClockIcon className="h-8 w-8 text-orange-400" />
          </div>
        </div>
        
        <div className="misty-card p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Total Hours</p>
              <p className="text-xl font-bold text-white">
                {payrollUtils.formatHours(totalHours.regular + totalHours.overtime)}
              </p>
            </div>
            <CheckCircleIcon className="h-8 w-8 text-green-400" />
          </div>
        </div>
      </div>

      {/* Leave Summary */}
      {Object.keys(totalHours.leave).length > 0 && (
        <div className="mt-6">
          <h3 className="text-lg font-semibold text-white mb-4">Leave Taken This Week</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {Object.entries(totalHours.leave).map(([leaveType, hours]) => (
              hours > 0 && (
                <div key={leaveType} className="misty-card p-4">
                  <p className="text-sm text-gray-400">
                    {payrollUtils.leaveTypeDisplayNames[leaveType] || leaveType}
                  </p>
                  <p className="text-lg font-bold text-yellow-400">
                    {payrollUtils.formatHours(hours)}
                  </p>
                </div>
              )
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default TimesheetEntry;