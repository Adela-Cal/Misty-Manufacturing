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
  const [suppliers, setSuppliers] = useState([]);  // Suppliers from Suppliers list
  const [machineryRates, setMachineryRates] = useState([]);  // Default machinery rates

  // Core Winding Specifications - Same data as in Machinery Specifications
  const coreWindingSpecs = [
    {
      id: 'cw_15_20',
      coreRange: '15–20 mm',
      paperWidth: '29–31 mm', 
      beltSize: '30 mm',
      recommendedAngle: '72°',
      workableRange: '70–74°',
      lengthFactor: '3.236',
      displayName: '15-20mm Core (72° angle, 29-31mm paper)'
    },
    {
      id: 'cw_21_30',
      coreRange: '21–30 mm',
      paperWidth: '37–41 mm',
      beltSize: '40 mm', 
      recommendedAngle: '70°',
      workableRange: '68–73°',
      lengthFactor: '2.924',
      displayName: '21-30mm Core (70° angle, 37-41mm paper)'
    },
    {
      id: 'cw_31_50',
      coreRange: '31–50 mm',
      paperWidth: '57–61 mm',
      beltSize: '60 mm',
      recommendedAngle: '68°', 
      workableRange: '66–72°',
      lengthFactor: '2.670',
      displayName: '31-50mm Core (68° angle, 57-61mm paper)'
    },
    {
      id: 'cw_51_70',
      coreRange: '51–70 mm',
      paperWidth: '76–81 mm',
      beltSize: '80 mm',
      recommendedAngle: '66°',
      workableRange: '64–70°', 
      lengthFactor: '2.459',
      displayName: '51-70mm Core (66° angle, 76-81mm paper)'
    },
    {
      id: 'cw_71_120',
      coreRange: '71–120 mm',
      paperWidth: '103–106 mm',
      beltSize: '105 mm',
      recommendedAngle: '65°',
      workableRange: '62–68°',
      lengthFactor: '2.366',
      displayName: '71-120mm Core (65° angle, 103-106mm paper)'
    },
    {
      id: 'cw_121_200',
      coreRange: '121–200 mm',
      paperWidth: '118–122 mm', 
      beltSize: '120 mm',
      recommendedAngle: '64°',
      workableRange: '60–66°',
      lengthFactor: '2.281',
      displayName: '121-200mm Core (64° angle, 118-122mm paper)'
    },
    {
      id: 'cw_201_plus',
      coreRange: '> 201 mm',
      paperWidth: '148–152 mm',
      beltSize: '150 mm', 
      recommendedAngle: '62°',
      workableRange: '58–65°',
      lengthFactor: '2.130',
      displayName: '> 201mm Core (62° angle, 148-152mm paper)'
    }
  ];

  // Helper function to get core winding specification details
  const getCoreWindingSpecById = (specId) => {
    return coreWindingSpecs.find(spec => spec.id === specId) || null;
  };

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
    core_winding_spec_id: '',  // Selected core winding specification
    grams_of_glue_per_layer_meter: '',  // Grams of glue per layer meter for Spiral/Composite cores
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
    box_currency: 'AUD',
    // Plastic Bags specific fields
    plastic_thickness: '',  // in μm
    plastic_composite: '',
    plastic_dimensions: {
      width: '',
      length: '',
      height: ''
    },
    plastic_supplier: '',
    plastic_price: '',
    plastic_currency: 'AUD',
    // Tapes specific fields
    tape_thickness: '',  // in μm
    tape_size: {
      width: '',
      length: ''
    },
    tape_adhesive_type: '',
    tape_substrate_type: '',
    tape_supplier: '',
    tape_price: '',
    tape_currency: 'AUD'
  });
  const [errors, setErrors] = useState({});
  const [calculatedThickness, setCalculatedThickness] = useState(0);
  const [thicknessOptions, setThicknessOptions] = useState([]);

  useEffect(() => {
    loadSpecifications();
    loadMaterials();
    loadProducts();
    loadSuppliers();
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

  const loadSuppliers = async () => {
    try {
      const response = await apiHelpers.getSuppliers();
      setSuppliers(response.data);
    } catch (error) {
      console.error('Failed to load suppliers:', error);
      toast.error('Failed to load suppliers');
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
      core_winding_spec_id: '',  // Selected core winding specification
      grams_of_glue_per_layer_meter: '',
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
      box_currency: 'AUD',
      // Plastic Bags specific fields
      plastic_thickness: '',
      plastic_composite: '',
      plastic_dimensions: {
        width: '',
        length: '',
        height: ''
      },
      plastic_supplier: '',
      plastic_price: '',
      plastic_currency: 'AUD',
      // Tapes specific fields
      tape_thickness: '',
      tape_size: {
        width: '',
        length: ''
      },
      tape_adhesive_type: '',
      tape_substrate_type: '',
      tape_supplier: '',
      tape_price: '',
      tape_currency: 'AUD'
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
      core_winding_spec_id: spec.core_winding_spec_id || '',
      grams_of_glue_per_layer_meter: spec.specifications?.grams_of_glue_per_layer_meter || '',
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
      box_currency: spec.specifications?.currency || 'AUD',
      // Plastic Bags specific fields
      plastic_thickness: spec.specifications?.thickness || '',
      plastic_composite: spec.specifications?.composite || '',
      plastic_dimensions: {
        width: spec.specifications?.dimensions?.width || '',
        length: spec.specifications?.dimensions?.length || '',
        height: spec.specifications?.dimensions?.height || ''
      },
      plastic_supplier: spec.specifications?.supplier || '',
      plastic_price: spec.specifications?.price || '',
      plastic_currency: spec.specifications?.currency || 'AUD',
      // Tapes specific fields
      tape_thickness: spec.specifications?.thickness || '',
      tape_size: {
        width: spec.specifications?.size?.width || '',
        length: spec.specifications?.size?.length || ''
      },
      tape_adhesive_type: spec.specifications?.adhesive_type || '',
      tape_substrate_type: spec.specifications?.substrate_type || '',
      tape_supplier: spec.specifications?.supplier || '',
      tape_price: spec.specifications?.price || '',
      tape_currency: spec.specifications?.currency || 'AUD'
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
        { layer_type: 'Outer Most Layer', width: '' }
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
          product_name: '',
          layer_type: 'Outer Most Layer',
          width: null,
          thickness: null,  // Don't default to 0 to avoid false calculations
          gsm: null,  // Don't default to 0 to avoid false calculations
          quantity: 1,  // Default quantity to 1
          notes: '',
          // Spiral core allocation fields
          spiral_allocation_percent: null,
          spiral_sequence: '',
          winding_direction: '',
          overlap_factor: 1.0,
          tension_level: '',
          feed_rate_mpm: null,
          qc_checkpoints: ''
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

  // Calculate automatic allocation percentage and overlap factor based on layer sequence
  const calculateSpiralAllocation = (sequence, totalLayers) => {
    const seq = parseInt(sequence);
    if (!seq || seq < 1 || seq > 5) return { allocation: null, overlap: null };
    
    // Spiral core allocation patterns based on manufacturing standards
    const allocationPatterns = {
      1: { base: 45, overlap: 1.2 }, // Inner most layer - highest allocation, more overlap for adhesion
      2: { base: 25, overlap: 1.1 }, // Second layer - medium allocation
      3: { base: 20, overlap: 1.0 }, // Third layer - standard overlap
      4: { base: 7, overlap: 0.9 },  // Fourth layer - minimal overlap
      5: { base: 3, overlap: 0.8 }   // Outer layer - least allocation, minimal overlap
    };
    
    // Adjust allocation based on total number of layers
    const pattern = allocationPatterns[seq];
    let adjustedAllocation = pattern.base;
    
    // If fewer layers, redistribute allocation
    if (totalLayers === 1) {
      adjustedAllocation = 100;
    } else if (totalLayers === 2) {
      adjustedAllocation = seq === 1 ? 70 : 30;
    } else if (totalLayers === 3) {
      const allocations = { 1: 50, 2: 30, 3: 20 };
      adjustedAllocation = allocations[seq] || pattern.base;
    }
    
    return {
      allocation: adjustedAllocation,
      overlap: pattern.overlap
    };
  };

  const handleMaterialLayerChange = (index, field, value) => {
    setFormData(prev => {
      const updatedLayers = [...prev.material_layers]; // Create a new array
      const currentLayer = { ...updatedLayers[index] }; // Create a new layer object
      
      // Update the field that was changed
      currentLayer[field] = value;
      
      // If spiral_sequence changes, automatically calculate allocation % and overlap factor
      if (field === 'spiral_sequence' && value) {
        const totalLayersWithSequence = updatedLayers.filter(layer => layer.spiral_sequence).length;
        const calculations = calculateSpiralAllocation(value, totalLayersWithSequence);
        
        if (calculations.allocation !== null) {
          currentLayer.spiral_allocation_percent = calculations.allocation;
          currentLayer.overlap_factor = calculations.overlap;
          
          // Also set some intelligent defaults based on sequence
          if (!currentLayer.winding_direction) {
            // Alternate winding direction by sequence for better spiral formation
            currentLayer.winding_direction = parseInt(value) % 2 === 1 ? 'clockwise' : 'counterclockwise';
          }
          
          if (!currentLayer.tension_level) {
            // Inner layers need higher tension, outer layers lower tension
            const tensionMap = { '1': 'high', '2': 'medium', '3': 'medium', '4': 'low', '5': 'low' };
            currentLayer.tension_level = tensionMap[value] || 'medium';
          }
          
          if (!currentLayer.feed_rate_mpm) {
            // Feed rate typically decreases for outer layers
            const feedRateMap = { '1': 15, '2': 12, '3': 10, '4': 8, '5': 6 };
            currentLayer.feed_rate_mpm = feedRateMap[value] || 10;
          }
        }
        
        console.log(`Auto-calculated for sequence ${value}:`, {
          allocation: calculations.allocation,
          overlap: calculations.overlap,
          winding: currentLayer.winding_direction,
          tension: currentLayer.tension_level,
          feedRate: currentLayer.feed_rate_mpm
        });
      }
      
      // If material_id changes, update material_name, thickness, and GSM
      if (field === 'material_id' && value) {
        // Check both materials and products for the item
        const allItems = [...materials, ...products];
        const item = allItems.find(m => m.id === value);
        
        if (item) {
          // Force update all related fields with new values
          currentLayer.material_name = item.material_description || item.product_name || item.material_name || 'Unknown Material';
          currentLayer.thickness = item.thickness_mm || item.thickness || 0;
          
          // Handle GSM - ensure it's properly set
          const gsmValue = item.gsm;
          if (gsmValue !== null && gsmValue !== undefined && gsmValue !== '') {
            currentLayer.gsm = typeof gsmValue === 'string' ? parseFloat(gsmValue) : Number(gsmValue);
          } else {
            currentLayer.gsm = null;
          }
          
          // Store product name separately for Job Card display
          currentLayer.product_name = item.material_description || item.product_name || item.material_name || 'Unknown Product';
          
          console.log('Material selection update:', {
            materialId: value,
            itemFound: !!item,
            gsmRaw: gsmValue,
            gsmProcessed: currentLayer.gsm,
            layerUpdated: currentLayer
          });
        } else {
          // Clear dependent fields if material not found
          currentLayer.material_name = 'Unknown Material';
          currentLayer.thickness = 0;
          currentLayer.gsm = null;
          currentLayer.product_name = 'Unknown Product';
        }
      }
      
      // Update the layer in the array
      updatedLayers[index] = currentLayer;
      
      return {
        ...prev,
        material_layers: updatedLayers
      };
    });
    
    // Recalculate thickness after any change
    setTimeout(() => {
      calculateTotalThickness();
    }, 0);
  };

  // Auto-balance all spiral allocations to total 100%
  const autoBalanceSpiralAllocations = () => {
    setFormData(prev => {
      const updatedLayers = [...prev.material_layers];
      const layersWithSequence = updatedLayers.filter(layer => layer.spiral_sequence);
      
      if (layersWithSequence.length === 0) return prev;
      
      // Recalculate all allocations based on sequences
      updatedLayers.forEach((layer, index) => {
        if (layer.spiral_sequence) {
          const calculations = calculateSpiralAllocation(layer.spiral_sequence, layersWithSequence.length);
          if (calculations.allocation !== null) {
            updatedLayers[index] = {
              ...layer,
              spiral_allocation_percent: calculations.allocation,
              overlap_factor: calculations.overlap
            };
          }
        }
      });
      
      // Fine-tune to ensure exactly 100% total
      const totalAllocation = updatedLayers.reduce((sum, layer) => {
        return sum + (parseFloat(layer.spiral_allocation_percent) || 0);
      }, 0);
      
      if (totalAllocation > 0 && totalAllocation !== 100) {
        const adjustmentFactor = 100 / totalAllocation;
        updatedLayers.forEach((layer, index) => {
          if (layer.spiral_allocation_percent) {
            updatedLayers[index] = {
              ...layer,
              spiral_allocation_percent: parseFloat((layer.spiral_allocation_percent * adjustmentFactor).toFixed(1))
            };
          }
        });
      }
      
      return {
        ...prev,
        material_layers: updatedLayers
      };
    });
    
    toast.success('Spiral allocations auto-balanced to 100%');
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

    // Validate Plastic Bags specific fields
    if (formData.product_type === 'Plastic Bags') {
      if (!formData.plastic_thickness || formData.plastic_thickness <= 0) {
        newErrors.plastic_thickness = 'Thickness is required';
      }
      if (!formData.plastic_composite.trim()) {
        newErrors.plastic_composite = 'Composite is required';
      }
      if (!formData.plastic_dimensions.width || formData.plastic_dimensions.width <= 0) {
        newErrors.plastic_width = 'Width is required';
      }
      if (!formData.plastic_dimensions.length || formData.plastic_dimensions.length <= 0) {
        newErrors.plastic_length = 'Length is required';
      }
      if (!formData.plastic_dimensions.height || formData.plastic_dimensions.height <= 0) {
        newErrors.plastic_height = 'Height is required';
      }
      if (!formData.plastic_supplier.trim()) {
        newErrors.plastic_supplier = 'Supplier is required';
      }
      if (!formData.plastic_price || formData.plastic_price <= 0) {
        newErrors.plastic_price = 'Price per unit is required';
      }
    }

    // Validate Tapes specific fields
    if (formData.product_type === 'Tapes') {
      if (!formData.tape_thickness || formData.tape_thickness <= 0) {
        newErrors.tape_thickness = 'Thickness is required';
      }
      if (!formData.tape_size.width || formData.tape_size.width <= 0) {
        newErrors.tape_width = 'Width is required';
      }
      if (!formData.tape_size.length || formData.tape_size.length <= 0) {
        newErrors.tape_length = 'Length is required';
      }
      if (!formData.tape_adhesive_type.trim()) {
        newErrors.tape_adhesive_type = 'Adhesive type is required';
      }
      if (!formData.tape_substrate_type.trim()) {
        newErrors.tape_substrate_type = 'Substrate type is required';
      }
      if (!formData.tape_supplier.trim()) {
        newErrors.tape_supplier = 'Supplier is required';
      }
      if (!formData.tape_price || formData.tape_price <= 0) {
        newErrors.tape_price = 'Price per unit is required';
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
        product_name: layer.product_name || layer.material_name || 'Unknown Product',
        layer_type: layer.layer_type || 'Outer Most Layer',
        thickness: parseFloat(layer.thickness) || 0,
        gsm: layer.gsm ? (typeof layer.gsm === 'string' ? parseFloat(layer.gsm) : layer.gsm) : null,
        quantity: parseFloat(layer.quantity) || 1,
        width: layer.width ? parseFloat(layer.width) : null,
        notes: layer.notes || '',
        // Spiral Core Allocation fields
        spiral_allocation_percent: layer.spiral_allocation_percent ? parseFloat(layer.spiral_allocation_percent) : null,
        spiral_sequence: layer.spiral_sequence ? parseInt(layer.spiral_sequence) : null,
        winding_direction: layer.winding_direction || null,
        overlap_factor: layer.overlap_factor ? parseFloat(layer.overlap_factor) : null
      }));

      let submitData = {
        product_name: formData.product_name,
        product_type: formData.product_type,
        specifications: formData.specifications || {},
        materials_composition: [],  // Keep empty for now
        material_layers: cleanMaterialLayers,
        machinery: formData.machinery || [],  // Include machinery data
        manufacturing_notes: formData.manufacturing_notes || '',
        selected_thickness: formData.selected_thickness || calculatedThickness,
        core_winding_spec_id: formData.core_winding_spec_id
      };

      // For Spiral Paper Cores and Composite Cores, add specific fields to specifications
      if (formData.product_type === 'Spiral Paper Core' || formData.product_type === 'Composite Core') {
        submitData.specifications = {
          ...submitData.specifications,
          internal_diameter: formData.internal_diameter ? parseFloat(formData.internal_diameter) : null,
          wall_thickness_required: formData.wall_thickness_required ? parseFloat(formData.wall_thickness_required) : null,
          selected_material_id: formData.selected_material_id || null,
          layers_required: formData.layers_required || null,
          layer_specifications: formData.layer_specifications || null,
          grams_of_glue_per_layer_meter: formData.grams_of_glue_per_layer_meter ? parseFloat(formData.grams_of_glue_per_layer_meter) : null
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
          currency: formData.pallet_currency || 'AUD',
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
          supplier: formData.box_supplier || null,
          price: formData.box_price ? parseFloat(formData.box_price) : null,
          currency: formData.box_currency || 'AUD'
        };
      }

      // For Plastic Bags, add specific fields to specifications
      if (formData.product_type === 'Plastic Bags') {
        submitData.specifications = {
          ...submitData.specifications,
          thickness: formData.plastic_thickness ? parseFloat(formData.plastic_thickness) : null,
          composite: formData.plastic_composite || null,
          dimensions: {
            width: formData.plastic_dimensions.width ? parseFloat(formData.plastic_dimensions.width) : null,
            length: formData.plastic_dimensions.length ? parseFloat(formData.plastic_dimensions.length) : null,
            height: formData.plastic_dimensions.height ? parseFloat(formData.plastic_dimensions.height) : null
          },
          supplier: formData.plastic_supplier || null,
          price: formData.plastic_price ? parseFloat(formData.plastic_price) : null,
          currency: formData.plastic_currency || 'AUD'
        };
      }

      // For Tapes, add specific fields to specifications
      if (formData.product_type === 'Tapes') {
        submitData.specifications = {
          ...submitData.specifications,
          thickness: formData.tape_thickness ? parseFloat(formData.tape_thickness) : null,
          size: {
            width: formData.tape_size.width ? parseFloat(formData.tape_size.width) : null,
            length: formData.tape_size.length ? parseFloat(formData.tape_size.length) : null
          },
          adhesive_type: formData.tape_adhesive_type || null,
          substrate_type: formData.tape_substrate_type || null,
          supplier: formData.tape_supplier || null,
          price: formData.tape_price ? parseFloat(formData.tape_price) : null,
          currency: formData.tape_currency || 'AUD'
        };
      }
      
      if (selectedSpec) {
        await apiHelpers.updateProductSpecification(selectedSpec.id, submitData);
        toast.success('Product specification updated successfully');
        
        // Sync to client products
        try {
          const syncResponse = await apiHelpers.syncProductSpecToClientProducts(selectedSpec.id);
          if (syncResponse.data?.data?.synced_count > 0) {
            toast.success(`Synced material layers to ${syncResponse.data.data.synced_count} client product(s)`);
          }
        } catch (syncError) {
          console.error('Sync warning:', syncError);
          toast.warning('Product saved but sync to client products failed');
        }
      } else {
        const createResponse = await apiHelpers.createProductSpecification(submitData);
        toast.success('Product specification created successfully');
        
        // Sync to client products if spec was created successfully
        if (createResponse.data?.data?.spec_id) {
          try {
            const syncResponse = await apiHelpers.syncProductSpecToClientProducts(createResponse.data.data.spec_id);
            if (syncResponse.data?.data?.synced_count > 0) {
              toast.success(`Synced material layers to ${syncResponse.data.data.synced_count} client product(s)`);
            }
          } catch (syncError) {
            console.error('Sync warning:', syncError);
            toast.warning('Product created but sync to client products failed');
          }
        }
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
    'Plastic Bags',
    'Tapes',
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
              placeholder=""
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="misty-input pl-16 w-full"
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

                {/* Specifications - Only show for non-Spiral Paper Core, non-Composite Core, non-Cardboard Boxes, non-Pallet, non-Plastic Bags, and non-Tapes types */}
                {formData.product_type !== 'Spiral Paper Core' && formData.product_type !== 'Composite Core' && formData.product_type !== 'Cardboard Boxes' && formData.product_type !== 'Pallet' && formData.product_type !== 'Plastic Bags' && formData.product_type !== 'Tapes' && (
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
                {(formData.product_type === 'Spiral Paper Core' || formData.product_type === 'Composite Core') && (
                  <div className="mb-8">
                    <h3 className="text-lg font-semibold text-white mb-4">Core Specifications</h3>
                    
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

                    {/* Core Winding Specification Selection */}
                    <div className="mb-6">
                      <label className="block text-sm font-medium text-gray-300 mb-1">
                        Core Winding Specification
                      </label>
                      <select
                        value={formData.core_winding_spec_id}
                        onChange={(e) => setFormData(prev => ({ 
                          ...prev, 
                          core_winding_spec_id: e.target.value
                        }))}
                        className="misty-select w-full"
                      >
                        <option value="">Select Core Winding Specification (Optional)</option>
                        {coreWindingSpecs.map(spec => (
                          <option key={spec.id} value={spec.id}>
                            {spec.displayName}
                          </option>
                        ))}
                      </select>
                      <p className="text-sm text-gray-400 mt-1">
                        Select the appropriate core winding parameters based on the core diameter range
                      </p>

                      {/* Display selected specification details */}
                      {formData.core_winding_spec_id && (
                        <div className="mt-3 p-3 bg-gray-700 rounded border border-gray-600">
                          {(() => {
                            const selectedSpec = getCoreWindingSpecById(formData.core_winding_spec_id);
                            return selectedSpec ? (
                              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 text-sm">
                                <div>
                                  <span className="text-gray-300">Paper Width:</span>
                                  <span className="text-white ml-2 font-medium">{selectedSpec.paperWidth}</span>
                                </div>
                                <div>
                                  <span className="text-gray-300">Belt Size:</span>
                                  <span className="text-white ml-2 font-medium">{selectedSpec.beltSize}</span>
                                </div>
                                <div>
                                  <span className="text-gray-300">Recommended Angle:</span>
                                  <span className="text-blue-400 ml-2 font-medium">{selectedSpec.recommendedAngle}</span>
                                </div>
                                <div>
                                  <span className="text-gray-300">Workable Range:</span>
                                  <span className="text-white ml-2 font-medium">{selectedSpec.workableRange}</span>
                                </div>
                                <div>
                                  <span className="text-gray-300">Length Factor:</span>
                                  <span className="text-white ml-2 font-mono">{selectedSpec.lengthFactor}</span>
                                </div>
                              </div>
                            ) : null;
                          })()}
                        </div>
                      )}
                    </div>

                    {/* Grams of Glue per Layer Meter */}
                    <div className="mb-6">
                      <label className="block text-sm font-medium text-gray-300 mb-1">
                        Grams of Glue per Layer Meter (g/m) *
                      </label>
                      <input
                        type="number"
                        step="0.01"
                        min="0"
                        value={formData.grams_of_glue_per_layer_meter}
                        onChange={(e) => setFormData(prev => ({ 
                          ...prev, 
                          grams_of_glue_per_layer_meter: e.target.value
                        }))}
                        className="misty-input w-full max-w-md"
                        placeholder="Enter grams of glue per layer meter"
                      />
                      <p className="text-sm text-gray-400 mt-1">
                        Specify the amount of glue used per meter of each layer (used for material cost calculations)
                      </p>
                    </div>
                  </div>
                )}

                {/* Enhanced Material Layers Section - Only show for non-Cardboard Boxes, non-Pallet, non-Plastic Bags, and non-Tapes types */}
                {formData.product_type !== 'Cardboard Boxes' && formData.product_type !== 'Pallet' && formData.product_type !== 'Plastic Bags' && formData.product_type !== 'Tapes' && (
                <div className="mb-8">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-white">Material Layers</h3>
                    <div className="flex items-center space-x-3">
                      <button
                        type="button"
                        onClick={autoBalanceSpiralAllocations}
                        className="misty-button misty-button-primary flex items-center text-sm"
                        title="Auto-calculate spiral allocations based on layer sequences"
                      >
                        <span className="mr-2">⚖️</span>
                        Auto-Balance Spiral
                      </button>
                      <button
                        type="button"
                        onClick={addMaterialLayer}
                        className="misty-button misty-button-secondary flex items-center text-sm"
                      >
                        <PlusIcon className="h-4 w-4 mr-2" />
                        Add Material Layer
                      </button>
                    </div>
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
                                      {material.material_description || material.material_name} ({material.thickness_mm || 0}mm thick, GSM: {material.gsm || 'N/A'})
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
                          {/* Product Name (Auto-populated, Read-only) */}
                          <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1">
                              Product Name
                            </label>
                            <input
                              type="text"
                              value={layer.product_name || layer.material_name || 'Not selected'}
                              className="misty-input w-full bg-gray-600"
                              placeholder="Auto-populated"
                              readOnly
                            />
                          </div>

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

                          {/* GSM (Auto-populated, Read-only) */}
                          <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1">
                              GSM
                            </label>
                            <input
                              type="text"
                              value={layer.gsm !== null && layer.gsm !== undefined ? layer.gsm : 'Not available'}
                              className="misty-input w-full bg-gray-600"
                              placeholder="Auto-populated from selected material"
                              readOnly
                            />
                          </div>

                          {/* Width Configuration - Same for all layer types */}
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
                        </div>

                        {/* Spiral Core Allocation Section */}
                        <div className="mt-4 p-3 bg-blue-900/10 border border-blue-600 rounded-lg">
                          <h5 className="text-sm font-medium text-blue-300 mb-3 flex items-center">
                            <span className="mr-2">🌀</span>
                            Spiral Core Allocation - Layer {index + 1} ({layer.layer_type})
                          </h5>
                          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                            
                            {/* Allocation Percentage */}
                            <div>
                              <label className="block text-xs font-medium text-blue-200 mb-1 flex items-center">
                                Allocation % * 
                                {layer.spiral_sequence && (
                                  <span className="ml-1 text-green-300" title="Auto-calculated based on layer sequence">
                                    ⚡
                                  </span>
                                )}
                              </label>
                              <input
                                type="number"
                                step="0.1"
                                min="0"
                                max="100"
                                value={layer.spiral_allocation_percent || ''}
                                onChange={(e) => handleMaterialLayerChange(index, 'spiral_allocation_percent', e.target.value)}
                                className={`misty-input w-full text-sm ${
                                  layer.spiral_sequence ? 'bg-green-900/20 border-green-600' : ''
                                }`}
                                placeholder="% of total"
                              />
                              <div className="text-xs text-blue-300 mt-1">
                                {layer.spiral_sequence 
                                  ? 'Auto-calculated from layer sequence' 
                                  : 'Percentage of this layer in spiral formation'
                                }
                              </div>
                            </div>

                            {/* Layer Sequence */}
                            <div>
                              <label className="block text-xs font-medium text-blue-200 mb-1">
                                Layer Sequence
                              </label>
                              <select
                                value={layer.spiral_sequence || ''}
                                onChange={(e) => handleMaterialLayerChange(index, 'spiral_sequence', e.target.value)}
                                className="misty-select w-full text-sm"
                              >
                                <option value="">Select sequence</option>
                                {Array.from({ length: formData.material_layers.length }, (_, i) => {
                                  const sequenceNumber = i + 1;
                                  const ordinalSuffix = ['th', 'st', 'nd', 'rd'][sequenceNumber % 10 > 3 ? 0 : (sequenceNumber % 100 - sequenceNumber % 10 !== 10) * sequenceNumber % 10];
                                  const label = sequenceNumber === 1 
                                    ? '1st Layer (Core contact)' 
                                    : sequenceNumber === formData.material_layers.length 
                                    ? `${sequenceNumber}${ordinalSuffix} Layer (Outer)` 
                                    : `${sequenceNumber}${ordinalSuffix} Layer`;
                                  
                                  return (
                                    <option key={sequenceNumber} value={sequenceNumber}>
                                      {label}
                                    </option>
                                  );
                                })}
                              </select>
                              <div className="text-xs text-blue-300 mt-1">
                                Order of application in spiral winding ({formData.material_layers.length} layer{formData.material_layers.length !== 1 ? 's' : ''} total)
                              </div>
                            </div>

                            {/* Winding Direction */}
                            <div>
                              <label className="block text-xs font-medium text-blue-200 mb-1">
                                Winding Direction
                              </label>
                              <select
                                value={layer.winding_direction || ''}
                                onChange={(e) => handleMaterialLayerChange(index, 'winding_direction', e.target.value)}
                                className="misty-select w-full text-sm"
                              >
                                <option value="">Select direction</option>
                                <option value="clockwise">Clockwise</option>
                                <option value="counterclockwise">Counter-clockwise</option>
                                <option value="alternating">Alternating</option>
                              </select>
                              <div className="text-xs text-blue-300 mt-1">
                                Direction of material application
                              </div>
                            </div>

                            {/* Overlap Factor */}
                            <div>
                              <label className="block text-xs font-medium text-blue-200 mb-1 flex items-center">
                                Overlap Factor
                                {layer.spiral_sequence && (
                                  <span className="ml-1 text-green-300" title="Auto-calculated based on layer sequence">
                                    ⚡
                                  </span>
                                )}
                              </label>
                              <input
                                type="number"
                                step="0.1"
                                min="0"
                                max="10"
                                value={layer.overlap_factor || ''}
                                onChange={(e) => handleMaterialLayerChange(index, 'overlap_factor', e.target.value)}
                                className={`misty-input w-full text-sm ${
                                  layer.spiral_sequence ? 'bg-green-900/20 border-green-600' : ''
                                }`}
                                placeholder="0.0 - 10.0"
                              />
                              <div className="text-xs text-blue-300 mt-1">
                                {layer.spiral_sequence 
                                  ? 'Auto-calculated from layer sequence' 
                                  : 'Material overlap multiplier (1.0 = no overlap)'
                                }
                              </div>
                            </div>
                          </div>

                          {/* Advanced Spiral Settings */}
                          <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
                            
                            {/* Tension Control */}
                            <div>
                              <label className="block text-xs font-medium text-blue-200 mb-1">
                                Tension Level
                              </label>
                              <select
                                value={layer.tension_level || ''}
                                onChange={(e) => handleMaterialLayerChange(index, 'tension_level', e.target.value)}
                                className="misty-select w-full text-sm"
                              >
                                <option value="">Select tension</option>
                                <option value="low">Low (1-3)</option>
                                <option value="medium">Medium (4-6)</option>
                                <option value="high">High (7-10)</option>
                              </select>
                            </div>

                            {/* Material Feed Rate */}
                            <div>
                              <label className="block text-xs font-medium text-blue-200 mb-1">
                                Feed Rate (m/min)
                              </label>
                              <input
                                type="number"
                                step="0.1"
                                min="0"
                                value={layer.feed_rate_mpm || ''}
                                onChange={(e) => handleMaterialLayerChange(index, 'feed_rate_mpm', e.target.value)}
                                className="misty-input w-full text-sm"
                                placeholder="Meters per minute"
                              />
                            </div>

                            {/* Quality Control Points */}
                            <div>
                              <label className="block text-xs font-medium text-blue-200 mb-1">
                                QC Check Points
                              </label>
                              <input
                                type="text"
                                value={layer.qc_checkpoints || ''}
                                onChange={(e) => handleMaterialLayerChange(index, 'qc_checkpoints', e.target.value)}
                                className="misty-input w-full text-sm"
                                placeholder="e.g., Every 10m, Visual, Thickness"
                              />
                            </div>
                          </div>
                        </div>

                        <div className="grid grid-cols-1 gap-4 mt-4">
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

                  {/* Spiral Core Allocation Summary */}
                  {formData.material_layers.length > 0 && (
                    <div className="mt-6 p-4 bg-gray-800/50 border border-gray-600 rounded-lg">
                      <h4 className="text-md font-medium text-white mb-3 flex items-center">
                        <span className="mr-2">📊</span>
                        Spiral Core Allocation Summary
                      </h4>
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {/* Allocation Breakdown */}
                        <div>
                          <h5 className="text-sm font-medium text-gray-300 mb-2">Layer Allocation Breakdown</h5>
                          <div className="space-y-2">
                            {formData.material_layers.map((layer, index) => {
                              const allocation = parseFloat(layer.spiral_allocation_percent) || 0;
                              return (
                                <div key={index} className="flex items-center justify-between text-sm">
                                  <div className="flex items-center">
                                    <div className="w-3 h-3 bg-blue-500 rounded-full mr-2"></div>
                                    <span className="text-gray-300">
                                      Layer {index + 1} ({layer.layer_type}):
                                    </span>
                                  </div>
                                  <div className="text-right">
                                    <span className={`font-medium ${allocation > 0 ? 'text-blue-300' : 'text-gray-500'}`}>
                                      {allocation.toFixed(1)}%
                                    </span>
                                    {layer.spiral_sequence && (
                                      <div className="text-xs text-gray-400">
                                        Seq: {layer.spiral_sequence}
                                      </div>
                                    )}
                                  </div>
                                </div>
                              );
                            })}
                            <div className="border-t border-gray-600 pt-2">
                              {(() => {
                                const totalAllocation = formData.material_layers.reduce((sum, layer) => {
                                  return sum + (parseFloat(layer.spiral_allocation_percent) || 0);
                                }, 0);
                                return (
                                  <div className="flex items-center justify-between text-sm font-medium">
                                    <span className="text-gray-300">Total Allocation:</span>
                                    <span className={`${
                                      Math.abs(totalAllocation - 100) < 0.1 
                                        ? 'text-green-400' 
                                        : totalAllocation > 100 
                                        ? 'text-red-400' 
                                        : 'text-yellow-400'
                                    }`}>
                                      {totalAllocation.toFixed(1)}%
                                      {Math.abs(totalAllocation - 100) < 0.1 && ' ✓'}
                                      {totalAllocation > 100 && ' ⚠️'}
                                      {totalAllocation < 100 && totalAllocation > 0 && ' ⚠️'}
                                    </span>
                                  </div>
                                );
                              })()}
                            </div>
                          </div>
                        </div>

                        {/* Formation Process Overview */}
                        <div>
                          <h5 className="text-sm font-medium text-gray-300 mb-2">Formation Process</h5>
                          <div className="space-y-2">
                            {formData.material_layers
                              .filter(layer => layer.spiral_sequence)
                              .sort((a, b) => parseInt(a.spiral_sequence) - parseInt(b.spiral_sequence))
                              .map((layer, seqIndex) => (
                                <div key={seqIndex} className="flex items-center text-xs">
                                  <div className="w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center mr-3 text-xs">
                                    {layer.spiral_sequence}
                                  </div>
                                  <div className="flex-1">
                                    <div className="text-gray-300">{layer.material_name || 'Material not selected'}</div>
                                    <div className="text-gray-500 flex items-center space-x-2">
                                      {layer.winding_direction && <span>↻ {layer.winding_direction}</span>}
                                      {layer.tension_level && <span>⚡ {layer.tension_level}</span>}
                                      {layer.overlap_factor && layer.overlap_factor !== '1' && (
                                        <span>⤴️ {layer.overlap_factor}x overlap</span>
                                      )}
                                    </div>
                                  </div>
                                </div>
                              ))
                            }
                            {formData.material_layers.filter(layer => layer.spiral_sequence).length === 0 && (
                              <div className="text-gray-500 text-xs italic">
                                No layer sequences defined yet
                              </div>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Validation Messages */}
                      {(() => {
                        const totalAllocation = formData.material_layers.reduce((sum, layer) => {
                          return sum + (parseFloat(layer.spiral_allocation_percent) || 0);
                        }, 0);
                        
                        if (totalAllocation > 100) {
                          return (
                            <div className="mt-4 p-3 bg-red-900/20 border border-red-600 rounded text-sm text-red-300">
                              ⚠️ Warning: Total allocation exceeds 100% ({totalAllocation.toFixed(1)}%). Please adjust layer percentages.
                            </div>
                          );
                        } else if (totalAllocation < 100 && totalAllocation > 0) {
                          return (
                            <div className="mt-4 p-3 bg-yellow-900/20 border border-yellow-600 rounded text-sm text-yellow-300">
                              ⚠️ Notice: Total allocation is {totalAllocation.toFixed(1)}%. Consider adding more layers or adjusting percentages to reach 100%.
                            </div>
                          );
                        } else if (Math.abs(totalAllocation - 100) < 0.1 && totalAllocation > 0) {
                          return (
                            <div className="mt-4 p-3 bg-green-900/20 border border-green-600 rounded text-sm text-green-300">
                              ✅ Perfect! Total allocation is {totalAllocation.toFixed(1)}%. Spiral core formation is properly defined.
                            </div>
                          );
                        }
                        return null;
                      })()}
                    </div>
                  )}
                </div>
                )}

                {/* Machinery Section - Only show for non-Cardboard Boxes, non-Pallet, non-Plastic Bags, and non-Tapes types */}
                {formData.product_type !== 'Cardboard Boxes' && formData.product_type !== 'Pallet' && formData.product_type !== 'Plastic Bags' && formData.product_type !== 'Tapes' && (
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
                                    <option value="winding">Core Winder</option>
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
                          {/* Price Per Unit Section */}
                          <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1">
                              Price Per Unit *
                            </label>
                            <div className="flex gap-2">
                              <select
                                value={formData.pallet_currency}
                                onChange={(e) => setFormData(prev => ({ ...prev, pallet_currency: e.target.value }))}
                                className="misty-select w-24"
                              >
                                <option value="AUD">AUD</option>
                                <option value="USD">USD</option>
                                <option value="EUR">EUR</option>
                                <option value="GBP">GBP</option>
                                <option value="NZD">NZD</option>
                                <option value="CAD">CAD</option>
                              </select>
                              <input
                                type="number"
                                step="0.01"
                                min="0"
                                value={formData.pallet_price}
                                onChange={(e) => setFormData(prev => ({ ...prev, pallet_price: e.target.value }))}
                                className="misty-input flex-1"
                                placeholder="25.00"
                                required
                              />
                            </div>
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1">
                              Supplier *
                            </label>
                            <select
                              value={formData.pallet_supplier}
                              onChange={(e) => setFormData(prev => ({ ...prev, pallet_supplier: e.target.value }))}
                              className="misty-select w-full"
                              required
                            >
                              <option value="">Select Supplier</option>
                              {suppliers.map(supplier => (
                                <option key={supplier.id} value={supplier.supplier_name}>
                                  {supplier.supplier_name}
                                </option>
                              ))}
                            </select>
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
                              {suppliers.map(supplier => (
                                <option key={supplier.id} value={supplier.supplier_name}>
                                  {supplier.supplier_name}
                                </option>
                              ))}
                            </select>
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1">
                              Price Per Unit *
                            </label>
                            <div className="flex gap-2">
                              <select
                                value={formData.box_currency}
                                onChange={(e) => setFormData(prev => ({ ...prev, box_currency: e.target.value }))}
                                className="misty-select w-24"
                              >
                                <option value="AUD">AUD</option>
                                <option value="USD">USD</option>
                                <option value="EUR">EUR</option>
                                <option value="GBP">GBP</option>
                                <option value="NZD">NZD</option>
                                <option value="CAD">CAD</option>
                              </select>
                              <input
                                type="number"
                                step="0.01"
                                min="0"
                                value={formData.box_price}
                                onChange={(e) => setFormData(prev => ({ ...prev, box_price: e.target.value }))}
                                className="misty-input flex-1"
                                placeholder="15.00"
                                required
                              />
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Plastic Bags Specifications */}
                {formData.product_type === 'Plastic Bags' && (
                  <div className="mb-8">
                    <h3 className="text-lg font-semibold text-white mb-4">Plastic Bags Specifications</h3>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      {/* Thickness and Composite */}
                      <div className="misty-card p-6">
                        <h4 className="text-md font-medium text-white mb-4">Material Properties</h4>
                        <div className="space-y-4">
                          <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1">
                              Thickness (μm) *
                            </label>
                            <input
                              type="number"
                              step="0.1"
                              min="0"
                              value={formData.plastic_thickness}
                              onChange={(e) => setFormData(prev => ({ ...prev, plastic_thickness: e.target.value }))}
                              className="misty-input w-full"
                              placeholder="25.0"
                              required
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1">
                              Composite *
                            </label>
                            <input
                              type="text"
                              value={formData.plastic_composite}
                              onChange={(e) => setFormData(prev => ({ ...prev, plastic_composite: e.target.value }))}
                              className="misty-input w-full"
                              placeholder="PE/PA/PE"
                              required
                            />
                          </div>
                        </div>
                      </div>

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
                              value={formData.plastic_dimensions.width}
                              onChange={(e) => setFormData(prev => ({
                                ...prev,
                                plastic_dimensions: {
                                  ...prev.plastic_dimensions,
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
                              value={formData.plastic_dimensions.length}
                              onChange={(e) => setFormData(prev => ({
                                ...prev,
                                plastic_dimensions: {
                                  ...prev.plastic_dimensions,
                                  length: e.target.value
                                }
                              }))}
                              className="misty-input w-full"
                              placeholder="400"
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
                              value={formData.plastic_dimensions.height}
                              onChange={(e) => setFormData(prev => ({
                                ...prev,
                                plastic_dimensions: {
                                  ...prev.plastic_dimensions,
                                  height: e.target.value
                                }
                              }))}
                              className="misty-input w-full"
                              placeholder="50"
                              required
                            />
                            <div className="text-xs text-gray-400 mt-1">mmH</div>
                          </div>
                        </div>
                        {/* Dimension Preview */}
                        {(formData.plastic_dimensions.width || formData.plastic_dimensions.length || formData.plastic_dimensions.height) && (
                          <div className="mt-4 p-3 bg-gray-700 rounded-md">
                            <div className="text-sm text-gray-300">
                              Preview: {formData.plastic_dimensions.width || '0'}mmW x {formData.plastic_dimensions.length || '0'}mmL x {formData.plastic_dimensions.height || '0'}mmH
                            </div>
                          </div>
                        )}
                      </div>

                      {/* Supplier and Price */}
                      <div className="misty-card p-6 md:col-span-2">
                        <h4 className="text-md font-medium text-white mb-4">Commercial Details</h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1">
                              Supplier *
                            </label>
                            <select
                              value={formData.plastic_supplier}
                              onChange={(e) => setFormData(prev => ({ ...prev, plastic_supplier: e.target.value }))}
                              className="misty-select w-full"
                              required
                            >
                              <option value="">Select Supplier</option>
                              {suppliers.map(supplier => (
                                <option key={supplier.id} value={supplier.supplier_name}>
                                  {supplier.supplier_name}
                                </option>
                              ))}
                            </select>
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1">
                              Price Per Unit *
                            </label>
                            <div className="flex gap-2">
                              <select
                                value={formData.plastic_currency}
                                onChange={(e) => setFormData(prev => ({ ...prev, plastic_currency: e.target.value }))}
                                className="misty-select w-24"
                              >
                                <option value="AUD">AUD</option>
                                <option value="USD">USD</option>
                                <option value="EUR">EUR</option>
                                <option value="GBP">GBP</option>
                                <option value="NZD">NZD</option>
                                <option value="CAD">CAD</option>
                              </select>
                              <input
                                type="number"
                                step="0.01"
                                min="0"
                                value={formData.plastic_price}
                                onChange={(e) => setFormData(prev => ({ ...prev, plastic_price: e.target.value }))}
                                className="misty-input flex-1"
                                placeholder="5.50"
                                required
                              />
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Tapes Specifications */}
                {formData.product_type === 'Tapes' && (
                  <div className="mb-8">
                    <h3 className="text-lg font-semibold text-white mb-4">Tapes Specifications</h3>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      {/* Thickness and Types */}
                      <div className="misty-card p-6">
                        <h4 className="text-md font-medium text-white mb-4">Material Properties</h4>
                        <div className="space-y-4">
                          <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1">
                              Thickness (μm) *
                            </label>
                            <input
                              type="number"
                              step="0.1"
                              min="0"
                              value={formData.tape_thickness}
                              onChange={(e) => setFormData(prev => ({ ...prev, tape_thickness: e.target.value }))}
                              className="misty-input w-full"
                              placeholder="50.0"
                              required
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1">
                              Adhesive Type *
                            </label>
                            <select
                              value={formData.tape_adhesive_type}
                              onChange={(e) => setFormData(prev => ({ ...prev, tape_adhesive_type: e.target.value }))}
                              className="misty-select w-full"
                              required
                            >
                              <option value="">Select Adhesive Type</option>
                              <option value="Acrylic">Acrylic</option>
                              <option value="Hot Melt">Hot Melt</option>
                              <option value="Rubber">Rubber</option>
                              <option value="Silicone">Silicone</option>
                              <option value="Water-based">Water-based</option>
                              <option value="Solvent-based">Solvent-based</option>
                            </select>
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1">
                              Substrate Type *
                            </label>
                            <select
                              value={formData.tape_substrate_type}
                              onChange={(e) => setFormData(prev => ({ ...prev, tape_substrate_type: e.target.value }))}
                              className="misty-select w-full"
                              required
                            >
                              <option value="">Select Substrate Type</option>
                              <option value="Paper">Paper</option>
                              <option value="Film">Film</option>
                              <option value="Fabric">Fabric</option>
                              <option value="Foam">Foam</option>
                              <option value="Metal">Metal</option>
                              <option value="Glass">Glass</option>
                              <option value="Plastic">Plastic</option>
                            </select>
                          </div>
                        </div>
                      </div>

                      {/* Size */}
                      <div className="misty-card p-6">
                        <h4 className="text-md font-medium text-white mb-4">Size</h4>
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1">
                              Width (mm) *
                            </label>
                            <input
                              type="number"
                              step="0.1"
                              min="0"
                              value={formData.tape_size.width}
                              onChange={(e) => setFormData(prev => ({
                                ...prev,
                                tape_size: {
                                  ...prev.tape_size,
                                  width: e.target.value
                                }
                              }))}
                              className="misty-input w-full"
                              placeholder="25"
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
                              value={formData.tape_size.length}
                              onChange={(e) => setFormData(prev => ({
                                ...prev,
                                tape_size: {
                                  ...prev.tape_size,
                                  length: e.target.value
                                }
                              }))}
                              className="misty-input w-full"
                              placeholder="50000"
                              required
                            />
                            <div className="text-xs text-gray-400 mt-1">mmL</div>
                          </div>
                        </div>
                        {/* Size Preview */}
                        {(formData.tape_size.width || formData.tape_size.length) && (
                          <div className="mt-4 p-3 bg-gray-700 rounded-md">
                            <div className="text-sm text-gray-300">
                              Preview: {formData.tape_size.width || '0'}mmW x {formData.tape_size.length || '0'}mmL
                            </div>
                          </div>
                        )}
                      </div>

                      {/* Supplier and Price */}
                      <div className="misty-card p-6 md:col-span-2">
                        <h4 className="text-md font-medium text-white mb-4">Commercial Details</h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1">
                              Supplier *
                            </label>
                            <select
                              value={formData.tape_supplier}
                              onChange={(e) => setFormData(prev => ({ ...prev, tape_supplier: e.target.value }))}
                              className="misty-select w-full"
                              required
                            >
                              <option value="">Select Supplier</option>
                              {suppliers.map(supplier => (
                                <option key={supplier.id} value={supplier.supplier_name}>
                                  {supplier.supplier_name}
                                </option>
                              ))}
                            </select>
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1">
                              Price Per Unit *
                            </label>
                            <div className="flex gap-2">
                              <select
                                value={formData.tape_currency}
                                onChange={(e) => setFormData(prev => ({ ...prev, tape_currency: e.target.value }))}
                                className="misty-select w-24"
                              >
                                <option value="AUD">AUD</option>
                                <option value="USD">USD</option>
                                <option value="EUR">EUR</option>
                                <option value="GBP">GBP</option>
                                <option value="NZD">NZD</option>
                                <option value="CAD">CAD</option>
                              </select>
                              <input
                                type="number"
                                step="0.01"
                                min="0"
                                value={formData.tape_price}
                                onChange={(e) => setFormData(prev => ({ ...prev, tape_price: e.target.value }))}
                                className="misty-input flex-1"
                                placeholder="12.50"
                                required
                              />
                            </div>
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