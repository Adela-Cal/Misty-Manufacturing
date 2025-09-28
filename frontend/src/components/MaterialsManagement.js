import React, { useState, useEffect } from 'react';
import Layout from './Layout';
import { apiHelpers } from '../utils/api';
import { toast } from 'sonner';
import { 
  PlusIcon, 
  PencilIcon, 
  TrashIcon, 
  MagnifyingGlassIcon,
  XMarkIcon,
  CheckIcon
} from '@heroicons/react/24/outline';

const MaterialsManagement = () => {
  const [materials, setMaterials] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [selectedMaterial, setSelectedMaterial] = useState(null);
  const [formData, setFormData] = useState({
    supplier: '',
    product_code: '',
    order_to_delivery_time: '',
    material_description: '',  // New field
    price: '',
    unit: 'm2',
    raw_substrate: false,
    gsm: '',
    thickness_mm: '',
    burst_strength_kpa: '',
    ply_bonding_jm2: '',
    moisture_percent: '',
    supplied_roll_weight: '',  // New field
    master_deckle_width_mm: ''  // New field
  });
  const [errors, setErrors] = useState({});

  useEffect(() => {
    loadMaterials();
  }, []);

  const loadMaterials = async () => {
    try {
      setLoading(true);
      const response = await apiHelpers.getMaterials();
      setMaterials(response.data);
    } catch (error) {
      console.error('Failed to load materials:', error);
      toast.error('Failed to load materials');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setSelectedMaterial(null);
    setFormData({
      supplier: '',
      product_code: '',
      order_to_delivery_time: '',
      material_description: '',  // New field
      price: '',
      unit: 'm2',
      raw_substrate: false,
      gsm: '',
      thickness_mm: '',
      burst_strength_kpa: '',
      ply_bonding_jm2: '',
      moisture_percent: '',
      supplied_roll_weight: '',  // New field
      master_deckle_width_mm: ''  // New field
    });
    setErrors({});
    setShowModal(true);
  };

  const handleEdit = (material) => {
    setSelectedMaterial(material);
    setFormData({
      supplier: material.supplier,
      product_code: material.product_code,
      order_to_delivery_time: material.order_to_delivery_time,
      material_description: material.material_description || '',  // New field
      price: material.price.toString(),
      unit: material.unit,
      raw_substrate: material.raw_substrate || false,
      gsm: material.gsm || '',
      thickness_mm: material.thickness_mm ? material.thickness_mm.toString() : '',
      burst_strength_kpa: material.burst_strength_kpa ? material.burst_strength_kpa.toString() : '',
      ply_bonding_jm2: material.ply_bonding_jm2 ? material.ply_bonding_jm2.toString() : '',
      moisture_percent: material.moisture_percent ? material.moisture_percent.toString() : '',
      supplied_roll_weight: material.supplied_roll_weight ? material.supplied_roll_weight.toString() : '',  // New field
      master_deckle_width_mm: material.master_deckle_width_mm ? material.master_deckle_width_mm.toString() : ''  // New field
    });
    setErrors({});
    setShowModal(true);
  };

  const handleDelete = async (material) => {
    if (window.confirm(`Are you sure you want to delete the material "${material.product_code}" from ${material.supplier}?`)) {
      try {
        await apiHelpers.deleteMaterial(material.id);
        toast.success('Material deleted successfully');
        loadMaterials();
      } catch (error) {
        console.error('Failed to delete material:', error);
        toast.error('Failed to delete material');
      }
    }
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
    
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.supplier.trim()) {
      newErrors.supplier = 'Supplier is required';
    }
    
    if (!formData.product_code.trim()) {
      newErrors.product_code = 'Product code is required';
    }
    
    if (!formData.order_to_delivery_time.trim()) {
      newErrors.order_to_delivery_time = 'Order to delivery time is required';
    }
    
    if (!formData.material_description.trim()) {
      newErrors.material_description = 'Material description is required';
    }
    
    if (!formData.price || parseFloat(formData.price) <= 0) {
      newErrors.price = 'Price must be greater than 0';
    }
    
    if (!formData.unit) {
      newErrors.unit = 'Unit is required';
    }

    // Validate raw substrate fields if selected
    if (formData.raw_substrate) {
      if (!formData.gsm.trim()) {
        newErrors.gsm = 'GSM is required for raw substrate';
      }
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
        supplier: formData.supplier,
        product_code: formData.product_code,
        order_to_delivery_time: formData.order_to_delivery_time,
        material_description: formData.material_description,  // New field
        price: parseFloat(formData.price),
        unit: formData.unit,
        raw_substrate: formData.raw_substrate,
        gsm: formData.raw_substrate && formData.gsm ? formData.gsm : null,
        thickness_mm: formData.raw_substrate && formData.thickness_mm ? parseFloat(formData.thickness_mm) : null,
        burst_strength_kpa: formData.raw_substrate && formData.burst_strength_kpa ? parseFloat(formData.burst_strength_kpa) : null,
        ply_bonding_jm2: formData.raw_substrate && formData.ply_bonding_jm2 ? parseFloat(formData.ply_bonding_jm2) : null,
        moisture_percent: formData.raw_substrate && formData.moisture_percent ? parseFloat(formData.moisture_percent) : null,
        supplied_roll_weight: formData.raw_substrate && formData.supplied_roll_weight ? parseFloat(formData.supplied_roll_weight) : null,  // New field
        master_deckle_width_mm: formData.raw_substrate && formData.master_deckle_width_mm ? parseFloat(formData.master_deckle_width_mm) : null  // New field
      };

      if (selectedMaterial) {
        await apiHelpers.updateMaterial(selectedMaterial.id, submitData);
        toast.success('Material updated successfully');
      } else {
        await apiHelpers.createMaterial(submitData);
        toast.success('Material created successfully');
      }
      
      setShowModal(false);
      loadMaterials();
    } catch (error) {
      console.error('Failed to save material:', error);
      const message = error.response?.data?.detail || 'Failed to save material';
      toast.error(message);
    }
  };

  const filteredMaterials = materials.filter(material =>
    material.supplier.toLowerCase().includes(searchTerm.toLowerCase()) ||
    material.product_code.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const unitOptions = [
    'm2',
    'By the Box',
    'Single Unit'
  ];

  // Calculate linear meters for raw substrate
  const calculateLinearMeters = () => {
    if (!formData.raw_substrate || !formData.gsm || !formData.supplied_roll_weight || !formData.master_deckle_width_mm) {
      return '';
    }
    
    const gsm = parseFloat(formData.gsm);
    const weight = parseFloat(formData.supplied_roll_weight);
    const width = parseFloat(formData.master_deckle_width_mm);
    
    if (gsm > 0 && weight > 0 && width > 0) {
      // Formula: Linear meters = (Weight in kg * 1,000,000) / (GSM * width in mm)
      const linearMeters = (weight * 1000000) / (gsm * width);
      return linearMeters.toFixed(2);
    }
    
    return '';
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
      <div className="p-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Products & Materials</h1>
            <p className="text-gray-400">Manage your materials database and specifications</p>
          </div>
          <button
            onClick={handleCreate}
            className="misty-button misty-button-primary flex items-center"
          >
            <PlusIcon className="h-5 w-5 mr-2" />
            Add Material
          </button>
        </div>

        {/* Search */}
        <div className="mb-6">
          <div className="relative max-w-md">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search materials..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="misty-input pl-10 w-full"
            />
          </div>
        </div>

        {/* Materials Table */}
        {filteredMaterials.length > 0 ? (
          <div className="misty-table">
            <table className="w-full">
              <thead>
                <tr>
                  <th>Supplier</th>
                  <th>Product Code</th>
                  <th>Description</th>
                  <th>Price</th>
                  <th>Unit</th>
                  <th>Delivery Time</th>
                  <th>Raw Substrate</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredMaterials.map((material) => (
                  <tr key={material.id}>
                    <td className="font-medium">{material.supplier}</td>
                    <td>{material.product_code}</td>
                    <td className="text-gray-300 max-w-xs truncate" title={material.material_description}>
                      {material.material_description || '—'}
                    </td>
                    <td className="text-yellow-400 font-medium">
                      ${material.price.toFixed(2)}
                    </td>
                    <td>{material.unit}</td>
                    <td>{material.order_to_delivery_time}</td>
                    <td>
                      {material.raw_substrate ? (
                        <CheckIcon className="h-4 w-4 text-green-400" />
                      ) : (
                        <span className="text-gray-400">—</span>
                      )}
                    </td>
                    <td>
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => handleEdit(material)}
                          className="text-gray-400 hover:text-yellow-400 transition-colors"
                          title="Edit material"
                        >
                          <PencilIcon className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(material)}
                          className="text-gray-400 hover:text-red-400 transition-colors"
                          title="Delete material"
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
              {searchTerm ? 'No materials found' : 'No materials'}
            </h3>
            <p className="mt-1 text-sm text-gray-400">
              {searchTerm
                ? 'Try adjusting your search criteria.'
                : 'Get started by adding your first material.'
              }
            </p>
            {!searchTerm && (
              <div className="mt-6">
                <button
                  onClick={handleCreate}
                  className="misty-button misty-button-primary"
                >
                  <PlusIcon className="h-5 w-5 mr-2" />
                  Add Material
                </button>
              </div>
            )}
          </div>
        )}

        {/* Material Form Modal */}
        {showModal && (
          <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && setShowModal(false)}>
            <div className="modal-content max-w-2xl max-h-[90vh] overflow-y-auto">
              <form onSubmit={handleSubmit} className="p-6">
                {/* Header */}
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-2xl font-bold text-white">
                    {selectedMaterial ? 'Edit Material' : 'Add New Material'}
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
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-1">
                        Supplier *
                      </label>
                      <input
                        type="text"
                        name="supplier"
                        value={formData.supplier}
                        onChange={handleInputChange}
                        className={`misty-input w-full ${errors.supplier ? 'border-red-500' : ''}`}
                        placeholder="Enter supplier name"
                        required
                      />
                      {errors.supplier && (
                        <p className="text-red-400 text-sm mt-1">{errors.supplier}</p>
                      )}
                    </div>

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
                        Price *
                      </label>
                      <input
                        type="number"
                        step="0.01"
                        min="0"
                        name="price"
                        value={formData.price}
                        onChange={handleInputChange}
                        className={`misty-input w-full ${errors.price ? 'border-red-500' : ''}`}
                        placeholder="0.00"
                        required
                      />
                      {errors.price && (
                        <p className="text-red-400 text-sm mt-1">{errors.price}</p>
                      )}
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-1">
                        Unit *
                      </label>
                      <select
                        name="unit"
                        value={formData.unit}
                        onChange={handleInputChange}
                        className={`misty-select w-full ${errors.unit ? 'border-red-500' : ''}`}
                        required
                      >
                        {unitOptions.map(unit => (
                          <option key={unit} value={unit}>{unit}</option>
                        ))}
                      </select>
                      {errors.unit && (
                        <p className="text-red-400 text-sm mt-1">{errors.unit}</p>
                      )}
                    </div>

                    <div className="md:col-span-2">
                      <label className="block text-sm font-medium text-gray-300 mb-1">
                        Order to Delivery Time *
                      </label>
                      <input
                        type="text"
                        name="order_to_delivery_time"
                        value={formData.order_to_delivery_time}
                        onChange={handleInputChange}
                        className={`misty-input w-full ${errors.order_to_delivery_time ? 'border-red-500' : ''}`}
                        placeholder="e.g., 5-7 business days"
                        required
                      />
                      {errors.order_to_delivery_time && (
                        <p className="text-red-400 text-sm mt-1">{errors.order_to_delivery_time}</p>
                      )}
                    </div>

                    <div className="md:col-span-2">
                      <label className="block text-sm font-medium text-gray-300 mb-1">
                        Material Description *
                      </label>
                      <textarea
                        name="material_description"
                        value={formData.material_description}
                        onChange={handleInputChange}
                        className={`misty-input w-full ${errors.material_description ? 'border-red-500' : ''}`}
                        placeholder="Enter detailed material description"
                        rows="3"
                        required
                      />
                      {errors.material_description && (
                        <p className="text-red-400 text-sm mt-1">{errors.material_description}</p>
                      )}
                    </div>
                  </div>
                </div>

                {/* Raw Substrate */}
                <div className="mb-6">
                  <label className="flex items-center space-x-2 cursor-pointer">
                    <input
                      type="checkbox"
                      name="raw_substrate"
                      checked={formData.raw_substrate}
                      onChange={handleInputChange}
                      className="form-checkbox h-4 w-4 text-yellow-400 bg-gray-700 border-gray-600 rounded focus:ring-yellow-400"
                    />
                    <span className="text-white font-medium">Raw Substrate</span>
                  </label>
                  <p className="text-sm text-gray-400 mt-1">
                    Check this if the material is a raw substrate with additional specifications
                  </p>
                </div>

                {/* Raw Substrate Specifications */}
                {formData.raw_substrate && (
                  <div className="mb-8">
                    <h3 className="text-lg font-semibold text-white mb-4">Raw Substrate Specifications</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-300 mb-1">
                          GSM *
                        </label>
                        <input
                          type="text"
                          name="gsm"
                          value={formData.gsm}
                          onChange={handleInputChange}
                          className={`misty-input w-full ${errors.gsm ? 'border-red-500' : ''}`}
                          placeholder="Enter GSM value"
                        />
                        {errors.gsm && (
                          <p className="text-red-400 text-sm mt-1">{errors.gsm}</p>
                        )}
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-300 mb-1">
                          Thickness (mm)
                        </label>
                        <input
                          type="number"
                          step="0.01"
                          min="0"
                          name="thickness_mm"
                          value={formData.thickness_mm}
                          onChange={handleInputChange}
                          className="misty-input w-full"
                          placeholder="0.00"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-300 mb-1">
                          Burst Strength (kPa)
                        </label>
                        <input
                          type="number"
                          step="0.01"
                          min="0"
                          name="burst_strength_kpa"
                          value={formData.burst_strength_kpa}
                          onChange={handleInputChange}
                          className="misty-input w-full"
                          placeholder="0.00"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-300 mb-1">
                          PlyBonding (j/m²)
                        </label>
                        <input
                          type="number"
                          step="0.01"
                          min="0"
                          name="ply_bonding_jm2"
                          value={formData.ply_bonding_jm2}
                          onChange={handleInputChange}
                          className="misty-input w-full"
                          placeholder="0.00"
                        />
                      </div>

                      <div className="md:col-span-2">
                        <label className="block text-sm font-medium text-gray-300 mb-1">
                          Moisture (%)
                        </label>
                        <input
                          type="number"
                          step="0.01"
                          min="0"
                          max="100"
                          name="moisture_percent"
                          value={formData.moisture_percent}
                          onChange={handleInputChange}
                          className="misty-input w-full"
                          placeholder="0.00"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-300 mb-1">
                          Supplied Roll Weight (kg)
                        </label>
                        <input
                          type="number"
                          step="0.01"
                          min="0"
                          name="supplied_roll_weight"
                          value={formData.supplied_roll_weight}
                          onChange={handleInputChange}
                          className="misty-input w-full"
                          placeholder="0.00"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-300 mb-1">
                          Master Deckle Width (mm)
                        </label>
                        <input
                          type="number"
                          step="0.01"
                          min="0"
                          name="master_deckle_width_mm"
                          value={formData.master_deckle_width_mm}
                          onChange={handleInputChange}
                          className="misty-input w-full"
                          placeholder="0.00"
                        />
                      </div>

                      {/* Linear Meters Calculation */}
                      {calculateLinearMeters() && (
                        <div className="md:col-span-2 mt-4 p-4 bg-gray-800 rounded-lg border border-gray-600">
                          <h4 className="text-md font-semibold text-white mb-2">Calculated Linear Meters</h4>
                          <div className="flex items-center justify-between">
                            <span className="text-gray-300">
                              Based on GSM ({formData.gsm}), Weight ({formData.supplied_roll_weight} kg), Width ({formData.master_deckle_width_mm} mm)
                            </span>
                            <span className="text-yellow-400 font-bold text-lg">
                              {calculateLinearMeters()} meters
                            </span>
                          </div>
                        </div>
                      )}
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
                    {selectedMaterial ? 'Update Material' : 'Create Material'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default MaterialsManagement;