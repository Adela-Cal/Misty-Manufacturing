import React, { useState, useEffect } from 'react';
import Layout from './Layout';
import { apiHelpers, formatCurrency, formatDate, stageDisplayNames } from '../utils/api';
import { toast } from 'sonner';
import { 
  PlusIcon, 
  EyeIcon, 
  DocumentArrowDownIcon,
  MagnifyingGlassIcon
} from '@heroicons/react/24/outline';

const OrderManagement = () => {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState(null);

  useEffect(() => {
    loadOrders();
  }, [statusFilter]);

  const loadOrders = async () => {
    try {
      setLoading(true);
      const response = await apiHelpers.getOrders(statusFilter);
      setOrders(response.data);
    } catch (error) {
      console.error('Failed to load orders:', error);
      toast.error('Failed to load orders');
    } finally {
      setLoading(false);
    }
  };

  const handleViewOrder = (order) => {
    setSelectedOrder(order);
    setShowModal(true);
  };

  const handleDownloadAcknowledgment = async (orderId, orderNumber) => {
    try {
      const response = await apiHelpers.generateAcknowledgment(orderId);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.download = `acknowledgment_${orderNumber}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      toast.success('Acknowledgment downloaded successfully');
    } catch (error) {
      console.error('Failed to download acknowledgment:', error);
      toast.error('Failed to download acknowledgment');
    }
  };

  const filteredOrders = orders.filter(order => 
    order.order_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
    order.client_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'text-green-400';
      case 'completed': return 'text-blue-400';
      case 'cancelled': return 'text-red-400';
      case 'overdue': return 'text-orange-400';
      default: return 'text-gray-400';
    }
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
      <div className="p-8" data-testid="order-management">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Order Management</h1>
            <p className="text-gray-400">Track and manage all manufacturing orders</p>
          </div>
          <button
            className="misty-button misty-button-primary flex items-center"
            data-testid="add-order-button"
          >
            <PlusIcon className="h-5 w-5 mr-2" />
            New Order
          </button>
        </div>

        {/* Filters */}
        <div className="mb-6 flex flex-col sm:flex-row gap-4">
          <div className="relative flex-1">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search orders..."
              className="misty-input pl-10 w-full"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              data-testid="order-search"
            />
          </div>
          <select
            className="misty-select"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            data-testid="status-filter"
          >
            <option value="">All Statuses</option>
            <option value="active">Active</option>
            <option value="completed">Completed</option>
            <option value="cancelled">Cancelled</option>
            <option value="overdue">Overdue</option>
          </select>
        </div>

        {/* Orders Table */}
        {filteredOrders.length > 0 ? (
          <div className="misty-table">
            <table className="w-full">
              <thead>
                <tr>
                  <th>Order #</th>
                  <th>Client</th>
                  <th>Amount</th>
                  <th>Status</th>
                  <th>Stage</th>
                  <th>Due Date</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredOrders.map((order) => (
                  <tr key={order.id} data-testid={`order-row-${order.id}`}>
                    <td className="font-medium">{order.order_number}</td>
                    <td>{order.client_name}</td>
                    <td className="font-medium text-yellow-400">
                      {formatCurrency(order.total_amount)}
                    </td>
                    <td>
                      <span className={`capitalize ${getStatusColor(order.status)}`}>
                        {order.status}
                      </span>
                    </td>
                    <td>
                      <span className="text-sm bg-gray-600 px-2 py-1 rounded">
                        {stageDisplayNames[order.current_stage] || order.current_stage}
                      </span>
                    </td>
                    <td>{formatDate(order.due_date)}</td>
                    <td>
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => handleViewOrder(order)}
                          className="text-gray-400 hover:text-yellow-400 transition-colors"
                          data-testid={`view-order-${order.id}`}
                        >
                          <EyeIcon className="h-5 w-5" />
                        </button>
                        <button
                          onClick={() => handleDownloadAcknowledgment(order.id, order.order_number)}
                          className="text-gray-400 hover:text-blue-400 transition-colors"
                          data-testid={`download-acknowledgment-${order.id}`}
                        >
                          <DocumentArrowDownIcon className="h-5 w-5" />
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
            <DocumentArrowDownIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-300">No orders found</h3>
            <p className="mt-1 text-sm text-gray-400">
              {searchTerm ? 'Try adjusting your search criteria.' : 'Get started by creating a new order.'}
            </p>
          </div>
        )}
      </div>

      {/* Order Details Modal */}
      {showModal && selectedOrder && (
        <div className="modal-overlay">
          <div className="modal-content max-w-4xl">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-bold text-white">
                  Order Details - {selectedOrder.order_number}
                </h2>
                <button
                  onClick={() => setShowModal(false)}
                  className="text-gray-400 hover:text-white"
                >
                  ×
                </button>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h3 className="font-semibold text-white mb-3">Order Information</h3>
                  <div className="space-y-2 text-sm">
                    <p><span className="text-gray-400">Client:</span> {selectedOrder.client_name}</p>
                    <p><span className="text-gray-400">Total:</span> {formatCurrency(selectedOrder.total_amount)}</p>
                    <p><span className="text-gray-400">Status:</span> 
                      <span className={`ml-1 capitalize ${getStatusColor(selectedOrder.status)}`}>
                        {selectedOrder.status}
                      </span>
                    </p>
                    <p><span className="text-gray-400">Stage:</span> {stageDisplayNames[selectedOrder.current_stage]}</p>
                    <p><span className="text-gray-400">Due Date:</span> {formatDate(selectedOrder.due_date)}</p>
                  </div>
                </div>
                
                <div>
                  <h3 className="font-semibold text-white mb-3">Order Items</h3>
                  <div className="space-y-2">
                    {selectedOrder.items.map((item, index) => (
                      <div key={index} className="flex justify-between text-sm">
                        <span className="text-gray-300">{item.product_name} (x{item.quantity})</span>
                        <span className="text-yellow-400">{formatCurrency(item.total_price)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
              
              <div className="flex justify-end space-x-3 mt-6 pt-6 border-t border-gray-700">
                <button
                  onClick={() => setShowModal(false)}
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

export default OrderManagement;