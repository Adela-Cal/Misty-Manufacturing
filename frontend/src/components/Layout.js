import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { apiHelpers } from '../utils/api';
import { toast } from 'sonner';
import { 
  HomeIcon, 
  UsersIcon, 
  ClipboardDocumentListIcon,
  Cog8ToothIcon,
  ChartBarIcon,
  BanknotesIcon,
  DocumentCurrencyDollarIcon,
  ArrowRightOnRectangleIcon,
  UserIcon,
  LinkIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';

const Layout = ({ children }) => {
  const { user, logout, hasPermission } = useAuth();
  const location = useLocation();
  const [xeroConnected, setXeroConnected] = useState(false);
  const [checkingXeroStatus, setCheckingXeroStatus] = useState(true);

  const navigation = [
    { name: 'Dashboard', href: '/', icon: HomeIcon, permission: null },
    { name: 'Clients', href: '/clients', icon: UsersIcon, permission: 'manage_clients' },
    { name: 'Orders', href: '/orders', icon: ClipboardDocumentListIcon, permission: 'create_orders' },
    { name: 'Production', href: '/production', icon: Cog8ToothIcon, permission: 'update_production' },
    { name: 'Invoicing', href: '/invoicing', icon: DocumentCurrencyDollarIcon, permission: 'view_reports' },
    { name: 'Payroll', href: '/payroll', icon: BanknotesIcon, permission: null },
    { name: 'Reports', href: '/reports', icon: ChartBarIcon, permission: 'view_reports' },
  ];

  const filteredNavigation = navigation.filter(item => 
    !item.permission || hasPermission(item.permission)
  );

  // Check Xero connection status on mount
  useEffect(() => {
    checkXeroConnectionStatus();
  }, []);

  const checkXeroConnectionStatus = async () => {
    try {
      const response = await apiHelpers.checkXeroConnection();
      setXeroConnected(response.data.connected);
    } catch (error) {
      console.error('Failed to check Xero status:', error);
      setXeroConnected(false);
    } finally {
      setCheckingXeroStatus(false);
    }
  };

  const handleXeroConnect = async () => {
    try {
      const response = await apiHelpers.getXeroAuthUrl();
      const { auth_url } = response.data;
      
      // Open Xero OAuth in a new window
      const authWindow = window.open(
        auth_url,
        'xero-auth',
        'width=600,height=700,scrollbars=yes,resizable=yes'
      );

      // Listen for the OAuth callback
      const checkClosed = setInterval(() => {
        if (authWindow.closed) {
          clearInterval(checkClosed);
          // Check connection status after auth window closes
          setTimeout(() => {
            checkXeroConnectionStatus();
          }, 1000);
        }
      }, 1000);

    } catch (error) {
      console.error('Failed to initiate Xero connection:', error);
      toast.error('Failed to connect to Xero');
    }
  };

  const handleXeroDisconnect = async () => {
    try {
      await apiHelpers.disconnectXero();
      setXeroConnected(false);
      toast.success('Disconnected from Xero');
    } catch (error) {
      console.error('Failed to disconnect from Xero:', error);
      toast.error('Failed to disconnect from Xero');
    }
  };

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Sidebar */}
      <div className="fixed inset-y-0 left-0 z-50 w-64 bg-gray-800 border-r border-gray-700">
        {/* Logo */}
        <div className="flex items-center h-16 px-4 border-b border-gray-700">
          <div className="flex items-center">
            <img 
              src="/logo.svg" 
              alt="Adela Merchants" 
              className="h-8 w-8 mr-3"
            />
            <div>
              <h1 className="text-lg font-bold text-yellow-400">Misty</h1>
              <p className="text-xs text-gray-400">Manufacturing</p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="mt-8 px-4">
          <ul className="space-y-2">
            {filteredNavigation.map((item) => {
              const isActive = location.pathname === item.href;
              return (
                <li key={item.name}>
                  <Link
                    to={item.href}
                    className={`
                      flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200
                      ${
                        isActive
                          ? 'bg-yellow-400 text-gray-900'
                          : 'text-gray-300 hover:bg-gray-700 hover:text-yellow-400'
                      }
                    `}
                    data-testid={`nav-${item.name.toLowerCase()}`}
                  >
                    <item.icon className="mr-3 h-5 w-5" />
                    {item.name}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* User info and logout */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-700">
          <div className="flex items-center mb-3">
            <div className="h-8 w-8 bg-gray-600 rounded-full flex items-center justify-center mr-3">
              <UserIcon className="h-5 w-5 text-gray-300" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-300 truncate">
                {user?.full_name}
              </p>
              <p className="text-xs text-gray-400 capitalize">
                {user?.role?.replace('_', ' ')}
              </p>
            </div>
          </div>
          <button
            onClick={logout}
            className="w-full flex items-center px-3 py-2 text-sm font-medium text-gray-300 hover:bg-gray-700 hover:text-red-400 rounded-md transition-colors duration-200"
            data-testid="logout-button"
          >
            <ArrowRightOnRectangleIcon className="mr-3 h-5 w-5" />
            Sign out
          </button>
        </div>
      </div>

      {/* Main content */}
      <div className="pl-64">
        <main className="min-h-screen">
          {children}
        </main>
      </div>
    </div>
  );
};

export default Layout;