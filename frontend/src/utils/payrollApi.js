import { api } from './api';

// Payroll API helper functions
export const payrollApi = {
  // Employee Management
  getEmployees: () => api.get('/payroll/employees'),
  createEmployee: (data) => api.post('/payroll/employees', data),
  updateEmployee: (id, data) => api.put(`/payroll/employees/${id}`, data),
  getEmployee: (id) => api.get(`/payroll/employees/${id}`),
  getMyEmployeeProfile: () => api.get('/payroll/employees/me/profile'),
  getEmployeeLeaveBalances: (id) => api.get(`/payroll/employees/${id}/leave-balances`),
  
  // Timesheet Management
  getCurrentWeekTimesheet: (employeeId) => api.get(`/payroll/timesheets/current-week/${employeeId}`),
  getEmployeeTimesheets: (employeeId) => api.get(`/payroll/timesheets/employee/${employeeId}`),
  updateTimesheet: (id, data) => api.put(`/payroll/timesheets/${id}`, data),
  submitTimesheet: (id) => api.post(`/payroll/timesheets/${id}/submit`),
  approveTimesheet: (id) => api.post(`/payroll/timesheets/${id}/approve`),
  getPendingTimesheets: () => api.get('/payroll/timesheets/pending'),
  
  // Leave Request Management
  createLeaveRequest: (data) => api.post('/payroll/leave-requests', data),
  getPendingLeaveRequests: () => api.get('/payroll/leave-requests/pending'),
  approveLeaveRequest: (id) => api.post(`/payroll/leave-requests/${id}/approve`),
  rejectLeaveRequest: (id, reason) => api.post(`/payroll/leave-requests/${id}/reject`, { rejection_reason: reason }),
  
  // Reports
  getPayrollSummary: (startDate, endDate) => api.get('/payroll/reports/payroll-summary', { 
    params: { start_date: startDate, end_date: endDate } 
  }),
  getLeaveBalancesReport: () => api.get('/payroll/reports/leave-balances'),
  
  // Dashboard
  getTimesheetReminder: () => api.get('/payroll/dashboard/timesheet-reminder'),
};

