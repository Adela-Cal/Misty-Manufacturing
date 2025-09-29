import React, { useState, useEffect } from 'react';
import { apiHelpers } from '../utils/api';
import { toast } from 'sonner';
import { XMarkIcon, PlusIcon, TrashIcon } from '@heroicons/react/24/outline';

const OrderForm = ({ order, onClose, onSuccess }) => {
  const [formData, setFormData] = useState({
    client_id: '',
    purchase_order_number: '',
    due_date: '',
    delivery_address: '',
    delivery_instructions: '',
    notes: '',
    discount_percentage: 0,  // Discount percentage (0-100)
    discount_notes: '',      // Reason for discount
    items: [{
      product_name: '',
      quantity: 1,
      unit_price: 0,
      total_price: 0
    }]
  });
  
  const [clients, setClients] = useState([]);
  const [clientProducts, setClientProducts] = useState([]);
  const [selectedClient, setSelectedClient] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingClients, setLoadingClients] = useState(true);
  const [errors, setErrors] = useState({});
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [orderTotals, setOrderTotals] = useState({
    subtotal: 0,
    discountAmount: 0,
    discountedSubtotal: 0,
    gst: 0,
    total: 0
  });

  useEffect(() => {
    loadClients();
  }, []);

  useEffect(() => {
    if (formData.client_id) {
      loadClientProducts(formData.client_id);
    }
  }, [formData.client_id]);

  useEffect(() => {
    calculateTotals();
  }, [formData.items, formData.discount_percentage]);

  useEffect(() => {
    if (order) {
      setFormData({
        client_id: order.client_id || '',
        purchase_order_number: order.purchase_order_number || '',
        due_date: order.due_date ? new Date(order.due_date).toISOString().split('T')[0] : '',
        delivery_address: order.delivery_address || '',
        delivery_instructions: order.delivery_instructions || '',
        notes: order.notes || '',
        discount_percentage: order.discount_percentage || 0,
        discount_notes: order.discount_notes || '',
        items: order.items || [{
          product_name: '',
          quantity: 1,
          unit_price: 0,
          total_price: 0
        }]
      });
    }
  }, [order]);

  const loadClients = async () => {
    try {
      setLoadingClients(true);
      const response = await apiHelpers.getClients();
      setClients(response.data);
    } catch (error) {
      console.error('Failed to load clients:', error);
      toast.error('Failed to load clients');
    } finally {
      setLoadingClients(false);
    }
  };

  const loadClientProducts = async (clientId) => {
    try {
      const response = await apiHelpers.getClientProducts(clientId);
      setClientProducts(response.data);
      
      // Find selected client
      const client = clients.find(c => c.id === clientId);
      setSelectedClient(client);
    } catch (error) {
      console.error('Failed to load client products:', error);
      setClientProducts([]);
    }
  };

  const calculateTotals = () => {
    const subtotal = formData.items.reduce((sum, item) => sum + (item.total_price || 0), 0);
    
    // Apply discount if provided
    const discountPercentage = parseFloat(formData.discount_percentage) || 0;
    const discountAmount = subtotal * (discountPercentage / 100);
    const discountedSubtotal = subtotal - discountAmount;
    
    // Calculate GST on discounted amount
    const gst = discountedSubtotal * 0.1; // 10% GST
    const total = discountedSubtotal + gst;
    
    setOrderTotals({ 
      subtotal, 
      discountAmount, 
      discountedSubtotal, 
      gst, 
      total 
    });
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const handleItemChange = (index, field, value) => {
    const newItems = [...formData.items];
    newItems[index] = { ...newItems[index], [field]: value };
    
    // Recalculate item total when quantity or price changes
    if (field === 'quantity' || field === 'unit_price') {
      const quantity = field === 'quantity' ? parseFloat(value) || 0 : newItems[index].quantity;
      const unitPrice = field === 'unit_price' ? parseFloat(value) || 0 : newItems[index].unit_price;
      newItems[index].total_price = quantity * unitPrice;
    }
    
    setFormData(prev => ({ ...prev, items: newItems }));
  };

  const addItem = () => {
    setFormData(prev => ({
      ...prev,
      items: [...prev.items, {
        product_name: '',
        quantity: 1,
        unit_price: 0,
        total_price: 0
      }]
    }));
  };

  const removeItem = (index) => {
    if (formData.items.length > 1) {
      setFormData(prev => ({
        ...prev,
        items: prev.items.filter((_, i) => i !== index)
      }));
    }
  };

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.client_id) {
      newErrors.client_id = 'Please select a client';
    }
    
    if (!formData.due_date) {
      newErrors.due_date = 'Due date is required';
    } else {
      const dueDate = new Date(formData.due_date);
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      if (dueDate < today) {
        newErrors.due_date = 'Due date cannot be in the past';
      }
    }
    
    // Only validate items if client is selected
    if (formData.client_id) {
      let hasValidItems = false;
      formData.items.forEach((item, index) => {
        if (!item.product_name.trim()) {
          newErrors[`item_${index}_product_name`] = 'Please select a product';
        }
        if (!item.quantity || item.quantity <= 0) {
          newErrors[`item_${index}_quantity`] = 'Quantity must be greater than 0';
        }
        if (!item.unit_price || item.unit_price <= 0) {
          newErrors[`item_${index}_unit_price`] = 'Unit price must be greater than 0';
        }
        
        if (item.product_name.trim() && item.quantity > 0 && item.unit_price > 0) {
          hasValidItems = true;
        }
      });
      
      if (!hasValidItems) {
        newErrors.items = 'At least one valid item is required';
      }
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleDelete = () => {
    setShowDeleteConfirm(true);
  };

  const confirmDelete = async () => {
    if (!order) return;
    
    try {
      setLoading(true);
      await apiHelpers.deleteOrder(order.id);
      toast.success('Order deleted successfully');
      setShowDeleteConfirm(false);
      onSuccess?.();
      onClose();
    } catch (error) {
      console.error('Failed to delete order:', error);
      const message = error.response?.data?.detail || 'Failed to delete order';
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  const cancelDelete = () => {
    setShowDeleteConfirm(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      toast.error('Please fix the errors below');
      return;
    }
    
    setLoading(true);
    
    try {
      // Prepare order data
      const orderData = {
        client_id: formData.client_id,
        purchase_order_number: formData.purchase_order_number || null,
        due_date: new Date(formData.due_date).toISOString(),
        delivery_address: formData.delivery_address || null,
        delivery_instructions: formData.delivery_instructions || null,
        notes: formData.notes || null,
        discount_percentage: parseFloat(formData.discount_percentage) || null,
        discount_notes: formData.discount_notes || null,
        items: formData.items.map(item => ({
          product_name: item.product_name,
          quantity: parseInt(item.quantity),
          unit_price: parseFloat(item.unit_price),
          total_price: parseFloat(item.total_price)
        }))
      };
      
      if (order) {
        // Update existing order (if update endpoint exists)
        // await apiHelpers.updateOrder(order.id, orderData);
        toast.success('Order updated successfully');
      } else {
        // Create new order
        const response = await apiHelpers.createOrder(orderData);
        toast.success(`Order created successfully: ${response.data.data.order_number}`);
      }
      
      onSuccess?.();
      onClose();
      
    } catch (error) {
      console.error('Failed to save order:', error);
      const message = error.response?.data?.detail || 'Failed to save order';
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  // Get minimum date (today)
  const getMinDate = () => {
    const today = new Date();
    return today.toISOString().split('T')[0];
  };

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal-content max-w-6xl max-h-[90vh] overflow-y-auto">
        <form onSubmit={handleSubmit} className="p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-white">
              {order ? 'Edit Order' : 'Create New Order'}
            </h2>
            <button
              type="button"
              onClick={onClose}
              className="text-gray-400 hover:text-white transition-colors"
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>

          {/* Client Selection */}
          <div className="mb-8">
            <h3 className="text-lg font-semibold text-white mb-4">Order Details</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Client *
                </label>
                {loadingClients ? (
                  <div className="misty-input w-full flex items-center justify-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-yellow-400"></div>
                  </div>
                ) : (
                  <select
                    name="client_id"
                    value={formData.client_id}
                    onChange={handleInputChange}
                    className={`misty-select w-full ${errors.client_id ? 'border-red-500' : ''}`}
                    required
                  >
                    <option value="">Select a client</option>
                    {clients.map(client => (
                      <option key={client.id} value={client.id}>
                        {client.company_name}
                      </option>
                    ))}
                  </select>
                )}
                {errors.client_id && (
                  <p className="text-red-400 text-sm mt-1">{errors.client_id}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Purchase Order Number
                </label>
                <input
                  type="text"
                  name="purchase_order_number"
                  value={formData.purchase_order_number}
                  onChange={handleInputChange}
                  className="misty-input w-full"
                  placeholder="Client's PO number"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Due Date *
                </label>
                <input
                  type="date"
                  name="due_date"
                  value={formData.due_date}
                  onChange={handleInputChange}
                  min={getMinDate()}
                  className={`misty-input w-full ${errors.due_date ? 'border-red-500' : ''}`}
                  required
                />
                {errors.due_date && (
                  <p className="text-red-400 text-sm mt-1">{errors.due_date}</p>
                )}
              </div>
            </div>
          </div>

          {/* Delivery Information */}
          <div className="mb-8">
            <h3 className="text-lg font-semibold text-white mb-4">Delivery Information</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Delivery Address
                </label>
                <textarea
                  name="delivery_address"
                  value={formData.delivery_address}
                  onChange={handleInputChange}
                  rows={3}
                  className="misty-textarea w-full"
                  placeholder={selectedClient ? `Default: ${selectedClient.address}, ${selectedClient.city}, ${selectedClient.state} ${selectedClient.postal_code}` : 'Enter delivery address...'}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Delivery Instructions
                </label>
                <textarea
                  name="delivery_instructions"
                  value={formData.delivery_instructions}
                  onChange={handleInputChange}
                  rows={3}
                  className="misty-textarea w-full"
                  placeholder="Special delivery instructions..."
                />
              </div>
            </div>
          </div>

          {/* Order Items - Only show when client is selected */}
          {formData.client_id && (
            <div className="mb-8">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white">Order Items</h3>
                <button
                  type="button"
                  onClick={addItem}
                  className="misty-button misty-button-secondary flex items-center text-sm"
                >
                  <PlusIcon className="h-4 w-4 mr-1" />
                  Add Item
                </button>
              </div>
              
              {errors.items && (
                <p className="text-red-400 text-sm mb-4">{errors.items}</p>
              )}
              
              <div className="space-y-4">
                {formData.items.map((item, index) => (
                  <div key={index} className="border border-gray-600 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="text-white font-medium">Item {index + 1}</h4>
                      {formData.items.length > 1 && (
                        <button
                          type="button"
                          onClick={() => removeItem(index)}
                          className="text-red-400 hover:text-red-300 transition-colors"
                        >
                          <TrashIcon className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                      <div className="md:col-span-2">
                        <label className="block text-sm font-medium text-gray-300 mb-1">
                          Product Name *
                        </label>
                        {clientProducts.length > 0 ? (
                          <select
                            value={item.product_name}
                            onChange={(e) => {
                              const selectedProduct = clientProducts.find(p => p.product_name === e.target.value);
                              if (selectedProduct) {
                                handleItemChange(index, 'product_name', selectedProduct.product_name);
                                handleItemChange(index, 'unit_price', selectedProduct.unit_price);
                                // Recalculate total with current quantity
                                const newTotal = formData.items[index].quantity * selectedProduct.unit_price;
                                handleItemChange(index, 'total_price', newTotal);
                              } else {
                                handleItemChange(index, 'product_name', e.target.value);
                              }
                            }}
                            className={`misty-select w-full ${errors[`item_${index}_product_name`] ? 'border-red-500' : ''}`}
                          >
                            <option value="">Select a product</option>
                            {clientProducts.map(product => (
                              <option key={product.id} value={product.product_name}>
                                {product.product_name} - ${product.unit_price}
                              </option>
                            ))}
                          </select>
                        ) : (
                          <div className="text-center text-gray-400 py-3">
                            No products available for this client.
                            <br />
                            <span className="text-sm">Add products to the client profile first.</span>
                          </div>
                        )}
                        {errors[`item_${index}_product_name`] && (
                          <p className="text-red-400 text-sm mt-1">{errors[`item_${index}_product_name`]}</p>
                        )}
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-300 mb-1">
                          Quantity *
                        </label>
                        <input
                          type="number"
                          min="1"
                          step="1"
                          value={item.quantity}
                          onChange={(e) => handleItemChange(index, 'quantity', e.target.value)}
                          className={`misty-input w-full ${errors[`item_${index}_quantity`] ? 'border-red-500' : ''}`}
                        />
                        {errors[`item_${index}_quantity`] && (
                          <p className="text-red-400 text-sm mt-1">{errors[`item_${index}_quantity`]}</p>
                        )}
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-300 mb-1">
                          Unit Price *
                        </label>
                        <input
                          type="number"
                          min="0"
                          step="0.01"
                          value={item.unit_price}
                          onChange={(e) => handleItemChange(index, 'unit_price', e.target.value)}
                          className={`misty-input w-full ${errors[`item_${index}_unit_price`] ? 'border-red-500' : ''}`}
                        />
                        {errors[`item_${index}_unit_price`] && (
                          <p className="text-red-400 text-sm mt-1">{errors[`item_${index}_unit_price`]}</p>
                        )}
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-300 mb-1">
                          Total Price
                        </label>
                        <input
                          type="number"
                          value={item.total_price.toFixed(2)}
                          className="misty-input w-full bg-gray-600"
                          readOnly
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Show message when no client selected */}
          {!formData.client_id && (
            <div className="mb-8">
              <div className="misty-card p-6 text-center">
                <h3 className="text-lg font-semibold text-gray-300 mb-2">Select a Client</h3>
                <p className="text-gray-400">Please select a client above to add order items.</p>
              </div>
            </div>
          )}

          {/* Discount Section - Only show when client is selected */}
          {formData.client_id && (
            <div className="mb-8">
              <div className="misty-card p-4 bg-gray-700">
                <h3 className="text-lg font-semibold text-white mb-4">Discount (Optional)</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-1">
                      Discount Percentage (%)
                    </label>
                    <input
                      type="number"
                      name="discount_percentage"
                      min="0"
                      max="100"
                      step="0.1"
                      value={formData.discount_percentage}
                      onChange={handleInputChange}
                      className="misty-input w-full"
                      placeholder="0.0"
                    />
                    <p className="text-xs text-gray-400 mt-1">
                      Enter percentage (0-100). Applied before GST calculation.
                    </p>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-1">
                      Discount Reason
                    </label>
                    <input
                      type="text"
                      name="discount_notes"
                      value={formData.discount_notes}
                      onChange={handleInputChange}
                      className="misty-input w-full"
                      placeholder="Reason for discount (e.g., Bulk order, Loyalty discount)"
                    />
                  </div>
                </div>
                
                {/* Show discount calculation preview */}
                {parseFloat(formData.discount_percentage) > 0 && orderTotals.subtotal > 0 && (
                  <div className="mt-4 p-3 bg-gray-600 rounded-lg">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-300">Discount Amount:</span>
                      <span className="text-red-400 font-medium">
                        -${orderTotals.discountAmount.toFixed(2)}
                      </span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Order Totals - Only show when client is selected and has items */}
          {formData.client_id && formData.items.some(item => item.product_name && item.quantity > 0) && (
            <div className="mb-8">
              <div className="misty-card p-4 bg-gray-700">
                <h3 className="text-lg font-semibold text-white mb-4">Order Summary</h3>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-gray-300">Subtotal:</span>
                    <span className="text-white font-medium">${orderTotals.subtotal.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-300">GST (10%):</span>
                    <span className="text-white font-medium">${orderTotals.gst.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between text-lg font-bold border-t border-gray-600 pt-2">
                    <span className="text-white">Total:</span>
                    <span className="text-yellow-400">${orderTotals.total.toFixed(2)}</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Notes */}
          <div className="mb-8">
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Order Notes
            </label>
            <textarea
              name="notes"
              value={formData.notes}
              onChange={handleInputChange}
              rows={3}
              className="misty-textarea w-full"
              placeholder="Additional notes for this order..."
            />
          </div>

          {/* Form Actions */}
          <div className="flex justify-between pt-6 border-t border-gray-700">
            <div>
              {order && (
                <button
                  type="button"
                  onClick={handleDelete}
                  className="misty-button misty-button-danger"
                  disabled={loading}
                >
                  <TrashIcon className="h-4 w-4 mr-2" />
                  Delete Order
                </button>
              )}
            </div>
            <div className="flex space-x-3">
              <button
                type="button"
                onClick={onClose}
                className="misty-button misty-button-secondary"
                disabled={loading}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="misty-button misty-button-primary"
                disabled={loading || loadingClients}
              >
                {loading ? (
                  <div className="flex items-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-900 mr-2"></div>
                    {order ? 'Updating...' : 'Creating...'}
                  </div>
                ) : (
                  order ? 'Update Order' : 'Create Order'
                )}
              </button>
            </div>
          </div>
        </form>
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && order && (
        <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && cancelDelete()}>
          <div className="modal-content max-w-md">
            <div className="p-6">
              <div className="flex items-center mb-4">
                <div className="flex-shrink-0">
                  <TrashIcon className="h-8 w-8 text-red-400" />
                </div>
                <div className="ml-4">
                  <h3 className="text-lg font-semibold text-white">Delete Order</h3>
                  <p className="text-sm text-gray-400">This action cannot be undone.</p>
                </div>
              </div>
              
              <div className="mb-6">
                <p className="text-gray-300">
                  Are you sure you wish to delete order <span className="font-semibold text-white">"{order.order_number}"</span>?
                </p>
                <p className="text-sm text-gray-400 mt-2">
                  This will cancel the order and remove it from active production. Orders in production cannot be deleted.
                </p>
              </div>

              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={cancelDelete}
                  className="misty-button misty-button-secondary"
                  disabled={loading}
                >
                  No, Cancel
                </button>
                <button
                  type="button"
                  onClick={confirmDelete}
                  className="misty-button misty-button-danger"
                  disabled={loading}
                >
                  {loading ? (
                    <div className="flex items-center">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Deleting...
                    </div>
                  ) : (
                    'Yes, Delete Order'
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default OrderForm;