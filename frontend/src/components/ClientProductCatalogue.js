import React, { useState, useEffect } from 'react';
import { apiHelpers } from '../utils/api';
import { toast } from 'sonner';
import { 
  PlusIcon, 
  PencilIcon, 
  TrashIcon, 
  DocumentDuplicateIcon,
  XMarkIcon,
  CheckIcon
} from '@heroicons/react/24/outline';

const ClientProductCatalogue = ({ clientId, onClose }) => {
  const [products, setProducts] = useState([]);
  const [materials, setMaterials] = useState([]);
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [showCopyModal, setShowCopyModal] = useState(false);
  const [copyProductId, setCopyProductId] = useState(null);
  const [targetClientId, setTargetClientId] = useState('');
  
  const [formData, setFormData] = useState({
    product_type: 'finished_goods',
    product_code: '',
    product_description: '',
    price_ex_gst: '',
    minimum_order_quantity: '',
    consignment: false,
    // Paper cores specific
    material_used: [],
    core_id: '',
    core_width: '',
    core_thickness: '',
    strength_quality_important: false,
    delivery_included: false
  });
  const [errors, setErrors] = useState({});

  useEffect(() => {
    loadData();
  }, [clientId]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [productsRes, materialsRes, clientsRes] = await Promise.all([
        apiHelpers.getClientCatalogue(clientId),
        apiHelpers.getMaterials(),
        apiHelpers.getClients()
      ]);
      
      setProducts(productsRes.data);
      setMaterials(materialsRes.data);
      setClients(clientsRes.data.filter(client => client.id !== clientId));
    } catch (error) {
      console.error('Failed to load data:', error);
      toast.error('Failed to load product catalogue data');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setSelectedProduct(null);
    setFormData({
      product_type: 'finished_goods',
      product_code: '',
      product_description: '',
      price_ex_gst: '',
      minimum_order_quantity: '',
      consignment: false,
      material_used: [],
      core_id: '',
      core_width: '',
      core_thickness: '',
      strength_quality_important: false,
      delivery_included: false
    });
    setErrors({});
    setShowModal(true);
  };

  const handleEdit = (product) => {
    setSelectedProduct(product);
    setFormData({
      product_type: product.product_type,
      product_code: product.product_code,
      product_description: product.product_description,
      price_ex_gst: product.price_ex_gst.toString(),
      minimum_order_quantity: product.minimum_order_quantity.toString(),
      consignment: product.consignment || false,
      material_used: product.material_used || [],
      core_id: product.core_id || '',
      core_width: product.core_width || '',
      core_thickness: product.core_thickness || '',
      strength_quality_important: product.strength_quality_important || false,
      delivery_included: product.delivery_included || false
    });
    setErrors({});
    setShowModal(true);
  };

  const handleDelete = async (product) => {
    if (window.confirm(`Are you sure you want to delete "${product.product_code}"?`)) {
      try {
        await apiHelpers.deleteClientProduct(clientId, product.id);
        toast.success('Product deleted successfully');
        loadData();
      } catch (error) {
        console.error('Failed to delete product:', error);
        toast.error('Failed to delete product');
      }
    }
  };

  const handleCopy = (productId) => {
    setCopyProductId(productId);
    setTargetClientId('');
    setShowCopyModal(true);
  };

  const handleCopyConfirm = async () => {
    if (!targetClientId) {
      toast.error('Please select a target client');
      return;
    }

    try {
      await apiHelpers.copyClientProduct(clientId, copyProductId, targetClientId);
      toast.success('Product copied successfully');
      setShowCopyModal(false);
    } catch (error) {
      console.error('Failed to copy product:', error);
      toast.error('Failed to copy product');
    }
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
    
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const handleMaterialChange = (materialId, isSelected) => {
    setFormData(prev => ({
      ...prev,
      material_used: isSelected 
        ? [...prev.material_used, materialId]
        : prev.material_used.filter(id => id !== materialId)
    }));
  };

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.product_code.trim()) {
      newErrors.product_code = 'Product code is required';
    }
    
    if (!formData.product_description.trim()) {
      newErrors.product_description = 'Product description is required';
    }
    
    if (!formData.price_ex_gst || parseFloat(formData.price_ex_gst) <= 0) {
      newErrors.price_ex_gst = 'Price must be greater than 0';
    }
    
    if (!formData.minimum_order_quantity || parseInt(formData.minimum_order_quantity) <= 0) {
      newErrors.minimum_order_quantity = 'Minimum order quantity must be greater than 0';
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
      const submitData = {
        product_type: formData.product_type,
        product_code: formData.product_code,
        product_description: formData.product_description,
        price_ex_gst: parseFloat(formData.price_ex_gst),
        minimum_order_quantity: parseInt(formData.minimum_order_quantity),
        consignment: formData.consignment,
        material_used: formData.product_type === 'paper_cores' ? formData.material_used : [],
        core_id: formData.product_type === 'paper_cores' ? formData.core_id || null : null,
        core_width: formData.product_type === 'paper_cores' ? formData.core_width || null : null,
        core_thickness: formData.product_type === 'paper_cores' ? formData.core_thickness || null : null,
        strength_quality_important: formData.product_type === 'paper_cores' ? formData.strength_quality_important : false,
        delivery_included: formData.product_type === 'paper_cores' ? formData.delivery_included : false
      };

      if (selectedProduct) {
        await apiHelpers.updateClientProduct(clientId, selectedProduct.id, submitData);
        toast.success('Product updated successfully');
      } else {
        await apiHelpers.createClientProduct(clientId, submitData);
        toast.success('Product created successfully');
      }
      
      setShowModal(false);
      loadData();
    } catch (error) {
      console.error('Failed to save product:', error);
      const message = error.response?.data?.detail || 'Failed to save product';
      toast.error(message);
    }
  };

  if (loading) {
    return (
      <div className="modal-overlay">
        <div className="modal-content max-w-6xl max-h-[90vh] overflow-y-auto">
          <div className="p-8">
            <div className="animate-pulse">
              <div className="h-8 bg-gray-700 rounded w-1/3 mb-8"></div>
              <div className="space-y-4">
                {[...Array(3)].map((_, i) => (
                  <div key={i} className="h-16 bg-gray-700 rounded"></div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal-content max-w-6xl max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-white">
              Client Product Catalogue
            </h2>
            <div className="flex items-center space-x-4">
              <button
                onClick={handleCreate}
                className="misty-button misty-button-primary flex items-center"
              >
                <PlusIcon className="h-4 w-4 mr-2" />
                Add Product
              </button>
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-white transition-colors"
              >
                <XMarkIcon className="h-6 w-6" />
              </button>
            </div>
          </div>

          {/* Products Table */}
          {products.length > 0 ? (
            <div className="misty-table">
              <table className="w-full">
                <thead>
                  <tr>
                    <th>Product Code</th>
                    <th>Description</th>
                    <th>Type</th>
                    <th>Price (ex GST)</th>
                    <th>Min Qty</th>
                    <th>Consignment</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {products.map((product) => (
                    <tr key={product.id}>
                      <td className="font-medium">{product.product_code}</td>
                      <td>{product.product_description}</td>
                      <td>
                        <span className={`text-xs px-2 py-1 rounded text-white ${
                          product.product_type === 'finished_goods' 
                            ? 'bg-blue-600' 
                            : 'bg-purple-600'
                        }`}>
                          {product.product_type === 'finished_goods' 
                            ? 'Finished Goods' 
                            : 'Paper Cores'
                          }
                        </span>
                      </td>
                      <td className="text-yellow-400 font-medium">
                        ${product.price_ex_gst.toFixed(2)}
                      </td>
                      <td>{product.minimum_order_quantity}</td>
                      <td>
                        {product.consignment ? (
                          <CheckIcon className="h-4 w-4 text-green-400" />
                        ) : (
                          <span className="text-gray-400">—</span>
                        )}
                      </td>
                      <td>
                        <div className="flex items-center space-x-2">
                          <button
                            onClick={() => handleEdit(product)}
                            className="text-gray-400 hover:text-yellow-400 transition-colors"
                            title="Edit product"
                          >
                            <PencilIcon className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => handleCopy(product.id)}
                            className="text-gray-400 hover:text-blue-400 transition-colors"
                            title="Copy to another client"
                          >
                            <DocumentDuplicateIcon className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => handleDelete(product)}
                            className="text-gray-400 hover:text-red-400 transition-colors"
                            title="Delete product"
                          >
                            <TrashIcon className="h-4 w-4" />
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
              <div className="mx-auto h-12 w-12 text-gray-400 mb-4">📦</div>
              <h3 className="text-sm font-medium text-gray-300">
                No products in catalogue
              </h3>
              <p className="mt-1 text-sm text-gray-400">
                Get started by adding your first product.
              </p>
              <div className="mt-6">
                <button
                  onClick={handleCreate}
                  className="misty-button misty-button-primary"
                >
                  <PlusIcon className="h-5 w-5 mr-2" />
                  Add Product
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Product Form Modal */}
        {showModal && (
          <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && setShowModal(false)}>
            <div className="modal-content max-w-3xl max-h-[90vh] overflow-y-auto">
              <form onSubmit={handleSubmit} className="p-6">
                {/* Header */}
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-xl font-bold text-white">
                    {selectedProduct ? 'Edit Product' : 'Add New Product'}
                  </h3>
                  <button
                    type="button"
                    onClick={() => setShowModal(false)}
                    className="text-gray-400 hover:text-white transition-colors"
                  >
                    <XMarkIcon className="h-5 w-5" />
                  </button>
                </div>

                {/* Product Type */}
                <div className="mb-6">
                  <label className="block text-sm font-medium text-gray-300 mb-3">
                    Product Type *
                  </label>
                  <div className="grid grid-cols-2 gap-4">
                    <label className="flex items-center space-x-3 p-4 border border-gray-600 rounded-lg cursor-pointer hover:bg-gray-700 transition-colors">
                      <input
                        type="radio"
                        name="product_type"
                        value="finished_goods"
                        checked={formData.product_type === 'finished_goods'}
                        onChange={handleInputChange}
                        className="text-yellow-400"
                      />
                      <div>
                        <div className="font-medium text-white">Finished Goods</div>
                        <div className="text-sm text-gray-400">Complete products ready for delivery</div>
                      </div>
                    </label>
                    <label className="flex items-center space-x-3 p-4 border border-gray-600 rounded-lg cursor-pointer hover:bg-gray-700 transition-colors">
                      <input
                        type="radio"
                        name="product_type"
                        value="paper_cores"
                        checked={formData.product_type === 'paper_cores'}
                        onChange={handleInputChange}
                        className="text-yellow-400"
                      />
                      <div>
                        <div className="font-medium text-white">Paper Cores</div>
                        <div className="text-sm text-gray-400">Paper core products with specifications</div>
                      </div>
                    </label>
                  </div>
                </div>

                {/* Basic Information */}
                <div className="mb-8">
                  <h4 className="text-lg font-semibold text-white mb-4">Basic Information</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-1">
                        Product Code *
                      </label>
                      <input
                        type="text"
                        name="product_code"
                        value={formData.product_code}
                        onChange={handleInputChange}
                        className={`misty-input w-full ${errors.product_code ? 'border-red-500' : ''}`}
                        placeholder="Enter product code"
                        required
                      />
                      {errors.product_code && (
                        <p className="text-red-400 text-sm mt-1">{errors.product_code}</p>
                      )}
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-1">
                        Price ex GST *
                      </label>
                      <input
                        type="number"
                        step="0.01"
                        min="0"
                        name="price_ex_gst"
                        value={formData.price_ex_gst}
                        onChange={handleInputChange}
                        className={`misty-input w-full ${errors.price_ex_gst ? 'border-red-500' : ''}`}
                        placeholder="0.00"
                        required
                      />
                      {errors.price_ex_gst && (
                        <p className="text-red-400 text-sm mt-1">{errors.price_ex_gst}</p>
                      )}
                    </div>

                    <div className="md:col-span-2">
                      <label className="block text-sm font-medium text-gray-300 mb-1">
                        Product Description *
                      </label>
                      <textarea
                        name="product_description"
                        value={formData.product_description}
                        onChange={handleInputChange}
                        rows={3}
                        className={`misty-textarea w-full ${errors.product_description ? 'border-red-500' : ''}`}
                        placeholder="Enter product description"
                        required
                      />
                      {errors.product_description && (
                        <p className="text-red-400 text-sm mt-1">{errors.product_description}</p>
                      )}
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-1">
                        Minimum Order Quantity *
                      </label>
                      <input
                        type="number"
                        min="1"
                        name="minimum_order_quantity"
                        value={formData.minimum_order_quantity}
                        onChange={handleInputChange}
                        className={`misty-input w-full ${errors.minimum_order_quantity ? 'border-red-500' : ''}`}
                        placeholder="1"
                        required
                      />
                      {errors.minimum_order_quantity && (
                        <p className="text-red-400 text-sm mt-1">{errors.minimum_order_quantity}</p>
                      )}
                    </div>

                    <div className="flex items-center">
                      <label className="flex items-center space-x-2 cursor-pointer">
                        <input
                          type="checkbox"
                          name="consignment"
                          checked={formData.consignment}
                          onChange={handleInputChange}
                          className="form-checkbox h-4 w-4 text-yellow-400 bg-gray-700 border-gray-600 rounded focus:ring-yellow-400"
                        />
                        <span className="text-white font-medium">Consignment?</span>
                      </label>
                    </div>
                  </div>
                </div>

                {/* Paper Cores Specifications */}
                {formData.product_type === 'paper_cores' && (
                  <div className="mb-8">
                    <h4 className="text-lg font-semibold text-white mb-4">Paper Cores Specifications</h4>
                    
                    {/* Materials Used */}
                    <div className="mb-6">
                      <label className="block text-sm font-medium text-gray-300 mb-3">
                        Material Used (GSM)
                      </label>
                      <div className="max-h-32 overflow-y-auto border border-gray-600 rounded-lg p-3">
                        {materials.length > 0 ? (
                          <div className="space-y-2">
                            {materials.map((material) => (
                              <label key={material.id} className="flex items-center space-x-2 cursor-pointer">
                                <input
                                  type="checkbox"
                                  checked={formData.material_used.includes(material.id)}
                                  onChange={(e) => handleMaterialChange(material.id, e.target.checked)}
                                  className="form-checkbox h-4 w-4 text-yellow-400 bg-gray-700 border-gray-600 rounded focus:ring-yellow-400"
                                />
                                <span className="text-sm text-gray-300">
                                  {material.supplier} - {material.product_code}
                                  {material.gsm && ` (${material.gsm} GSM)`}
                                </span>
                              </label>
                            ))}
                          </div>
                        ) : (
                          <p className="text-sm text-gray-400">No materials available. Create materials first.</p>
                        )}
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-300 mb-1">
                          Core ID
                        </label>
                        <input
                          type="text"
                          name="core_id"
                          value={formData.core_id}
                          onChange={handleInputChange}
                          className="misty-input w-full"
                          placeholder="Enter core ID"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-300 mb-1">
                          Core Width
                        </label>
                        <input
                          type="text"
                          name="core_width"
                          value={formData.core_width}
                          onChange={handleInputChange}
                          className="misty-input w-full"
                          placeholder="Enter core width"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-300 mb-1">
                          Core Thickness
                        </label>
                        <input
                          type="text"
                          name="core_thickness"
                          value={formData.core_thickness}
                          onChange={handleInputChange}
                          className="misty-input w-full"
                          placeholder="Enter core thickness"
                        />
                      </div>

                      <div className="flex items-center">
                        <label className="flex items-center space-x-2 cursor-pointer">
                          <input
                            type="checkbox"
                            name="strength_quality_important"
                            checked={formData.strength_quality_important}
                            onChange={handleInputChange}
                            className="form-checkbox h-4 w-4 text-yellow-400 bg-gray-700 border-gray-600 rounded focus:ring-yellow-400"
                          />
                          <span className="text-white font-medium">Is strength and Quality important?</span>
                        </label>
                      </div>

                      <div className="flex items-center">
                        <label className="flex items-center space-x-2 cursor-pointer">
                          <input
                            type="checkbox"
                            name="delivery_included"
                            checked={formData.delivery_included}
                            onChange={handleInputChange}
                            className="form-checkbox h-4 w-4 text-yellow-400 bg-gray-700 border-gray-600 rounded focus:ring-yellow-400"
                          />
                          <span className="text-white font-medium">Delivery Included?</span>
                        </label>
                      </div>
                    </div>
                  </div>
                )}

                {/* Form Actions */}
                <div className="flex justify-end space-x-3 pt-6 border-t border-gray-700">
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
                    {selectedProduct ? 'Update Product' : 'Create Product'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Copy Product Modal */}
        {showCopyModal && (
          <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && setShowCopyModal(false)}>
            <div className="modal-content max-w-md">
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-bold text-white">Copy Product</h3>
                  <button
                    onClick={() => setShowCopyModal(false)}
                    className="text-gray-400 hover:text-white transition-colors"
                  >
                    <XMarkIcon className="h-5 w-5" />
                  </button>
                </div>

                <div className="mb-6">
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Copy to client:
                  </label>
                  <select
                    value={targetClientId}
                    onChange={(e) => setTargetClientId(e.target.value)}
                    className="misty-select w-full"
                  >
                    <option value="">Select client...</option>
                    {clients.map((client) => (
                      <option key={client.id} value={client.id}>
                        {client.company_name}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="flex justify-end space-x-3">
                  <button
                    onClick={() => setShowCopyModal(false)}
                    className="misty-button misty-button-secondary"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleCopyConfirm}
                    className="misty-button misty-button-primary"
                  >
                    Copy Product
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ClientProductCatalogue;