// Payroll utility functions
export const payrollUtils = {
  // Leave type display names
  leaveTypeDisplayNames: {
    annual_leave: 'Annual Leave',
    sick_leave: 'Sick Leave',
    personal_leave: 'Personal Leave',
    maternity_leave: 'Maternity Leave',
    paternity_leave: 'Paternity Leave',
    training_leave: 'Training Leave',
    conference_leave: 'Conference Leave',
    compassionate_leave: 'Compassionate Leave',
    unpaid_leave: 'Unpaid Leave'
  },
  
  // Employment type display names
  employmentTypeDisplayNames: {
    full_time: 'Full Time',
    part_time: 'Part Time',
    casual: 'Casual',
    contract: 'Contract'
  },
  
  // Timesheet status display names
  timesheetStatusDisplayNames: {
    draft: 'Draft',
    submitted: 'Submitted',
    approved: 'Approved',
    rejected: 'Rejected',
    paid: 'Paid'
  },
  
  // Leave status display names
  leaveStatusDisplayNames: {
    pending: 'Pending',
    approved: 'Approved',
    rejected: 'Rejected',
    cancelled: 'Cancelled'
  },
  
  // Calculate hours between dates (excluding weekends)
  calculateLeaveHours: (startDate, endDate, dailyHours = 7.6) => {
    const start = new Date(startDate);
    const end = new Date(endDate);
    let totalHours = 0;
    
    for (let date = new Date(start); date <= end; date.setDate(date.getDate() + 1)) {
      // Skip weekends (Saturday = 6, Sunday = 0)
      if (date.getDay() !== 0 && date.getDay() !== 6) {
        totalHours += dailyHours;
      }
    }
    
    return totalHours;
  },
  
  // Format hours as hours and minutes
  formatHours: (hours) => {
    const wholeHours = Math.floor(hours);
    const minutes = Math.round((hours - wholeHours) * 60);
    
    if (minutes === 0) {
      return `${wholeHours}h`;
    } else {
      return `${wholeHours}h ${minutes}m`;
    }
  },
  
  // Calculate pay from hours and rate
  calculatePay: (regularHours, overtimeHours, hourlyRate, overtimeMultiplier = 1.5) => {
    const regularPay = regularHours * hourlyRate;
    const overtimePay = overtimeHours * hourlyRate * overtimeMultiplier;
    return regularPay + overtimePay;
  },
  
  // Get current week dates (Monday to Sunday)
  getCurrentWeekDates: () => {
    const today = new Date();
    const monday = new Date(today);
    monday.setDate(today.getDate() - today.getDay() + 1);
    
    const sunday = new Date(monday);
    sunday.setDate(monday.getDate() + 6);
    
    return { monday, sunday };
  },
  
  // Check if today is timesheet reminder day (Thursday)
  isTimesheetReminderDay: () => {
    return new Date().getDay() === 4; // Thursday
  },
  
  // Validate Australian Tax File Number format
  validateTFN: (tfn) => {
    if (!tfn) return true; // TFN is optional
    
    // Remove spaces and check format
    const cleanTFN = tfn.replace(/\s/g, '');
    
    // Must be 8 or 9 digits
    if (!/^\d{8,9}$/.test(cleanTFN)) {
      return false;
    }
    
    // Basic TFN validation algorithm
    const weights = [1, 4, 3, 7, 5, 8, 6, 9, 10];
    const digits = cleanTFN.split('').map(Number);
    
    let sum = 0;
    for (let i = 0; i < digits.length - 1; i++) {
      sum += digits[i] * weights[i];
    }
    
    const remainder = sum % 11;
    const checkDigit = remainder < 2 ? remainder : 11 - remainder;
    
    return checkDigit === digits[digits.length - 1];
  },
  
  // Validate Australian BSB format
  validateBSB: (bsb) => {
    if (!bsb) return false;
    
    // Remove spaces and hyphens
    const cleanBSB = bsb.replace(/[\s-]/g, '');
    
    // Must be exactly 6 digits
    return /^\d{6}$/.test(cleanBSB);
  },
  
  // Format BSB for display
  formatBSB: (bsb) => {
    if (!bsb) return '';
    
    const cleanBSB = bsb.replace(/[\s-]/g, '');
    if (cleanBSB.length === 6) {
      return `${cleanBSB.slice(0, 3)}-${cleanBSB.slice(3)}`;
    }
    return bsb;
  },
  
  // Calculate superannuation contribution (currently 11% in Australia)
  calculateSuperannuation: (grossPay, rate = 0.11) => {
    return grossPay * rate;
  },
  
  // Calculate leave accrual based on hours worked
  calculateLeaveAccrual: (hoursWorked, annualEntitlement, fullTimeHours = 38) => {
    const workFraction = hoursWorked / fullTimeHours;
    const weeklyAccrual = annualEntitlement / 52;
    return weeklyAccrual * workFraction;
  }
};

// Payroll form validation schemas
export const payrollValidation = {
  employee: {
    firstName: (value) => {
      if (!value?.trim()) return 'First name is required';
      if (value.length < 2) return 'First name must be at least 2 characters';
      return null;
    },
    lastName: (value) => {
      if (!value?.trim()) return 'Last name is required';
      if (value.length < 2) return 'Last name must be at least 2 characters';
      return null;
    },
    email: (value) => {
      if (!value?.trim()) return 'Email is required';
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(value)) return 'Please enter a valid email address';
      return null;
    },
    employeeNumber: (value) => {
      if (!value?.trim()) return 'Employee number is required';
      if (value.length < 3) return 'Employee number must be at least 3 characters';
      return null;
    },
    hourlyRate: (value) => {
      if (!value || value <= 0) return 'Hourly rate must be greater than 0';
      if (value > 1000) return 'Hourly rate seems unusually high';
      return null;
    },
    tfn: (value) => {
      if (value && !payrollUtils.validateTFN(value)) {
        return 'Please enter a valid Tax File Number';
      }
      return null;
    },
    bsb: (value) => {
      if (value && !payrollUtils.validateBSB(value)) {
        return 'Please enter a valid BSB (6 digits)';
      }
      return null;
    }
  },
  
  timesheet: {
    hours: (value) => {
      if (value < 0) return 'Hours cannot be negative';
      if (value > 24) return 'Hours cannot exceed 24 per day';
      return null;
    },
    weeklyHours: (totalHours) => {
      if (totalHours > 80) return 'Weekly hours seem unusually high (over 80 hours)';
      return null;
    }
  },
  
  leaveRequest: {
    hours: (value) => {
      if (!value || value <= 0) return 'Hours requested must be greater than 0';
      if (value > 400) return 'Leave hours seem unusually high';
      return null;
    },
    dateRange: (startDate, endDate) => {
      if (!startDate || !endDate) return 'Both start and end dates are required';
      if (new Date(endDate) < new Date(startDate)) {
        return 'End date must be after start date';
      }
      return null;
    }
  }
};