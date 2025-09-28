import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import './App.css';
import { Toaster } from 'sonner';
import Login from './components/Login';
import Dashboard from './components/Dashboard';
import ClientManagement from './components/ClientManagement';
import OrderManagement from './components/OrderManagement';
import ProductionBoard from './components/ProductionBoard';
import Reports from './components/Reports';
import MaterialsManagement from './components/MaterialsManagement';
import SuppliersManagement from './components/SuppliersManagement';
import ProductSpecifications from './components/ProductSpecifications';
import Calculators from './components/Calculators';
import Stocktake from './components/Stocktake';
import PayrollManagement from './components/PayrollManagement';
import Invoicing from './components/Invoicing';
import StaffSecurity from './components/StaffSecurity';
import XeroCallback from './components/XeroCallback';
import { AuthProvider, useAuth } from './contexts/AuthContext';

function AppRoutes() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-yellow-400"></div>
      </div>
    );
  }

  if (!user) {
    return <Login />;
  }

  return (
    <div className="min-h-screen bg-gray-900">
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/clients" element={<ClientManagement />} />
        <Route path="/orders" element={<OrderManagement />} />
        <Route path="/production" element={<ProductionBoard />} />
        <Route path="/invoicing" element={<Invoicing />} />
        <Route path="/reports" element={<Reports />} />
        <Route path="/products-materials" element={<MaterialsManagement />} />
        <Route path="/suppliers" element={<SuppliersManagement />} />
        <Route path="/product-specifications" element={<ProductSpecifications />} />
        <Route path="/calculators" element={<Calculators />} />
        <Route path="/stocktake" element={<Stocktake />} />
        <Route path="/payroll" element={<PayrollManagement />} />
        <Route path="/xero/callback" element={<XeroCallback />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <div className="App">
          <AppRoutes />
          <Toaster 
            position="top-right" 
            theme="dark"
            toastOptions={{
              style: {
                background: '#1f2937',
                color: '#f9fafb',
                border: '1px solid #374151',
              },
            }}
          />
        </div>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;