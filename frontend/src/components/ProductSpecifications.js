import React, { useState, useEffect } from 'react';
import Layout from './Layout';
import { apiHelpers } from '../utils/api';
import { toast } from 'sonner';
import { 
  PlusIcon, 
  MagnifyingGlassIcon,
  XMarkIcon,
  TrashIcon,
  MinusIcon
} from '@heroicons/react/24/outline';

const ProductSpecifications = () => {
  const [specifications, setSpecifications] = useState([]);
  const [materials, setMaterials] = useState([]);  // New state for materials
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [selectedSpec, setSelectedSpec] = useState(null);
  const [formData, setFormData] = useState({
    product_name: '',
    product_type: '',
    specifications: {},
    materials_composition: [],
    manufacturing_notes: '',
    // Spiral Paper Core specific fields
    internal_diameter: '',
    wall_thickness_required: '',
    selected_material_id: '',
    layers_required: 0,
    layer_specifications: []
  });
  const [errors, setErrors] = useState({});

  useEffect(() => {
    loadSpecifications();
    loadMaterials();
  }, []);

  const loadMaterials = async () => {
    try {
      const response = await apiHelpers.getMaterials();
      setMaterials(response.data);
    } catch (error) {
      console.error('Failed to load materials:', error);
      toast.error('Failed to load materials');
    }
  };

  const loadSpecifications = async () => {
    try {
      setLoading(true);
      const response = await apiHelpers.getProductSpecifications();
      setSpecifications(response.data);
    } catch (error) {
      console.error('Failed to load product specifications:', error);
      toast.error('Failed to load product specifications');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setSelectedSpec(null);
    setFormData({
      product_name: '',
      product_type: 'Paper Core',
      specifications: {},  // Start with empty specifications
      materials_composition: [],
      manufacturing_notes: '',
      // Spiral Paper Core specific fields
      internal_diameter: '',
      wall_thickness_required: '',
      selected_material_id: '',
      layers_required: 0,
      layer_specifications: []
    });
    setErrors({});
    setShowModal(true);
  };

  const handleEdit = (spec) => {
    setSelectedSpec(spec);
    setFormData({
      product_name: spec.product_name,
      product_type: spec.product_type,
      specifications: spec.specifications || {},
      materials_composition: spec.materials_composition || [],
      manufacturing_notes: spec.manufacturing_notes || '',
      // Spiral Paper Core specific fields
      internal_diameter: spec.specifications?.internal_diameter || '',
      wall_thickness_required: spec.specifications?.wall_thickness_required || '',
      selected_material_id: spec.specifications?.selected_material_id || '',
      layers_required: spec.specifications?.layers_required || 0,
      layer_specifications: spec.specifications?.layer_specifications || []
    });
    setErrors({});
    setShowModal(true);
  };

  const handleDelete = async (spec) => {
    if (window.confirm(`Are you sure you want to delete the specification for "${spec.product_name}"?`)) {
      try {
        await apiHelpers.deleteProductSpecification(spec.id);
        toast.success('Product specification deleted successfully');
        setShowModal(false);
        loadSpecifications();
      } catch (error) {
        console.error('Failed to delete specification:', error);
        toast.error('Failed to delete specification');
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

  const handleSpecificationChange = (key, value) => {
    setFormData(prev => ({
      ...prev,
      specifications: {
        ...prev.specifications,
        [key]: value
      }
    }));
  };

  const removeSpecification = (key) => {
    setFormData(prev => {
      const newSpecs = { ...prev.specifications };
      delete newSpecs[key];
      return {
        ...prev,
        specifications: newSpecs
      };
    });
  };

  const addMaterialComposition = () => {
    setFormData(prev => ({
      ...prev,
      materials_composition: [
        ...prev.materials_composition,
        { material_name: '', percentage: '', gsm: '', thickness: '' }
      ]
    }));
  };

  const removeMaterialComposition = (index) => {
    setFormData(prev => ({
      ...prev,
      materials_composition: prev.materials_composition.filter((_, i) => i !== index)
    }));
  };

  const handleMaterialChange = (index, field, value) => {
    setFormData(prev => ({
      ...prev,
      materials_composition: prev.materials_composition.map((item, i) => 
        i === index ? { ...item, [field]: value } : item
      )
    }));
  };

  // Spiral Paper Core specific functions
  const calculateLayers = (materialId, requiredThickness) => {
    const material = materials.find(m => m.id === materialId);
    if (!material || !material.thickness_mm || !requiredThickness) return 0;
    
    return Math.ceil(parseFloat(requiredThickness) / parseFloat(material.thickness_mm));
  };

  const getLayerOptions = (materialId, requiredThickness) => {
    const material = materials.find(m => m.id === materialId);
    if (!material || !material.thickness_mm || !requiredThickness) return [];
    
    const materialThickness = parseFloat(material.thickness_mm);
    const required = parseFloat(requiredThickness);
    
    const exactLayers = required / materialThickness;
    const lowerLayers = Math.floor(exactLayers);
    const upperLayers = Math.ceil(exactLayers);
    
    const options = [];
    
    if (lowerLayers > 0) {
      options.push({
        layers: lowerLayers,
        totalThickness: (lowerLayers * materialThickness).toFixed(2),
        difference: Math.abs(required - (lowerLayers * materialThickness)).toFixed(2)
      });
    }
    
    if (upperLayers !== lowerLayers) {
      options.push({
        layers: upperLayers,
        totalThickness: (upperLayers * materialThickness).toFixed(2),
        difference: Math.abs(required - (upperLayers * materialThickness)).toFixed(2)
      });
    }
    
    return options;
  };

  const handleMaterialSelect = (materialId) => {
    const material = materials.find(m => m.id === materialId);
    if (!material) return;
    
    const layers = calculateLayers(materialId, formData.wall_thickness_required);
    
    setFormData(prev => ({
      ...prev,
      selected_material_id: materialId,
      layers_required: layers
    }));
  };

  const addLayerSpecification = () => {
    setFormData(prev => ({
      ...prev,
      layer_specifications: [
        ...prev.layer_specifications,
        { layer_type: 'Outer Most Layer', width: '', width_range: '' }
      ]
    }));
  };

  const removeLayerSpecification = (index) => {
    setFormData(prev => ({
      ...prev,
      layer_specifications: prev.layer_specifications.filter((_, i) => i !== index)
    }));
  };

  const handleLayerSpecChange = (index, field, value) => {
    setFormData(prev => ({
      ...prev,
      layer_specifications: prev.layer_specifications.map((item, i) => 
        i === index ? { ...item, [field]: value } : item
      )
    }));
  };

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.product_name.trim()) {
      newErrors.product_name = 'Product name is required';
    }
    
    if (!formData.product_type.trim()) {
      newErrors.product_type = 'Product type is required';
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
      let submitData = {
        product_name: formData.product_name,
        product_type: formData.product_type,
        specifications: { ...formData.specifications },
        materials_composition: formData.materials_composition,
        manufacturing_notes: formData.manufacturing_notes
      };

      // For Spiral Paper Cores, add specific fields to specifications
      if (formData.product_type === 'Spiral Paper Core') {
        submitData.specifications = {
          ...submitData.specifications,
          internal_diameter: formData.internal_diameter,
          wall_thickness_required: formData.wall_thickness_required,
          selected_material_id: formData.selected_material_id,
          layers_required: formData.layers_required,
          layer_specifications: formData.layer_specifications
        };
      }
      
      if (selectedSpec) {
        await apiHelpers.updateProductSpecification(selectedSpec.id, submitData);
        toast.success('Product specification updated successfully');
      } else {
        await apiHelpers.createProductSpecification(submitData);
        toast.success('Product specification created successfully');
      }
      
      setShowModal(false);
      loadSpecifications();
    } catch (error) {
      console.error('Failed to save specification:', error);
      const message = error.response?.data?.detail || 'Failed to save specification';
      toast.error(message);
    }
  };

  const filteredSpecifications = specifications.filter(spec =>
    spec.product_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    spec.product_type.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const productTypes = [
    'Paper Core',
    'Spiral Paper Core',
    'Cardboard Tube',
    'Composite Core',
    'Other'
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
            <h1 className="text-3xl font-bold text-white mb-2">Product Specifications</h1>
            <p className="text-gray-400">Manage manufacturing specifications for products • Double-click any specification to edit</p>
          </div>
          <button
            onClick={handleCreate}
            className="misty-button misty-button-primary"
          >
            <PlusIcon className="h-5 w-5 mr-2" />
            Add Specification
          </button>
        </div>

        {/* Search */}
        <div className="mb-6">
          <div className="relative max-w-md">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search specifications..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="misty-input pl-10 w-full"
            />
          </div>
        </div>

        {/* Specifications Table */}
        {filteredSpecifications.length > 0 ? (
          <div className="misty-table">
            <table className="w-full">
              <thead>
                <tr>
                  <th className="py-2 text-sm">Product Name</th>
                  <th className="py-2 text-sm">Type</th>
                  <th className="py-2 text-sm">Materials</th>
                  <th className="py-2 text-sm">Specifications</th>
                  <th className="py-2 text-sm">Notes</th>
                </tr>
              </thead>
              <tbody>
                {filteredSpecifications.map((spec) => (
                  <tr 
                    key={spec.id}
                    onDoubleClick={() => handleEdit(spec)}
                    className="cursor-pointer hover:bg-gray-700/50 transition-colors border-b border-gray-700/50"
                    title="Double-click to edit"
                  >
                    <td className="font-medium text-sm py-2 px-3">{spec.product_name}</td>
                    <td className="text-sm py-2 px-3">{spec.product_type}</td>
                    <td className="text-sm py-2 px-3">
                      {spec.materials_composition?.length > 0 
                        ? `${spec.materials_composition.length} materials`
                        : '—'
                      }
                    </td>
                    <td className="text-sm py-2 px-3">
                      {Object.keys(spec.specifications || {}).length > 0
                        ? `${Object.keys(spec.specifications).length} specs`
                        : '—'
                      }
                    </td>
                    <td className="text-gray-300 text-sm py-2 px-3 max-w-xs truncate">
                      {spec.manufacturing_notes || '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-12">
            <div className="mx-auto h-12 w-12 text-gray-400 mb-4">📋</div>
            <h3 className="text-sm font-medium text-gray-300">
              {searchTerm ? 'No specifications found' : 'No product specifications'}
            </h3>
            <p className="mt-1 text-sm text-gray-400">
              {searchTerm
                ? 'Try adjusting your search criteria.'
                : 'Get started by adding your first product specification.'
              }
            </p>
            {!searchTerm && (
              <div className="mt-6">
                <button
                  onClick={handleCreate}
                  className="misty-button misty-button-primary"
                >
                  <PlusIcon className="h-5 w-5 mr-2" />
                  Add Specification
                </button>
              </div>
            )}
          </div>
        )}

        {/* Specification Form Modal */}
        {showModal && (
          <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && setShowModal(false)}>
            <div className="modal-content max-w-6xl max-h-[90vh] overflow-y-auto">
              <div className="sticky top-0 bg-gray-900 z-10 p-6 pb-0 border-b border-gray-700">
                {/* Header */}
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-2xl font-bold text-white">
                    {selectedSpec ? 'Edit Product Specification' : 'Add New Product Specification'}
                  </h2>
                  <button
                    type="button"
                    onClick={() => setShowModal(false)}
                    className="text-gray-400 hover:text-white transition-colors"
                  >
                    <XMarkIcon className="h-6 w-6" />
                  </button>
                </div>
              </div>
              <form onSubmit={handleSubmit} className="px-6 pb-6">
                {/* Basic Information */}
                <div className="mb-8">
                  <h3 className="text-lg font-semibold text-white mb-4">Basic Information</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-1">
                        Product Name *
                      </label>
                      <input
                        type="text"
                        name="product_name"
                        value={formData.product_name}
                        onChange={handleInputChange}
                        className={`misty-input w-full ${errors.product_name ? 'border-red-500' : ''}`}
                        placeholder="Enter product name"
                        required
                      />
                      {errors.product_name && (
                        <p className="text-red-400 text-sm mt-1">{errors.product_name}</p>
                      )}
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-1">
                        Product Type *
                      </label>
                      <select
                        name="product_type"
                        value={formData.product_type}
                        onChange={handleInputChange}
                        className={`misty-select w-full ${errors.product_type ? 'border-red-500' : ''}`}
                        required
                      >
                        {productTypes.map(type => (
                          <option key={type} value={type}>{type}</option>
                        ))}
                      </select>
                      {errors.product_type && (
                        <p className="text-red-400 text-sm mt-1">{errors.product_type}</p>
                      )}
                    </div>

                    <div className="md:col-span-2">
                      <label className="block text-sm font-medium text-gray-300 mb-1">
                        Manufacturing Notes
                      </label>
                      <textarea
                        name="manufacturing_notes"
                        value={formData.manufacturing_notes}
                        onChange={handleInputChange}
                        className="misty-input w-full"
                        placeholder="Enter manufacturing notes and instructions"
                        rows="3"
                      />
                    </div>
                  </div>
                </div>

                {/* Specifications - Only show for non-Spiral Paper Core types */}
                {formData.product_type !== 'Spiral Paper Core' && (
                  <div className="mb-8">
                    <h3 className="text-lg font-semibold text-white mb-4">Product Specifications</h3>
                    <div className="space-y-4">
                      {Object.entries(formData.specifications).map(([key, value]) => (
                        <div key={key} className="flex items-center space-x-2">
                          <input
                            type="text"
                            value={key}
                            onChange={(e) => {
                              const newKey = e.target.value;
                              const newSpecs = { ...formData.specifications };
                              delete newSpecs[key];
                              newSpecs[newKey] = value;
                              setFormData(prev => ({ ...prev, specifications: newSpecs }));
                            }}
                            className="misty-input flex-1"
                            placeholder="Specification name (e.g., Core ID, Width)"
                          />
                          <input
                            type="text"
                            value={value}
                            onChange={(e) => handleSpecificationChange(key, e.target.value)}
                            className="misty-input flex-1"
                            placeholder="Specification value"
                          />
                          <button
                            type="button"
                            onClick={() => removeSpecification(key)}
                            className="text-red-400 hover:text-red-300 p-2"
                          >
                            <MinusIcon className="h-4 w-4" />
                          </button>
                        </div>
                      ))}
                      <button
                        type="button"
                        onClick={() => handleSpecificationChange(`spec_${Date.now()}`, '')}
                        className="text-yellow-400 hover:text-yellow-300 text-sm flex items-center"
                      >
                        <PlusIcon className="h-4 w-4 mr-1" />
                        Add Specification
                      </button>
                    </div>
                  </div>
                )}

                {/* Materials Composition - Conditional Based on Product Type */}
                {formData.product_type === 'Spiral Paper Core' ? (
                  <div className="mb-8">
                    <h3 className="text-lg font-semibold text-white mb-4">Spiral Paper Core Specifications</h3>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                      <div>
                        <label className="block text-sm font-medium text-gray-300 mb-1">
                          Product Internal Diameter (mm) *
                        </label>
                        <input
                          type="number"
                          step="0.1"
                          min="0"
                          value={formData.internal_diameter}
                          onChange={(e) => setFormData(prev => ({ 
                            ...prev, 
                            internal_diameter: e.target.value
                          }))}
                          className="misty-input w-full"
                          placeholder="Enter internal diameter"
                        />
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-300 mb-1">
                          Product Wall Thickness Required (mm) *
                        </label>
                        <input
                          type="number"
                          step="0.1"
                          min="0"
                          value={formData.wall_thickness_required}
                          onChange={(e) => {
                            setFormData(prev => ({ 
                              ...prev, 
                              wall_thickness_required: e.target.value
                            }));
                            // Recalculate layers if material is selected
                            if (formData.selected_material_id) {
                              const layers = calculateLayers(formData.selected_material_id, e.target.value);
                              setFormData(prev => ({ 
                                ...prev, 
                                layers_required: layers
                              }));
                            }
                          }}
                          className="misty-input w-full"
                          placeholder="Enter wall thickness"
                        />
                      </div>
                    </div>

                    <div className="mb-6">
                      <label className="block text-sm font-medium text-gray-300 mb-1">
                        Material Name *
                      </label>
                      <select
                        value={formData.selected_material_id}
                        onChange={(e) => handleMaterialSelect(e.target.value)}
                        className="misty-select w-full"
                      >
                        <option value="">Select a material</option>
                        {materials.filter(m => m.raw_substrate).map(material => (
                          <option key={material.id} value={material.id}>
                            {material.product_code} - {material.supplier} (GSM: {material.gsm}, Thickness: {material.thickness_mm}mm)
                          </option>
                        ))}
                      </select>
                    </div>

                    {formData.selected_material_id && formData.wall_thickness_required && (
                      <div className="mb-6 p-4 bg-gray-800 rounded-lg">
                        <h4 className="text-md font-medium text-white mb-3">Material Calculations</h4>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                          <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1">GSM (Generated)</label>
                            <input
                              type="text"
                              value={materials.find(m => m.id === formData.selected_material_id)?.gsm || ''}
                              className="misty-input w-full bg-gray-700"
                              disabled
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1">Thickness (mm) (Generated)</label>
                            <input
                              type="text"
                              value={materials.find(m => m.id === formData.selected_material_id)?.thickness_mm || ''}
                              className="misty-input w-full bg-gray-700"
                              disabled
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1">Layers Required (Calculated)</label>
                            <input
                              type="text"
                              value={formData.layers_required}
                              className="misty-input w-full bg-gray-700"
                              disabled
                            />
                          </div>
                        </div>

                        {/* Show layer options if thickness doesn't match exactly */}
                        {(() => {
                          const layerOptions = getLayerOptions(formData.selected_material_id, formData.wall_thickness_required);
                          if (layerOptions.length > 1) {
                            return (
                              <div className="mt-4">
                                <label className="block text-sm font-medium text-gray-300 mb-2">
                                  Thickness Options (exact match not possible):
                                </label>
                                <div className="space-y-2">
                                  {layerOptions.map((option, index) => (
                                    <div key={index} className="flex items-center justify-between bg-gray-700 p-2 rounded">
                                      <span className="text-gray-300">
                                        {option.layers} layers = {option.totalThickness}mm
                                      </span>
                                      <span className={`text-sm ${parseFloat(option.difference) < 0.1 ? 'text-green-400' : 'text-yellow-400'}`}>
                                        Difference: ±{option.difference}mm
                                      </span>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            );
                          }
                          return null;
                        })()}
                      </div>
                    )}

                    {/* Layer Specifications */}
                    <div className="mb-6">
                      <div className="flex items-center justify-between mb-4">
                        <h4 className="text-md font-medium text-white">Layer Specifications</h4>
                        <button
                          type="button"
                          onClick={addLayerSpecification}
                          className="text-yellow-400 hover:text-yellow-300 text-sm flex items-center"
                        >
                          <PlusIcon className="h-4 w-4 mr-1" />
                          Add Layer
                        </button>
                      </div>
                      
                      <div className="space-y-4">
                        {formData.layer_specifications.map((layer, index) => (
                          <div key={index} className="grid grid-cols-1 md:grid-cols-4 gap-4 p-4 bg-gray-800 rounded-lg">
                            <div>
                              <label className="block text-sm font-medium text-gray-300 mb-1">
                                Layer Type
                              </label>
                              <select
                                value={layer.layer_type}
                                onChange={(e) => handleLayerSpecChange(index, 'layer_type', e.target.value)}
                                className="misty-select w-full"
                              >
                                <option value="Outer Most Layer">Outer Most Layer</option>
                                <option value="Central Layer">Central Layer</option>
                                <option value="Inner Most Layer">Inner Most Layer</option>
                              </select>
                            </div>
                            
                            {layer.layer_type === 'Central Layer' ? (
                              <div>
                                <label className="block text-sm font-medium text-gray-300 mb-1">
                                  Width Range (mm)
                                </label>
                                <input
                                  type="text"
                                  value={layer.width_range}
                                  onChange={(e) => handleLayerSpecChange(index, 'width_range', e.target.value)}
                                  className="misty-input w-full"
                                  placeholder="e.g., 61-68"
                                />
                              </div>
                            ) : (
                              <div>
                                <label className="block text-sm font-medium text-gray-300 mb-1">
                                  Width (mm)
                                </label>
                                <input
                                  type="number"
                                  step="0.1"
                                  min="0"
                                  value={layer.width}
                                  onChange={(e) => handleLayerSpecChange(index, 'width', e.target.value)}
                                  className="misty-input w-full"
                                  placeholder="Width in mm"
                                />
                              </div>
                            )}
                            
                            <div className="flex items-end">
                              <button
                                type="button"
                                onClick={() => removeLayerSpecification(index)}
                                className="misty-button misty-button-danger w-full"
                              >
                                <MinusIcon className="h-4 w-4 mr-1" />
                                Remove
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                ) : (
                  // Original Materials Composition for other product types
                  <div className="mb-8">
                    <h3 className="text-lg font-semibold text-white mb-4">Materials Composition</h3>
                    <div className="space-y-4">
                      {formData.materials_composition.map((material, index) => (
                        <div key={index} className="grid grid-cols-1 md:grid-cols-4 gap-4 p-4 bg-gray-800 rounded-lg">
                          <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1">
                              Material Name
                            </label>
                            <input
                              type="text"
                              value={material.material_name}
                              onChange={(e) => handleMaterialChange(index, 'material_name', e.target.value)}
                              className="misty-input w-full"
                              placeholder="Material name"
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1">
                              Percentage (%)
                            </label>
                            <input
                              type="number"
                              step="0.1"
                              min="0"
                              max="100"
                              value={material.percentage}
                              onChange={(e) => handleMaterialChange(index, 'percentage', e.target.value)}
                              className="misty-input w-full"
                              placeholder="0.0"
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1">
                              GSM
                            </label>
                            <input
                              type="text"
                              value={material.gsm}
                              onChange={(e) => handleMaterialChange(index, 'gsm', e.target.value)}
                              className="misty-input w-full"
                              placeholder="GSM value"
                            />
                          </div>
                          <div className="flex items-end">
                            <button
                              type="button"
                              onClick={() => removeMaterialComposition(index)}
                              className="misty-button misty-button-danger w-full"
                            >
                              <MinusIcon className="h-4 w-4 mr-1" />
                              Remove
                            </button>
                          </div>
                        </div>
                      ))}
                      <button
                        type="button"
                        onClick={addMaterialComposition}
                        className="text-yellow-400 hover:text-yellow-300 text-sm flex items-center"
                      >
                        <PlusIcon className="h-4 w-4 mr-1" />
                        Add Material
                      </button>
                    </div>
                  </div>
                )}

                {/* Form Actions */}
                <div className="sticky bottom-0 bg-gray-900 flex justify-between pt-6 border-t border-gray-700 mt-8">
                  <div>
                    {selectedSpec && (
                      <button
                        type="button"
                        onClick={() => handleDelete(selectedSpec)}
                        className="misty-button misty-button-danger"
                      >
                        <TrashIcon className="h-4 w-4 mr-2" />
                        Delete Specification
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
                      {selectedSpec ? 'Update Specification' : 'Create Specification'}
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

export default ProductSpecifications;