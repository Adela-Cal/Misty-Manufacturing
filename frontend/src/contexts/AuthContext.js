import React, { createContext, useContext, useState, useEffect } from 'react';
import { api } from '../utils/api';
import { toast } from 'sonner';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [refreshToken, setRefreshToken] = useState(localStorage.getItem('refreshToken'));

  // Auto-refresh token before expiry
  useEffect(() => {
    if (!token || !refreshToken) return;
    
    try {
      // Parse JWT to get expiry time
      const tokenData = JSON.parse(atob(token.split('.')[1]));
      const expiryTime = tokenData.exp * 1000; // Convert to milliseconds
      const currentTime = Date.now();
      const timeUntilExpiry = expiryTime - currentTime;
      
      // Refresh 5 minutes before expiry
      const refreshTime = timeUntilExpiry - (5 * 60 * 1000);
      
      if (refreshTime > 0) {
        const timeoutId = setTimeout(async () => {
          await refreshAccessToken();
        }, refreshTime);
        
        return () => clearTimeout(timeoutId);
      } else if (timeUntilExpiry > 0) {
        // Token expires soon, refresh immediately
        refreshAccessToken();
      }
    } catch (error) {
      console.error('Error parsing token for auto-refresh:', error);
    }
  }, [token, refreshToken]);

  useEffect(() => {
    if (token) {
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchCurrentUser();
    } else {
      setLoading(false);
    }
  }, [token]);

  const fetchCurrentUser = async () => {
    try {
      const response = await api.get('/auth/me');
      setUser(response.data);
    } catch (error) {
      console.error('Failed to fetch current user:', error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const refreshAccessToken = async () => {
    try {
      console.log('Refreshing access token...');
      const response = await api.post(`/auth/refresh?refresh_token=${refreshToken}`);
      const { access_token, refresh_token: newRefreshToken } = response.data;
      
      localStorage.setItem('token', access_token);
      setToken(access_token);
      api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      // Update refresh token if it was rotated
      if (newRefreshToken && newRefreshToken !== refreshToken) {
        localStorage.setItem('refreshToken', newRefreshToken);
        setRefreshToken(newRefreshToken);
      }
      
      console.log('Access token refreshed successfully');
      return true;
    } catch (error) {
      console.error('Token refresh failed:', error);
      toast.error('Your session has expired. Please log in again.');
      logout();
      return false;
    }
  };

  const login = async (credentials) => {
    try {
      const response = await api.post('/auth/login', credentials);
      const { access_token, refresh_token, user: userData } = response.data;
      
      localStorage.setItem('token', access_token);
      localStorage.setItem('refreshToken', refresh_token);
      setToken(access_token);
      setRefreshToken(refresh_token);
      setUser(userData);
      api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      toast.success(`Welcome back, ${userData.full_name}!`);
      return { success: true };
    } catch (error) {
      const message = error.response?.data?.detail || 'Login failed';
      toast.error(message);
      return { success: false, error: message };
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('refreshToken');
    setToken(null);
    setRefreshToken(null);
    setUser(null);
    delete api.defaults.headers.common['Authorization'];
    toast.info('Logged out successfully');
  };

  const hasPermission = (permission) => {
    if (!user) return false;
    
    const role = user.role;
    
    switch (permission) {
      case 'admin':
        return role === 'admin';
      case 'manage_clients':
        return ['admin', 'sales', 'manager'].includes(role);
      case 'create_orders':
        return ['admin', 'production_manager', 'sales', 'manager'].includes(role);
      case 'update_production':
        return ['admin', 'production_manager', 'production_team', 'production_staff', 'manager'].includes(role);
      case 'invoice':
        return ['admin', 'production_manager', 'manager'].includes(role);
      case 'view_reports':
        return ['admin', 'production_manager', 'sales', 'manager'].includes(role);
      case 'delete_orders':
        return ['admin', 'production_manager'].includes(role);
      case 'manage_payroll':
        return ['admin', 'manager'].includes(role);
      case 'view_all_timesheets':
        return ['admin', 'production_manager', 'manager'].includes(role);
      case 'approve_leave':
        return ['admin', 'production_manager', 'manager'].includes(role);
      case 'view_payroll_reports':
        return ['admin', 'manager'].includes(role);
      case 'submit_timesheet':
        return ['admin', 'manager', 'production_manager', 'employee', 'production_staff'].includes(role);
      case 'view_dashboard':
        return true; // All authenticated users
      case 'view_production_board':
        return ['admin', 'production_manager', 'production_team', 'production_staff', 'manager'].includes(role);
      case 'use_calculators':
        return ['admin', 'production_manager', 'production_team', 'production_staff', 'manager', 'sales'].includes(role);
      case 'use_label_designer':
        return ['admin', 'production_manager', 'production_team', 'production_staff', 'manager'].includes(role);
      case 'access_payroll':
        return true; // All users can access their own timesheets
      default:
        return true;
    }
  };

  const value = {
    user,
    loading,
    login,
    logout,
    hasPermission
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};