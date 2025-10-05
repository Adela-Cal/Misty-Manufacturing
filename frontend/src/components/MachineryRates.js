import React, { useState, useEffect } from 'react';
import Layout from './Layout';
import { apiHelpers } from '../utils/api';
import { toast } from 'sonner';
import { 
  PlusIcon, 
  PencilIcon,
  TrashIcon,
  MagnifyingGlassIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';

const MachineryRates = () => {
  const [rates, setRates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [selectedRate, setSelectedRate] = useState(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [rateToDelete, setRateToDelete] = useState(null);
  const [formData, setFormData] = useState({
    function: '',
    rate_per_hour: '',
    description: ''
  });
  const [errors, setErrors] = useState({});

  // Core Winding Specifications - Static data based on manufacturing requirements
  const coreWindingSpecs = [
    {
      coreRange: '15–20 mm',
      paperWidth: '29–31 mm', 
      beltSize: '30 mm',
      recommendedAngle: '72°',
      workableRange: '70–74°',
      lengthFactor: '3.236'
    },
    {
      coreRange: '21–30 mm',
      paperWidth: '37–41 mm',
      beltSize: '40 mm', 
      recommendedAngle: '70°',
      workableRange: '68–73°',
      lengthFactor: '2.924'
    },
    {
      coreRange: '31–50 mm',
      paperWidth: '57–61 mm',
      beltSize: '60 mm',
      recommendedAngle: '68°', 
      workableRange: '66–72°',
      lengthFactor: '2.670'
    },
    {
      coreRange: '51–70 mm',
      paperWidth: '76–81 mm',
      beltSize: '80 mm',
      recommendedAngle: '66°',
      workableRange: '64–70°', 
      lengthFactor: '2.459'
    },
    {
      coreRange: '71–120 mm',
      paperWidth: '103–106 mm',
      beltSize: '105 mm',
      recommendedAngle: '65°',
      workableRange: '62–68°',
      lengthFactor: '2.366'
    },
    {
      coreRange: '121–200 mm',
      paperWidth: '118–122 mm', 
      beltSize: '120 mm',
      recommendedAngle: '64°',
      workableRange: '60–66°',
      lengthFactor: '2.281'
    },
    {
      coreRange: '> 201 mm',
      paperWidth: '148–152 mm',
      beltSize: '150 mm', 
      recommendedAngle: '62°',
      workableRange: '58–65°',
      lengthFactor: '2.130'
    }
  ];

  // Available function types
  const functionOptions = [
    'Slitting',
    'core_winder', 
    'Cutting/Indexing',
    'splitting',
    'Packing',
    'Delivery Time'
  ];

  useEffect(() => {
    loadRates();
  }, []);

  const loadRates = async () => {
    try {
      setLoading(true);
      const response = await apiHelpers.getMachineryRates();
      setRates(response.data);
    } catch (error) {
      console.error('Failed to load machinery rates:', error);
      toast.error('Failed to load machinery rates');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setSelectedRate(null);
    setFormData({
      function: '',
      rate_per_hour: '',
      description: ''
    });
    setErrors({});
    setShowModal(true);
  };

  const handleEdit = (rate) => {
    setSelectedRate(rate);
    setFormData({
      function: rate.function,
      rate_per_hour: rate.rate_per_hour.toString(),
      description: rate.description || ''
    });
    setErrors({});
    setShowModal(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Reset errors
    setErrors({});
    
    // Validate form
    const newErrors = {};
    if (!formData.function.trim()) {
      newErrors.function = 'Function is required';
    }
    if (!formData.rate_per_hour.trim()) {
      newErrors.rate_per_hour = 'Rate per hour is required';
    } else if (isNaN(parseFloat(formData.rate_per_hour)) || parseFloat(formData.rate_per_hour) <= 0) {
      newErrors.rate_per_hour = 'Rate per hour must be a positive number';
    }
    
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    try {
      const submitData = {
        function: formData.function.trim(),
        rate_per_hour: parseFloat(formData.rate_per_hour),
        description: formData.description.trim() || null
      };

      if (selectedRate) {
        // Update existing rate
        await apiHelpers.updateMachineryRate(selectedRate.id, submitData);
        toast.success('Machinery rate updated successfully');
      } else {
        // Create new rate
        await apiHelpers.createMachineryRate(submitData);
        toast.success('Machinery rate created successfully');
      }

      setShowModal(false);
      loadRates(); // Reload the rates list
    } catch (error) {
      console.error('Error saving machinery rate:', error);
      
      // Handle validation errors from the API
      if (error.response && error.response.status === 422 && error.response.data.detail) {
        if (Array.isArray(error.response.data.detail)) {
          const errorMessage = error.response.data.detail.map(err => err.msg || err.message || 'Validation error').join(', ');
          toast.error(errorMessage);
        } else {
          toast.error('Please fix the validation errors');
        }
      } else if (error.response && error.response.status === 400) {
        toast.error(error.response.data.detail || 'Rate for this function already exists');
      } else {
        toast.error('Failed to save machinery rate');
      }
    }
  };

  const handleDeleteClick = (rate) => {
    setRateToDelete(rate);
    setShowDeleteConfirm(true);
  };

  const handleDeleteConfirm = async () => {
    if (!rateToDelete) return;

    try {
      await apiHelpers.deleteMachineryRate(rateToDelete.id);
      toast.success('Machinery rate deleted successfully');
      setShowDeleteConfirm(false);
      setRateToDelete(null);
      setShowModal(false);
      loadRates(); // Reload the rates list
    } catch (error) {
      console.error('Error deleting machinery rate:', error);
      toast.error('Failed to delete machinery rate');
    }
  };

  const handleDeleteCancel = () => {
    setShowDeleteConfirm(false);
    setRateToDelete(null);
  };

  const filteredRates = rates.filter(rate =>
    rate.function.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (rate.description && rate.description.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  if (loading) {
    return (
      <Layout>
        <div className="flex justify-center items-center h-64">
          <div className="text-white">Loading machinery rates...</div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-white">Machinery Specifications</h1>
            <p className="text-gray-400 mt-1">Manage machinery specifications and core winding parameters</p>
          </div>
          <button 
            onClick={handleCreate}
            className="misty-button misty-button-primary flex items-center"
          >
            <PlusIcon className="h-5 w-5 mr-2" />
            Add Specification
          </button>
        </div>

        {/* Search */}
        <div className="relative">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search by function or description..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:border-blue-500 focus:outline-none"
          />
        </div>

        {/* Rates Table */}
        <div className="bg-gray-800 rounded-lg overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-700">
            <h2 className="text-xl font-semibold text-white">
              Machinery Specifications ({filteredRates.length})
            </h2>
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-700">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Function
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Rate per Hour
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Description
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Created
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {filteredRates.length > 0 ? (
                  filteredRates.map((rate) => (
                    <tr key={rate.id} className="hover:bg-gray-700">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-white">{rate.function}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-white">${rate.rate_per_hour.toFixed(2)}</div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm text-gray-300 max-w-xs truncate">
                          {rate.description || '-'}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-300">
                          {new Date(rate.created_at).toLocaleDateString()}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <div className="flex space-x-2">
                          <button
                            onClick={() => handleEdit(rate)}
                            className="text-blue-400 hover:text-blue-300"
                          >
                            <PencilIcon className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => handleDeleteClick(rate)}
                            className="text-red-400 hover:text-red-300"
                          >
                            <TrashIcon className="h-4 w-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="5" className="px-6 py-8 text-center">
                      <div className="text-gray-400">
                        {searchTerm ? 'No rates found matching your search.' : 'No machinery rates configured yet.'}
                      </div>
                      {!searchTerm && (
                        <button 
                          onClick={handleCreate}
                          className="mt-2 text-blue-400 hover:text-blue-300 text-sm"
                        >
                          Add your first machinery rate
                        </button>
                      )}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Core Winding Specifications Table */}
        <div className="bg-gray-800 rounded-lg overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-700">
            <h2 className="text-xl font-semibold text-white">
              Core Winding Specifications
            </h2>
            <p className="text-gray-400 text-sm mt-1">
              Manufacturing parameters for different core diameters
            </p>
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-700">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Core Ø
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Paper Width
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Belt Size
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Recommended Angle
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Workable Range
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Length Factor
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {coreWindingSpecs.map((spec, index) => (
                  <tr key={index} className="hover:bg-gray-700 transition-colors">
                    <td className="px-4 py-3 text-sm font-medium text-white">
                      {spec.coreRange}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-300">
                      {spec.paperWidth}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-300">
                      {spec.beltSize}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-300">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        {spec.recommendedAngle}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-300">
                      {spec.workableRange}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-300">
                      <span className="font-mono">
                        {spec.lengthFactor}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Create/Edit Modal */}
        {showModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-gray-800 rounded-lg max-w-md w-full mx-4">
              <div className="flex justify-between items-center p-6 border-b border-gray-700">
                <h3 className="text-lg font-medium text-white">
                  {selectedRate ? 'Edit Machinery Rate' : 'Add Machinery Rate'}
                </h3>
                <button
                  onClick={() => setShowModal(false)}
                  className="text-gray-400 hover:text-white"
                >
                  <XMarkIcon className="h-6 w-6" />
                </button>
              </div>

              <form onSubmit={handleSubmit} className="p-6">
                <div className="space-y-4">
                  {/* Function Selection */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Function <span className="text-red-400">*</span>
                    </label>
                    <select
                      value={formData.function}
                      onChange={(e) => setFormData(prev => ({ ...prev, function: e.target.value }))}
                      className={`w-full px-3 py-2 bg-gray-700 border rounded-lg text-white focus:outline-none focus:border-blue-500 ${
                        errors.function ? 'border-red-500' : 'border-gray-600'
                      }`}
                    >
                      <option value="">Select a function</option>
                      {functionOptions.map(option => (
                        <option key={option} value={option}>{option}</option>
                      ))}
                    </select>
                    {errors.function && (
                      <p className="text-red-400 text-sm mt-1">{errors.function}</p>
                    )}
                  </div>

                  {/* Rate per Hour */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Rate per Hour ($) <span className="text-red-400">*</span>
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      value={formData.rate_per_hour}
                      onChange={(e) => setFormData(prev => ({ ...prev, rate_per_hour: e.target.value }))}
                      className={`w-full px-3 py-2 bg-gray-700 border rounded-lg text-white focus:outline-none focus:border-blue-500 ${
                        errors.rate_per_hour ? 'border-red-500' : 'border-gray-600'
                      }`}
                      placeholder="0.00"
                    />
                    {errors.rate_per_hour && (
                      <p className="text-red-400 text-sm mt-1">{errors.rate_per_hour}</p>
                    )}
                  </div>

                  {/* Description */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Description (Optional)
                    </label>
                    <textarea
                      value={formData.description}
                      onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                      rows={3}
                      className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                      placeholder="Optional description for this rate..."
                    />
                  </div>
                </div>

                <div className="flex justify-between items-center mt-6 pt-4 border-t border-gray-700">
                  {selectedRate && (
                    <button
                      type="button"
                      onClick={() => handleDeleteClick(selectedRate)}
                      className="misty-button misty-button-danger mr-auto"
                    >
                      Delete Rate
                    </button>
                  )}
                  
                  <div className="flex space-x-3 ml-auto">
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
                      {selectedRate ? 'Update Rate' : 'Create Rate'}
                    </button>
                  </div>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Delete Confirmation Modal */}
        {showDeleteConfirm && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-gray-800 rounded-lg max-w-md w-full mx-4">
              <div className="p-6">
                <h3 className="text-lg font-medium text-white mb-4">Confirm Delete</h3>
                <p className="text-gray-300 mb-6">
                  Are you sure you want to delete the rate for "{rateToDelete?.function}"? This action cannot be undone.
                </p>
                
                <div className="flex justify-end space-x-3">
                  <button
                    onClick={handleDeleteCancel}
                    className="misty-button misty-button-secondary"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleDeleteConfirm}
                    className="misty-button misty-button-danger"
                  >
                    Delete
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

export default MachineryRates;