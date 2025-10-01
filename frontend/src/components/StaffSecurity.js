import React, { useState, useEffect } from 'react';
import Layout from './Layout';
import { useAuth } from '../contexts/AuthContext';
import { apiHelpers } from '../utils/api';
import { payrollApi } from '../utils/payrollApi';
import { toast } from 'sonner';
import { 
  UsersIcon,
  PlusIcon,
  MagnifyingGlassIcon,
  XMarkIcon,
  TrashIcon,
  KeyIcon,
  EyeIcon,
  EyeSlashIcon
} from '@heroicons/react/24/outline';

const StaffSecurity = () => {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [userToDelete, setUserToDelete] = useState(null);
  const [showPasswordForm, setShowPasswordForm] = useState(false);
  const [pendingTimesheets, setPendingTimesheets] = useState([]);
  const [timesheetLoading, setTimesheetLoading] = useState(false);
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    full_name: '',
    role: 'production_staff',
    department: '',
    phone: '',
    employment_type: 'full_time'
  });
  const [passwordData, setPasswordData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: ''
  });
  const [errors, setErrors] = useState({});
  const [showPassword, setShowPassword] = useState(false);

  useEffect(() => {
    loadUsers();
    loadPendingTimesheets();
  }, []);

  const loadUsers = async () => {
    try {
      setLoading(true);
      const response = await apiHelpers.getUsers();
      // Ensure all user fields are properly defined
      const cleanUsers = response.data.map(user => ({
        ...user,
        username: user.username || '',
        email: user.email || '',
        full_name: user.full_name || '',
        role: user.role || 'production_team',
        department: user.department || '',
        phone: user.phone || '',
        employment_type: user.employment_type || 'full_time',
        is_active: user.is_active !== undefined ? user.is_active : true
      }));
      setUsers(cleanUsers);
    } catch (error) {
      console.error('Failed to load users:', error);
      toast.error('Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  const loadPendingTimesheets = async () => {
    try {
      setTimesheetLoading(true);
      const response = await payrollApi.getPendingTimesheets();
      setPendingTimesheets(response.data || []);
    } catch (error) {
      console.error('Failed to load pending timesheets:', error);
      // Don't show error toast as this is secondary functionality
    } finally {
      setTimesheetLoading(false);
    }
  };

  const handleTimesheetApproval = async (timesheetId, action) => {
    try {
      if (action === 'approve') {
        await payrollApi.approveTimesheet(timesheetId);
        toast.success('Timesheet approved successfully');
      } else {
        // For now, we'll just implement approve. Reject can be added later if needed
        toast.info('Reject functionality not yet implemented');
        return;
      }
      
      // Reload pending timesheets
      await loadPendingTimesheets();
    } catch (error) {
      console.error('Failed to process timesheet:', error);
      toast.error('Failed to process timesheet');
    }
  };

  const handleCreate = () => {
    setSelectedUser(null);
    setFormData({
      username: '',
      email: '',
      password: '',
      full_name: '',
      role: 'production_staff',
      department: '',
      phone: '',
      employment_type: 'full_time'
    });
    setErrors({});
    setShowModal(true);
  };

  const handleEdit = (user) => {
    setSelectedUser(user);
    setFormData({
      username: user.username || '',
      email: user.email || '',
      password: '', // Don't populate password for edit
      full_name: user.full_name || '',
      role: user.role || 'production_team',
      department: user.department || '',
      phone: user.phone || '',
      employment_type: user.employment_type || 'full_time'
    });
    setErrors({});
    setShowModal(true);
  };

  const handleDelete = (user) => {
    console.log('Delete button clicked for user:', user);
    setUserToDelete(user);
    setShowDeleteConfirm(true);
  };

  const confirmDelete = async () => {
    if (userToDelete) {
      try {
        console.log('User confirmed deletion, calling API...');
        await apiHelpers.deleteUser(userToDelete.id);
        toast.success('User deleted successfully');
        setShowModal(false);
        setShowDeleteConfirm(false);
        setUserToDelete(null);
        loadUsers();
      } catch (error) {
        console.error('Failed to delete user:', error);
        toast.error('Failed to delete user');
      }
    }
  };

  const cancelDelete = () => {
    console.log('User cancelled deletion');
    setShowDeleteConfirm(false);
    setUserToDelete(null);
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.username.trim()) {
      newErrors.username = 'Username is required';
    }
    
    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Email is not valid';
    }
    
    if (!selectedUser && !formData.password) {
      newErrors.password = 'Password is required for new users';
    } else if (formData.password && formData.password.length < 6) {
      newErrors.password = 'Password must be at least 6 characters';
    }
    
    if (!formData.full_name.trim()) {
      newErrors.full_name = 'Full name is required';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      toast.error('Please fix the errors below');
      return;
    }
    
    try {
      const submitData = { ...formData };
      if (selectedUser && !formData.password) {
        delete submitData.password; // Don't send empty password on update
      }
      
      if (selectedUser) {
        await apiHelpers.updateUser(selectedUser.id, submitData);
        toast.success('User updated successfully');
      } else {
        await apiHelpers.createUser(submitData);
        toast.success('User created successfully');
      }
      
      setShowModal(false);
      loadUsers();
    } catch (error) {
      console.error('Failed to save user:', error);
      
      // Handle validation errors
      if (error.response?.status === 422 && error.response?.data?.detail) {
        const validationErrors = error.response.data.detail;
        const newErrors = {};
        
        if (Array.isArray(validationErrors)) {
          validationErrors.forEach(err => {
            if (err.loc && err.loc.length > 1) {
              const field = err.loc[err.loc.length - 1];
              newErrors[field] = err.msg || 'Invalid value';
            }
          });
          setErrors(newErrors);
          toast.error('Please fix the validation errors');
        } else if (typeof validationErrors === 'string') {
          toast.error(validationErrors);
        } else {
          toast.error('Failed to save user');
        }
      } else {
        let message = 'Failed to save user';
        if (error.response?.data?.detail) {
          // Handle FastAPI validation errors that weren't caught by the 422 check above
          if (Array.isArray(error.response.data.detail)) {
            message = error.response.data.detail
              .map(err => err.msg || err.message || 'Validation error')
              .join(', ');
          } else if (typeof error.response.data.detail === 'string') {
            message = error.response.data.detail;
          }
        }
        toast.error(message);
      }
    }
  };

  const handlePasswordChange = async (e) => {
    e.preventDefault();
    
    if (!passwordData.current_password || !passwordData.new_password) {
      toast.error('Both current and new passwords are required');
      return;
    }
    
    if (passwordData.new_password !== passwordData.confirm_password) {
      toast.error('New passwords do not match');
      return;
    }
    
    if (passwordData.new_password.length < 6) {
      toast.error('New password must be at least 6 characters');
      return;
    }
    
    try {
      await apiHelpers.changePassword({
        current_password: passwordData.current_password,
        new_password: passwordData.new_password
      });
      
      toast.success('Password changed successfully');
      setShowPasswordModal(false);
      setPasswordData({
        current_password: '',
        new_password: '',
        confirm_password: ''
      });
    } catch (error) {
      console.error('Failed to change password:', error);
      toast.error('Failed to change password');
    }
  };

  const filteredUsers = users.filter(user =>
    user.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.full_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const roles = [
    { value: 'admin', label: 'Admin', description: 'Access to everything and anything' },
    { value: 'manager', label: 'Manager', description: 'Ability to do anything other than change privileges' },
    { value: 'supervisor', label: 'Supervisor', description: 'Orders, Production, Calculator and Payroll options' },
    { value: 'production_staff', label: 'Production Staff', description: 'Production Board and Payroll options only' },
    { value: 'sales', label: 'Sales', description: 'Sales and client management functions' }
  ];

  const getRoleInfo = (roleValue) => {
    return roles.find(role => role.value === roleValue) || { label: roleValue, description: '' };
  };

  if (loading) {
    return (
      <Layout>
        <div className="p-8">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-700 rounded w-1/4 mb-8"></div>
            <div className="space-y-4">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="h-16 bg-gray-700 rounded"></div>
              ))}
            </div>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="p-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Staff & Security</h1>
            <p className="text-gray-400">Manage user accounts and access privileges • Double-click any user to edit</p>
          </div>
          <div className="flex space-x-3">
            <button
              onClick={() => setShowPasswordModal(true)}
              className="misty-button misty-button-secondary"
            >
              <KeyIcon className="h-5 w-5 mr-2" />
              Change Password
            </button>
            <button
              onClick={handleCreate}
              className="misty-button misty-button-primary"
            >
              <PlusIcon className="h-5 w-5 mr-2" />
              Add User
            </button>
          </div>
        </div>

        {/* Search */}
        <div className="mb-6">
          <div className="relative max-w-md">
            <MagnifyingGlassIcon className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search users..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="misty-input pl-12 w-full"
            />
          </div>
        </div>

        {/* Users Table */}
        {filteredUsers.length > 0 ? (
          <div className="misty-table">
            <table className="w-full">
              <thead>
                <tr>
                  <th className="py-2 text-sm">Username</th>
                  <th className="py-2 text-sm">Full Name</th>
                  <th className="py-2 text-sm">Email</th>
                  <th className="py-2 text-sm">Role</th>
                  <th className="py-2 text-sm">Department</th>
                  <th className="py-2 text-sm">Employment Type</th>
                  <th className="py-2 text-sm">Status</th>
                </tr>
              </thead>
              <tbody>
                {filteredUsers.map((user) => (
                  <tr 
                    key={user.id}
                    onDoubleClick={() => handleEdit(user)}
                    className="cursor-pointer hover:bg-gray-700/50 transition-colors border-b border-gray-700/50"
                    title="Double-click to edit"
                  >
                    <td className="font-medium text-sm py-2 px-3">{user.username}</td>
                    <td className="text-sm py-2 px-3">{user.full_name}</td>
                    <td className="text-sm py-2 px-3">{user.email}</td>
                    <td className="text-sm py-2 px-3">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        user.role === 'admin' ? 'bg-red-900 text-red-200' :
                        user.role === 'manager' ? 'bg-blue-900 text-blue-200' :
                        user.role === 'supervisor' ? 'bg-green-900 text-green-200' :
                        user.role === 'production_staff' ? 'bg-yellow-900 text-yellow-200' :
                        'bg-gray-700 text-gray-300'
                      }`}>
                        {getRoleInfo(user.role).label}
                      </span>
                    </td>
                    <td className="text-sm py-2 px-3">{user.department || '—'}</td>
                    <td className="text-sm py-2 px-3">
                      <span className="px-2 py-1 rounded text-xs font-medium bg-blue-900 text-blue-200">
                        {user.employment_type ? user.employment_type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()) : 'Full Time'}
                      </span>
                    </td>
                    <td className="text-sm py-2 px-3">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        user.is_active ? 'bg-green-900 text-green-200' : 'bg-red-900 text-red-200'
                      }`}>
                        {user.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-12">
            <div className="mx-auto h-12 w-12 text-gray-400 mb-4">👥</div>
            <h3 className="text-sm font-medium text-gray-300">
              {searchTerm ? 'No users found' : 'No users'}
            </h3>
            <p className="mt-1 text-sm text-gray-400">
              {searchTerm
                ? 'Try adjusting your search criteria.'
                : 'Get started by adding your first user account.'
              }
            </p>
            {!searchTerm && (
              <div className="mt-6">
                <button
                  onClick={handleCreate}
                  className="misty-button misty-button-primary"
                >
                  <PlusIcon className="h-5 w-5 mr-2" />
                  Add User
                </button>
              </div>
            )}
          </div>
        )}

        {/* Timesheet Approval Section - Only visible to managers and admins */}
        {(currentUser?.role === 'manager' || currentUser?.role === 'admin') && (
          <div className="mt-12">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-2xl font-bold text-white mb-2">Timesheet Approvals</h2>
                <p className="text-gray-400">Review and approve submitted timesheets from team members</p>
              </div>
              <button
                onClick={loadPendingTimesheets}
                className="misty-button misty-button-secondary"
                disabled={timesheetLoading}
              >
                {timesheetLoading ? 'Loading...' : 'Refresh'}
              </button>
            </div>

            {pendingTimesheets.length > 0 ? (
              <div className="misty-table">
                <table className="w-full">
                  <thead>
                    <tr>
                      <th className="py-2 text-sm">Employee</th>
                      <th className="py-2 text-sm">Week Period</th>
                      <th className="py-2 text-sm">Total Hours</th>
                      <th className="py-2 text-sm">Overtime</th>
                      <th className="py-2 text-sm">Submitted</th>
                      <th className="py-2 text-sm">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {pendingTimesheets.map((timesheet) => (
                      <tr key={timesheet.id} className="border-b border-gray-700/50">
                        <td className="text-sm py-2 px-3 font-medium">
                          {timesheet.employee_name || 'Unknown Employee'}
                        </td>
                        <td className="text-sm py-2 px-3">
                          {timesheet.week_starting} - {timesheet.week_ending}
                        </td>
                        <td className="text-sm py-2 px-3">
                          {timesheet.total_regular_hours || 0}h
                        </td>
                        <td className="text-sm py-2 px-3">
                          {timesheet.total_overtime_hours || 0}h
                        </td>
                        <td className="text-sm py-2 px-3">
                          {timesheet.submitted_at ? new Date(timesheet.submitted_at).toLocaleDateString() : '—'}
                        </td>
                        <td className="text-sm py-2 px-3">
                          <div className="flex space-x-2">
                            <button
                              onClick={() => handleTimesheetApproval(timesheet.id, 'approve')}
                              className="misty-button misty-button-primary text-xs"
                            >
                              Approve
                            </button>
                            <button
                              onClick={() => handleTimesheetApproval(timesheet.id, 'reject')}
                              className="misty-button misty-button-danger text-xs"
                            >
                              Reject
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
                <div className="mx-auto h-12 w-12 text-gray-400 mb-4">📋</div>
                <h3 className="text-sm font-medium text-gray-300">No Pending Timesheets</h3>
                <p className="mt-1 text-sm text-gray-400">
                  All timesheets have been reviewed or no submissions are pending approval.
                </p>
              </div>
            )}
          </div>
        )}

        {/* User Form Modal */}
        {showModal && (
          <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && setShowModal(false)}>
            <div className="modal-content max-w-2xl max-h-[90vh] overflow-y-auto">
              <form onSubmit={handleSubmit} className="p-6">
                {/* Header */}
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-2xl font-bold text-white">
                    {selectedUser ? 'Edit User Account' : 'Create New User Account'}
                  </h2>
                  <button
                    type="button"
                    onClick={() => setShowModal(false)}
                    className="text-gray-400 hover:text-white transition-colors"
                  >
                    <XMarkIcon className="h-6 w-6" />
                  </button>
                </div>

                {/* Basic Information */}
                <div className="mb-8">
                  <h3 className="text-lg font-semibold text-white mb-4">Basic Information</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-1">
                        Username *
                      </label>
                      <input
                        type="text"
                        name="username"
                        value={formData.username}
                        onChange={handleInputChange}
                        className={`misty-input w-full ${errors.username ? 'border-red-500' : ''}`}
                        placeholder="Enter username"
                        required
                      />
                      {errors.username && (
                        <p className="text-red-400 text-sm mt-1">{String(errors.username)}</p>
                      )}
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-1">
                        Full Name *
                      </label>
                      <input
                        type="text"
                        name="full_name"
                        value={formData.full_name}
                        onChange={handleInputChange}
                        className={`misty-input w-full ${errors.full_name ? 'border-red-500' : ''}`}
                        placeholder="Enter full name"
                        required
                      />
                      {errors.full_name && (
                        <p className="text-red-400 text-sm mt-1">{String(errors.full_name)}</p>
                      )}
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-1">
                        Email *
                      </label>
                      <input
                        type="email"
                        name="email"
                        value={formData.email}
                        onChange={handleInputChange}
                        className={`misty-input w-full ${errors.email ? 'border-red-500' : ''}`}
                        placeholder="Enter email address"
                        required
                      />
                      {errors.email && (
                        <p className="text-red-400 text-sm mt-1">{String(errors.email)}</p>
                      )}
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-1">
                        Phone Number
                      </label>
                      <input
                        type="text"
                        name="phone"
                        value={formData.phone}
                        onChange={handleInputChange}
                        className="misty-input w-full"
                        placeholder="Enter phone number"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-1">
                        Department
                      </label>
                      <input
                        type="text"
                        name="department"
                        value={formData.department}
                        onChange={handleInputChange}
                        className="misty-input w-full"
                        placeholder="Enter department"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-1">
                        Employment Type
                      </label>
                      <select
                        name="employment_type"
                        value={formData.employment_type}
                        onChange={handleInputChange}
                        className="misty-select w-full"
                      >
                        <option value="full_time">Full Time</option>
                        <option value="part_time">Part Time</option>
                        <option value="casual">Casual</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-1">
                        Password {selectedUser ? '' : '*'}
                      </label>
                      <div className="relative">
                        <input
                          type={showPassword ? 'text' : 'password'}
                          name="password"
                          value={formData.password}
                          onChange={handleInputChange}
                          className={`misty-input w-full pr-10 ${errors.password ? 'border-red-500' : ''}`}
                          placeholder={selectedUser ? 'Leave blank to keep current password' : 'Enter password'}
                          required={!selectedUser}
                        />
                        <button
                          type="button"
                          onClick={() => setShowPassword(!showPassword)}
                          className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-white"
                        >
                          {showPassword ? (
                            <EyeSlashIcon className="h-4 w-4" />
                          ) : (
                            <EyeIcon className="h-4 w-4" />
                          )}
                        </button>
                      </div>
                      {errors.password && (
                        <p className="text-red-400 text-sm mt-1">{String(errors.password)}</p>
                      )}
                    </div>
                  </div>
                </div>

                {/* Role & Permissions */}
                <div className="mb-8">
                  <h3 className="text-lg font-semibold text-white mb-4">Role & Permissions</h3>
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-1">
                      User Role *
                    </label>
                    <select
                      name="role"
                      value={formData.role}
                      onChange={handleInputChange}
                      className="misty-select w-full"
                      required
                    >
                      {roles.map(role => (
                        <option key={role.value} value={role.value}>
                          {role.label}
                        </option>
                      ))}
                    </select>
                    {formData.role && (
                      <p className="text-sm text-gray-400 mt-2">
                        <strong>{getRoleInfo(formData.role).label}:</strong> {getRoleInfo(formData.role).description}
                      </p>
                    )}
                  </div>
                </div>

                {/* Form Actions */}
                <div className="flex justify-between pt-6 border-t border-gray-700">
                  <div>
                    {selectedUser && (
                      <button
                        type="button"
                        onClick={(e) => {
                          e.preventDefault();
                          e.stopPropagation();
                          console.log('Delete button clicked, selectedUser:', selectedUser);
                          handleDelete(selectedUser);
                        }}
                        className="misty-button misty-button-danger"
                      >
                        <TrashIcon className="h-4 w-4 mr-2" />
                        Delete User
                      </button>
                    )}
                  </div>
                  <div className="flex space-x-3">
                    <button
                      type="button"
                      onClick={() => setShowModal(false)}
                      className="misty-button misty-button-secondary"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="misty-button misty-button-primary"
                    >
                      {selectedUser ? 'Update User' : 'Create User'}
                    </button>
                  </div>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Password Change Modal */}
        {showPasswordModal && (
          <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && setShowPasswordModal(false)}>
            <div className="modal-content max-w-md">
              <form onSubmit={handlePasswordChange} className="p-6">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-xl font-bold text-white">Change Password</h2>
                  <button
                    type="button"
                    onClick={() => setShowPasswordModal(false)}
                    className="text-gray-400 hover:text-white transition-colors"
                  >
                    <XMarkIcon className="h-6 w-6" />
                  </button>
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-1">
                      Current Password *
                    </label>
                    <input
                      type="password"
                      value={passwordData.current_password}
                      onChange={(e) => setPasswordData({...passwordData, current_password: e.target.value})}
                      className="misty-input w-full"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-1">
                      New Password *
                    </label>
                    <input
                      type="password"
                      value={passwordData.new_password}
                      onChange={(e) => setPasswordData({...passwordData, new_password: e.target.value})}
                      className="misty-input w-full"
                      minLength="6"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-1">
                      Confirm New Password *
                    </label>
                    <input
                      type="password"
                      value={passwordData.confirm_password}
                      onChange={(e) => setPasswordData({...passwordData, confirm_password: e.target.value})}
                      className="misty-input w-full"
                      required
                    />
                  </div>
                </div>

                <div className="flex justify-end space-x-3 pt-6 border-t border-gray-700 mt-6">
                  <button
                    type="button"
                    onClick={() => setShowPasswordModal(false)}
                    className="misty-button misty-button-secondary"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="misty-button misty-button-primary"
                  >
                    Change Password
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Delete Confirmation Modal */}
        {showDeleteConfirm && userToDelete && (
          <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && cancelDelete()}>
            <div className="modal-content max-w-md">
              <div className="p-6">
                <div className="flex items-center mb-4">
                  <div className="flex-shrink-0">
                    <TrashIcon className="h-8 w-8 text-red-400" />
                  </div>
                  <div className="ml-4">
                    <h3 className="text-lg font-semibold text-white">Delete User</h3>
                    <p className="text-sm text-gray-400">This action cannot be undone.</p>
                  </div>
                </div>
                
                <div className="mb-6">
                  <p className="text-gray-300">
                    Are you sure you wish to delete user <span className="font-semibold text-white">"{userToDelete.username}"</span>?
                  </p>
                  <p className="text-sm text-gray-400 mt-2">
                    This will permanently remove the user account and all associated data.
                  </p>
                </div>

                <div className="flex justify-end space-x-3">
                  <button
                    type="button"
                    onClick={cancelDelete}
                    className="misty-button misty-button-secondary"
                  >
                    No, Cancel
                  </button>
                  <button
                    type="button"
                    onClick={confirmDelete}
                    className="misty-button misty-button-danger"
                  >
                    Yes, Delete User
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

      </div>
    </Layout>
  );
};

export default StaffSecurity;