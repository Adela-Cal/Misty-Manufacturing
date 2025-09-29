import React, { useState, useEffect } from 'react';
import Layout from './Layout';
import { apiHelpers } from '../utils/api';
import { toast } from 'sonner';
import { 
  PlusIcon, 
  PencilIcon,
  MagnifyingGlassIcon,
  XMarkIcon,
  TrashIcon
} from '@heroicons/react/24/outline';

const SuppliersManagement = () => {
  const [suppliers, setSuppliers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [selectedSupplier, setSelectedSupplier] = useState(null);
  const [formData, setFormData] = useState({
    supplier_name: '',
    contact_person: '',
    phone_number: '',
    email: '',
    physical_address: '',
    post_code: '',
    currency_accepted: 'AUD',
    bank_name: '',
    bank_address: '',
    account_name: '',  // New field
    bank_account_number: '',
    swift_code: ''
  });
  const [errors, setErrors] = useState({});

  useEffect(() => {
    loadSuppliers();
  }, []);

  const loadSuppliers = async () => {
    try {
      setLoading(true);
      const response = await apiHelpers.getSuppliers();
      setSuppliers(response.data);
    } catch (error) {
      console.error('Failed to load suppliers:', error);
      toast.error('Failed to load suppliers');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setSelectedSupplier(null);
    setFormData({
      supplier_name: '',
      contact_person: '',
      phone_number: '',
      email: '',
      physical_address: '',
      post_code: '',
      currency_accepted: 'AUD',
      bank_name: '',
      bank_address: '',
      account_name: '',  // New field
      bank_account_number: '',
      swift_code: ''
    });
    setErrors({});
    setShowModal(true);
  };

  const handleEdit = (supplier) => {
    setSelectedSupplier(supplier);
    setFormData({
      supplier_name: supplier.supplier_name,
      contact_person: supplier.contact_person || '',
      phone_number: supplier.phone_number,
      email: supplier.email,
      physical_address: supplier.physical_address,
      post_code: supplier.post_code,
      currency_accepted: supplier.currency_accepted || 'AUD',
      bank_name: supplier.bank_name,
      bank_address: supplier.bank_address,
      account_name: supplier.account_name || '',  // New field
      bank_account_number: supplier.bank_account_number,
      swift_code: supplier.swift_code || ''
    });
    setErrors({});
    setShowModal(true);
  };

  const handleDelete = async (supplier) => {
    if (window.confirm(`Are you sure you want to delete the supplier "${supplier.supplier_name}"?`)) {
      try {
        await apiHelpers.deleteSupplier(supplier.id);
        toast.success('Supplier deleted successfully');
        setShowModal(false);
        loadSuppliers();
      } catch (error) {
        console.error('Failed to delete supplier:', error);
        toast.error('Failed to delete supplier');
      }
    }
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
    
    if (!formData.supplier_name.trim()) {
      newErrors.supplier_name = 'Supplier name is required';
    }
    
    if (!formData.phone_number.trim()) {
      newErrors.phone_number = 'Phone number is required';
    }
    
    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Email is not valid';
    }
    
    if (!formData.physical_address.trim()) {
      newErrors.physical_address = 'Physical address is required';
    }
    
    if (!formData.post_code.trim()) {
      newErrors.post_code = 'Post code is required';
    }
    
    if (!formData.bank_name.trim()) {
      newErrors.bank_name = 'Bank name is required';
    }
    
    if (!formData.account_name.trim()) {
      newErrors.account_name = 'Account name is required';
    }
    
    if (!formData.bank_account_number.trim()) {
      newErrors.bank_account_number = 'Bank account number is required';
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
      if (selectedSupplier) {
        await apiHelpers.updateSupplier(selectedSupplier.id, formData);
        toast.success('Supplier updated successfully');
      } else {
        await apiHelpers.createSupplier(formData);
        toast.success('Supplier created successfully');
      }
      
      setShowModal(false);
      loadSuppliers();
    } catch (error) {
      console.error('Failed to save supplier:', error);
      const message = error.response?.data?.detail || 'Failed to save supplier';
      toast.error(message);
    }
  };

  const filteredSuppliers = suppliers.filter(supplier =>
    supplier.supplier_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    supplier.email.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const currencyOptions = [
    'AUD', 'USD', 'EUR', 'GBP', 'JPY', 'CAD', 'NZD', 'SGD'
  ];

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
            <h1 className="text-3xl font-bold text-white mb-2">Suppliers List</h1>
            <p className="text-gray-400">Manage supplier information and contact details • Double-click any supplier to edit</p>
          </div>
          <button
            onClick={handleCreate}
            className="misty-button misty-button-primary"
          >
            <PlusIcon className="h-5 w-5 mr-2" />
            Add Supplier
          </button>
        </div>

        {/* Search */}
        <div className="mb-6">
          <div className="relative max-w-md">
            <MagnifyingGlassIcon className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search suppliers..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="misty-input pl-12 w-full"
            />
          </div>
        </div>

        {/* Suppliers Table */}
        {filteredSuppliers.length > 0 ? (
          <div className="misty-table">
            <table className="w-full">
              <thead>
                <tr>
                  <th className="py-2 text-sm">Supplier Name</th>
                  <th className="py-2 text-sm">Contact Person</th>
                  <th className="py-2 text-sm">Email</th>
                  <th className="py-2 text-sm">Phone</th>
                  <th className="py-2 text-sm">Currency</th>
                  <th className="py-2 text-sm">Bank</th>
                  <th className="py-2 text-sm">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredSuppliers.map((supplier) => (
                  <tr 
                    key={supplier.id}
                    onDoubleClick={() => handleEdit(supplier)}
                    className="cursor-pointer hover:bg-gray-700/50 transition-colors border-b border-gray-700/50"
                    title="Double-click to edit"
                  >
                    <td className="font-medium text-sm py-2 px-3">{supplier.supplier_name}</td>
                    <td className="text-sm py-2 px-3">{supplier.contact_person || '—'}</td>
                    <td className="text-sm py-2 px-3">{supplier.email}</td>
                    <td className="text-sm py-2 px-3">{supplier.phone_number}</td>
                    <td className="text-yellow-400 font-medium text-sm py-2 px-3">{supplier.currency_accepted}</td>
                    <td className="text-sm py-2 px-3">{supplier.bank_name}</td>
                    <td className="py-2 px-3">
                      <div className="flex items-center justify-center space-x-2">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleEdit(supplier);
                          }}
                          className="text-blue-400 hover:text-blue-300 transition-colors"
                          title="Edit supplier"
                        >
                          <PencilIcon className="h-4 w-4" />
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDelete(supplier);
                          }}
                          className="text-red-400 hover:text-red-300 transition-colors"
                          title="Delete supplier"
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
            <div className="mx-auto h-12 w-12 text-gray-400 mb-4">🏢</div>
            <h3 className="text-sm font-medium text-gray-300">
              {searchTerm ? 'No suppliers found' : 'No suppliers'}
            </h3>
            <p className="mt-1 text-sm text-gray-400">
              {searchTerm
                ? 'Try adjusting your search criteria.'
                : 'Get started by adding your first supplier.'
              }
            </p>
            {!searchTerm && (
              <div className="mt-6">
                <button
                  onClick={handleCreate}
                  className="misty-button misty-button-primary"
                >
                  <PlusIcon className="h-5 w-5 mr-2" />
                  Add Supplier
                </button>
              </div>
            )}
          </div>
        )}

        {/* Supplier Form Modal */}
        {showModal && (
          <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && setShowModal(false)}>
            <div className="modal-content max-w-4xl max-h-[90vh] overflow-y-auto">
              <form onSubmit={handleSubmit} className="p-6">
                {/* Header */}
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-2xl font-bold text-white">
                    {selectedSupplier ? 'Edit Supplier' : 'Add New Supplier'}
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
                    <div className="md:col-span-2">
                      <label className="block text-sm font-medium text-gray-300 mb-1">
                        Supplier Name *
                      </label>
                      <input
                        type="text"
                        name="supplier_name"
                        value={formData.supplier_name}
                        onChange={handleInputChange}
                        className={`misty-input w-full ${errors.supplier_name ? 'border-red-500' : ''}`}
                        placeholder="Enter supplier name"
                        required
                      />
                      {errors.supplier_name && (
                        <p className="text-red-400 text-sm mt-1">{errors.supplier_name}</p>
                      )}
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-1">
                        Contact Person
                      </label>
                      <input
                        type="text"
                        name="contact_person"
                        value={formData.contact_person}
                        onChange={handleInputChange}
                        className="misty-input w-full"
                        placeholder="Enter contact person name"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-1">
                        Phone Number *
                      </label>
                      <input
                        type="text"
                        name="phone_number"
                        value={formData.phone_number}
                        onChange={handleInputChange}
                        className={`misty-input w-full ${errors.phone_number ? 'border-red-500' : ''}`}
                        placeholder="Enter phone number"
                        required
                      />
                      {errors.phone_number && (
                        <p className="text-red-400 text-sm mt-1">{errors.phone_number}</p>
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
                        <p className="text-red-400 text-sm mt-1">{errors.email}</p>
                      )}
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-1">
                        Currency Accepted *
                      </label>
                      <select
                        name="currency_accepted"
                        value={formData.currency_accepted}
                        onChange={handleInputChange}
                        className="misty-select w-full"
                        required
                      >
                        {currencyOptions.map(currency => (
                          <option key={currency} value={currency}>{currency}</option>
                        ))}
                      </select>
                    </div>

                    <div className="md:col-span-2">
                      <label className="block text-sm font-medium text-gray-300 mb-1">
                        Physical Address *
                      </label>
                      <textarea
                        name="physical_address"
                        value={formData.physical_address}
                        onChange={handleInputChange}
                        className={`misty-input w-full ${errors.physical_address ? 'border-red-500' : ''}`}
                        placeholder="Enter physical business address"
                        rows="2"
                        required
                      />
                      {errors.physical_address && (
                        <p className="text-red-400 text-sm mt-1">{errors.physical_address}</p>
                      )}
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-1">
                        Post Code *
                      </label>
                      <input
                        type="text"
                        name="post_code"
                        value={formData.post_code}
                        onChange={handleInputChange}
                        className={`misty-input w-full ${errors.post_code ? 'border-red-500' : ''}`}
                        placeholder="Enter post code"
                        required
                      />
                      {errors.post_code && (
                        <p className="text-red-400 text-sm mt-1">{errors.post_code}</p>
                      )}
                    </div>
                  </div>
                </div>

                {/* Bank Details */}
                <div className="mb-8">
                  <h3 className="text-lg font-semibold text-white mb-4">Bank Details</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-1">
                        Bank Name *
                      </label>
                      <input
                        type="text"
                        name="bank_name"
                        value={formData.bank_name}
                        onChange={handleInputChange}
                        className={`misty-input w-full ${errors.bank_name ? 'border-red-500' : ''}`}
                        placeholder="Enter bank name"
                        required
                      />
                      {errors.bank_name && (
                        <p className="text-red-400 text-sm mt-1">{errors.bank_name}</p>
                      )}
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-1">
                        Account Name *
                      </label>
                      <input
                        type="text"
                        name="account_name"
                        value={formData.account_name}
                        onChange={handleInputChange}
                        className={`misty-input w-full ${errors.account_name ? 'border-red-500' : ''}`}
                        placeholder="Enter account holder name"
                        required
                      />
                      {errors.account_name && (
                        <p className="text-red-400 text-sm mt-1">{errors.account_name}</p>
                      )}
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-1">
                        Bank Account Number *
                      </label>
                      <input
                        type="text"
                        name="bank_account_number"
                        value={formData.bank_account_number}
                        onChange={handleInputChange}
                        className={`misty-input w-full ${errors.bank_account_number ? 'border-red-500' : ''}`}
                        placeholder="Enter bank account number"
                        required
                      />
                      {errors.bank_account_number && (
                        <p className="text-red-400 text-sm mt-1">{errors.bank_account_number}</p>
                      )}
                    </div>

                    <div className="md:col-span-2">
                      <label className="block text-sm font-medium text-gray-300 mb-1">
                        Bank Address
                      </label>
                      <textarea
                        name="bank_address"
                        value={formData.bank_address}
                        onChange={handleInputChange}
                        className="misty-input w-full"
                        placeholder="Enter bank address"
                        rows="2"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-1">
                        SWIFT Code
                      </label>
                      <input
                        type="text"
                        name="swift_code"
                        value={formData.swift_code}
                        onChange={handleInputChange}
                        className="misty-input w-full"
                        placeholder="Enter SWIFT code (optional)"
                      />
                    </div>
                  </div>
                </div>

                {/* Form Actions */}
                <div className="flex justify-between pt-6 border-t border-gray-700">
                  <div>
                    {selectedSupplier && (
                      <button
                        type="button"
                        onClick={() => handleDelete(selectedSupplier)}
                        className="misty-button misty-button-danger"
                      >
                        <TrashIcon className="h-4 w-4 mr-2" />
                        Delete Supplier
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
                      {selectedSupplier ? 'Update Supplier' : 'Create Supplier'}
                    </button>
                  </div>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default SuppliersManagement;