import React, { useState, useEffect } from 'react';
import Layout from './Layout';
import OrderForm from './OrderForm';
import { apiHelpers, formatCurrency, formatDate, stageDisplayNames } from '../utils/api';
import { toast } from 'sonner';
import { 
  PlusIcon, 
  EyeIcon, 
  DocumentArrowDownIcon,
  MagnifyingGlassIcon,
  PencilIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';

const OrderManagement = () => {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [showOrderModal, setShowOrderModal] = useState(false);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [showTemplateModal, setShowTemplateModal] = useState(false);
  const [selectedOrderForPdf, setSelectedOrderForPdf] = useState(null);
  const [pageTemplates, setPageTemplates] = useState([]);
  const [loadingTemplates, setLoadingTemplates] = useState(false);

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

  const handleCreateOrder = () => {
    setSelectedOrder(null);
    setShowOrderModal(true);
  };

  const handleEditOrder = (order) => {
    setSelectedOrder(order);
    setShowOrderModal(true);
  };

  const handleViewOrder = (order) => {
    setSelectedOrder(order);
    setShowDetailsModal(true);
  };

  const handleCloseOrderModal = () => {
    setShowOrderModal(false);
    setSelectedOrder(null);
  };

  const handleCloseDetailsModal = () => {
    setShowDetailsModal(false);
    setSelectedOrder(null);
  };

  const handleOrderSuccess = () => {
    loadOrders(); // Reload orders after successful create/update
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

  const getStageColor = (stage) => {
    switch (stage) {
      case 'order_entered': return 'bg-blue-600';
      case 'pending_material': return 'bg-orange-600';
      case 'paper_slitting': return 'bg-purple-600';
      case 'winding': return 'bg-indigo-600';
      case 'finishing': return 'bg-green-600';
      case 'delivery': return 'bg-teal-600';
      case 'invoicing': return 'bg-yellow-600';
      case 'cleared': return 'bg-gray-600';
      default: return 'bg-gray-600';
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
            onClick={handleCreateOrder}
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
            <MagnifyingGlassIcon className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder=""
              className="misty-input pl-16 w-full"
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
                {filteredOrders.map((order) => {
                  const isOverdue = new Date(order.due_date) < new Date() && order.status === 'active';
                  return (
                    <tr key={order.id} data-testid={`order-row-${order.id}`} className={isOverdue ? 'bg-red-900/20' : ''}>
                      <td className="font-medium">
                        <div>
                          {order.order_number}
                          {isOverdue && <span className="text-red-400 text-xs block">Overdue</span>}
                        </div>
                      </td>
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
                        <span className={`text-xs px-2 py-1 rounded text-white ${getStageColor(order.current_stage)}`}>
                          {stageDisplayNames[order.current_stage] || order.current_stage}
                        </span>
                      </td>
                      <td>
                        <div className={isOverdue ? 'text-red-400' : ''}>
                          {formatDate(order.due_date)}
                        </div>
                      </td>
                      <td>
                        <div className="flex items-center space-x-2">
                          <button
                            onClick={() => handleViewOrder(order)}
                            className="text-gray-400 hover:text-yellow-400 transition-colors"
                            data-testid={`view-order-${order.id}`}
                            title="View details"
                          >
                            <EyeIcon className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => handleEditOrder(order)}
                            className="text-gray-400 hover:text-blue-400 transition-colors"
                            data-testid={`edit-order-${order.id}`}
                            title="Edit order"
                          >
                            <PencilIcon className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => handleDownloadAcknowledgment(order.id, order.order_number)}
                            className="text-gray-400 hover:text-green-400 transition-colors"
                            data-testid={`download-acknowledgment-${order.id}`}
                            title="Download acknowledgment"
                          >
                            <DocumentArrowDownIcon className="h-4 w-4" />
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
          <div className="text-center py-12">
            <DocumentArrowDownIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-300">
              {searchTerm || statusFilter ? 'No orders found' : 'No orders'}
            </h3>
            <p className="mt-1 text-sm text-gray-400">
              {searchTerm || statusFilter
                ? 'Try adjusting your search criteria.' 
                : 'Get started by creating your first order.'
              }
            </p>
            {!searchTerm && !statusFilter && (
              <div className="mt-6">
                <button
                  onClick={handleCreateOrder}
                  className="misty-button misty-button-primary"
                >
                  <PlusIcon className="h-5 w-5 mr-2" />
                  Create Order
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Order Form Modal */}
      {showOrderModal && (
        <OrderForm
          order={selectedOrder}
          onClose={handleCloseOrderModal}
          onSuccess={handleOrderSuccess}
        />
      )}

      {/* Order Details Modal */}
      {showDetailsModal && selectedOrder && (
        <div className="modal-overlay">
          <div className="modal-content max-w-4xl max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-bold text-white">
                  Order Details - {selectedOrder.order_number}
                </h2>
                <button
                  onClick={handleCloseDetailsModal}
                  className="text-gray-400 hover:text-white transition-colors"
                >
                  <XMarkIcon className="h-6 w-6" />
                </button>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                <div>
                  <h3 className="font-semibold text-white mb-3">Order Information</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-400">Client:</span>
                      <span className="text-white">{selectedOrder.client_name}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Total:</span>
                      <span className="text-yellow-400 font-medium">{formatCurrency(selectedOrder.total_amount)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Status:</span>
                      <span className={`capitalize ${getStatusColor(selectedOrder.status)}`}>
                        {selectedOrder.status}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Stage:</span>
                      <span className={`text-xs px-2 py-1 rounded text-white ${getStageColor(selectedOrder.current_stage)}`}>
                        {stageDisplayNames[selectedOrder.current_stage]}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Due Date:</span>
                      <span className="text-white">{formatDate(selectedOrder.due_date)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Created:</span>
                      <span className="text-white">{formatDate(selectedOrder.created_at)}</span>
                    </div>
                  </div>
                </div>
                
                <div>
                  <h3 className="font-semibold text-white mb-3">Delivery Information</h3>
                  <div className="space-y-2 text-sm">
                    <div>
                      <span className="text-gray-400">Address:</span>
                      <p className="text-white mt-1">
                        {selectedOrder.delivery_address || 'Use client default address'}
                      </p>
                    </div>
                    {selectedOrder.delivery_instructions && (
                      <div>
                        <span className="text-gray-400">Instructions:</span>
                        <p className="text-white mt-1">{selectedOrder.delivery_instructions}</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
              
              <div className="mb-6">
                <h3 className="font-semibold text-white mb-3">Order Items</h3>
                <div className="misty-table">
                  <table className="w-full">
                    <thead>
                      <tr>
                        <th>Product</th>
                        <th>Quantity</th>
                        <th>Unit Price</th>
                        <th>Total</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selectedOrder.items.map((item, index) => (
                        <tr key={index}>
                          <td>{item.product_name}</td>
                          <td>{item.quantity}</td>
                          <td>{formatCurrency(item.unit_price)}</td>
                          <td className="text-yellow-400 font-medium">{formatCurrency(item.total_price)}</td>
                        </tr>
                      ))}
                      <tr className="border-t-2 border-gray-600">
                        <td colSpan="3" className="text-right font-medium">Subtotal:</td>
                        <td className="font-medium">{formatCurrency(selectedOrder.subtotal)}</td>
                      </tr>
                      <tr>
                        <td colSpan="3" className="text-right font-medium">GST (10%):</td>
                        <td className="font-medium">{formatCurrency(selectedOrder.gst)}</td>
                      </tr>
                      <tr>
                        <td colSpan="3" className="text-right font-bold text-lg">Total:</td>
                        <td className="font-bold text-lg text-yellow-400">{formatCurrency(selectedOrder.total_amount)}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
              
              {selectedOrder.notes && (
                <div className="mb-6">
                  <h3 className="font-semibold text-white mb-3">Notes</h3>
                  <p className="text-gray-300 bg-gray-700 p-3 rounded">{selectedOrder.notes}</p>
                </div>
              )}
              
              <div className="flex justify-end space-x-3 pt-6 border-t border-gray-700">
                <button
                  onClick={() => handleDownloadAcknowledgment(selectedOrder.id, selectedOrder.order_number)}
                  className="misty-button misty-button-secondary flex items-center"
                >
                  <DocumentArrowDownIcon className="h-4 w-4 mr-2" />
                  Download Acknowledgment
                </button>
                <button
                  onClick={handleCloseDetailsModal}
                  className="misty-button misty-button-primary"
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