import React, { useState, useEffect } from 'react';
import Layout from './Layout';
import { apiHelpers } from '../utils/api';
import { toast } from 'sonner';
import { 
  PlusIcon, 
  PencilIcon,
  MagnifyingGlassIcon,
  XMarkIcon,
  TrashIcon,
  MinusIcon
} from '@heroicons/react/24/outline';

const ProductSpecifications = () => {
  const [specifications, setSpecifications] = useState([]);
  const [materials, setMaterials] = useState([]);  // Materials from Products & Materials
  const [products, setProducts] = useState([]);   // Products from Products & Materials
  const [machineryRates, setMachineryRates] = useState([]);  // Default machinery rates
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [selectedSpec, setSelectedSpec] = useState(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [specToDelete, setSpecToDelete] = useState(null);
  const [formData, setFormData] = useState({
    product_name: '',
    product_type: '',
    specifications: {},
    materials_composition: [],
    material_layers: [],  // New enhanced material layers
    machinery: [],  // Machinery specifications for job card/run sheet
    manufacturing_notes: '',
    selected_thickness: null,  // User-selected thickness from calculated options
    // Spiral Paper Core specific fields
    internal_diameter: '',
    wall_thickness_required: '',
    selected_material_id: '',
    layers_required: 0,
    layer_specifications: [],
    // Pallet specific fields
    pallet_dimensions: {
      length: '',
      width: '', 
      height: ''
    },
    pallet_price: '',
    pallet_currency: 'AUD',
    pallet_supplier: '',
    // Cardboard Boxes specific fields
    box_dimensions: {
      length: '',
      width: '',
      height: ''
    },
    box_wall_thickness: '',
    box_flute_type: '',
    box_supplier: '',
    box_price: '',
    box_currency: 'AUD'
  });
  const [errors, setErrors] = useState({});
  const [calculatedThickness, setCalculatedThickness] = useState(0);
  const [thicknessOptions, setThicknessOptions] = useState([]);

  useEffect(() => {
    loadSpecifications();
    loadMaterials();
    loadProducts();
    loadMachineryRates();
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

  const loadProducts = async () => {
    try {
      const response = await apiHelpers.getProducts();
      setProducts(response.data);
    } catch (error) {
      console.error('Failed to load products:', error);
      toast.error('Failed to load products');
    }
  };

  const loadMachineryRates = async () => {
    try {
      const response = await apiHelpers.getMachineryRates();
      setMachineryRates(response.data);
    } catch (error) {
      console.error('Failed to load machinery rates:', error);
      // Don't show error toast for machinery rates as they're optional
    }
  };

  // Helper function to convert time format (HH:MM) to decimal hours
  const convertTimeToHours = (timeString) => {
    if (!timeString) return null;
    try {
      const [hours, minutes] = timeString.split(':').map(Number);
      return hours + (minutes / 60);
    } catch {
      return null;
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
      product_type: 'Spiral Paper Core',
      specifications: {},  // Start with empty specifications
      materials_composition: [],
      material_layers: [],  // New enhanced material layers
      machinery: [],  // Machinery specifications
      manufacturing_notes: '',
      selected_thickness: null,
      // Spiral Paper Core specific fields
      internal_diameter: '',
      wall_thickness_required: '',
      selected_material_id: '',
      layers_required: 0,
      layer_specifications: [],
      // Pallet specific fields
      pallet_dimensions: {
        length: '',
        width: '', 
        height: ''
      },
      pallet_price: '',
      pallet_currency: 'AUD',
      pallet_supplier: '',
      // Cardboard Boxes specific fields
      box_dimensions: {
        length: '',
        width: '',
        height: ''
      },
      box_wall_thickness: '',
      box_flute_type: '',
      box_supplier: '',
      box_price: '',
      box_currency: 'AUD'
    });
    setCalculatedThickness(0);
    setThicknessOptions([]);
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
      material_layers: spec.material_layers || [],  // Load enhanced material layers
      machinery: (spec.machinery || []).map(machine => ({
        ...machine,
        // Map old field names to new field names for backward compatibility
        setup_hours: machine.setup_hours || (machine.setup_time ? convertTimeToHours(machine.setup_time) : null),
        pack_up_hours: machine.pack_up_hours || (machine.pack_up_time ? convertTimeToHours(machine.pack_up_time) : null)
      })),  // Load machinery specifications
      manufacturing_notes: spec.manufacturing_notes || '',
      selected_thickness: spec.selected_thickness || null,
      // Spiral Paper Core specific fields
      internal_diameter: spec.specifications?.internal_diameter || '',
      wall_thickness_required: spec.specifications?.wall_thickness_required || '',
      selected_material_id: spec.specifications?.selected_material_id || '',
      layers_required: spec.specifications?.layers_required || 0,
      layer_specifications: spec.specifications?.layer_specifications || [],
      // Pallet specific fields
      pallet_dimensions: {
        length: spec.specifications?.dimensions?.length || '',
        width: spec.specifications?.dimensions?.width || '',
        height: spec.specifications?.dimensions?.height || ''
      },
      pallet_price: spec.specifications?.price || '',
      pallet_currency: spec.specifications?.currency || 'AUD',
      pallet_supplier: spec.specifications?.supplier || '',
      // Cardboard Boxes specific fields
      box_dimensions: {
        length: spec.specifications?.dimensions?.length || '',
        width: spec.specifications?.dimensions?.width || '',
        height: spec.specifications?.dimensions?.height || ''
      },
      box_wall_thickness: spec.specifications?.wall_thickness || '',
      box_flute_type: spec.specifications?.flute_type || '',
      box_supplier: spec.specifications?.supplier || '',
      box_price: spec.specifications?.price || '',
      box_currency: spec.specifications?.currency || 'AUD'
    });
    setCalculatedThickness(spec.calculated_total_thickness || 0);
    setThicknessOptions(spec.thickness_options || []);
    setErrors({});
    setShowModal(true);
  };

  const handleDelete = (spec) => {
    setSpecToDelete(spec);
    setShowDeleteConfirm(true);
  };

  const confirmDelete = async () => {
    if (!specToDelete) return;
    
    try {
      await apiHelpers.deleteProductSpecification(specToDelete.id);
      toast.success('Product specification deleted successfully');
      setShowModal(false);
      setShowDeleteConfirm(false);
      setSpecToDelete(null);
      loadSpecifications();
    } catch (error) {
      console.error('Failed to delete specification:', error);
      toast.error('Failed to delete specification');
      setShowDeleteConfirm(false);
      setSpecToDelete(null);
    }
  };

  const cancelDelete = () => {
    setShowDeleteConfirm(false);
    setSpecToDelete(null);
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

  // New functions for enhanced material layers
  const addMaterialLayer = () => {
    setFormData(prev => ({
      ...prev,
      material_layers: [
        ...prev.material_layers,
        {
          material_id: '',
          material_name: '',
          layer_type: 'Outer Most Layer',
          width: null,
          width_range: null,
          thickness: null,  // Don't default to 0 to avoid false calculations
          gsm: null,  // Don't default to 0 to avoid false calculations
          quantity: 1,  // Default quantity to 1
          notes: ''
        }
      ]
    }));
  };

  const removeMaterialLayer = (index) => {
    setFormData(prev => ({
      ...prev,
      material_layers: prev.material_layers.filter((_, i) => i !== index)
    }));
    // Recalculate thickness after removing a layer
    calculateTotalThickness();
  };

  const handleMaterialLayerChange = (index, field, value) => {
    setFormData(prev => {
      const updatedLayers = prev.material_layers.map((layer, i) => {
        if (i === index) {
          const updatedLayer = { ...layer, [field]: value };
          
          // If material_id changes, update material_name, thickness, and GSM
          if (field === 'material_id') {
            // Check both materials and products for the item
            const allItems = [...materials, ...products];
            const item = allItems.find(m => m.id === value);
            if (item) {
              updatedLayer.material_name = item.material_name || item.product_name;
              // Use thickness_mm as the actual thickness value
              updatedLayer.thickness = item.thickness_mm || 0;
              // Add GSM information if available
              updatedLayer.gsm = item.gsm || 0;
            }
          }
          
          return updatedLayer;
        }
        return layer;
      });
      
      return { ...prev, material_layers: updatedLayers };
    });
    
    // Recalculate thickness after any change
    setTimeout(() => calculateTotalThickness(), 100);
  };

  const calculateTotalThickness = () => {
    const total = formData.material_layers.reduce((sum, layer) => {
      const thickness = parseFloat(layer.thickness) || 0;
      const quantity = parseFloat(layer.quantity) || 1;
      return sum + (thickness * quantity);
    }, 0);
    
    setCalculatedThickness(total);
    
    // Auto-set the selected thickness to the calculated value
    setFormData(prev => ({
      ...prev,
      selected_thickness: Math.round(total * 1000) / 1000
    }));
  };

  // Machinery functions
  const addMachinery = () => {
    setFormData(prev => ({
      ...prev,
      machinery: [
        ...prev.machinery,
        {
          machine_name: '',
          running_speed: null,
          setup_hours: null,
          pack_up_hours: null,
          functions: []
        }
      ]
    }));
  };

  const removeMachinery = (index) => {
    setFormData(prev => ({
      ...prev,
      machinery: prev.machinery.filter((_, i) => i !== index)
    }));
  };

  const handleMachineryChange = (index, field, value) => {
    setFormData(prev => ({
      ...prev,
      machinery: prev.machinery.map((machine, i) => 
        i === index ? { ...machine, [field]: value } : machine
      )
    }));
  };

  const addMachineryFunction = (machineIndex) => {
    // Get default rate for Slitting function
    const defaultRate = machineryRates.find(rate => rate.function === 'Slitting');
    const defaultRateValue = defaultRate ? defaultRate.rate_per_hour : null;
    
    setFormData(prev => ({
      ...prev,
      machinery: prev.machinery.map((machine, i) => 
        i === machineIndex ? {
          ...machine,
          functions: [
            ...machine.functions,
            { function: 'Slitting', rate_per_hour: defaultRateValue }
          ]
        } : machine
      )
    }));
  };

  const removeMachineryFunction = (machineIndex, functionIndex) => {
    setFormData(prev => ({
      ...prev,
      machinery: prev.machinery.map((machine, i) => 
        i === machineIndex ? {
          ...machine,
          functions: machine.functions.filter((_, j) => j !== functionIndex)
        } : machine
      )
    }));
  };

  const handleMachineryFunctionChange = (machineIndex, functionIndex, field, value) => {
    setFormData(prev => ({
      ...prev,
      machinery: prev.machinery.map((machine, i) => 
        i === machineIndex ? {
          ...machine,
          functions: machine.functions.map((func, j) => {
            if (j === functionIndex) {
              const updatedFunc = { ...func, [field]: value };
              
              // If function type is changing, apply default rate
              if (field === 'function') {
                const defaultRate = machineryRates.find(rate => rate.function === value);
                if (defaultRate) {
                  updatedFunc.rate_per_hour = defaultRate.rate_per_hour;
                }
              }
              
              return updatedFunc;
            }
            return func;
          })
        } : machine
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

    // Validate Pallet specific fields
    if (formData.product_type === 'Pallet') {
      if (!formData.pallet_dimensions.length || formData.pallet_dimensions.length <= 0) {
        newErrors.pallet_length = 'Pallet length is required';
      }
      if (!formData.pallet_dimensions.width || formData.pallet_dimensions.width <= 0) {
        newErrors.pallet_width = 'Pallet width is required';
      }
      if (!formData.pallet_dimensions.height || formData.pallet_dimensions.height <= 0) {
        newErrors.pallet_height = 'Pallet height is required';
      }
      if (!formData.pallet_price || formData.pallet_price <= 0) {
        newErrors.pallet_price = 'Pallet price is required';
      }
      if (!formData.pallet_supplier.trim()) {
        newErrors.pallet_supplier = 'Pallet supplier is required';
      }
    }

    // Validate Cardboard Boxes specific fields
    if (formData.product_type === 'Cardboard Boxes') {
      if (!formData.box_dimensions.length || formData.box_dimensions.length <= 0) {
        newErrors.box_length = 'Box length is required';
      }
      if (!formData.box_dimensions.width || formData.box_dimensions.width <= 0) {
        newErrors.box_width = 'Box width is required';
      }
      if (!formData.box_dimensions.height || formData.box_dimensions.height <= 0) {
        newErrors.box_height = 'Box height is required';
      }
      if (!formData.box_wall_thickness || formData.box_wall_thickness <= 0) {
        newErrors.box_wall_thickness = 'Wall thickness is required';
      }
      if (!formData.box_flute_type.trim()) {
        newErrors.box_flute_type = 'Flute type is required';
      }
      if (!formData.box_supplier.trim()) {
        newErrors.box_supplier = 'Supplier is required';
      }
      if (!formData.box_price || formData.box_price <= 0) {
        newErrors.box_price = 'Price per unit is required';
      }
    }
    
    // Validate material layers - each layer must have required fields
    formData.material_layers.forEach((layer, index) => {
      const layerErrors = [];
      
      if (!layer.material_id || !layer.material_id.trim()) {
        layerErrors.push('Material selection');
      }
      
      if (!layer.layer_type || !layer.layer_type.trim()) {
        layerErrors.push('Layer type');
      }
      
      if (!layer.thickness || layer.thickness <= 0) {
        layerErrors.push('Thickness');
      }
      
      if (layerErrors.length > 0) {
        newErrors[`material_layer_${index}`] = `Layer ${index + 1}: ${layerErrors.join(', ')} required`;
      }
    });

    // Validate machinery - each machine must have a machine type selected
    formData.machinery.forEach((machine, index) => {
      if (!machine.machine_name || !machine.machine_name.trim()) {
        newErrors[`machinery_${index}`] = `Machine ${index + 1}: Machine type is required`;
      }
    });
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      const errorCount = Object.keys(errors).length;
      toast.error(`Please fix the ${errorCount} validation error${errorCount > 1 ? 's' : ''} below`);
      return;
    }
    
    try {
      // Clean up material layers - ensure they have valid material_id
      const cleanMaterialLayers = formData.material_layers.map(layer => ({
        material_id: layer.material_id || 'unknown',
        material_name: layer.material_name || 'Unknown Material',
        layer_type: layer.layer_type || 'Outer Most Layer',
        thickness: parseFloat(layer.thickness) || 0,
        quantity: parseFloat(layer.quantity) || 1,
        width: layer.width ? parseFloat(layer.width) : null,
        notes: layer.notes || ''
      }));

      let submitData = {
        product_name: formData.product_name,
        product_type: formData.product_type,
        specifications: formData.specifications || {},
        materials_composition: [],  // Keep empty for now
        material_layers: cleanMaterialLayers,
        machinery: formData.machinery || [],  // Include machinery data
        manufacturing_notes: formData.manufacturing_notes || '',
        selected_thickness: formData.selected_thickness || calculatedThickness
      };

      // For Spiral Paper Cores, add specific fields to specifications
      if (formData.product_type === 'Spiral Paper Core') {
        submitData.specifications = {
          ...submitData.specifications,
          internal_diameter: formData.internal_diameter ? parseFloat(formData.internal_diameter) : null,
          wall_thickness_required: formData.wall_thickness_required ? parseFloat(formData.wall_thickness_required) : null,
          selected_material_id: formData.selected_material_id || null,
          layers_required: formData.layers_required || null,
          layer_specifications: formData.layer_specifications || null
        };
      }

      // For Pallets, add specific fields to specifications
      if (formData.product_type === 'Pallet') {
        submitData.specifications = {
          ...submitData.specifications,
          dimensions: {
            length: formData.pallet_dimensions.length ? parseFloat(formData.pallet_dimensions.length) : null,
            width: formData.pallet_dimensions.width ? parseFloat(formData.pallet_dimensions.width) : null,
            height: formData.pallet_dimensions.height ? parseFloat(formData.pallet_dimensions.height) : null
          },
          price: formData.pallet_price ? parseFloat(formData.pallet_price) : null,
          supplier: formData.pallet_supplier || null
        };
      }

      // For Cardboard Boxes, add specific fields to specifications  
      if (formData.product_type === 'Cardboard Boxes') {
        submitData.specifications = {
          ...submitData.specifications,
          dimensions: {
            length: formData.box_dimensions.length ? parseFloat(formData.box_dimensions.length) : null,
            width: formData.box_dimensions.width ? parseFloat(formData.box_dimensions.width) : null,
            height: formData.box_dimensions.height ? parseFloat(formData.box_dimensions.height) : null
          },
          wall_thickness: formData.box_wall_thickness ? parseFloat(formData.box_wall_thickness) : null,
          flute_type: formData.box_flute_type || null,
          supplier: formData.box_supplier || null
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
      
      let message = 'Failed to save specification';
      if (error.response?.data?.detail) {
        // Handle FastAPI validation errors (422 status)
        if (Array.isArray(error.response.data.detail)) {
          // Extract messages from validation error objects
          message = error.response.data.detail
            .map(err => err.msg || err.message || 'Validation error')
            .join(', ');
        } else if (typeof error.response.data.detail === 'string') {
          // Handle simple string error messages
          message = error.response.data.detail;
        }
      }
      
      toast.error(message);
    }
  };

  const filteredSpecifications = specifications.filter(spec =>
    spec.product_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    spec.product_type.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const productTypes = [
    'Spiral Paper Core',
    'Composite Core',
    'Pallet',
    'Cardboard Boxes',
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
            <MagnifyingGlassIcon className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search specifications..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="misty-input pl-12 w-full"
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
                  <th className="py-2 text-sm">Actions</th>
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
                    <td className="py-2 px-3">
                      <div className="flex items-center justify-center space-x-2">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleEdit(spec);
                          }}
                          className="text-blue-400 hover:text-blue-300 transition-colors"
                          title="Edit specification"
                        >
                          <PencilIcon className="h-4 w-4" />
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDelete(spec);
                          }}
                          className="text-red-400 hover:text-red-300 transition-colors"
                          title="Delete specification"
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

                {/* Specifications - Only show for non-Spiral Paper Core, non-Cardboard Boxes, and non-Pallet types */}
                {formData.product_type !== 'Spiral Paper Core' && formData.product_type !== 'Cardboard Boxes' && formData.product_type !== 'Pallet' && (
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

                {/* Spiral Paper Core Specifications - Moved here after Basic Information */}
                {formData.product_type === 'Spiral Paper Core' && (
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
                          Wall Thickness Required (mm) *
                        </label>
                        <input
                          type="number"
                          step="0.1"
                          min="0"
                          value={formData.wall_thickness_required}
                          onChange={(e) => setFormData(prev => ({ 
                            ...prev, 
                            wall_thickness_required: e.target.value
                          }))}
                          className="misty-input w-full"
                          placeholder="Enter wall thickness"
                        />
                      </div>
                    </div>
                  </div>
                )}

                {/* Enhanced Material Layers Section - Only show for non-Cardboard Boxes and non-Pallet types */}
                {formData.product_type !== 'Cardboard Boxes' && formData.product_type !== 'Pallet' && (
                <div className="mb-8">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-white">Material Layers</h3>
                    <button
                      type="button"
                      onClick={addMaterialLayer}
                      className="misty-button misty-button-secondary flex items-center text-sm"
                    >
                      <PlusIcon className="h-4 w-4 mr-2" />
                      Add Material Layer
                    </button>
                  </div>
                  
                  <div className="space-y-4">
                    {formData.material_layers.map((layer, index) => (
                      <div key={index} className="p-4 bg-gray-800 rounded-lg">
                        <div className="flex items-center justify-between mb-4">
                          <h4 className="text-md font-medium text-white">Layer {index + 1}</h4>
                          {formData.material_layers.length > 1 && (
                            <button
                              type="button"
                              onClick={() => removeMaterialLayer(index)}
                              className="text-red-400 hover:text-red-300"
                            >
                              <TrashIcon className="h-4 w-4" />
                            </button>
                          )}
                        </div>
                        
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
                          {/* Material/Product Selection */}
                          <div className="md:col-span-2">
                            <label className="block text-sm font-medium text-gray-300 mb-1">
                              Material/Product *
                            </label>
                            <select
                              value={layer.material_id}
                              onChange={(e) => handleMaterialLayerChange(index, 'material_id', e.target.value)}
                              className="misty-select w-full"
                            >
                              <option value="">Select Material/Product</option>
                              {materials.length > 0 && (
                                <optgroup label="Materials">
                                  {materials.map(material => (
                                    <option key={material.id} value={material.id}>
                                      {material.material_name} ({material.thickness_mm || 0}mm thick)
                                    </option>
                                  ))}
                                </optgroup>
                              )}
                              {products.length > 0 && (
                                <optgroup label="Products">
                                  {products.map(product => (
                                    <option key={product.id} value={product.id}>
                                      {product.product_name} ({product.thickness_mm || 0}mm thick)
                                    </option>
                                  ))}
                                </optgroup>
                              )}
                            </select>
                          </div>

                          {/* Layer Type Selection */}
                          <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1">
                              Layer Position *
                            </label>
                            <select
                              value={layer.layer_type}
                              onChange={(e) => handleMaterialLayerChange(index, 'layer_type', e.target.value)}
                              className="misty-select w-full"
                            >
                              <option value="Outer Most Layer">Outer Most Layer</option>
                              <option value="Central Layer">Central Layer</option>
                              <option value="Inner Most Layer">Inner Most Layer</option>
                            </select>
                          </div>

                          {/* Quantity/Usage */}
                          <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1">
                              Quantity/Usage *
                            </label>
                            <input
                              type="number"
                              step="0.01"
                              min="0.01"
                              value={layer.quantity || 1}
                              onChange={(e) => handleMaterialLayerChange(index, 'quantity', e.target.value)}
                              className="misty-input w-full"
                              placeholder="1"
                            />
                          </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                          {/* Auto-populated Thickness (Read-only) */}
                          <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1">
                              Thickness (mm)
                            </label>
                            <input
                              type="number"
                              step="0.001"
                              value={layer.thickness || 0}
                              className="misty-input w-full bg-gray-600"
                              placeholder="Auto-populated"
                              readOnly
                            />
                          </div>

                          {/* Auto-populated GSM (Read-only) */}
                          <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1">
                              GSM
                            </label>
                            <input
                              type="number"
                              value={layer.gsm || 0}
                              className="misty-input w-full bg-gray-600"
                              placeholder="Auto-populated"
                              readOnly
                            />
                          </div>

                          {/* Width Configuration */}
                          {layer.layer_type === 'Central Layer' ? (
                            <div>
                              <label className="block text-sm font-medium text-gray-300 mb-1">
                                Width Range (mm)
                              </label>
                              <input
                                type="text"
                                value={layer.width_range || ''}
                                onChange={(e) => handleMaterialLayerChange(index, 'width_range', e.target.value)}
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
                                value={layer.width || ''}
                                onChange={(e) => handleMaterialLayerChange(index, 'width', e.target.value)}
                                className="misty-input w-full"
                                placeholder="Width in mm"
                              />
                            </div>
                          )}

                          {/* Notes */}
                          <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1">
                              Notes
                            </label>
                            <input
                              type="text"
                              value={layer.notes || ''}
                              onChange={(e) => handleMaterialLayerChange(index, 'notes', e.target.value)}
                              className="misty-input w-full"
                              placeholder="Optional notes"
                            />
                          </div>
                        </div>
                        
                        {/* Material Layer Error Display */}
                        {errors[`material_layer_${index}`] && (
                          <div className="mt-2 text-red-400 text-sm">
                            {errors[`material_layer_${index}`]}
                          </div>
                        )}
                      </div>
                    ))}
                    
                    {formData.material_layers.length === 0 && (
                      <div className="text-center py-8 text-gray-400">
                        <p>No material layers added yet.</p>
                        <p className="text-sm">Click "Add Material Layer" to get started.</p>
                      </div>
                    )}
                  </div>
                </div>
                )}

                {/* Machinery Section - Only show for non-Cardboard Boxes and non-Pallet types */}
                {formData.product_type !== 'Cardboard Boxes' && formData.product_type !== 'Pallet' && (
                <div className="mb-8">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-white">Machinery</h3>
                    <button
                      type="button"
                      onClick={addMachinery}
                      className="misty-button misty-button-secondary flex items-center text-sm"
                    >
                      <PlusIcon className="h-4 w-4 mr-2" />
                      Enter Machine
                    </button>
                  </div>
                  
                  <div className="space-y-6">
                    {formData.machinery.map((machine, machineIndex) => (
                      <div key={machineIndex} className="p-6 bg-gray-800 rounded-lg">
                        <div className="flex items-center justify-between mb-4">
                          <h4 className="text-md font-medium text-white">Machine {machineIndex + 1}</h4>
                          <button
                            type="button"
                            onClick={() => removeMachinery(machineIndex)}
                            className="text-red-400 hover:text-red-300"
                          >
                            <TrashIcon className="h-4 w-4" />
                          </button>
                        </div>
                        
                        {/* Machine Basic Info */}
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                          <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1">
                              Machine Type *
                            </label>
                            <select
                              value={machine.machine_name || ''}
                              onChange={(e) => handleMachineryChange(machineIndex, 'machine_name', e.target.value)}
                              className="misty-select w-full"
                              required
                            >
                              <option value="">Select Machine Type</option>
                              {machineryRates.map((rate, index) => (
                                <option key={index} value={rate.function}>
                                  {rate.function} - ${rate.rate_per_hour?.toFixed(2)}/hr
                                </option>
                              ))}
                            </select>
                          </div>

                          <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1">
                              Running Speed (Meters Per Minute)
                            </label>
                            <input
                              type="number"
                              step="0.1"
                              min="0"
                              value={machine.running_speed || ''}
                              onChange={(e) => handleMachineryChange(machineIndex, 'running_speed', e.target.value ? parseFloat(e.target.value) : null)}
                              className="misty-input w-full"
                              placeholder="0.0"
                            />
                          </div>

                          <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1">
                              Set up Time (Hours)
                            </label>
                            <input
                              type="number"
                              step="0.25"
                              min="0"
                              max="24"
                              value={machine.setup_hours || ''}
                              onChange={(e) => handleMachineryChange(machineIndex, 'setup_hours', e.target.value ? parseFloat(e.target.value) : null)}
                              className="misty-input w-full"
                              placeholder="1.5"
                            />
                          </div>

                          <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1">
                              Pack up Time (Hours)
                            </label>
                            <input
                              type="number"
                              step="0.25"
                              min="0"
                              max="24"
                              value={machine.pack_up_hours || ''}
                              onChange={(e) => handleMachineryChange(machineIndex, 'pack_up_hours', e.target.value ? parseFloat(e.target.value) : null)}
                              className="misty-input w-full"
                              placeholder="1.0"
                            />
                          </div>
                        </div>

                        {/* Functions Section */}
                        <div className="border-t border-gray-700 pt-4">
                          <div className="flex items-center justify-between mb-4">
                            <h5 className="text-sm font-medium text-white">Functions & Rates</h5>
                            <button
                              type="button"
                              onClick={() => addMachineryFunction(machineIndex)}
                              className="misty-button misty-button-secondary text-xs flex items-center"
                            >
                              <PlusIcon className="h-3 w-3 mr-1" />
                              Add Function
                            </button>
                          </div>

                          <div className="space-y-3">
                            {machine.functions.map((func, functionIndex) => (
                              <div key={functionIndex} className="grid grid-cols-1 md:grid-cols-3 gap-4 p-3 bg-gray-700 rounded">
                                <div>
                                  <label className="block text-xs font-medium text-gray-300 mb-1">
                                    Function
                                  </label>
                                  <select
                                    value={func.function}
                                    onChange={(e) => handleMachineryFunctionChange(machineIndex, functionIndex, 'function', e.target.value)}
                                    className="misty-select w-full text-sm"
                                  >
                                    <option value="Slitting">Slitting</option>
                                    <option value="winding">Winding</option>
                                    <option value="Cutting/Indexing">Cutting/Indexing</option>
                                    <option value="splitting">Splitting</option>
                                    <option value="Packing">Packing</option>
                                    <option value="Delivery Time">Delivery Time</option>
                                  </select>
                                </div>

                                <div>
                                  <label className="block text-xs font-medium text-gray-300 mb-1">
                                    Rate per Hour ($)
                                    {machineryRates.find(rate => rate.function === func.function) && (
                                      <button
                                        type="button"
                                        onClick={() => {
                                          const defaultRate = machineryRates.find(rate => rate.function === func.function);
                                          if (defaultRate) {
                                            handleMachineryFunctionChange(machineIndex, functionIndex, 'rate_per_hour', defaultRate.rate_per_hour);
                                          }
                                        }}
                                        className="ml-2 text-xs text-blue-400 hover:text-blue-300"
                                        title={`Apply default rate: $${machineryRates.find(rate => rate.function === func.function)?.rate_per_hour?.toFixed(2)}`}
                                      >
                                        (Use Default: ${machineryRates.find(rate => rate.function === func.function)?.rate_per_hour?.toFixed(2)})
                                      </button>
                                    )}
                                  </label>
                                  <input
                                    type="number"
                                    step="0.01"
                                    min="0"
                                    value={func.rate_per_hour || ''}
                                    onChange={(e) => handleMachineryFunctionChange(machineIndex, functionIndex, 'rate_per_hour', e.target.value ? parseFloat(e.target.value) : null)}
                                    className="misty-input w-full text-sm"
                                    placeholder="0.00"
                                  />
                                </div>

                                <div className="flex items-end">
                                  <button
                                    type="button"
                                    onClick={() => removeMachineryFunction(machineIndex, functionIndex)}
                                    className="text-red-400 hover:text-red-300 p-2"
                                  >
                                    <MinusIcon className="h-4 w-4" />
                                  </button>
                                </div>
                              </div>
                            ))}
                            
                            {machine.functions.length === 0 && (
                              <div className="text-center py-4 text-gray-400 text-sm">
                                <p>No functions added yet.</p>
                                <p className="text-xs">Click "Add Function" to add machine functions and rates.</p>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                    
                    {formData.machinery.length === 0 && (
                      <div className="text-center py-8 text-gray-400">
                        <p>No machinery added yet.</p>
                        <p className="text-sm">Click "Enter Machine" to add machinery specifications for the job card/run sheet.</p>
                      </div>
                    )}
                  </div>
                </div>
                )}

                {/* Calculated Thickness Display and Selection */}
                {calculatedThickness > 0 && (
                  <div className="mb-8">
                    <h3 className="text-lg font-semibold text-white mb-4">Total Thickness</h3>
                    
                    <div className="misty-card p-4 bg-gray-700">
                      <div className="text-center">
                        <h4 className="text-md font-medium text-white mb-2">Calculated Thickness</h4>
                        <div className="text-3xl font-bold text-yellow-400">
                          {calculatedThickness.toFixed(3)} mm
                        </div>
                        <p className="text-sm text-gray-400 mt-1">
                          Sum of all material layer thicknesses
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Pallet Specifications */}
                {formData.product_type === 'Pallet' && (
                  <div className="mb-8">
                    <h3 className="text-lg font-semibold text-white mb-4">Pallet Specifications</h3>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      {/* Dimensions */}
                      <div className="misty-card p-6">
                        <h4 className="text-md font-medium text-white mb-4">Dimensions</h4>
                        <div className="grid grid-cols-3 gap-4">
                          <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1">
                              Length (mm) *
                            </label>
                            <input
                              type="number"
                              step="0.1"
                              min="0"
                              value={formData.pallet_dimensions.length}
                              onChange={(e) => setFormData(prev => ({
                                ...prev,
                                pallet_dimensions: {
                                  ...prev.pallet_dimensions,
                                  length: e.target.value
                                }
                              }))}
                              className="misty-input w-full"
                              placeholder="1200"
                              required
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1">
                              Width (mm) *
                            </label>
                            <input
                              type="number"
                              step="0.1"
                              min="0"
                              value={formData.pallet_dimensions.width}
                              onChange={(e) => setFormData(prev => ({
                                ...prev,
                                pallet_dimensions: {
                                  ...prev.pallet_dimensions,
                                  width: e.target.value
                                }
                              }))}
                              className="misty-input w-full"
                              placeholder="800"
                              required
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1">
                              Height (mm) *
                            </label>
                            <input
                              type="number"
                              step="0.1"
                              min="0"
                              value={formData.pallet_dimensions.height}
                              onChange={(e) => setFormData(prev => ({
                                ...prev,
                                pallet_dimensions: {
                                  ...prev.pallet_dimensions,
                                  height: e.target.value
                                }
                              }))}
                              className="misty-input w-full"
                              placeholder="150"
                              required
                            />
                          </div>
                        </div>
                      </div>
                      
                      {/* Price and Supplier */}
                      <div className="misty-card p-6">
                        <h4 className="text-md font-medium text-white mb-4">Commercial Details</h4>
                        <div className="space-y-4">
                          <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1">
                              Price per Unit ($) *
                            </label>
                            <input
                              type="number"
                              step="0.01"
                              min="0"
                              value={formData.pallet_price}
                              onChange={(e) => setFormData(prev => ({ ...prev, pallet_price: e.target.value }))}
                              className="misty-input w-full"
                              placeholder="25.00"
                              required
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1">
                              Supplier *
                            </label>
                            <input
                              type="text"
                              value={formData.pallet_supplier}
                              onChange={(e) => setFormData(prev => ({ ...prev, pallet_supplier: e.target.value }))}
                              className="misty-input w-full"
                              placeholder="Supplier Name"
                              required
                            />
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Cardboard Boxes Specifications */}
                {formData.product_type === 'Cardboard Boxes' && (
                  <div className="mb-8">
                    <h3 className="text-lg font-semibold text-white mb-4">Cardboard Boxes Specifications</h3>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      {/* Dimensions */}
                      <div className="misty-card p-6">
                        <h4 className="text-md font-medium text-white mb-4">Dimensions</h4>
                        <div className="grid grid-cols-3 gap-4">
                          <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1">
                              Width (mm) *
                            </label>
                            <input
                              type="number"
                              step="0.1"
                              min="0"
                              value={formData.box_dimensions.width}
                              onChange={(e) => setFormData(prev => ({
                                ...prev,
                                box_dimensions: {
                                  ...prev.box_dimensions,
                                  width: e.target.value
                                }
                              }))}
                              className="misty-input w-full"
                              placeholder="300"
                              required
                            />
                            <div className="text-xs text-gray-400 mt-1">mmW</div>
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1">
                              Length (mm) *
                            </label>
                            <input
                              type="number"
                              step="0.1"
                              min="0"
                              value={formData.box_dimensions.length}
                              onChange={(e) => setFormData(prev => ({
                                ...prev,
                                box_dimensions: {
                                  ...prev.box_dimensions,
                                  length: e.target.value
                                }
                              }))}
                              className="misty-input w-full"
                              placeholder="200"
                              required
                            />
                            <div className="text-xs text-gray-400 mt-1">mmL</div>
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1">
                              Height (mm) *
                            </label>
                            <input
                              type="number"
                              step="0.1"
                              min="0"
                              value={formData.box_dimensions.height}
                              onChange={(e) => setFormData(prev => ({
                                ...prev,
                                box_dimensions: {
                                  ...prev.box_dimensions,
                                  height: e.target.value
                                }
                              }))}
                              className="misty-input w-full"
                              placeholder="100"
                              required
                            />
                            <div className="text-xs text-gray-400 mt-1">mmH</div>
                          </div>
                        </div>
                        {/* Dimension Preview */}
                        {(formData.box_dimensions.width || formData.box_dimensions.length || formData.box_dimensions.height) && (
                          <div className="mt-4 p-3 bg-gray-700 rounded-md">
                            <div className="text-sm text-gray-300">
                              Preview: {formData.box_dimensions.width || '0'}mmW x {formData.box_dimensions.length || '0'}mmL x {formData.box_dimensions.height || '0'}mmH
                            </div>
                          </div>
                        )}
                      </div>
                      
                      {/* Wall Thickness, Flute Type, and Supplier */}
                      <div className="misty-card p-6">
                        <h4 className="text-md font-medium text-white mb-4">Specifications</h4>
                        <div className="space-y-4">
                          <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1">
                              Wall Thickness (mm) *
                            </label>
                            <input
                              type="number"
                              step="0.1"
                              min="0"
                              value={formData.box_wall_thickness}
                              onChange={(e) => setFormData(prev => ({ ...prev, box_wall_thickness: e.target.value }))}
                              className="misty-input w-full"
                              placeholder="3.5"
                              required
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1">
                              Flute Type *
                            </label>
                            <select
                              value={formData.box_flute_type}
                              onChange={(e) => setFormData(prev => ({ ...prev, box_flute_type: e.target.value }))}
                              className="misty-select w-full"
                              required
                            >
                              <option value="">Select Flute Type</option>
                              <option value="A">A Flute (4.5-4.8mm)</option>
                              <option value="B">B Flute (2.5-3.2mm)</option>
                              <option value="C">C Flute (3.5-4.0mm)</option>
                              <option value="E">E Flute (1.1-1.9mm)</option>
                              <option value="F">F Flute (0.5-0.9mm)</option>
                              <option value="BC">BC Double Wall</option>
                              <option value="AB">AB Double Wall</option>
                              <option value="EB">EB Double Wall</option>
                            </select>
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1">
                              Supplier *
                            </label>
                            <select
                              value={formData.box_supplier}
                              onChange={(e) => setFormData(prev => ({ ...prev, box_supplier: e.target.value }))}
                              className="misty-select w-full"
                              required
                            >
                              <option value="">Select Supplier</option>
                              {/* Get unique suppliers from products data */}
                              {[...new Set(products
                                .filter(product => product.supplier && product.supplier.trim() !== '')
                                .map(product => product.supplier)
                              )].map(supplier => (
                                <option key={supplier} value={supplier}>
                                  {supplier}
                                </option>
                              ))}
                            </select>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Legacy Materials Composition - Replaced by Enhanced Material Layers Above */}
                {formData.materials_composition.length > 0 && (
                  <div className="mb-8">
                    <h3 className="text-lg font-semibold text-white mb-4">Legacy Materials Composition</h3>
                    <div className="misty-card p-4 bg-gray-700">
                      <p className="text-gray-300 text-sm mb-2">
                        This product specification contains legacy material composition data. 
                        Please use the Material Layers section above for new specifications.
                      </p>
                      <p className="text-xs text-gray-400">
                        Legacy materials: {formData.materials_composition.map(m => m.material_name).join(', ')}
                      </p>
                    </div>
                  </div>
                )}

                {/* Form Actions */}
                <div className="pt-6 border-t border-gray-700">
                  <div className="flex items-center justify-end space-x-4">
                    {selectedSpec && (
                      <button
                        type="button"
                        onClick={() => handleDelete(selectedSpec)}
                        className="misty-button misty-button-danger mr-auto"
                      >
                        <TrashIcon className="h-4 w-4 mr-2" />
                        Delete Specification
                      </button>
                    )}
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

        {/* Delete Confirmation Modal */}
        {showDeleteConfirm && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-gray-800 rounded-lg p-6 max-w-md w-full mx-4">
              <div className="flex items-center mb-4">
                <TrashIcon className="h-6 w-6 text-red-400 mr-2" />
                <h3 className="text-lg font-semibold text-white">
                  Confirm Delete
                </h3>
              </div>
              
              <p className="text-gray-300 mb-6">
                Are you sure you want to delete the specification for "{specToDelete?.product_name}"? 
                This action cannot be undone.
              </p>
              
              <div className="flex justify-end space-x-4">
                <button
                  onClick={cancelDelete}
                  className="misty-button misty-button-secondary"
                >
                  Cancel
                </button>
                <button
                  onClick={confirmDelete}
                  className="misty-button misty-button-danger"
                >
                  <TrashIcon className="h-4 w-4 mr-2" />
                  Delete
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default ProductSpecifications;