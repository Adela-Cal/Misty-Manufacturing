import React, { useState, useEffect } from 'react';
import { apiHelpers } from '../utils/api';
import { toast } from 'sonner';
import { XMarkIcon, PhotoIcon, PlusIcon } from '@heroicons/react/24/outline';
import ClientProductCatalog from './ClientProductCatalog';

const ClientForm = ({ client, onClose, onSuccess }) => {
  const [formData, setFormData] = useState({
    company_name: '',
    abn: '',
    address: '',
    city: '',
    state: '',
    postal_code: '',
    country: 'Australia',
    phone: '',
    email: '',
    website: '',
    payment_terms: 'Net 30 days',
    lead_time_days: 7,
    contacts: [],
    bank_details: {
      bank_name: '',
      account_name: '',
      bsb: '',
      account_number: '',
      reference: ''
    },
    notes: ''
  });
  
  const [logoFile, setLogoFile] = useState(null);
  const [logoPreview, setLogoPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});
  const [showBankDetails, setShowBankDetails] = useState(false);
  const [showContacts, setShowContacts] = useState(false);

  useEffect(() => {
    if (client) {
      setFormData({
        company_name: client.company_name || '',
        abn: client.abn || '',
        address: client.address || '',
        city: client.city || '',
        state: client.state || '',
        postal_code: client.postal_code || '',
        country: client.country || 'Australia',
        phone: client.phone || '',
        email: client.email || '',
        website: client.website || '',
        payment_terms: client.payment_terms || 'Net 30 days',
        lead_time_days: client.lead_time_days || 7,
        contacts: client.contacts || [],
        bank_details: client.bank_details || {
          bank_name: '',
          account_name: '',
          bsb: '',
          account_number: '',
          reference: ''
        },
        notes: client.notes || ''
      });
      setShowBankDetails(!!client.bank_details?.bank_name);
      setShowContacts(client.contacts?.length > 0);
    }
  }, [client]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    
    if (name.startsWith('bank_')) {
      const bankField = name.replace('bank_', '');
      setFormData(prev => ({
        ...prev,
        bank_details: {
          ...prev.bank_details,
          [bankField]: value
        }
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        [name]: value
      }));
    }
    
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const handleLogoChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (file.size > 5 * 1024 * 1024) {
        toast.error('Logo file must be less than 5MB');
        return;
      }
      
      const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
      if (!allowedTypes.includes(file.type)) {
        toast.error('Logo must be a JPEG, PNG, GIF, or WebP image');
        return;
      }
      
      setLogoFile(file);
      
      // Create preview
      const reader = new FileReader();
      reader.onload = (e) => setLogoPreview(e.target.result);
      reader.readAsDataURL(file);
    }
  };

  const addContact = () => {
    setFormData(prev => ({
      ...prev,
      contacts: [...prev.contacts, {
        name: '',
        position: '',
        email: '',
        phone: '',
        is_primary: prev.contacts.length === 0
      }]
    }));
    setShowContacts(true);
  };

  const updateContact = (index, field, value) => {
    setFormData(prev => ({
      ...prev,
      contacts: prev.contacts.map((contact, i) => 
        i === index ? { ...contact, [field]: value } : contact
      )
    }));
  };

  const removeContact = (index) => {
    setFormData(prev => ({
      ...prev,
      contacts: prev.contacts.filter((_, i) => i !== index)
    }));
  };

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.company_name.trim()) {
      newErrors.company_name = 'Company name is required';
    }
    
    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }
    
    if (!formData.phone.trim()) {
      newErrors.phone = 'Phone number is required';
    }
    
    if (!formData.address.trim()) {
      newErrors.address = 'Address is required';
    }
    
    if (!formData.city.trim()) {
      newErrors.city = 'City is required';
    }
    
    if (!formData.state.trim()) {
      newErrors.state = 'State is required';
    }
    
    if (!formData.postal_code.trim()) {
      newErrors.postal_code = 'Postal code is required';
    }
    
    // Validate BSB if provided
    if (showBankDetails && formData.bank_details.bsb && !/^\d{6}$/.test(formData.bank_details.bsb.replace(/[-\s]/g, ''))) {
      newErrors.bank_bsb = 'BSB must be 6 digits (e.g., 012-345)';
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
    
    setLoading(true);
    
    try {
      let clientData = { ...formData };
      
      // Clean up bank details if not provided
      if (!showBankDetails || !clientData.bank_details.bank_name) {
        clientData.bank_details = null;
      }
      
      // Clean up contacts if empty
      if (!showContacts || clientData.contacts.length === 0) {
        clientData.contacts = [];
      }
      
      let savedClient;
      if (client) {
        // Update existing client
        await apiHelpers.updateClient(client.id, clientData);
        savedClient = { ...client, ...clientData };
        toast.success('Client updated successfully');
      } else {
        // Create new client
        const response = await apiHelpers.createClient(clientData);
        savedClient = { id: response.data.data.id, ...clientData };
        toast.success('Client created successfully');
      }
      
      // Upload logo if provided
      if (logoFile && savedClient.id) {
        try {
          await apiHelpers.uploadClientLogo(savedClient.id, logoFile);
          toast.success('Logo uploaded successfully');
        } catch (logoError) {
          console.error('Logo upload failed:', logoError);
          toast.error('Client saved but logo upload failed');
        }
      }
      
      onSuccess?.();
      onClose();
      
    } catch (error) {
      console.error('Failed to save client:', error);
      const message = error.response?.data?.detail || 'Failed to save client';
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  const australianStates = [
    'NSW', 'VIC', 'QLD', 'WA', 'SA', 'TAS', 'ACT', 'NT'
  ];

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal-content max-w-4xl max-h-[90vh] overflow-y-auto">
        <form onSubmit={handleSubmit} className="p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-white">
              {client ? 'Edit Client' : 'Add New Client'}
            </h2>
            <button
              type="button"
              onClick={onClose}
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
                  Company Name *
                </label>
                <input
                  type="text"
                  name="company_name"
                  value={formData.company_name}
                  onChange={handleInputChange}
                  className={`misty-input w-full ${errors.company_name ? 'border-red-500' : ''}`}
                  placeholder="Enter company name"
                  required
                />
                {errors.company_name && (
                  <p className="text-red-400 text-sm mt-1">{errors.company_name}</p>
                )}
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  ABN
                </label>
                <input
                  type="text"
                  name="abn"
                  value={formData.abn}
                  onChange={handleInputChange}
                  className="misty-input w-full"
                  placeholder="XX XXX XXX XXX"
                />
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
                  placeholder="company@example.com"
                  required
                />
                {errors.email && (
                  <p className="text-red-400 text-sm mt-1">{errors.email}</p>
                )}
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Phone *
                </label>
                <input
                  type="tel"
                  name="phone"
                  value={formData.phone}
                  onChange={handleInputChange}
                  className={`misty-input w-full ${errors.phone ? 'border-red-500' : ''}`}
                  placeholder="(02) 1234 5678"
                  required
                />
                {errors.phone && (
                  <p className="text-red-400 text-sm mt-1">{errors.phone}</p>
                )}
              </div>
              
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Website
                </label>
                <input
                  type="url"
                  name="website"
                  value={formData.website}
                  onChange={handleInputChange}
                  className="misty-input w-full"
                  placeholder="https://www.example.com"
                />
              </div>
            </div>
          </div>

          {/* Address */}
          <div className="mb-8">
            <h3 className="text-lg font-semibold text-white mb-4">Address</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Street Address *
                </label>
                <input
                  type="text"
                  name="address"
                  value={formData.address}
                  onChange={handleInputChange}
                  className={`misty-input w-full ${errors.address ? 'border-red-500' : ''}`}
                  placeholder="123 Business Street"
                  required
                />
                {errors.address && (
                  <p className="text-red-400 text-sm mt-1">{errors.address}</p>
                )}
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  City *
                </label>
                <input
                  type="text"
                  name="city"
                  value={formData.city}
                  onChange={handleInputChange}
                  className={`misty-input w-full ${errors.city ? 'border-red-500' : ''}`}
                  placeholder="Sydney"
                  required
                />
                {errors.city && (
                  <p className="text-red-400 text-sm mt-1">{errors.city}</p>
                )}
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  State *
                </label>
                <select
                  name="state"
                  value={formData.state}
                  onChange={handleInputChange}
                  className={`misty-select w-full ${errors.state ? 'border-red-500' : ''}`}
                  required
                >
                  <option value="">Select State</option>
                  {australianStates.map(state => (
                    <option key={state} value={state}>{state}</option>
                  ))}
                </select>
                {errors.state && (
                  <p className="text-red-400 text-sm mt-1">{errors.state}</p>
                )}
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Postal Code *
                </label>
                <input
                  type="text"
                  name="postal_code"
                  value={formData.postal_code}
                  onChange={handleInputChange}
                  className={`misty-input w-full ${errors.postal_code ? 'border-red-500' : ''}`}
                  placeholder="2000"
                  required
                />
                {errors.postal_code && (
                  <p className="text-red-400 text-sm mt-1">{errors.postal_code}</p>
                )}
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Country
                </label>
                <input
                  type="text"
                  name="country"
                  value={formData.country}
                  onChange={handleInputChange}
                  className="misty-input w-full"
                  placeholder="Australia"
                />
              </div>
            </div>
          </div>

          {/* Business Terms */}
          <div className="mb-8">
            <h3 className="text-lg font-semibold text-white mb-4">Business Terms</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Payment Terms
                </label>
                <select
                  name="payment_terms"
                  value={formData.payment_terms}
                  onChange={handleInputChange}
                  className="misty-select w-full"
                >
                  <option value="Net 7 days">Net 7 days</option>
                  <option value="Net 14 days">Net 14 days</option>
                  <option value="Net 30 days">Net 30 days</option>
                  <option value="Net 45 days">Net 45 days</option>
                  <option value="Net 60 days">Net 60 days</option>
                  <option value="Cash on Delivery">Cash on Delivery</option>
                  <option value="Payment in advance">Payment in advance</option>
                  <option value="2/10 Net 30">2/10 Net 30</option>
                </select>
                <p className="text-xs text-gray-400 mt-1">
                  Payment terms for invoices
                </p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Standard Lead Time (Days)
                </label>
                <input
                  type="number"
                  name="lead_time_days"
                  value={formData.lead_time_days}
                  onChange={handleInputChange}
                  min="1"
                  max="365"
                  className="misty-input w-full"
                  placeholder="7"
                />
                <p className="text-xs text-gray-400 mt-1">
                  Default lead time for this client's orders
                </p>
              </div>
            </div>
          </div>

          {/* Logo Upload */}
          <div className="mb-8">
            <h3 className="text-lg font-semibold text-white mb-4">Company Logo</h3>
            <div className="flex items-center space-x-4">
              <div className="flex-shrink-0">
                {logoPreview || client?.logo_path ? (
                  <img
                    src={logoPreview || client.logo_path}
                    alt="Logo preview"
                    className="h-20 w-20 rounded-lg object-cover border border-gray-600"
                  />
                ) : (
                  <div className="h-20 w-20 bg-gray-600 rounded-lg flex items-center justify-center border border-gray-600">
                    <PhotoIcon className="h-8 w-8 text-gray-400" />
                  </div>
                )}
              </div>
              <div className="flex-1">
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleLogoChange}
                  className="hidden"
                  id="logo-upload"
                />
                <label
                  htmlFor="logo-upload"
                  className="misty-button misty-button-secondary cursor-pointer inline-block"
                >
                  Choose Logo
                </label>
                <p className="text-sm text-gray-400 mt-1">
                  Upload a logo (max 5MB, JPEG/PNG/GIF/WebP)
                </p>
              </div>
            </div>
          </div>

          {/* Bank Details Toggle */}
          <div className="mb-6">
            <label className="flex items-center space-x-2 cursor-pointer">
              <input
                type="checkbox"
                checked={showBankDetails}
                onChange={(e) => setShowBankDetails(e.target.checked)}
                className="form-checkbox h-4 w-4 text-yellow-400 bg-gray-700 border-gray-600 rounded focus:ring-yellow-400"
              />
              <span className="text-white font-medium">Add Bank Details</span>
            </label>
          </div>

          {/* Bank Details */}
          {showBankDetails && (
            <div className="mb-8">
              <h3 className="text-lg font-semibold text-white mb-4">Bank Details</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Bank Name
                  </label>
                  <input
                    type="text"
                    name="bank_bank_name"
                    value={formData.bank_details.bank_name}
                    onChange={handleInputChange}
                    className="misty-input w-full"
                    placeholder="Commonwealth Bank"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Account Name
                  </label>
                  <input
                    type="text"
                    name="bank_account_name"
                    value={formData.bank_details.account_name}
                    onChange={handleInputChange}
                    className="misty-input w-full"
                    placeholder="Company Name Pty Ltd"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    BSB
                  </label>
                  <input
                    type="text"
                    name="bank_bsb"
                    value={formData.bank_details.bsb}
                    onChange={handleInputChange}
                    className={`misty-input w-full ${errors.bank_bsb ? 'border-red-500' : ''}`}
                    placeholder="012-345"
                  />
                  {errors.bank_bsb && (
                    <p className="text-red-400 text-sm mt-1">{errors.bank_bsb}</p>
                  )}
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Account Number
                  </label>
                  <input
                    type="text"
                    name="bank_account_number"
                    value={formData.bank_details.account_number}
                    onChange={handleInputChange}
                    className="misty-input w-full"
                    placeholder="123456789"
                  />
                </div>
                
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Payment Reference
                  </label>
                  <input
                    type="text"
                    name="bank_reference"
                    value={formData.bank_details.reference}
                    onChange={handleInputChange}
                    className="misty-input w-full"
                    placeholder="Invoice number or reference"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Contacts Toggle */}
          <div className="mb-6">
            <label className="flex items-center space-x-2 cursor-pointer">
              <input
                type="checkbox"
                checked={showContacts}
                onChange={(e) => setShowContacts(e.target.checked)}
                className="form-checkbox h-4 w-4 text-yellow-400 bg-gray-700 border-gray-600 rounded focus:ring-yellow-400"
              />
              <span className="text-white font-medium">Add Contact Details</span>
            </label>
          </div>

          {/* Contacts */}
          {showContacts && (
            <div className="mb-8">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white">Contacts</h3>
                <button
                  type="button"
                  onClick={addContact}
                  className="misty-button misty-button-secondary text-sm"
                >
                  Add Contact
                </button>
              </div>
              
              {formData.contacts.map((contact, index) => (
                <div key={index} className="border border-gray-600 rounded-lg p-4 mb-4">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-white font-medium">Contact {index + 1}</h4>
                    <button
                      type="button"
                      onClick={() => removeContact(index)}
                      className="text-red-400 hover:text-red-300 text-sm"
                    >
                      Remove
                    </button>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-1">
                        Name
                      </label>
                      <input
                        type="text"
                        value={contact.name}
                        onChange={(e) => updateContact(index, 'name', e.target.value)}
                        className="misty-input w-full"
                        placeholder="John Smith"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-1">
                        Position
                      </label>
                      <input
                        type="text"
                        value={contact.position}
                        onChange={(e) => updateContact(index, 'position', e.target.value)}
                        className="misty-input w-full"
                        placeholder="Operations Manager"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-1">
                        Email
                      </label>
                      <input
                        type="email"
                        value={contact.email}
                        onChange={(e) => updateContact(index, 'email', e.target.value)}
                        className="misty-input w-full"
                        placeholder="john@company.com"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-1">
                        Phone
                      </label>
                      <input
                        type="tel"
                        value={contact.phone}
                        onChange={(e) => updateContact(index, 'phone', e.target.value)}
                        className="misty-input w-full"
                        placeholder="(02) 1234 5678"
                      />
                    </div>
                  </div>
                  
                  <div className="mt-3">
                    <label className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={contact.is_primary}
                        onChange={(e) => updateContact(index, 'is_primary', e.target.checked)}
                        className="form-checkbox h-4 w-4 text-yellow-400 bg-gray-700 border-gray-600 rounded focus:ring-yellow-400"
                      />
                      <span className="text-sm text-gray-300">Primary Contact</span>
                    </label>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Notes */}
          <div className="mb-8">
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Notes
            </label>
            <textarea
              name="notes"
              value={formData.notes}
              onChange={handleInputChange}
              rows={3}
              className="misty-textarea w-full"
              placeholder="Additional notes about this client..."
            />
          </div>

          {/* Form Actions */}
          <div className="flex justify-end space-x-3 pt-6 border-t border-gray-700">
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
              disabled={loading}
            >
              {loading ? (
                <div className="flex items-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-900 mr-2"></div>
                  {client ? 'Updating...' : 'Creating...'}
                </div>
              ) : (
                client ? 'Update Client' : 'Create Client'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ClientForm;